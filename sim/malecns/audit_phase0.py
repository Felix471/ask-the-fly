# SPDX-License-Identifier: MIT
"""Independent M1 raw-data audit; no Brian2 imports or simulation."""
import hashlib
import json
from pathlib import Path

import numpy as np

from sim.malecns.substrate import DATA, ROOT, file_record, write_json, verify_record


def raw_gate_checks(rows, side):
    # Independent formulation, operating on reconstructed raw per-trial rates.
    group = lambda letter: sorted([r for r in rows if r['gate']==letter],key=lambda r:(r['sugar_hz'],r['bitter_hz']))
    a,b,c,d = group('A'),group('B'),group('C'),group('D')[0]
    am = np.array([r[side+'_mean'] for r in a])
    bm = np.array([r[side+'_mean'] for r in b])
    dm,ds = d[side+'_mean'],d[side+'_sd']
    checks = {'A':bool(np.all((np.diff(am)>0)|((am[:-1]==0)&(am[1:]==0))) and am[-1]>dm+5*ds+5),
              'B':bool(np.all(np.diff(bm)<=0) and bm[-1]<bm[0]*.5),
              'C':bool(max(r[side+'_mean'] for r in c)<=dm+2*ds+1),
              'D':bool(d['n_trials']>=30), 'D_literal_zero':bool(dm==ds==0),
              'C_literal_zero':bool(all(r[side+'_mean']==r[side+'_sd']==0 for r in c))}
    checks['overall'] = all(checks[g] for g in 'ABCD')
    return checks


def digest_events(indices,times,slot):
    # Spike-time vector for an identified physical Poisson slot.
    return hashlib.sha256(np.ascontiguousarray(times[indices==slot]).tobytes()).hexdigest()


def run():
    verify_record()
    summary_record = json.loads((DATA/'phase0_results.json').read_text(encoding='utf-8'))
    ledger = summary_record['raw_ledger']
    if file_record(ROOT/ledger['path'])!=ledger:
        raise ValueError('Full trial ledger hash mismatch')
    result = json.loads((ROOT/ledger['path']).read_text(encoding='utf-8'))
    if {k:v for k,v in result.items() if k!='raw'}!={k:v for k,v in summary_record.items() if k not in ['raw_ledger','packaging']}:
        raise ValueError('Compact summary differs from full original ledger')
    plan = json.loads((DATA/'phase0_plan.json').read_text(encoding='utf-8'))
    cells = json.loads((DATA/'cells.json').read_text(encoding='utf-8'))['sets']
    for source in result['metadata']['sources']:
        if file_record(ROOT/source['path']) != source:
            raise ValueError(f'M1 source changed: {source["path"]}')
    if len(plan['conditions'])!=16 or plan['total_trials']!=480:
        raise ValueError('Unexpected design')
    if {r['condition']['id'] for r in result['raw']}!={c['id'] for c in plan['conditions']}:
        raise ValueError('Missing condition')
    slots = [body for group in ['sugar','bitter','water','ir94e'] for body in cells[group]['ids']]
    if len(slots)!=91 or len(set(slots))!=91:
        raise ValueError('Physical slot layout differs')
    slot_index = {body:i for i,body in enumerate(slots)}
    summary = {r['id']:r for r in result['conditions']}
    event_hashes, m0_matches = {}, 0
    rebuilt = []
    raw_rates = {}
    raw_digests = {}
    checked = 0
    for item in result['raw']:
        cond = item['condition']
        cid = cond['id']
        rows = sorted(item['rows'],key=lambda r:r['trial'])
        if len(rows)!=30 or [r['trial'] for r in rows]!=list(range(30)) or [r['seed'] for r in rows]!=list(range(20260910,20260940)):
            raise ValueError(f'Bad trial/seed ledger: {cid}')
        frequencies = {body:cond['sugar_hz'] for body in cells[cond['sugar_set']]['ids']}
        frequencies.update({body:cond['bitter_hz'] for body in cells['bitter']['ids']})
        values = {'R':[],'L':[]}
        latencies = {'R':[],'L':[]}
        for row in rows:
            p = ROOT/row['spikes']['path']
            if file_record(p)!=row['spikes']:
                raise ValueError('Raw spike file hash mismatch')
            with np.load(p,allow_pickle=False) as raw:
                body,times = raw['body_id'],raw['time_s']
                pi,pt = raw['poisson_index'],raw['poisson_time_s']
                if len(body)!=len(times) or len(pi)!=len(pt) or not np.isfinite(times).all() or not np.isfinite(pt).all():
                    raise ValueError('Malformed spike arrays')
                if (times<0).any() or (times>=1).any() or (np.diff(times)<0).any() or (pt<0).any() or (pt>=1).any() or (np.diff(pt)<0).any():
                    raise ValueError('Invalid spike times')
                if (pi<0).any() or (pi>=91).any() or row['whole_network_spikes']!=len(times):
                    raise ValueError('Invalid slot or spike count')
                observed_ids,observed_counts = np.unique(body,return_counts=True)
                counts = dict(zip(observed_ids.tolist(),observed_counts.tolist()))
                if row['source_spike_counts']!=[counts.get(i,0) for i in slots]:
                    raise ValueError('Driven-cell rate record mismatch')
                for side,root in [('R',16949),('L',10331)]:
                    st = times[body==root]
                    rate = len(st)
                    latency = float(st[0]*1000) if rate else None
                    if row[side+'_hz']!=rate or row[side+'_latency_ms']!=latency:
                        raise ValueError('MN9 rate/latency mismatch')
                    values[side].append(rate)
                    if latency is not None:
                        latencies[side].append(latency)
                hashes = []
                for slot,source_id in enumerate(slots):
                    if frequencies.get(source_id,0)==0 and np.any(pi==slot):
                        raise ValueError('Poisson events in an undriven input slot')
                    hashes.append(digest_events(pi,pt,slot))
                event_hashes[cid,row['trial']] = hashes
                raw_digests[cid,row['trial']] = (hashlib.sha256(body.tobytes()).hexdigest(),hashlib.sha256(times.tobytes()).hexdigest())
                # Existing M0 contains per-neuron arrays. Check both MN9s and all 91 physical sources.
                if row['trial']<5 and cid in ['A_s200_b0','B_s200_b0','D_s0_b0']:
                    old = DATA/'runs/m0'/('baseline' if cid=='D_s0_b0' else 'sugar200')/f'trial_{row["trial"]:02d}.npz'
                    with np.load(old,allow_pickle=False) as m0:
                        for root in slots+[16949,10331]:
                            expected = m0[str(root)] if str(root) in m0.files else np.array([])
                            np.testing.assert_array_equal(times[body==root],expected)
                            m0_matches += 1
            checked += 1
        sr = dict(cond)
        for side in ['R','L']:
            sr[side+'_mean'],sr[side+'_sd'] = float(np.mean(values[side])),float(np.std(values[side],ddof=0))
            for key in ['mean','sd']:
                if not np.isclose(sr[side+'_'+key],summary[cid][side+'_'+key],rtol=0,atol=1e-12):
                    raise ValueError('Summary mean/SD mismatch')
            med = float(np.median(latencies[side])) if latencies[side] else None
            if summary[cid][side+'_latency_median_ms']!=med or summary[cid][side+'_firing_trials']!=len(latencies[side]):
                raise ValueError('Latency summary mismatch')
        raw_rates[cid] = values
        rebuilt.append(sr)
        print(f'Audited {checked}/480 raw trials',flush=True)
    for side in ['R','L']:
        for key,value in raw_gate_checks(rebuilt,side).items():
            if result['gates'][side][key]!=value:
                raise ValueError(f'Independent gate mismatch: {side} {key}')
        diffs = np.array(raw_rates['AP_sugar_lb3c_120'][side])-np.array(raw_rates['AP_sugar_120'][side])
        expected = result['a_prime'][side]
        if not np.isclose(expected['mean_hz'],diffs.mean(),rtol=0,atol=1e-12) or not np.isclose(expected['sd_hz'],diffs.std(),rtol=0,atol=1e-12):
            raise ValueError('A-prime paired statistics mismatch')
        if (expected['lower_trials'],expected['equal_trials'],expected['higher_trials'])!=(int((diffs<0).sum()),int((diffs==0).sum()),int((diffs>0).sum())):
            raise ValueError('A-prime paired direction counts mismatch')
    shared = 0
    for trial in range(30):
        if raw_digests['A_s200_b0',trial]!=raw_digests['B_s200_b0',trial]:
            raise ValueError('Identical A200/B0 conditions differ in whole-network spikes')
        for source_id in cells['sugar']['ids']:
            slot = slot_index[source_id]
            reference = event_hashes['A_s200_b0',trial][slot]
            for bitter in [0,25,50,100,200]:
                if event_hashes[f'B_s200_b{bitter}',trial][slot]!=reference:
                    raise ValueError('Shared sugar Poisson train mismatch across bitter conditions')
                shared += 1
        for source_id in cells['sugar_lb3c']['ids']:
            slot = slot_index[source_id]
            if event_hashes['AP_sugar_120',trial][slot]!=event_hashes['AP_sugar_lb3c_120',trial][slot]:
                raise ValueError('A-prime common LB3c Poisson train mismatch')
            shared += 1
    report = {'raw_trials_verified':checked,'mn9_neuron_trials_verified':2*checked,
              'M0_neuron_train_comparisons':m0_matches,'shared_Poisson_train_comparisons':shared,
              'A200_B0_whole_network_pairs_identical':30,'bilateral_gate_reconstruction':'MATCH',
              'rates_latencies_summary_and_paired_statistics':'PASS',
              'sources':[file_record(DATA/'phase0_results.json'),ledger,file_record(Path(__file__))]}
    write_json(DATA/'phase0_audit.json',report)
    print(json.dumps(report,indent=2),flush=True)


if __name__=='__main__':
    run()
