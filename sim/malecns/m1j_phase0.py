# SPDX-License-Identifier: MIT
"""M1j male runner and shared execution, preserving the M1 trial routine."""
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
import json
import multiprocessing as mp
from pathlib import Path
import sys
import time
if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import numpy as np
from sim.malecns import m1j_adapter as adapter, phase0, rescale, split
from sim.malecns.substrate import DATA, ROOT, file_record, write_json

OUT = DATA / 'runs/m1j/male'


def output_path(brain):
    return OUT if brain == 'male' else ROOT / 'results/m1j/female'


def result_path(brain):
    return DATA / 'm1j_male_results.json' if brain == 'male' else ROOT / 'data/m1j_female_results.json'


def init_worker(brain='male'):
    model, p, cells, monitor = adapter.build(brain)
    phase0._MODEL, phase0._PROTOCOL, phase0._CELLS = model, p, cells
    phase0._POISSON_MONITOR = monitor
    phase0._BODY_IDS = np.array([model.i2flyid[i] for i in range(len(model.i2flyid))], dtype='int64')
    # Process-local bindings only; the frozen module on disk remains unchanged.
    phase0.SIDES = {'L': p['readout']['primary'], 'R': p['readout']['secondary']}
    phase0.OUT = output_path(brain)


def run_condition(condition):
    result = phase0.run_condition(condition)
    for row in result['rows']:
        with np.load(ROOT / row['spikes']['path'], allow_pickle=False) as z:
            row['neurons_fired'] = int(len(np.unique(z['body_id'])))
    # Preserve the write-once historical per-trial JSON; extended rows live in
    # this separate condition ledger and the final full ledger.
    write_json(phase0.OUT / condition['id'] / 'condition_ledger.json', result)
    return result


def summarize(results):
    compact = rescale.summarize(results)
    for value in compact['a_prime'].values():
        value['difference_definition'] = 'Bilateral LB3c subset minus bilateral LB3b union LB3c, paired by seed'
    compact['shape_gate'] = split.shape_gate(compact['conditions'])
    compact['overall_primary'] = compact['gates']['L']['overall'] and compact['shape_gate']['S']
    return compact


def run(host_free_kib, brain='male'):
    adapter.require_m0()
    if sys.platform != 'linux':
        raise RuntimeError('--run requires WSL flybrain')
    out, target = output_path(brain), result_path(brain)
    if out.exists() or target.exists():
        raise FileExistsError('M1j outputs exist; no retry, resume or overwrite')
    plan, memory = adapter.check_plan(brain, host_free_kib)
    m0_record = adapter.require_m0()
    out.mkdir(parents=True)
    started = time.perf_counter()
    meta = {'stage': 'M1j', 'brain': brain, 'started_utc': datetime.now(timezone.utc).isoformat(),
            'sources': plan['sources'], 'plan': file_record(adapter.plan_path(brain)), 'memory': memory,
            'm0_recheck': m0_record, 'readouts': plan['readouts'],
            'python': sys.version, 'brian2': __import__('brian2').__version__, 'codegen': 'cython'}
    write_json(out / 'run_meta_start.json', meta)
    results = []
    with ProcessPoolExecutor(max_workers=memory['workers'], mp_context=mp.get_context('spawn'),
                             initializer=init_worker, initargs=(brain,)) as pool:
        futures = [pool.submit(run_condition, c) for c in plan['conditions']]
        for future in as_completed(futures):
            results.append(future.result())
    for source in plan['sources'] + [m0_record, meta['plan']]:
        adapter.check_file(source)
    compact = summarize(results)
    meta.update(completed_utc=datetime.now(timezone.utc).isoformat(), walltime_s=time.perf_counter() - started,
                total_trials=480, peak_worker_rss_gib=max(t['worker_peak_rss_kib'] for r in results for t in r['rows']) / 1024**2)
    compact['metadata'] = meta
    write_json(out / 'full_results.json', dict(compact, raw=results))
    compact['raw_ledger'] = file_record(out / 'full_results.json')
    write_json(target, compact)


def main(brain='male'):
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    for name in ('check', 'plan', 'run'):
        modes.add_argument('--' + name, action='store_true')
    parser.add_argument('--host-free-kib', type=int)
    args = parser.parse_args()
    if not args.check and (args.host_free_kib is None or args.host_free_kib <= 0):
        parser.error('--plan and --run require positive --host-free-kib measured on Windows')
    try:
        if args.check:
            print(json.dumps(adapter.check(brain), indent=2))
        elif args.plan:
            print(json.dumps(adapter.make_plan(brain, args.host_free_kib), indent=2))
        else:
            run(args.host_free_kib, brain)
    except (ValueError, OSError, RuntimeError) as exc:
        parser.exit(1, f'M1j: {exc}\n')


if __name__ == '__main__':
    main()
