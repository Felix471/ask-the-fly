# SPDX-License-Identifier: MIT
"""Independent saved-record crosschecks and time-binned regional spike shares."""
import json
import numpy as np
import pandas as pd
from sim.malecns.substrate import DATA, ROOT, sha256, write_json, file_record


def main():
    d=json.loads((DATA/'m1b_diagnosis.json').read_text())
    path=ROOT/d['full_ledger']['path']
    assert sha256(path)==d['full_ledger']['sha256']
    full=json.loads(path.read_text())
    rows=full['trials']
    assert len(rows)==480
    for c in d['conditions']:
        r=[x for x in rows if x['condition']==c['condition']]
        assert len(r)==30 and sorted(x['trial'] for x in r)==list(range(30))
        assert all(x['seed']==20260910+x['trial'] for x in r)
        for metric in ('spikes','neurons'):
            values=sorted(x[metric] for x in r)
            assert c[metric]['median']==(values[14]+values[15])/2
            assert c[metric]['min']==values[0] and c[metric]['max']==values[-1]
        for x in r:
            assert sum(x['spikes_per_50ms'])==x['spikes']
            assert sum(x['early'][k]['spikes'] for k in x['early'])==x['spikes_per_50ms'][0]
            assert sum(x['late'][k]['spikes'] for k in x['late'])==sum(x['spikes_per_50ms'][10:])
    # Reconstruct degrees with pandas groupby, independently of bincount implementation.
    protocol=json.loads((ROOT/'data/stim_protocol.json').read_text())
    for sex,graph,roster in [('male',DATA/'derived/connectivity.parquet',None),
                              ('female',ROOT/protocol['connectivity_file'],None)]:
        e=pd.read_parquet(graph,columns=['Presynaptic_Index','Postsynaptic_Index','Connectivity'])
        expected=full[sex+'_density']
        degrees=e.groupby('Postsynaptic_Index').Connectivity.sum().reindex(range(expected['neurons']),fill_value=0)
        assert float(degrees.mean())==expected['all']['mean']
        assert float(degrees.median())==expected['all']['median']
        if sex=='male':
            ids=pd.read_csv(DATA/'derived/neuron_index.csv',usecols=['bodyId']).bodyId.tolist()
        else:
            ids=pd.read_csv(ROOT/protocol['completeness_file'],index_col=0).index.tolist()
        lookup={b:i for i,b in enumerate(ids)}
        for side,n in expected['neighborhoods'].items():
            actual=e.loc[e.Postsynaptic_Index==lookup[n['mn9']]].groupby('Presynaptic_Index').Connectivity.sum()
            ranked=sorted([(int(w),ids[int(i)]) for i,w in actual.items()],key=lambda x:(-x[0],x[1]))[:200]
            assert [b for _,b in ranked]==[x['body_id'] for x in n['partners']]
            assert [int(degrees.loc[lookup[b]]) for _,b in ranked]==[x['indegree'] for x in n['partners']]
        del e
    roster=pd.read_csv(DATA/'derived/neuron_index.csv',usecols=['bodyId','superclass']).sort_values('bodyId')
    ids=roster.bodyId.to_numpy()
    keys=['brain','VNC','crossing','unclassified']
    codes=roster.superclass.map(d['region_proxy']['mapping']).map({k:i for i,k in enumerate(keys)}).to_numpy()
    selected=['A_s25_b0','B_s200_b25','C_s0_b25']
    regional=[]
    for r in rows:
        if r['condition'] not in selected or r['group']!='runaway':
            continue
        with np.load(DATA/f"runs/m1/{r['condition']}/trial_{r['trial']:02d}.npz") as z:
            body=z['body_id']; times=z['time_s']
            assert float(np.sort(times)[999]*1000)==r['first_1000_ms']
            region_codes=codes[np.searchsorted(ids,body)]
            binned=np.histogram2d(times,region_codes,bins=[np.linspace(0,1,21),np.arange(5)-.5])[0].astype(int)
            assert binned.sum()==len(body)
            for region_i,key in enumerate(keys):
                assert binned[0,region_i]==r['early'][key]['spikes']
                assert binned[10:,region_i].sum()==r['late'][key]['spikes']
            regional.append({'condition':r['condition'],'trial':r['trial'],'spikes_per_bin_brain_vnc_crossing_unclassified':binned.tolist()})
    pooled={name:np.sum([x['spikes_per_bin_brain_vnc_crossing_unclassified'] for x in regional if x['condition']==name],axis=0) for name in selected}
    maxima={name:float((bins[:,1]/np.maximum(1,bins.sum(axis=1))).max()) for name,bins in pooled.items()}
    vnc_majority=[{'condition':r['condition'],'trial':r['trial'],'bin':i,'spikes':bin_counts} for r in regional
                  for i,bin_counts in enumerate(r['spikes_per_bin_brain_vnc_crossing_unclassified']) if bin_counts[1]>sum(bin_counts)/2]
    result={'verified_trials':480, 'verified_top_partner_rows':737,
            'onset_and_region_rechecks':len(regional),
            'network_bins':'20 half-open 50-ms bins, spike counts (not neuron counts)',
            'selected_conditions_max_pooled_vnc_share_any_50ms_bin':maxima,
            'individual_trial_bins_with_vnc_majority':vnc_majority,
            'region_bin_trials':regional, 'diagnosis':file_record(DATA/'m1b_diagnosis.json')}
    write_json(DATA/'runs/m1b/audit.json',result)
    print(json.dumps({k:v for k,v in result.items() if k!='region_bin_trials'},indent=2))


if __name__=='__main__':
    main()
