# SPDX-License-Identifier: MIT
"""M1d: density-scaled recurrence, frozen female external kick; 480 trials."""
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
from sim.malecns import phase0, rescale
from sim.malecns.adapter import load_configuration
from sim.malecns.substrate import DATA, ROOT, file_record, write_json, verify_record

PROTOCOL = DATA/'stim_protocol_malecns_split.json'
PLAN = DATA/'split_plan.json'
OUT = DATA/'runs/m1d'
SOURCE_PATHS = rescale.SOURCE_PATHS + ['sim/malecns/split.py', 'data/malecns/stim_protocol_malecns_split.json']
RULE = ('Each further variant needs a distinct structural rationale written before running, '
        'all gates including S, and reporting regardless of outcome. No w_syn sweep, '
        'isolated failed-gate repair, or removal of failed variants.')


def expected_protocol():
    base, _ = load_configuration(verify=False)
    ratio = json.loads((DATA/'m1b_diagnosis.json').read_text())['proposed_candidates']['r_all']
    p = deepcopy(base)
    p['protocol_version'] = 'malecns-m1d-split-1.0'
    p['model']['w_syn_mV'] = base['model']['w_syn_mV']/ratio
    p['readout']['primary'], p['readout']['secondary'] = 10331, 16949
    p['split_provenance'] = {
        'reference_protocol':file_record(DATA/'stim_protocol_malecns.json'),
        'density_source':file_record(DATA/'m1b_diagnosis.json'),
        'r_all':ratio, 'w_syn_rec_mV':p['model']['w_syn_mV'],
        'w_syn_stim_base_mV':base['model']['w_syn_mV'],
        'external_kick_mV':base['model']['w_syn_mV']*base['model']['f_poi'],
        'derivation':'Recurrent: 0.275 / r_all, full measured precision. External: 0.275 * 250 = 68.75 mV/event.',
        'structural_rationale':'Measured in-degree increase concerns recurrent connectivity, not externally imposed Poisson drive; M1c scaled both together.',
        'overrides':'Only recurrent weight and separated external weight rule change dynamics. Primary L10331 is the post-M1c completeness decision; R16949 secondary. All other model/trial/layout values unchanged.',
        'implementation':'sim/malecns/split.py; unchanged M1 trial runner and shared network equations',
        'shape_gate':{'side':'L10331','sugar_hz':[25,50,100,120,200], 'other_inputs_hz':0,
                      'n':30,'seeds':list(range(20260910,20260940)),
                      'S1':'At least four of five mean MN9 rates > 0 Hz.',
                      'S2':'Every adjacent decrease <= sqrt((population_SD_before^2 + population_SD_after^2)/2).',
                      'S3':'Sugar200 whole-network spike max/min < 3; zero minimum fails (undefined or infinite ratio).',
                      'reuse':'A provides 25/50/100/200; AP_sugar_120 provides 120. No added S runs.'},
        'pass_rule':'A, B, C, D (historical predicates) and S1, S2, S3 must all pass on L10331. R recorded, not deciding.',
        'further_variant_rule':RULE,'scope':'420 A-D + 60 A-prime; 480 trials; no M2.'}
    return p


def validate_protocol(p):
    if p != expected_protocol():
        raise ValueError('Split protocol differs from declaration')
    return p


def shape_gate(summary):
    byid = {r['id']:r for r in summary}
    rows = [byid[f'A_s{s}_b0'] if s!=120 else byid['AP_sugar_120'] for s in [25,50,100,120,200]]
    coverage = sum(r['L_mean']>0 for r in rows)
    adjacent = [{'from_hz':a['sugar_hz'],'to_hz':b['sugar_hz'],
                 'decrease_hz':a['L_mean']-b['L_mean'],
                 'pooled_sd_hz':float(np.sqrt((a['L_sd']**2+b['L_sd']**2)/2))}
                for a,b in zip(rows,rows[1:])]
    counts = rows[-1]['whole_network_spikes']
    ratio = counts['max']/counts['min'] if counts['min']>0 else None
    result = {'coverage':coverage,'adjacent':adjacent,'network_max_min_ratio':ratio,
              'S1':coverage>=4,'S2':all(x['decrease_hz']<=x['pooled_sd_hz'] for x in adjacent),
              'S3':ratio is not None and ratio<3}
    result['S'] = all(result[k] for k in ['S1','S2','S3'])
    return result


def make_plan(host_free_kib):
    verify_record()
    validate_protocol(json.loads(PROTOCOL.read_text()))
    peak = json.loads((DATA/'phase0_results.json').read_text())['metadata']['peak_worker_rss_gib']
    memory = phase0.choose_workers(phase0.mem_available_gib(),host_free_kib/1024**2,peak,os.cpu_count())
    memory['measured_m1_peak_gib'] = memory.pop('measured_m0_peak_gib')
    memory['rule'] = memory['rule'].replace('M0 peak','M1 peak')
    if PLAN.exists():
        raise FileExistsError(PLAN)
    write_json(PLAN,{'stage':'M1d','planned_utc':datetime.now(timezone.utc).isoformat(),
                     'conditions':phase0.conditions(),'total_trials':480,
                     'seeds':list(range(20260910,20260940)),'memory':memory,
                     'sources':[file_record(ROOT/p) for p in SOURCE_PATHS],
                     'pass_rule':expected_protocol()['split_provenance']['pass_rule']})
    print(json.dumps(memory,indent=2),flush=True)


def init_worker():
    from brian2 import SpikeMonitor, second, mV
    from sim.network import build_network
    p = validate_protocol(json.loads(PROTOCOL.read_text()))
    _, cells = load_configuration(verify=False)
    model = build_network(p,cells,phase0.CHANNELS)
    stim = model.net['stimulus_synapses']
    stim.w_stim = p['split_provenance']['external_kick_mV']*mV
    np.testing.assert_allclose(stim.w_stim[:]/mV,68.75,rtol=0,atol=1e-12)
    monitor = SpikeMonitor(model.poisson,name='male_m1_input_monitor')
    model.net.add(monitor)
    model.net.store('m1_init')
    model.net.run(0*second)  # compile only, not a trial
    phase0._MODEL, phase0._PROTOCOL, phase0._CELLS = model,p,cells
    phase0._POISSON_MONITOR = monitor
    phase0._BODY_IDS = np.array([model.i2flyid[i] for i in range(len(model.i2flyid))],dtype='int64')
    phase0.OUT = OUT


def check_sources(plan):
    if any(file_record(ROOT/f['path'])!=f for f in plan['sources']):
        raise ValueError('Frozen planned source changed')
    if plan['conditions']!=phase0.conditions() or plan['seeds']!=list(range(20260910,20260940)):
        raise ValueError('Plan design changed')


def run():
    verify_record()
    plan = json.loads(PLAN.read_text()); check_sources(plan)
    memory = plan['memory']
    if phase0.mem_available_gib()<memory['reserve_gib']+memory['workers']*memory['worker_budget_gib']:
        raise RuntimeError('Insufficient reserved RAM')
    OUT.mkdir(parents=True)  # refuse overwrite, resume or automatic rerun
    started = time.perf_counter()
    meta = {'stage':'M1d','started_utc':datetime.now(timezone.utc).isoformat(),
            'git_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
            'plan':file_record(PLAN),'protocol':file_record(PROTOCOL),'sources':plan['sources'],
            'memory':memory,'python':sys.version,'brian2':__import__('brian2').__version__,'codegen':'cython'}
    write_json(OUT/'run_meta_start.json',meta)
    results = []
    with ProcessPoolExecutor(max_workers=memory['workers'],mp_context=mp.get_context('spawn'),initializer=init_worker) as pool:
        futures = [pool.submit(phase0.run_condition,c) for c in plan['conditions']]
        for future in as_completed(futures):
            result = future.result()
            for row in result['rows']:
                with np.load(ROOT/row['spikes']['path'],allow_pickle=False) as z:
                    row['neurons_fired'] = int(len(np.unique(z['body_id'])))
            results.append(result)
            print(f'M1d completed {len(results)}/16 conditions',flush=True)
    check_sources(plan)
    meta.update(completed_utc=datetime.now(timezone.utc).isoformat(),walltime_s=time.perf_counter()-started,
                total_trials=480,peak_worker_rss_gib=max(t['worker_peak_rss_kib'] for r in results for t in r['rows'])/1024**2)
    compact = rescale.summarize(results)
    compact['shape_gate'] = shape_gate(compact['conditions'])
    compact['overall_primary'] = compact['gates']['L']['overall'] and compact['shape_gate']['S']
    compact['metadata'] = meta
    write_json(OUT/'full_results.json',dict(compact,raw=results))
    compact['raw_ledger'] = file_record(OUT/'full_results.json')
    write_json(DATA/'split_results.json',compact)
    print(json.dumps({k:compact[k] for k in ['gates','shape_gate','overall_primary','a_prime']},indent=2),flush=True)


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--freeze',action='store_true'); mode.add_argument('--plan',action='store_true'); mode.add_argument('--run',action='store_true')
    parser.add_argument('--host-free-kib',type=int)
    args = parser.parse_args()
    if args.freeze:
        if PROTOCOL.exists():
            raise FileExistsError(PROTOCOL)
        write_json(PROTOCOL,expected_protocol())
    else:
        if sys.platform!='linux':
            parser.error('Planning/running require WSL')
        if args.plan and not args.host_free_kib:
            parser.error('Fresh host RAM measurement required')
        make_plan(args.host_free_kib) if args.plan else run()
