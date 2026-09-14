# SPDX-License-Identifier: MIT
"""Exactly two pre-declared M1c weights; reuse the unchanged M1 trial and gates."""
from __future__ import annotations
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from copy import deepcopy
from datetime import datetime, timezone
import json
import multiprocessing as mp
import os
import subprocess
import sys
import time
import numpy as np
from sim.malecns import phase0
from sim.malecns.adapter import load_configuration
from sim.malecns.substrate import DATA, ROOT, file_record, write_json, verify_record

CANDIDATES = ('all', 'mn9')
PLAN = DATA/'rescale_plan.json'
OUT = DATA/'runs/m1c'
SOURCE_PATHS = ['sim/malecns/rescale.py', 'sim/malecns/phase0.py',
                'sim/malecns/adapter.py', 'sim/malecns/substrate.py', 'sim/network.py',
                'data/stim_protocol.json', 'data/malecns/stim_protocol_malecns.json',
                'data/malecns/cells.json', 'data/malecns/substrate_record.json',
                'data/malecns/m1b_diagnosis.json', 'data/malecns/rescale_preflight.json']


def protocol_path(candidate):
    if candidate not in CANDIDATES:
        raise ValueError('Only the two owner-approved candidates are allowed')
    return DATA/f'stim_protocol_malecns_{candidate}.json'


def expected_protocol(candidate):
    protocol_path(candidate)
    base, _ = load_configuration(verify=False)
    diagnosis = json.loads((DATA/'m1b_diagnosis.json').read_text())['proposed_candidates']
    ratio = diagnosis['r_all'] if candidate == 'all' else diagnosis['alternative_needs_owner_approval']['ratio']
    p = deepcopy(base)
    p['protocol_version'] = f'malecns-m1c-{candidate}-1.0'
    p['model']['w_syn_mV'] = base['model']['w_syn_mV']/ratio
    p['rescale_provenance'] = {
        'candidate':candidate, 'approved_before_runs':True,
        'reference_protocol':file_record(DATA/'stim_protocol_malecns.json'),
        'density_source':file_record(DATA/'m1b_diagnosis.json'),
        'original_w_syn_mV':base['model']['w_syn_mV'], 'male_female_ratio':ratio,
        'derivation':'0.275 / r_all' if candidate=='all' else '0.275 / r_mn9',
        'ratio_definition': 'Ratio of all-roster mean unsigned synaptic in-degrees, including zero-input neurons.' if candidate=='all' else
        '(male contra mean + male ipsi mean)/(female contra mean + female ipsi mean), using min(200, available) strongest partners per MN9; male R has 137, other neighborhoods 200; equal side weights.',
        'precision':'Full precision of approved mean-based definition; displayed rounded weights are 0.145104 and 0.138504 mV.',
        'external_kick':'w_syn*f_poi remains tied; f_poi unchanged. Not recurrent-only rescaling.',
        'overrides':'Only model.w_syn_mV changes. Inherited male_provenance describes M0, superseded for this field and adapter by this record.',
        'adapter':'sim/malecns/rescale.py', 'trial_runner':'unchanged sim/malecns/phase0.py',
        'scope':'A-D plus both A-prime arms only; 480 trials; no Phase 1 or M2.',
        'readout':'Both MN9 sides independently gated; inherited primary field is historical, no new primary chosen.',
        'stop_rule':'Pass only if all historical A-D gates pass on at least one side. If neither candidate passes, male line stops; no third weight.'}
    return p


def validate_protocol(candidate, protocol):
    if protocol != expected_protocol(candidate):
        raise ValueError('Candidate differs from the pre-declared protocol')
    return protocol


def freeze_protocols():
    for candidate in CANDIDATES:
        if protocol_path(candidate).exists():
            raise FileExistsError(protocol_path(candidate))
    for candidate in CANDIDATES:
        write_json(protocol_path(candidate), expected_protocol(candidate))


def make_plan(host_free_kib):
    verify_record()
    for candidate in CANDIDATES:
        validate_protocol(candidate, json.loads(protocol_path(candidate).read_text()))
    old = json.loads((DATA/'phase0_results.json').read_text())
    peak = old['metadata']['peak_worker_rss_gib']
    memory = phase0.choose_workers(phase0.mem_available_gib(), host_free_kib/1024**2, peak, os.cpu_count())
    memory['measured_m1_peak_gib'] = memory.pop('measured_m0_peak_gib')
    memory['rule'] = memory['rule'].replace('M0 peak', 'M1 peak')
    sources = SOURCE_PATHS + [str(protocol_path(c).relative_to(ROOT)) for c in CANDIDATES]
    plan = {'stage':'M1c', 'planned_utc':datetime.now(timezone.utc).isoformat(),
            'candidates':list(CANDIDATES), 'conditions':phase0.conditions(),
            'trials_per_candidate':480, 'total_trials':960, 'gate_trials':840, 'a_prime_trials':120,
            'seeds':list(range(20260910,20260940)), 'memory':memory,
            'execution':'Sequential candidate pools; no simultaneous candidate pools or automatic retries.',
            'sources':[file_record(ROOT/p) for p in sources],
            'stop_rule':expected_protocol('all')['rescale_provenance']['stop_rule']}
    write_json(PLAN, plan)
    print(json.dumps(plan['memory'], indent=2), flush=True)


def init_worker(candidate):
    from brian2 import SpikeMonitor, second
    from sim.network import build_network
    protocol = validate_protocol(candidate, json.loads(protocol_path(candidate).read_text()))
    _, cells = load_configuration(verify=False)
    model = build_network(protocol, cells, phase0.CHANNELS)
    monitor = SpikeMonitor(model.poisson, name='male_m1_input_monitor')
    model.net.add(monitor)
    model.net.store('m1_init')
    model.net.run(0*second)  # compile only; no extra trial
    phase0._MODEL, phase0._PROTOCOL, phase0._CELLS = model, protocol, cells
    phase0._POISSON_MONITOR = monitor
    phase0._BODY_IDS = np.array([model.i2flyid[i] for i in range(len(model.i2flyid))], dtype='int64')
    phase0.OUT = OUT/candidate


def activity_stats(values):
    return {'median':float(np.median(values)), 'min':int(min(values)), 'max':int(max(values))}


def summarize(results):
    order = {c['id']:i for i,c in enumerate(phase0.conditions())}
    results.sort(key=lambda r:order[r['condition']['id']])
    summary = phase0.summary_from_rows(results)
    for s,r in zip(summary,results):
        for key in ('whole_network_spikes','neurons_fired'):
            s[key] = activity_stats([t[key] for t in r['rows']])
    union = next(r['rows'] for r in results if r['condition']['id']=='AP_sugar_120')
    subset = next(r['rows'] for r in results if r['condition']['id']=='AP_sugar_lb3c_120')
    ap = {}
    for side in phase0.SIDES:
        diffs = [b[f'{side}_hz']-a[f'{side}_hz'] for a,b in zip(union,subset)]
        ap[side] = {'difference_definition':'LB3c12 minus sugar17, paired by seed',
                    'mean_hz':float(np.mean(diffs)), 'sd_hz':float(np.std(diffs,ddof=0)),
                    'lower_trials':sum(x<0 for x in diffs), 'equal_trials':sum(x==0 for x in diffs),
                    'higher_trials':sum(x>0 for x in diffs)}
    return {'conditions':summary, 'gates':phase0.evaluate_gates(summary), 'a_prime':ap}


def check_sources(plan):
    if any(file_record(ROOT/f['path']) != f for f in plan['sources']):
        raise ValueError('A frozen planned source changed')
    if plan['candidates'] != list(CANDIDATES) or plan['conditions'] != phase0.conditions() or plan['seeds'] != list(range(20260910,20260940)):
        raise ValueError('Pre-declared plan changed')


def run():
    verify_record()
    plan = json.loads(PLAN.read_text())
    check_sources(plan)
    memory = plan['memory']
    if phase0.mem_available_gib() < memory['reserve_gib']+memory['workers']*memory['worker_budget_gib']:
        raise RuntimeError('Available WSL RAM below reserved launch plan')
    OUT.mkdir(parents=True)  # no resume, overwrite or implicit rerun
    final = {}
    for candidate in CANDIDATES:
        check_sources(plan)
        dest = OUT/candidate
        dest.mkdir()
        started = time.perf_counter()
        meta = {'stage':'M1c', 'candidate':candidate, 'started_utc':datetime.now(timezone.utc).isoformat(),
                'git_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                'plan':file_record(PLAN), 'protocol':file_record(protocol_path(candidate)),
                'python':sys.version, 'brian2':__import__('brian2').__version__, 'codegen':'cython',
                'memory':memory, 'sources':plan['sources']}
        write_json(dest/'run_meta_start.json',meta)
        results = []
        with ProcessPoolExecutor(max_workers=memory['workers'], mp_context=mp.get_context('spawn'),
                                 initializer=init_worker, initargs=(candidate,)) as pool:
            futures = [pool.submit(phase0.run_condition,c) for c in plan['conditions']]
            for future in as_completed(futures):
                result = future.result()
                for row in result['rows']:
                    with np.load(ROOT/row['spikes']['path'], allow_pickle=False) as spikes:
                        row['neurons_fired'] = int(len(np.unique(spikes['body_id'])))
                results.append(result)
                print(f'{candidate}: completed {len(results)}/16 conditions', flush=True)
        check_sources(plan)
        meta.update(completed_utc=datetime.now(timezone.utc).isoformat(), walltime_s=time.perf_counter()-started,
                    total_trials=480, peak_worker_rss_gib=max(t['worker_peak_rss_kib'] for r in results for t in r['rows'])/1024**2)
        compact = summarize(results)
        compact['metadata'] = meta
        write_json(dest/'full_results.json',dict(compact,raw=results))
        compact['raw_ledger'] = file_record(dest/'full_results.json')
        write_json(DATA/f'rescale_{candidate}_results.json',compact)
        final[candidate] = compact['gates']
        print(json.dumps({'candidate':candidate,'gates':compact['gates'],'a_prime':compact['a_prime'], 'wall_s':meta['walltime_s']},indent=2),flush=True)
    print(json.dumps({'all_candidates':final,'passing_candidates':[c for c in final if any(g['overall'] for g in final[c].values())]},indent=2),flush=True)


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--freeze',action='store_true')
    mode.add_argument('--plan',action='store_true')
    mode.add_argument('--run',action='store_true')
    parser.add_argument('--host-free-kib',type=int)
    args = parser.parse_args()
    if args.freeze:
        freeze_protocols()
    else:
        if sys.platform != 'linux':
            parser.error('Planning/simulation require WSL flybrain')
        if args.plan and not args.host_free_kib:
            parser.error('Plan requires freshly measured host-free-kib')
        make_plan(args.host_free_kib) if args.plan else run()
