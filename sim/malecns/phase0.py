# SPDX-License-Identifier: MIT
"""M1: 420 A-D trials plus 60 paired A-prime trials, both MN9s; no M2."""
from __future__ import annotations
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
import json
import math
import multiprocessing as mp
import os
from pathlib import Path
import subprocess
import sys
import time

import numpy as np

from sim.malecns.substrate import DATA, ROOT, file_record, write_json, verify_record

PLAN = DATA / 'phase0_plan.json'
OUT = DATA / 'runs/m1'
SIDES = {'R': 16949, 'L': 10331}
CHANNELS = ['sugar', 'bitter', 'water', 'ir94e']


def conditions():
    rows = []
    for gate, pairs in [('A', [(s,0) for s in [25,50,100,200]]),
                        ('B', [(200,b) for b in [0,25,50,100,200]]),
                        ('C', [(0,b) for b in [25,50,100,200]]), ('D', [(0,0)])]:
        for s,b in pairs:
            rows.append({'id': f'{gate}_s{s}_b{b}', 'gate': gate, 'sugar_hz': s, 'bitter_hz': b,
                         'sugar_set': 'sugar', 'n_trials': 30})
    for key in ('sugar', 'sugar_lb3c'):
        rows.append({'id': f'AP_{key}_120', 'gate': 'AP', 'sugar_hz':120, 'bitter_hz':0,
                     'sugar_set':key, 'n_trials':30})
    return rows


def choose_workers(wsl_available_gib, host_free_gib, peak_gib, cpus):
    available = min(wsl_available_gib, host_free_gib)
    reserve = max(8., available*.25)
    budget = math.ceil(peak_gib*1.5*10)/10
    workers = min(16, max(1, cpus//2), math.floor((available-reserve)/budget))
    if workers < 1:
        raise ValueError('Insufficient available RAM with headroom; do not launch')
    return {'workers':workers, 'wsl_available_gib':wsl_available_gib, 'host_free_gib':host_free_gib,
            'limiting_available_gib':available, 'reserve_gib':reserve, 'worker_budget_gib':budget,
            'measured_m0_peak_gib':peak_gib, 'cpus':cpus,
            'rule':'min(16 conditions, logical_cpus//2, floor((min(WSL available, host free)-max(8GiB,25%))/ceil(1.5*M0 peak to 0.1GiB)))'}


def mem_available_gib():
    for line in Path('/proc/meminfo').read_text().splitlines():
        if line.startswith('MemAvailable:'):
            return int(line.split()[1])/1024**2
    raise RuntimeError('No Linux MemAvailable measurement')


def source_rates(condition, sets):
    selected = set(sets[condition['sugar_set']]['ids'])
    return [condition['sugar_hz'] if key=='sugar' and body in selected else
            condition['bitter_hz'] if key=='bitter' else 0
            for key in CHANNELS for body in sets[key]['ids']]


def evaluate_gates(rows):
    if len(rows) != 16 or {r['id'] for r in rows} != {r['id'] for r in conditions()}:
        raise ValueError('Incomplete or duplicated M1 condition design')
    if any(r['n_trials'] != 30 for r in rows):
        raise ValueError('Every M1 condition requires exactly 30 trials')
    result = {}
    for side in SIDES:
        group = lambda g: sorted([r for r in rows if r['gate']==g], key=lambda r:(r['sugar_hz'],r['bitter_hz']))
        d = group('D')[0]
        dm, ds = d[f'{side}_mean'], d[f'{side}_sd']
        a = [r[f'{side}_mean'] for r in group('A')]
        b = [r[f'{side}_mean'] for r in group('B')]
        c = group('C')
        result[side] = {
            'A':bool(all(y>x or x==y==0 for x,y in zip(a,a[1:])) and a[-1]>dm+5*ds+5),
            'B':bool(all(y<=x for x,y in zip(b,b[1:])) and b[-1]<.5*b[0]),
            'C':bool(all(r[f'{side}_mean']<=dm+2*ds+1 for r in c)),
            'D':bool(d['n_trials']>=30),
            'D_literal_zero':bool(dm==0 and ds==0),
            'C_literal_zero':bool(all(r[f'{side}_mean']==0 and r[f'{side}_sd']==0 for r in c)),
            'A_threshold_hz':dm+5*ds+5, 'C_limit_hz':dm+2*ds+1,
            'bitter200_suppression_fraction':1-b[-1]/b[0] if b[0] else None}
        result[side]['overall'] = all(result[side][g] for g in 'ABCD')
    return result


def make_plan(host_free_kib):
    verify_record()
    bench = json.loads((DATA/'benchmark_m0.json').read_text(encoding='utf-8'))
    peak = max(w['peak_worker_rss_kib'] for w in bench['workers'])/1024**2
    memory = choose_workers(mem_available_gib(), host_free_kib/1024**2, peak, os.cpu_count())
    plan = {'stage':'M1', 'planned_utc':datetime.now(timezone.utc).isoformat(), 'conditions':conditions(),
            'total_trials':480, 'gate_trials':420, 'a_prime_trials':60, 'seeds':list(range(20260910,20260940)),
            'reference_protocol':file_record(DATA/'stim_protocol_malecns.json'),
            'substrate_record':file_record(DATA/'substrate_record.json'),
            'cells':file_record(DATA/'cells.json'), 'm0_benchmark':file_record(DATA/'benchmark_m0.json'),
            'female_gate_source':file_record(ROOT/'scripts/phase0_report.py'),
            'female_comparison':file_record(ROOT/'results/phase0/full/summary.csv'),
            'memory':memory, 'readouts':SIDES,
            'readout_decision':'Both MN9s gated separately; R16949 retained as M0 reference only; primary choice deferred until after M1.',
            'layout':'Same 91 physical Poisson slots/order as M0, including inactive channels. A-prime zeros only the five LB3b slots/rates; their refractory returns to t_rfc.',
            'gate_rule':'Exact A-D predicates from female report source, separately per side. Historical D is trial-count completeness; literal D-zero and C-zero are additional reported checks.',
            'scope':'M1 only; no M2, no model-parameter or frozen-file changes.'}
    write_json(PLAN, plan)
    print(json.dumps(memory, indent=2), flush=True)


_MODEL = _PROTOCOL = _CELLS = _POISSON_MONITOR = _BODY_IDS = None


def init_worker():
    global _MODEL, _PROTOCOL, _CELLS, _POISSON_MONITOR, _BODY_IDS
    from sim.malecns.adapter import build_male_network
    from brian2 import SpikeMonitor, second
    _MODEL, _PROTOCOL, _CELLS = build_male_network(verify=False)
    _POISSON_MONITOR = SpikeMonitor(_MODEL.poisson, name='male_m1_input_monitor')
    _MODEL.net.add(_POISSON_MONITOR)
    _MODEL.net.store('m1_init')
    _MODEL.net.run(0*second)  # compile/preparation only, not an extra simulation trial
    _BODY_IDS = np.array([_MODEL.i2flyid[i] for i in range(len(_MODEL.i2flyid))], dtype='int64')


def run_condition(condition):
    import resource
    from brian2 import Hz, ms, second, seed as brian_seed
    out = OUT/condition['id']
    out.mkdir()
    rows = []
    rates = np.array(source_rates(condition, _CELLS['sets']), dtype=float)
    model = _MODEL
    for trial in range(30):
        before = time.perf_counter()
        model.net.restore('m1_init')
        model.set_rates({'sugar':condition['sugar_hz'], 'bitter':condition['bitter_hz'], 'water':0, 'ir94e':0})
        model.poisson.rates = rates*Hz
        # Restore all physical targets to the ordinary refractory value, then zero only driven targets.
        model.neurons.rfc[model.target_indices] = model.t_rfc
        model.neurons.rfc[model.target_indices[rates>0]] = 0*ms
        brian_seed(20260910+trial)
        model.net.run(_PROTOCOL['trial']['duration_ms']*ms)
        indices = np.asarray(model.monitor.i[:], dtype='int32')
        times = np.asarray(model.monitor.t[:]/second, dtype=float)
        body = _BODY_IDS[indices]
        elapsed = time.perf_counter()-before
        path = out/f'trial_{trial:02d}.npz'
        with path.open('xb') as f:
            np.savez_compressed(f, body_id=body, time_s=times,
                                poisson_index=np.asarray(_POISSON_MONITOR.i[:], dtype='int32'),
                                poisson_time_s=np.asarray(_POISSON_MONITOR.t[:]/second, dtype=float))
        counts = np.bincount(indices, minlength=len(_BODY_IDS))
        row = {'condition':condition['id'], 'trial':trial, 'seed':20260910+trial,
               'trial_wall_s':elapsed, 'worker_peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
               'whole_network_spikes':len(times), 'source_spike_counts':counts[model.target_indices].tolist(),
               'spikes':file_record(path)}
        for side, root in SIDES.items():
            st = times[body==root]
            row[f'{side}_hz'] = len(st)/(_PROTOCOL['trial']['duration_ms']/1000)
            row[f'{side}_latency_ms'] = float(st[0]*1000) if len(st) else None
        write_json(out/f'trial_{trial:02d}.json', row)
        rows.append(row)
        if (trial+1)%5==0:
            print(f'{condition["id"]}: {trial+1}/30, MN9 R/L {row["R_hz"]:.0f}/{row["L_hz"]:.0f}Hz, peak {row["worker_peak_rss_kib"]/1024**2:.2f}GiB', flush=True)
    return {'condition':condition, 'rows':rows, 'pid':os.getpid()}


def summary_from_rows(results):
    summary = []
    for result in results:
        row = dict(result['condition'])
        trials = sorted(result['rows'], key=lambda r:r['trial'])
        if len(trials)!=30 or [r['trial'] for r in trials]!=list(range(30)) or [r['seed'] for r in trials]!=list(range(20260910,20260940)):
            raise ValueError('Incorrect trial count or seed ledger')
        for side in SIDES:
            values = [r[f'{side}_hz'] for r in trials]
            latency = [r[f'{side}_latency_ms'] for r in trials if r[f'{side}_latency_ms'] is not None]
            row.update({f'{side}_mean':float(np.mean(values)), f'{side}_sd':float(np.std(values,ddof=0)),
                        f'{side}_latency_median_ms':float(np.median(latency)) if latency else None,
                        f'{side}_firing_trials':len(latency)})
        summary.append(row)
    return summary


def run():
    verify_record()
    plan = json.loads(PLAN.read_text(encoding='utf-8'))
    for key in ('reference_protocol','substrate_record','cells','m0_benchmark','female_gate_source','female_comparison'):
        f = plan[key]
        if file_record(ROOT/f['path']) != f:
            raise ValueError(f'Planned source changed: {key}')
    memory = plan['memory']
    now = mem_available_gib()
    if now < memory['reserve_gib']+memory['workers']*memory['worker_budget_gib']:
        raise RuntimeError('Available WSL RAM fell below the reserved plan; not launching')
    OUT.mkdir(parents=True)  # fails closed on an existing run; no implicit resume/rerun
    sources = [file_record(ROOT/p) for p in ['sim/malecns/phase0.py','sim/malecns/adapter.py',
               'sim/malecns/substrate.py','sim/network.py','data/stim_protocol.json','data/malecns/phase0_plan.json']]
    started = time.perf_counter()
    meta = {'stage':'M1','started_utc':datetime.now(timezone.utc).isoformat(),
            'git_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
            'sources':sources, 'memory_plan':memory, 'launch_available_gib':now,
            'python':sys.version, 'brian2_version':__import__('brian2').__version__, 'codegen_target':'cython'}
    write_json(OUT/'run_meta_start.json',meta)
    results = []
    with ProcessPoolExecutor(max_workers=memory['workers'], mp_context=mp.get_context('spawn'), initializer=init_worker) as pool:
        futures = [pool.submit(run_condition,c) for c in plan['conditions']]
        for f in as_completed(futures):
            result = f.result()
            results.append(result)
            print(f'Completed {len(results)}/16 conditions ({len(results)*30}/480 trials)',flush=True)
    if any(file_record(ROOT/f['path']) != f for f in sources):
        raise ValueError('Source changed during M1')
    order = {c['id']:i for i,c in enumerate(conditions())}
    results.sort(key=lambda r:order[r['condition']['id']])
    summary = summary_from_rows(results)
    left = next(r['rows'] for r in results if r['condition']['id']=='AP_sugar_120')
    right = next(r['rows'] for r in results if r['condition']['id']=='AP_sugar_lb3c_120')
    ap = {}
    for side in SIDES:
        diffs = [b[f'{side}_hz']-a[f'{side}_hz'] for a,b in zip(left,right)]
        ap[side] = {'difference_definition':'LB3c12 minus sugar17, paired by seed',
                    'mean_hz':float(np.mean(diffs)), 'sd_hz':float(np.std(diffs,ddof=0)),
                    'lower_trials':sum(x<0 for x in diffs),'equal_trials':sum(x==0 for x in diffs),'higher_trials':sum(x>0 for x in diffs)}
    meta.update(completed_utc=datetime.now(timezone.utc).isoformat(), walltime_s=time.perf_counter()-started,
                total_trials=480, worker_pids=sorted(set(r['pid'] for r in results)),
                peak_worker_rss_gib=max(t['worker_peak_rss_kib'] for r in results for t in r['rows'])/1024**2)
    final = {'metadata':meta,'conditions':summary,'gates':evaluate_gates(summary),'a_prime':ap,'raw':results,
             'primary_readout_status':'Deferred until after M1; both sides independently evaluated.','M2':'not executed'}
    write_json(DATA/'phase0_results.json',final)
    print(json.dumps({'gates':final['gates'],'a_prime':ap,'walltime_s':meta['walltime_s']},indent=2),flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    g = parser.add_mutually_exclusive_group(required=True)
    g.add_argument('--plan',action='store_true')
    g.add_argument('--run',action='store_true')
    parser.add_argument('--host-free-kib',type=int)
    args = parser.parse_args()
    if sys.platform!='linux':
        parser.error('Planning and simulation use the existing WSL environment')
    if args.plan and not args.host_free_kib:
        parser.error('--plan requires measured --host-free-kib')
    make_plan(args.host_free_kib) if args.plan else run()
