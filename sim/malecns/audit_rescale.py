# SPDX-License-Identifier: MIT
"""Reconstruct both M1c candidates from saved events; never imports Brian2."""
import hashlib
import json
from pathlib import Path
import numpy as np
from sim.malecns.audit_phase0 import raw_gate_checks, digest_events
from sim.malecns.substrate import DATA, ROOT, file_record, write_json, verify_record


def require(check, message):
    if not check:
        raise ValueError(message)


def stats(values):
    return {'median':float(np.median(values)), 'min':int(min(values)), 'max':int(max(values))}


def run():
    verify_record()
    preflight=json.loads((DATA/'rescale_preflight.json').read_text())
    for source in preflight['sources']:
        require(file_record(ROOT/source['path'])==source,'Preflight source changed')
    for row in preflight['female_activity']:
        if not row['n_trials']:
            require(row['requested_rates_hz'][0]==25 or row['requested_rates_hz'][1]==25,'Unexpected missing comparison')
            continue
        require(file_record(ROOT/row['source']['path'])==row['source'],'Female replay source hash')
        with np.load(ROOT/row['source']['path'],allow_pickle=False) as replay:
            require(row['network_spikes']==len(replay['t_ms']),'Female network count')
            require(row['neurons_fired']==len(np.unique(replay['flywire_id'])),'Female neuron count')
            require(row['seed']==int(replay['seed']),'Female seed')
            np.testing.assert_array_equal(row['requested_rates_hz'],replay['rates'])
    cells=json.loads((DATA/'cells.json').read_text())['sets']
    slots=[b for c in ['sugar','bitter','water','ir94e'] for b in cells[c]['ids']]
    reports={}
    previous={}
    for candidate in ['all','mn9']:
        compact=json.loads((DATA/f'rescale_{candidate}_results.json').read_text())
        ledger=compact['raw_ledger']
        require(file_record(ROOT/ledger['path'])==ledger,'Full ledger changed')
        full=json.loads((ROOT/ledger['path']).read_text())
        require({k:v for k,v in full.items() if k!='raw'}=={k:v for k,v in compact.items() if k!='raw_ledger'},'Compact/full mismatch')
        for source in full['metadata']['sources']:
            require(file_record(ROOT/source['path'])==source,'Planned source changed')
        require(file_record(DATA/'rescale_plan.json')==full['metadata']['plan'],'Run plan changed')
        rebuilt=[]
        rates_by_condition={}
        event_hashes={}
        network_hashes={}
        checked=matched_m1=matched_candidate=0
        summary={r['id']:r for r in compact['conditions']}
        require(len(full['raw'])==len(summary)==16,'Incomplete design')
        for group in full['raw']:
            c=group['condition']; cid=c['id']
            rows=sorted(group['rows'],key=lambda r:r['trial'])
            require([r['trial'] for r in rows]==list(range(30)),'Trial ledger')
            require([r['seed'] for r in rows]==list(range(20260910,20260940)),'Seed ledger')
            values={s:[] for s in ['R','L']}; latency={s:[] for s in ['R','L']}
            network=[]; neurons=[]
            frequencies={b:c['sugar_hz'] for b in cells[c['sugar_set']]['ids']}
            frequencies.update({b:c['bitter_hz'] for b in cells['bitter']['ids']})
            for row in rows:
                path=ROOT/row['spikes']['path']
                require(file_record(path)==row['spikes'],'Raw hash')
                with np.load(path,allow_pickle=False) as z:
                    body,t=z['body_id'],z['time_s']; pi,pt=z['poisson_index'],z['poisson_time_s']
                    require(len(body)==len(t) and len(pi)==len(pt),'Event lengths')
                    for x in [t,pt]:
                        require(np.isfinite(x).all() and (x>=0).all() and (x<1).all() and (np.diff(x)>=0).all(),'Event times')
                    require((pi>=0).all() and (pi<91).all(),'Poisson slots')
                    ids,counts=np.unique(body,return_counts=True)
                    countmap=dict(zip(ids.tolist(),counts.tolist()))
                    require(row['whole_network_spikes']==len(t) and row['neurons_fired']==len(ids),'Network counts')
                    require(row['source_spike_counts']==[countmap.get(i,0) for i in slots],'Driven-cell counts')
                    network.append(len(t)); neurons.append(len(ids))
                    for side,root in [('R',16949),('L',10331)]:
                        st=t[body==root]; lat=float(st[0]*1000) if len(st) else None
                        require(row[side+'_hz']==len(st) and row[side+'_latency_ms']==lat,'MN9 rate/latency')
                        values[side].append(len(st))
                        if lat is not None:
                            latency[side].append(lat)
                    hashes=[]
                    for slot,b in enumerate(slots):
                        require(frequencies.get(b,0)>0 or not np.any(pi==slot),'Inactive Poisson slot fired')
                        hashes.append(digest_events(pi,pt,slot))
                    key=(cid,row['trial'])
                    event_hashes[key]=hashes
                    network_hashes[key]=(hashlib.sha256(body.tobytes()).hexdigest(),hashlib.sha256(t.tobytes()).hexdigest())
                    with np.load(DATA/'runs/m1'/cid/f'trial_{row["trial"]:02d}.npz',allow_pickle=False) as old:
                        np.testing.assert_array_equal(pi,old['poisson_index'])
                        np.testing.assert_array_equal(pt,old['poisson_time_s'])
                        matched_m1+=1
                    if candidate=='mn9':
                        require(previous[key]==hashes,'Input trains differ between candidate weights')
                        matched_candidate+=91
                checked+=1
            sr=dict(c)
            for side in ['R','L']:
                sr[side+'_mean']=float(np.mean(values[side])); sr[side+'_sd']=float(np.std(values[side]))
                sr[side+'_latency_median_ms']=float(np.median(latency[side])) if latency[side] else None
                sr[side+'_firing_trials']=len(latency[side])
            sr['whole_network_spikes']=stats(network); sr['neurons_fired']=stats(neurons)
            require(sr==summary[cid],'Reconstructed condition summary')
            rates_by_condition[cid]=values
            rebuilt.append(sr)
            print(f'Audit {candidate}: {checked}/480 raw trials',flush=True)
        for side in ['R','L']:
            for key,value in raw_gate_checks(rebuilt,side).items():
                require(compact['gates'][side][key]==value,'Independent gate predicate mismatch')
            diff=np.array(rates_by_condition['AP_sugar_lb3c_120'][side])-np.array(rates_by_condition['AP_sugar_120'][side])
            ap=compact['a_prime'][side]
            require(ap['mean_hz']==float(diff.mean()) and ap['sd_hz']==float(diff.std()),'A-prime statistics')
            require([ap[k+'_trials'] for k in ['lower','equal','higher']]==[int((diff<0).sum()),int((diff==0).sum()),int((diff>0).sum())],'A-prime signs')
        shared=0
        for trial in range(30):
            require(network_hashes['A_s200_b0',trial]==network_hashes['B_s200_b0',trial],'A200/B0 whole-network mismatch')
            for b in cells['sugar_lb3c']['ids']:
                slot=slots.index(b)
                require(event_hashes['AP_sugar_120',trial][slot]==event_hashes['AP_sugar_lb3c_120',trial][slot],'A-prime paired source mismatch')
                shared+=1
        previous=event_hashes
        reports[candidate]={'raw_trials':checked,'MN9_neuron_trials':2*checked,'M1_full_Poisson_array_pairs_identical':matched_m1,
                            'cross_candidate_Poisson_train_pairs_identical':matched_candidate,
                            'AP_shared_LB3c_trains_identical':shared,'A200_B0_network_pairs_identical':30,
                            'network_counts_rates_latencies_gates_AP':'PASS','sources':[file_record(DATA/f'rescale_{candidate}_results.json'),ledger]}
    result={'candidates':reports,'total_trials':sum(r['raw_trials'] for r in reports.values()),
            'preflight_sources_and_three_female_replays':'PASS; two 25-Hz comparisons unavailable, no substitution',
            'audit_source':file_record(Path(__file__)),'simulation':'none; saved-event reconstruction only'}
    write_json(DATA/'rescale_audit.json',result)
    print(json.dumps(result,indent=2),flush=True)


if __name__=='__main__':
    run()
