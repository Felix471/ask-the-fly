# SPDX-License-Identifier: MIT
"""M1i run a: unchanged M1 trial implementation and A-D/S evaluators."""
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
from sim.malecns import fbm_adapter as adapter, phase0, rescale, split
from sim.malecns.substrate import DATA, ROOT, file_record, write_json

OUT = DATA / 'runs/m1i/a'


def expected_protocol():
    return adapter.expected_protocol('a')


def validate_protocol(p):
    return adapter.validate_protocol('a', p)


def init_worker():
    model, p, cells, monitor = adapter.build('a')
    phase0._MODEL, phase0._PROTOCOL, phase0._CELLS = model, p, cells
    phase0._POISSON_MONITOR = monitor
    phase0._BODY_IDS = np.array([model.i2flyid[i] for i in range(len(model.i2flyid))], dtype='int64')
    phase0.OUT = OUT


def run(host_free_kib):
    plan, memory = adapter.check_plan('a', host_free_kib)
    OUT.mkdir(parents=True)
    started = time.perf_counter()
    meta = {'stage': 'M1i a', 'started_utc': datetime.now(timezone.utc).isoformat(),
            'sources': plan['sources'], 'plan': file_record(adapter.plan_path('a')), 'memory': memory,
            'python': sys.version, 'brian2': __import__('brian2').__version__, 'codegen': 'cython'}
    write_json(OUT / 'run_meta_start.json', meta)
    results = []
    with ProcessPoolExecutor(max_workers=memory['workers'], mp_context=mp.get_context('spawn'), initializer=init_worker) as pool:
        futures = [pool.submit(phase0.run_condition, c) for c in plan['conditions']]
        for future in as_completed(futures):
            result = future.result()
            for row in result['rows']:
                with np.load(ROOT / row['spikes']['path'], allow_pickle=False) as z:
                    row['neurons_fired'] = int(len(np.unique(z['body_id'])))
            results.append(result)
    for source in plan['sources']:
        adapter.check_file(source)
    # rescale.summarize imports phase0.summary_from_rows/evaluate_gates unchanged.
    compact = rescale.summarize(results)
    compact['shape_gate'] = split.shape_gate(compact['conditions'])
    compact['overall_primary'] = compact['gates']['L']['overall'] and compact['shape_gate']['S']
    meta.update(completed_utc=datetime.now(timezone.utc).isoformat(), walltime_s=time.perf_counter() - started,
                total_trials=480, peak_worker_rss_gib=max(t['worker_peak_rss_kib'] for r in results for t in r['rows']) / 1024**2)
    compact['metadata'] = meta
    write_json(OUT / 'full_results.json', dict(compact, raw=results))
    compact['raw_ledger'] = file_record(OUT / 'full_results.json')
    write_json(DATA / 'm1i_a_results.json', compact)


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
        print(json.dumps(adapter.check('a'), indent=2))
    elif args.plan:
        print(json.dumps(adapter.make_plan('a', args.host_free_kib), indent=2))
    else:
        if sys.platform != 'linux':
            parser.error('--run requires WSL')
        run(args.host_free_kib)


if __name__ == '__main__':
    main()
