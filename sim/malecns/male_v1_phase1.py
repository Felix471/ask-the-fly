# SPDX-License-Identifier: MIT
"""Male-v1 Phase 1: exactly 35 conditions x 30 trials; no retry or resume."""
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
import multiprocessing as mp
import os
from pathlib import Path
import sys
import time
if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import json
import numpy as np
from sim.malecns import male_v1_adapter as adapter
from sim.malecns.substrate import DATA, ROOT, file_record, write_json

OUT = DATA / 'runs/male_v1/phase1'
RESULT = DATA / 'male_v1_phase1_results.json'


def event_readouts(body, times, p, slots):
    duration = p['trial']['duration_ms'] / 1000
    ids, counts = np.unique(body, return_counts=True)
    lookup = dict(zip(ids, counts))
    row = dict(whole_network_spikes=len(body), neurons_fired=len(ids),
               source_spike_counts=[int(lookup.get(b, 0)) for b in slots])
    groups = dict(L=[p['readout']['primary']], R=[p['readout']['secondary']], **p['readout']['extra_readouts'])
    for group, bodies in groups.items():
        values = []
        for b in bodies:
            ts = times[body == b]
            key = group if group in ('L', 'R') else f'{group}_{b}'
            row[key + '_hz'] = len(ts) / duration
            row[key + '_latency_ms'] = float(ts[0] * 1000) if len(ts) else None
            values.append(row[key + '_hz'])
        if group not in ('L', 'R'):
            row[group + '_hz'] = float(np.mean(values))
            ts = times[np.isin(body, bodies)]
            row[group + '_latency_ms'] = float(ts[0] * 1000) if len(ts) else None
    return row


def init_worker():
    global _MODEL, _P, _CELLS, _MONITOR, _BODY, _SLOTS
    _MODEL, _P, _CELLS, _MONITOR = adapter.build()
    _BODY = np.array([_MODEL.i2flyid[i] for i in range(len(_MODEL.i2flyid))], dtype='int64')
    _SLOTS = [b for c in adapter.CHANNELS for b in _CELLS['sets'][c]['ids']]


def run_condition(condition):
    import resource
    from brian2 import ms, second, seed
    out = OUT / condition['id']
    out.mkdir()
    rows = []
    for trial, trial_seed in enumerate(adapter.SEEDS):
        before = time.perf_counter()
        _MODEL.net.restore('init')
        _MODEL.set_rates({c: condition[c + '_hz'] for c in adapter.CHANNELS})
        seed(trial_seed)
        _MODEL.net.run(_P['trial']['duration_ms'] * ms)
        body = _BODY[np.asarray(_MODEL.monitor.i[:], dtype='int32')]
        times = np.asarray(_MODEL.monitor.t[:] / second, dtype=float)
        elapsed = time.perf_counter() - before
        path = out / f'trial_{trial:02d}.npz'
        with path.open('xb') as stream:
            np.savez_compressed(stream, body_id=body, time_s=times,
                                poisson_index=np.asarray(_MONITOR.i[:], dtype='int32'),
                                poisson_time_s=np.asarray(_MONITOR.t[:] / second, dtype=float))
        row = dict(condition=condition['id'], trial=trial, seed=trial_seed, trial_wall_s=elapsed,
                   worker_peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                   spikes=file_record(path), **event_readouts(body, times, _P, _SLOTS))
        write_json(path.with_suffix('.json'), row)
        rows.append(row)
    result = dict(condition=condition, rows=rows, pid=os.getpid())
    write_json(out / 'condition_ledger.json', result)
    return result


def derived_tables(rows):
    by_id = {r['id']: r for r in rows}
    tables = {}
    fields = ('L_mean','L_sd','R_mean','R_sd','mn11d_mean','mn11d_sd','mn11v_mean','mn11v_sd',
              'cem_mean','cem_sd','whole_network_spikes_median')
    for channel, levels in [('water', (0,60,180,240)), ('ir94e', (0,60,120,200))]:
        table = []
        for sugar in (0,60,80,120,200):
            for level in levels:
                cid = f's{sugar}_b0_w{level if channel == "water" else 0}_i{level if channel == "ir94e" else 0}'
                r = by_id[cid]
                table.append(dict(id=cid,sugar_hz=sugar,**{channel+'_hz':level},**{k:r[k] for k in fields}))
        tables[channel+'_alone'] = [r for r in table if r['sugar_hz'] == 0]
        tables[channel+'_x_sugar'] = table
    return tables


def summarize(results, p):
    expected = adapter.conditions(p)
    groups = {r['condition']['id']:r for r in results}
    if len(groups) != len(results) or set(groups) != {c['id'] for c in expected}:
        raise ValueError('Incorrect condition inventory')
    summary = []
    for c in expected:
        g = groups[c['id']]
        trials = g['rows']
        if (g['condition'] != c or len(trials) != 30 or [r['trial'] for r in trials] != list(range(30))
                or [r['seed'] for r in trials] != adapter.SEEDS or any(r['condition'] != c['id'] for r in trials)):
            raise ValueError('Incorrect condition/trial/seed ledger')
        row = dict(c)
        for key in trials[0]:
            if not key.endswith('_hz'):
                continue
            prefix = key[:-3]
            values = [r[key] for r in trials]
            latencies = [r[prefix+'_latency_ms'] for r in trials if r[prefix+'_latency_ms'] is not None]
            row.update({prefix+'_mean':float(np.mean(values)), prefix+'_sd':float(np.std(values, ddof=0)),
                        prefix+'_firing_trials':sum(v > 0 for v in values),
                        prefix+'_latency_median_ms':float(np.median(latencies)) if latencies else None})
        for key in ('whole_network_spikes', 'neurons_fired'):
            values = [r[key] for r in trials]
            row.update({key+'_median':float(np.median(values)), key+'_min':min(values), key+'_max':max(values)})
        summary.append(row)
    return dict(conditions=summary, tables=derived_tables(summary))


def run(host_free_kib):
    if sys.platform != 'linux':
        raise RuntimeError('--run requires WSL flybrain')
    if OUT.exists() or RESULT.exists():
        raise FileExistsError('Phase 1 outputs exist; no retry, resume or overwrite')
    plan, memory = adapter.check_plan(host_free_kib)
    OUT.mkdir(parents=True)
    started = time.perf_counter()
    meta = dict(stage='male-v1 Phase 1', started_utc=datetime.now(timezone.utc).isoformat(),
                sources=plan['sources'], plan=file_record(adapter.PLAN), memory=memory,
                python=sys.version, brian2=__import__('brian2').__version__, codegen='cython')
    write_json(OUT / 'run_meta_start.json', meta)
    results = []
    with ProcessPoolExecutor(max_workers=memory['workers'], mp_context=mp.get_context('spawn'), initializer=init_worker) as pool:
        futures = [pool.submit(run_condition, c) for c in plan['conditions']]
        for future in as_completed(futures):
            results.append(future.result())
            print(f'Completed {len(results)}/35 conditions', flush=True)
    for record in plan['sources'] + [meta['plan']]:
        adapter.check_file(record)
    results.sort(key=lambda r: next(i for i,c in enumerate(plan['conditions']) if c['id'] == r['condition']['id']))
    compact = summarize(results, adapter.read(adapter.PROTOCOL))
    meta.update(completed_utc=datetime.now(timezone.utc).isoformat(), walltime_s=time.perf_counter()-started,
                total_trials=1050, peak_worker_rss_gib=max(t['worker_peak_rss_kib'] for r in results for t in r['rows'])/1024**2)
    compact['metadata'] = meta
    write_json(OUT / 'full_results.json', dict(compact, raw=results))
    compact['raw_ledger'] = file_record(OUT / 'full_results.json')
    write_json(RESULT, compact)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    for name in ('check', 'plan', 'run'):
        modes.add_argument('--'+name, action='store_true')
    parser.add_argument('--host-free-kib', type=int)
    args = parser.parse_args()
    if not args.check and (args.host_free_kib is None or args.host_free_kib <= 0):
        parser.error('--plan and --run require positive --host-free-kib measured on Windows')
    if args.check:
        print(json.dumps(adapter.check(), indent=2))
    elif args.plan:
        print(json.dumps(adapter.make_plan(args.host_free_kib), indent=2))
    else:
        run(args.host_free_kib)


if __name__ == '__main__':
    main()
