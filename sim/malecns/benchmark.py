# SPDX-License-Identifier: MIT
"""M0 only: two fresh sequential workers, five baseline and five sugar200 trials.

python -m sim.malecns.benchmark --run
No M1/M2 conditions are available here. Artifacts are never overwritten.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

import numpy as np

from sim.malecns.substrate import DATA, ROOT, file_record, write_json, verify_record

CONDITIONS = {'baseline': 0, 'sugar200': 200}


def summarise(rows):
    result = {}
    for name in CONDITIONS:
        trials = [r for r in rows if r['condition'] == name]
        if len(trials) != 5 or sorted(r['trial'] for r in trials) != list(range(5)):
            raise ValueError(f'expected exactly five distinct {name} trials')
        if [r['seed'] for r in sorted(trials, key=lambda x: x['trial'])] != list(range(20260910, 20260915)):
            raise ValueError('benchmark seeds differ from protocol')
        times = np.array([r['trial_wall_s'] for r in trials])
        result[name] = {'trials': 5, 'per_trial_wall_s': times.tolist(), 'mean_wall_s': float(times.mean()),
                        'sd_wall_s': float(times.std(ddof=0)), 'median_wall_s': float(np.median(times)),
                        'min_wall_s': float(times.min()), 'max_wall_s': float(times.max()),
                        'peak_worker_rss_gib': max(r['peak_worker_rss_kib'] for r in trials) / 1024**2}
        for key in ('MN9_R_primary_hz', 'MN9_L_secondary_hz', 'driven_sugar_mean_hz'):
            values = [r[key] for r in trials if r[key] is not None]
            result[name][key] = {'mean': float(np.mean(values)), 'sd': float(np.std(values, ddof=0))} if values else None
    return result


def worker(name):
    import resource
    from sim.malecns.adapter import build_male_network
    from brian2 import __version__ as brian_version, second
    started = time.perf_counter()
    model, protocol, cells = build_male_network(verify=False)  # Parent checks all hashes before launch.
    build_s = time.perf_counter() - started
    # Zero-duration preparation compiles code but does not simulate a timestep or an extra trial.
    compile_start = time.perf_counter()
    model.net.run(0 * second)
    prepare_s = time.perf_counter() - compile_start
    out = DATA / 'runs/m0' / name
    out.mkdir()
    rows = []
    print(f'{name}: build {build_s:.2f}s, zero-duration compile/preparation {prepare_s:.2f}s', flush=True)
    for trial in range(5):
        seed = 20260910 + trial
        before = time.perf_counter()
        spikes = model.run_trial({'sugar': CONDITIONS[name], 'bitter': 0, 'water': 0, 'ir94e': 0},
                                 seed, protocol['trial']['duration_ms'])
        elapsed = time.perf_counter() - before
        # Linux ru_maxrss: lifetime high-water RSS of this Python worker, in KiB.
        peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        rates = {i: len(spikes.get(i, ())) / (protocol['trial']['duration_ms'] / 1000) for i in (16949, 10331)}
        for times in spikes.values():
            if not np.isfinite(times).all() or (times < 0).any() or (times >= 1).any() or (np.diff(times) < 0).any():
                raise ValueError('invalid recorded spike times')
        spike_file = out / f'trial_{trial:02d}.npz'
        with spike_file.open('xb') as f:
            np.savez_compressed(f, **{str(i): times for i, times in spikes.items()})
        row = {'condition': name, 'trial': trial, 'seed': seed, 'sugar_hz': CONDITIONS[name],
               'trial_wall_s': elapsed, 'peak_worker_rss_kib': peak,
               'MN9_R_primary_hz': rates[16949], 'MN9_L_secondary_hz': rates[10331],
               'MN9_R_latency_ms': float(spikes[16949][0] * 1000) if 16949 in spikes else None,
               'MN9_L_latency_ms': float(spikes[10331][0] * 1000) if 10331 in spikes else None,
               'driven_sugar_mean_hz': float(np.mean([len(spikes.get(i, ())) for i in cells['sets']['sugar']['ids']])) if CONDITIONS[name] else None,
               'whole_network_spikes': sum(len(x) for x in spikes.values()), 'spikes': file_record(spike_file)}
        write_json(out / f'trial_{trial:02d}.json', row)
        rows.append(row)
        print(f'{name} trial {trial+1}/5: {elapsed:.3f}s, peak {peak/1024**2:.3f}GiB, '
              f'MN9 R/L {rates[16949]:.0f}/{rates[10331]:.0f}Hz', flush=True)
    result = {'condition': name, 'build_wall_s': build_s, 'zero_duration_prepare_s': prepare_s,
              'peak_worker_rss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
              'brian2': brian_version, 'pid': os.getpid(), 'rows': rows}
    write_json(out / 'worker.json', result)


def run():
    if sys.platform != 'linux':
        raise RuntimeError('Benchmark requires WSL2 Linux, not native Windows')
    verify_record()
    out = DATA / 'runs/m0'
    if out.exists() or (DATA / 'benchmark_m0.json').exists():
        raise FileExistsError('M0 outputs already exist; no implicit rerun or overwrite')
    out.mkdir(parents=True)
    source_files = ['sim/malecns/adapter.py', 'sim/malecns/benchmark.py', 'sim/malecns/substrate.py',
                    'sim/network.py', 'data/malecns/substrate_record.json', 'data/stim_protocol.json']
    provenance = [file_record(ROOT / p) for p in source_files]
    started = time.perf_counter()
    children = []
    for name in CONDITIONS:
        subprocess.run([sys.executable, '-B', '-m', 'sim.malecns.benchmark', '--worker', name],
                       cwd=ROOT, check=True)
        children.append(json.loads((out / name / 'worker.json').read_text(encoding='utf-8')))
    rows = [r for c in children for r in c['rows']]
    if provenance != [file_record(ROOT / p) for p in source_files]:
        raise ValueError('Source changed during benchmark')
    result = {'stage': 'M0', 'completed_utc': datetime.now(timezone.utc).isoformat(),
              'git_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
              'platform': platform.platform(), 'python': sys.version, 'brian2': children[0]['brian2'],
              'cpu_model': next((line.split(':', 1)[1].strip() for line in Path('/proc/cpuinfo').read_text().splitlines()
                                 if line.startswith('model name')), 'unknown'),
              'wsl_mem_total': Path('/proc/meminfo').read_text().splitlines()[0],
              'logical_cpus': os.cpu_count(), 'workers_simultaneous': 1, 'fresh_workers': 2,
              'codegen': 'cython', 'sources': provenance, 'total_wall_s': time.perf_counter() - started,
              'timing_definition': 'Per trial includes restore, drive assignment, run(1000 ms), and spike extraction; '
                                   'excludes graph build, zero-duration compile/preparation and file writes. No warm-up simulation.',
              'memory_definition': 'Linux resource.RUSAGE_SELF.ru_maxrss (KiB): lifetime peak Python worker RSS, '
                                    'including graph load/build and preparation; compiler subprocess RSS excluded.',
              'seed_definition': 'Both conditions use seeds 20260910..20260914; fixed 91-Poisson-unit layout.',
              'summary': summarise(rows),
              'workers': [{k: v for k, v in c.items() if k != 'rows'} for c in children], 'trials': rows,
              'scope': 'Ten M0 benchmark trials only; not a Phase 0 gate result. M1/M2 not executed.'}
    for child in children:
        result['summary'][child['condition']]['peak_worker_rss_gib'] = child['peak_worker_rss_kib'] / 1024**2
    write_json(DATA / 'benchmark_m0.json', result)
    print(json.dumps(result['summary'], indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--run', action='store_true')
    group.add_argument('--worker', choices=CONDITIONS, help=argparse.SUPPRESS)
    args = parser.parse_args()
    worker(args.worker) if args.worker else run()
