# SPDX-License-Identifier: MIT
"""M1i run b: 242 physical inputs, 90 replication and five paired KC trials."""
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
import json
import multiprocessing as mp
import os
from pathlib import Path
import sys
import time
if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import numpy as np
from sim.malecns import fbm_adapter as adapter, phase0
from sim.malecns.substrate import DATA, file_record, write_json

OUT = DATA / 'runs/m1i/b'


def expected_protocol():
    return adapter.expected_protocol('b')


def validate_protocol(p):
    return adapter.validate_protocol('b', p)


def bilateral_metrics(body, times):
    selected = times[np.isin(body, [10331, 16949])]
    bins = np.histogram(selected, bins=np.linspace(0, 1, 21))[0] / (2 * .05)
    return {'bilateral_mean_hz': len(selected) / 2., 'bilateral_bin_hz': bins.tolist()}


def run_condition(condition):
    import resource
    from brian2 import Hz, ms, second, seed as brian_seed
    model, p, cells, monitor = adapter.build('b', kc=condition['id'] == 'fbm_sugar_kc')
    body_ids = np.array([model.i2flyid[i] for i in range(len(model.i2flyid))], dtype='int64')
    rates = np.array([condition['rates_hz'][name] for name in adapter.CHANNELS_B
                      for _ in cells['sets'][name]['ids']], dtype=float)
    out = OUT / condition['id']
    out.mkdir()
    rows = []
    for trial, seed in enumerate(condition['seeds']):
        before = time.perf_counter()
        model.net.restore('m1_init')
        model.set_rates(condition['rates_hz'])
        model.poisson.rates = rates * Hz
        model.neurons.rfc[model.target_indices] = model.t_rfc
        model.neurons.rfc[model.target_indices[rates > 0]] = 0 * ms
        brian_seed(seed)
        model.net.run(p['trial']['duration_ms'] * ms)
        indices = np.asarray(model.monitor.i[:], dtype='int32')
        times = np.asarray(model.monitor.t[:] / second, dtype=float)
        body = body_ids[indices]
        path = out / f'trial_{trial:02d}.npz'
        with path.open('xb') as stream:
            np.savez_compressed(stream, body_id=body, time_s=times,
                                poisson_index=np.asarray(monitor.i[:], dtype='int32'),
                                poisson_time_s=np.asarray(monitor.t[:] / second, dtype=float))
        counts = np.bincount(indices, minlength=len(body_ids))
        row = {'condition': condition['id'], 'trial': trial, 'seed': seed,
               'trial_wall_s': time.perf_counter() - before,
               'worker_peak_rss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
               'whole_network_spikes': len(times), 'source_spike_counts': counts[model.target_indices].tolist(),
               'spikes': file_record(path), **bilateral_metrics(body, times)}
        for side, root in phase0.SIDES.items():
            st = times[body == root]
            row[f'{side}_hz'] = len(st) / (p['trial']['duration_ms'] / 1000)
            row[f'{side}_latency_ms'] = float(st[0] * 1000) if len(st) else None
        write_json(out / f'trial_{trial:02d}.json', row)
        rows.append(row)
    return {'condition': condition, 'rows': rows, 'pid': os.getpid()}


def stats(values):
    return {'min': float(np.min(values)), 'median': float(np.median(values)), 'max': float(np.max(values))}


def summarize(results):
    protocol = expected_protocol()
    byid = {r['condition']['id']: r for r in results}
    if len(results) != 4 or set(byid) != {c['id'] for c in protocol['conditions']}:
        raise ValueError('Incomplete/duplicate replication conditions')
    summary = []
    for condition in protocol['conditions']:
        result = byid[condition['id']]
        rows = sorted(result['rows'], key=lambda r: r['trial'])
        if result['condition'] != condition or [r['trial'] for r in rows] != list(range(condition['n_trials'])) or [r['seed'] for r in rows] != condition['seeds']:
            raise ValueError('Replication condition/trial/seed mismatch')
        item = dict(condition)
        for key in ('L_hz', 'R_hz', 'bilateral_mean_hz'):
            values = [r[key] for r in rows]
            item[key] = {'mean': float(np.mean(values)), 'sd': float(np.std(values)), 'positive_trials': sum(x > 0 for x in values)}
        for side in phase0.SIDES:
            latencies = [r[f'{side}_latency_ms'] for r in rows if r[f'{side}_latency_ms'] is not None]
            item[f'{side}_latency_median_ms'] = float(np.median(latencies)) if latencies else None
        item['bilateral_bin_hz'] = stats([value for r in rows for value in r['bilateral_bin_hz']])
        item['whole_network_spikes'] = stats([r['whole_network_spikes'] for r in rows])
        summary.append(item)
    sugar = summary[0]['bilateral_mean_hz']
    criteria = {'fbm_sugar': 30 <= sugar['mean'] <= 90 and sugar['positive_trials'] == 30}
    for name in ('fbm_bitter', 'fbm_both'):
        criteria[name] = all(r['L_hz'] == r['R_hz'] == 0 for r in byid[name]['rows'])
    paired = {}
    sugar_rows = sorted(byid['fbm_sugar']['rows'], key=lambda r: r['trial'])[:5]
    kc_rows = sorted(byid['fbm_sugar_kc']['rows'], key=lambda r: r['trial'])
    for key in ('L_hz', 'R_hz', 'bilateral_mean_hz'):
        values = [b[key] - a[key] for a, b in zip(sugar_rows, kc_rows)]
        paired[key] = {'differences': values, 'mean': float(np.mean(values)), 'sd': float(np.std(values))}
    return {'conditions': summary, 'replication_criteria': criteria,
            'kc_paired_difference': {'definition': 'KC minus unscaled, seeds 20260910-20260914', 'criterion': None, 'metrics': paired}}


def run(host_free_kib):
    plan, memory = adapter.check_plan('b', host_free_kib)
    OUT.mkdir(parents=True)
    started = time.perf_counter()
    meta = {'stage': 'M1i b', 'started_utc': datetime.now(timezone.utc).isoformat(),
            'sources': plan['sources'], 'plan': file_record(adapter.plan_path('b')), 'memory': memory,
            'python': sys.version, 'brian2': __import__('brian2').__version__, 'codegen': 'cython'}
    write_json(OUT / 'run_meta_start.json', meta)
    results = []
    # Each task constructs one graph; KC therefore never shares an unscaled network.
    with ProcessPoolExecutor(max_workers=min(4, memory['workers']), mp_context=mp.get_context('spawn')) as pool:
        futures = [pool.submit(run_condition, c) for c in plan['conditions']]
        for future in as_completed(futures):
            results.append(future.result())
    for source in plan['sources']:
        adapter.check_file(source)
    compact = summarize(results)
    meta.update(completed_utc=datetime.now(timezone.utc).isoformat(), walltime_s=time.perf_counter() - started,
                total_trials=95, peak_worker_rss_gib=max(t['worker_peak_rss_kib'] for r in results for t in r['rows']) / 1024**2)
    compact['metadata'] = meta
    write_json(OUT / 'full_results.json', dict(compact, raw=results))
    compact['raw_ledger'] = file_record(OUT / 'full_results.json')
    write_json(DATA / 'm1i_b_results.json', compact)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    for name in ('check', 'plan', 'run'):
        modes.add_argument('--' + name, action='store_true')
    parser.add_argument('--host-free-kib', type=int)
    args = parser.parse_args()
    if not args.check and args.host_free_kib is None:
        parser.error('--plan and --run require --host-free-kib measured on Windows')
    if args.check:
        print(json.dumps(adapter.check('b'), indent=2))
    elif args.plan:
        print(json.dumps(adapter.make_plan('b', args.host_free_kib), indent=2))
    else:
        if sys.platform != 'linux':
            parser.error('--run requires WSL')
        run(args.host_free_kib)


if __name__ == '__main__':
    main()
