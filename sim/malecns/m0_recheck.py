# SPDX-License-Identifier: MIT
"""Write-once M0 environment recheck; exact per-neuron comparison, no tolerance."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import numpy as np
from sim.malecns.substrate import DATA, ROOT, file_record, write_json, verify_record
from sim.malecns.benchmark import CONDITIONS

OUT = DATA / 'runs/m0_recheck'
RECORD = DATA / 'm0_recheck.json'
M0_SOURCE_PATHS = ['sim/malecns/adapter.py', 'sim/malecns/benchmark.py', 'sim/malecns/substrate.py',
                   'sim/network.py', 'data/malecns/substrate_record.json', 'data/stim_protocol.json']
ROW_KEYS = ('condition', 'trial', 'seed', 'sugar_hz', 'MN9_R_primary_hz', 'MN9_L_secondary_hz',
            'MN9_R_latency_ms', 'MN9_L_latency_ms', 'whole_network_spikes', 'driven_sugar_mean_hz')


def worker(name):
    if sys.platform != 'linux':
        raise RuntimeError('M0 recheck requires WSL flybrain')
    launch = json.loads((OUT / 'launch.json').read_text(encoding='utf-8'))
    if any(file_record(ROOT / r['path']) != r for r in launch['sources']):
        raise ValueError('Launch source changed')
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
    out = OUT / name
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


def compare_trial(original, recheck):
    """Compare every array, including those after the first difference."""
    with np.load(original, allow_pickle=False) as a, np.load(recheck, allow_pickle=False) as b:
        ka, kb = set(a.files), set(b.files)
        first = next(iter(sorted(ka ^ kb)), None)
        compared = 0
        spikes_compared = 0
        differing = []
        for key in sorted(ka & kb):
            compared += 1
            spikes_compared += len(a[key])
            if not np.array_equal(a[key], b[key]):
                differing.append(key)
                if first is None:
                    first = key
        return {'identical': ka == kb and not differing, 'key_sets_identical': ka == kb,
                'neurons_compared': compared, 'spikes_compared': spikes_compared,
                'original_neurons': len(ka), 'recheck_neurons': len(kb),
                'original_spikes': sum(len(a[k]) for k in ka),
                'recheck_spikes': sum(len(b[k]) for k in kb),
                'first_differing_key': first, 'differing_arrays': len(differing),
                'missing_keys': sorted(ka - kb), 'extra_keys': sorted(kb - ka)}


def compare_rows(original, recheck):
    return [key for key in ROW_KEYS if key not in original or key not in recheck or original[key] != recheck[key]]


def compare():
    if not OUT.is_dir():
        raise FileNotFoundError('M0 recheck directory absent; no comparison or verdict written')
    if RECORD.exists():
        raise FileExistsError('M0 recheck verdict already exists; no overwrite')
    bench = json.loads((DATA / 'benchmark_m0.json').read_text(encoding='utf-8'))
    trials = []
    workers = []
    for name in CONDITIONS:
        workers.append(json.loads((OUT / name / 'worker.json').read_text(encoding='utf-8')))
        for trial in range(5):
            old = DATA / 'runs/m0' / name / f'trial_{trial:02d}'
            new = OUT / name / f'trial_{trial:02d}'
            original_row = json.loads(old.with_suffix('.json').read_text(encoding='utf-8'))
            new_row = json.loads(new.with_suffix('.json').read_text(encoding='utf-8'))
            r = compare_trial(old.with_suffix('.npz'), new.with_suffix('.npz'))
            r.update(condition=name, trial=trial, row_differences=compare_rows(original_row, new_row))
            r['identical'] = r['identical'] and not r['row_differences']
            r['original'] = file_record(old.with_suffix('.npz'))
            r['recheck'] = file_record(new.with_suffix('.npz'))
            # Detect a ledger pointing at changed archives as well as unequal arrays.
            r['archive_records_match'] = (r['original'] == original_row['spikes'] and r['recheck'] == new_row['spikes'])
            r['identical'] = r['identical'] and r['archive_records_match']
            trials.append(r)
    stored = {s['path']: s for s in bench['sources']}
    sources = []
    for name in M0_SOURCE_PATHS:
        current = file_record(ROOT / name)
        sources.append({'path': name, 'stored_m0': stored[name], 'current': current,
                        'differs': current != stored[name]})
    result = {'verdict': 'IDENTICAL' if all(r['identical'] for r in trials) else 'DIFFERENT',
              'compared_utc': datetime.now(timezone.utc).isoformat(), 'trials': trials,
              'neurons_compared': sum(r['neurons_compared'] for r in trials),
              'spikes_compared': sum(r['spikes_compared'] for r in trials),
              'sources': sources, 'source_note': 'Historical source-hash differences are expected and reported; arrays decide equivalence.',
              'brian2': sorted({w['brian2'] for w in workers}), 'platform': platform.platform(),
              'execution': json.loads((OUT / 'launch.json').read_text(encoding='utf-8')),
              'comparison_source': file_record(Path(__file__))}
    write_json(RECORD, result)
    return result


def run():
    if sys.platform != 'linux':
        raise RuntimeError('M0 recheck requires WSL flybrain')
    if OUT.exists() or RECORD.exists():
        raise FileExistsError('M0 recheck outputs exist; no retry/resume/overwrite')
    verify_record()
    sources = [file_record(ROOT / p) for p in M0_SOURCE_PATHS + ['sim/malecns/m0_recheck.py']]
    OUT.mkdir(parents=True)
    write_json(OUT / 'launch.json', {'sources': sources, 'platform': platform.platform(),
                                   'python': sys.version, 'started_utc': datetime.now(timezone.utc).isoformat()})
    for name in CONDITIONS:
        subprocess.run([sys.executable, '-B', '-m', 'sim.malecns.m0_recheck', '--worker', name], cwd=ROOT, check=True)
    if sources != [file_record(ROOT / s['path']) for s in sources]:
        raise ValueError('Source changed during M0 recheck')
    return compare()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument('--compare', action='store_true')
    modes.add_argument('--run', action='store_true')
    modes.add_argument('--worker', choices=CONDITIONS, help=argparse.SUPPRESS)
    args = parser.parse_args()
    try:
        if args.worker:
            worker(args.worker)
            return
        result = compare() if args.compare else run()
        print(json.dumps(result, indent=2))
        if result['verdict'] != 'IDENTICAL':
            parser.exit(1, 'M0 recheck DIFFERENT; no M1j trial permitted\n')
    except (ValueError, OSError, RuntimeError) as exc:
        parser.exit(1, f'M0 recheck: {exc}\n')


if __name__ == '__main__':
    main()
