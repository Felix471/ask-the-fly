"""M1h single density-matched candidate; fixed external kick, 480 trials."""
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
import pandas as pd
from sim.malecns import phase0, rescale, split, brain_phase0
from sim.malecns import density_match_substrate as brain_substrate
from sim.malecns.adapter import load_configuration
from sim.malecns.substrate import DATA,ROOT,file_record,write_json

CANDIDATES=('density_matched',)
PLAN=DATA/'density_matched_plan.json'
OUT=DATA/'runs/m1h'
SOURCES=split.SOURCE_PATHS+['sim/malecns/brain_phase0.py','sim/malecns/brain_substrate.py','data/malecns/substrate_record_brain.json','sim/malecns/density_matched_phase0.py','sim/malecns/density_match_substrate.py','data/malecns/substrate_record_density_matched.json','data/malecns/m1h_output_retention.json']


def protocol_path(candidate):
    if candidate not in CANDIDATES:
        raise ValueError('Only the single predeclared M1h candidate')
    return DATA/'stim_protocol_malecns_density_matched.json'


def verify_substrate():
    r=json.loads(brain_substrate.RECORD.read_text())
    for f in list(r['artifacts'].values())+[r['builder']]:
        if file_record(ROOT/f['path'])!=f:
            raise ValueError('M1h substrate freeze changed: '+f['path'])
    return r


def expected_protocol(candidate):
    protocol_path(candidate)
    p=brain_phase0.expected_protocol('unscaled')
    r=json.loads(brain_substrate.RECORD.read_text())
    p['protocol_version']='malecns-m1h-density-matched-1.0'
    p['data_version']='male-cns:v1.0-brain-density-matched-1'
    p['connectivity_file']='data/malecns/derived/density_matched/connectivity.parquet'
    p['completeness_file']='data/malecns/derived/density_matched/completeness.csv'
    p.pop('brain_provenance')
    p['density_matched_provenance']={
        'substrate':file_record(brain_substrate.RECORD),
        'c_star':r['c_star'], 'density_ratio':r['density']['ratio'],
        'rationale':'Density, not gates, selected the graph cutoff. Female-calibrated recurrent0.275 mV; no weight search.',
        'w_syn_rec_mV':0.275, 'external_kick_mV':68.75,
        'shape_gate':deepcopy(split.expected_protocol()['split_provenance']['shape_gate']),
        'pass_rule':'Historical A-D and S1-S3 all pass on L10331; R16949 recorded, not deciding.',
        'scope':'One candidate,420 A-D plus60 AP,480 trials. M1 seeds. No subsequent variant pending external replies.',
        'outgoing_audit':file_record(DATA/'m1h_output_retention.json'),
        'flag_decision':'2026-09-14 after audit, before simulation: owner proceeds despite all four sets below50%; crossed flag remains.',
        'changes':'Only substrate changes versus M1f unscaled; all dynamics, stimulus layout, seeds and refractory rules unchanged.',
    }
    return p


def validate(candidate,p):
    if p!=expected_protocol(candidate):
        raise ValueError('Brain protocol changed')
    return p


def freeze():
    verify_substrate()
    for c in CANDIDATES:
        if protocol_path(c).exists():
            raise FileExistsError(protocol_path(c))
    for c in CANDIDATES:
        write_json(protocol_path(c),expected_protocol(c))


def make_plan(host_free_kib):
    verify_substrate()
    for c in CANDIDATES:
        validate(c,json.loads(protocol_path(c).read_text()))
    peak=json.loads((DATA/'phase0_results.json').read_text())['metadata']['peak_worker_rss_gib']
    memory=phase0.choose_workers(phase0.mem_available_gib(),host_free_kib/1024**2,peak,os.cpu_count())
    memory['measured_m1_peak_gib']=memory.pop('measured_m0_peak_gib')
    memory['rule']=memory['rule'].replace('M0 peak','M1 peak')
    write_json(PLAN,{'stage':'M1h','planned_utc':datetime.now(timezone.utc).isoformat(),
                     'candidates':list(CANDIDATES),'conditions':phase0.conditions(),'total_trials':480,
                     'trials_per_candidate':480,'seeds':list(range(20260910,20260940)),
                     'memory':memory,'execution':'Sequential candidate pools, no automatic retries/resume.',
                     'sources':[file_record(ROOT/p) for p in SOURCES]+[file_record(protocol_path(c)) for c in CANDIDATES]})
    print(json.dumps(memory,indent=2),flush=True)


def init_worker(candidate):
    from brian2 import SpikeMonitor,second,mV
    from sim.network import build_network
    p=validate(candidate,json.loads(protocol_path(candidate).read_text()))
    _,cells=load_configuration(verify=False)
    model=build_network(p,cells,phase0.CHANNELS)
    model.net['stimulus_synapses'].w_stim=68.75*mV
    mon=SpikeMonitor(model.poisson,name='male_m1_input_monitor')
    model.net.add(mon); model.net.store('m1_init'); model.net.run(0*second)
    observations=[]
    signed=pd.read_parquet(brain_substrate.TARGET/'connectivity.parquet',columns=['Excitatory x Connectivity']).iloc[:,0].to_numpy()
    for state in ['constructed','restored']:
        if state=='restored':
            model.net.restore('m1_init')
        stim=np.asarray(model.net['stimulus_synapses'].w_stim[:]/mV)
        rec=np.asarray(model.net['default_synapses'].w[:]/mV)
        np.testing.assert_allclose(stim,68.75,rtol=0,atol=1e-12)
        np.testing.assert_allclose(rec,signed*p['model']['w_syn_mV'],rtol=1e-14,atol=1e-12)
        observations.append({'state':state,'stimulus_mV_min':float(stim.min()),'stimulus_mV_max':float(stim.max()),
                             'recurrent_unit_mV_min':float((rec/signed).min()),'recurrent_unit_mV_max':float((rec/signed).max())})
    write_json(OUT/candidate/f'worker_{os.getpid()}_weights.json',{'candidate':candidate,'pid':os.getpid(),'weights':observations})
    phase0._MODEL,phase0._PROTOCOL,phase0._CELLS=model,p,cells
    phase0._POISSON_MONITOR=mon
    phase0._BODY_IDS=np.array([model.i2flyid[i] for i in range(len(model.i2flyid))],dtype='int64')
    phase0.OUT=OUT/candidate


def check_sources(plan):
    if any(file_record(ROOT/f['path'])!=f for f in plan['sources']):
        raise ValueError('Frozen planned source changed')
    if plan['candidates']!=list(CANDIDATES) or plan['conditions']!=phase0.conditions():
        raise ValueError('Plan changed')


def run():
    verify_substrate(); plan=json.loads(PLAN.read_text()); check_sources(plan)
    memory=plan['memory']
    if phase0.mem_available_gib()<memory['reserve_gib']+memory['workers']*memory['worker_budget_gib']:
        raise RuntimeError('Insufficient reserved RAM')
    OUT.mkdir(parents=True)
    for candidate in CANDIDATES:
        check_sources(plan); dest=OUT/candidate; dest.mkdir()
        started=time.perf_counter()
        meta={'stage':'M1h','candidate':candidate,'started_utc':datetime.now(timezone.utc).isoformat(),
              'git_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
              'plan':file_record(PLAN),'protocol':file_record(protocol_path(candidate)),'sources':plan['sources'],
              'memory':memory,'python':sys.version,'brian2':__import__('brian2').__version__,'codegen':'cython'}
        write_json(dest/'run_meta_start.json',meta); results=[]
        with ProcessPoolExecutor(max_workers=memory['workers'],mp_context=mp.get_context('spawn'),initializer=init_worker,initargs=(candidate,)) as pool:
            futures=[pool.submit(phase0.run_condition,c) for c in plan['conditions']]
            for future in as_completed(futures):
                result=future.result()
                for row in result['rows']:
                    with np.load(ROOT/row['spikes']['path'],allow_pickle=False) as z:
                        row['neurons_fired']=int(len(np.unique(z['body_id'])))
                results.append(result)
                print(f'M1h {candidate}: {len(results)}/16 conditions',flush=True)
        check_sources(plan)
        meta.update(completed_utc=datetime.now(timezone.utc).isoformat(),walltime_s=time.perf_counter()-started,total_trials=480,
                    peak_worker_rss_gib=max(t['worker_peak_rss_kib'] for r in results for t in r['rows'])/1024**2,
                    weight_logs=[file_record(p) for p in sorted(dest.glob('worker_*_weights.json'))])
        compact=rescale.summarize(results)
        compact['shape_gate']=split.shape_gate(compact['conditions'])
        compact['overall_primary']=compact['gates']['L']['overall'] and compact['shape_gate']['S']
        compact['metadata']=meta
        write_json(dest/'full_results.json',dict(compact,raw=results))
        compact['raw_ledger']=file_record(dest/'full_results.json')
        write_json(DATA/'m1h_results.json',compact)
        print(json.dumps({'candidate':candidate,'gates':compact['gates'],'shape':compact['shape_gate'],'overall':compact['overall_primary']},indent=2),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--freeze',action='store_true');mode.add_argument('--plan',action='store_true');mode.add_argument('--run',action='store_true')
    parser.add_argument('--host-free-kib',type=int);args=parser.parse_args()
    if args.freeze:
        freeze()
    else:
        if sys.platform!='linux' or (args.plan and not args.host_free_kib):
            parser.error('WSL and fresh host RAM required')
        make_plan(args.host_free_kib) if args.plan else run()
