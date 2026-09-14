# SPDX-License-Identifier: MIT
"""M1b: saved-spike and structural diagnostics only; never imports Brian2."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
from sim.malecns.substrate import ROOT, DATA, file_record, sha256, write_json
from sim.malecns.phase0 import conditions

OUT = DATA / 'runs/m1b'
THRESHOLD = 500_000
REGIONS = ('brain', 'VNC', 'crossing', 'unclassified')


def region(superclass):
    """Anatomical superclass proxy, NOT a nonexistent release region column."""
    if superclass.startswith(('ol_', 'cb_')) or superclass in ('visual_projection', 'visual_centrifugal', 'visual_projection_tbc'):
        return 'brain'
    if superclass.startswith('vnc_'):
        return 'VNC'
    if 'ascending' in superclass or 'descending' in superclass:
        return 'crossing'
    return 'unclassified'


def stats(values):
    x = np.asarray(values)
    if not len(x):
        return None
    return dict(n=len(x), mean=float(x.mean()), sd=float(x.std()),
                median=float(np.median(x)), min=float(x.min()), max=float(x.max()))


def window_counts(ids, times, labels, start, end):
    chosen = ids[(times >= start) & (times < end)]
    unique = np.unique(chosen)
    return {key: {'spikes': int(np.count_nonzero(labels.loc[chosen].to_numpy()==key)),
                  'neurons': int(np.count_nonzero(labels.loc[unique].to_numpy()==key))}
            for key in REGIONS}


def density(edges, ids, mn9, require_full=True):
    n = len(ids)
    pre = edges.Presynaptic_Index.to_numpy()
    post = edges.Postsynaptic_Index.to_numpy()
    weight = edges.Connectivity.to_numpy()
    if min(pre.min(), post.min()) < 0 or max(pre.max(),post.max()) >= n or np.any(weight <= 0):
        raise ValueError('Invalid connectivity index/count')
    degree = np.bincount(post, weights=weight, minlength=n)
    if int(degree.sum()) != int(weight.sum()):
        raise ValueError('Synapse conservation failed')
    index = {int(body): i for i,body in enumerate(ids)}
    neighborhoods = {}
    samples = []
    for side, body in mn9.items():
        selected = edges.loc[edges.Postsynaptic_Index == index[body], ['Presynaptic_Index','Connectivity']]
        selected = selected.groupby('Presynaptic_Index',as_index=False).Connectivity.sum()
        selected['body_id'] = ids[selected.Presynaptic_Index.to_numpy()]
        available = len(selected)
        selected = selected.sort_values(['Connectivity','body_id'],ascending=[False,True]).head(200)
        if require_full and len(selected)!=200:
            raise ValueError('Fewer than 200 MN9 partners')
        values = degree[selected.Presynaptic_Index.to_numpy()]
        samples.extend(values.tolist())
        neighborhoods[side] = {'mn9':body, 'available_partners':available, 'selected_partners':len(selected),
                              'incoming_synapses':int(degree[index[body]]),
                              'partner_indegree':stats(values),
                              'partners':[{'body_id':int(b), 'synapses_to_mn9':int(w), 'indegree':int(d)}
                                          for b,w,d in zip(selected.body_id,selected.Connectivity,values)]}
    return {'neurons':n, 'edges':len(edges), 'synapses':int(weight.sum()),
            'all':stats(degree), 'mn9_available_pooled':stats(samples), 'neighborhoods':neighborhoods}


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    final = DATA/'m1b_diagnosis.json'
    if final.exists():
        raise FileExistsError('M1b record already exists; do not overwrite it')
    record = json.loads((DATA/'substrate_record.json').read_text())
    inputs = [record['sources']['annotations'], record['artifacts']['neuron_index'],
              record['artifacts']['signed_connectivity']]
    for source in inputs:
        if sha256(ROOT/source['path']) != source['sha256']:
            raise ValueError(f"Source hash mismatch: {source['path']}")
    roster = pd.read_csv(DATA/'derived/neuron_index.csv',usecols=['index','bodyId','superclass']).sort_values('index')
    annotations = pd.read_feather(ROOT/record['sources']['annotations']['path'])
    if 'region' in annotations.columns:
        raise ValueError('Source schema changed; review anatomical grouping')
    labels = roster.set_index('bodyId').superclass.map(region)
    trials=[]
    for condition in conditions():
        name=condition['id']
        for trial in range(30):
            path=DATA/f'runs/m1/{name}/trial_{trial:02d}.json'
            ledger=json.loads(path.read_text())
            spike_path=ROOT/ledger['spikes']['path']
            if sha256(spike_path)!=ledger['spikes']['sha256']:
                raise ValueError(f'Spike hash mismatch {spike_path}')
            with np.load(spike_path,allow_pickle=False) as z:
                ids=z['body_id']; times=z['time_s']
                if len(ids)!=ledger['whole_network_spikes'] or len(ids)!=len(times):
                    raise ValueError('Spike count mismatch')
                if np.any(times<0) or np.any(times>=1) or not np.isin(ids,roster.bodyId).all():
                    raise ValueError('Invalid spike IDs/times')
                row={'condition':name,'trial':trial,'seed':ledger['seed'],
                     'spikes':len(ids),'neurons':len(np.unique(ids)),
                     'group':'runaway' if len(ids)>=THRESHOLD else 'quiet',
                     'first_1000_ms':float(np.partition(times,999)[999]*1000) if len(ids)>=1000 else None,
                     'R_hz':int(np.count_nonzero(ids==16949)), 'L_hz':int(np.count_nonzero(ids==10331)),
                     'spikes_sha256':ledger['spikes']['sha256']}
                for side in ('R','L'):
                    if row[f'{side}_hz']!=ledger[f'{side}_hz']:
                        raise ValueError('MN9 rate mismatch')
                for key,start,end in [('early',0,.05),('late',.5,1)]:
                    row[key]=window_counts(ids,times,labels,start,end)
                # Per-window total activity exposes growth without a regional inference.
                row['spikes_per_50ms']=np.histogram(times,bins=np.linspace(0,1,21))[0].tolist()
                trials.append(row)
        print(f'Checked {name}: 30 saved trials',flush=True)
    summaries=[]
    for condition in conditions():
        rows=[r for r in trials if r['condition']==condition['id']]
        summaries.append({'condition':condition['id'],'spikes':stats([r['spikes'] for r in rows]),
                          'neurons':stats([r['neurons'] for r in rows]),
                          'runaway_n':sum(r['group']=='runaway' for r in rows)})
    selected=['A_s25_b0','B_s200_b25','C_s0_b25']
    groups=[]
    for name in selected:
        for group in ('quiet','runaway'):
            rows=[r for r in trials if r['condition']==name and r['group']==group]
            item={'condition':name,'group':group,'n':len(rows),
                  'trials':[r['trial'] for r in rows],
                  'R_hz':stats([r['R_hz'] for r in rows]),'L_hz':stats([r['L_hz'] for r in rows]),
                  'first_1000_ms':stats([r['first_1000_ms'] for r in rows if r['first_1000_ms'] is not None])}
            for window in ('early','late'):
                item[window]={key:{metric:stats([r[window][key][metric] for r in rows])
                                  for metric in ('spikes','neurons')} for key in REGIONS}
                item[window+'_pooled_spike_share']={key:sum(r[window][key]['spikes'] for r in rows)/max(1,sum(r[window][k]['spikes'] for r in rows for k in REGIONS)) for key in REGIONS}
            groups.append(item)
    male_edges=pd.read_parquet(DATA/'derived/connectivity.parquet',columns=['Presynaptic_Index','Postsynaptic_Index','Connectivity'])
    # Explicit incomplete-neighborhood diagnostic, NOT the requested r_mn9.
    male=density(male_edges,roster.bodyId.to_numpy(),{'contra':16949,'ipsi':10331},require_full=False)
    del male_edges
    female_protocol=json.loads((ROOT/'data/stim_protocol.json').read_text())
    female_ids=pd.read_csv(ROOT/female_protocol['completeness_file'],index_col=0).index.to_numpy(dtype=np.int64)
    female_edges=pd.read_parquet(ROOT/female_protocol['connectivity_file'],columns=['Presynaptic_Index','Postsynaptic_Index','Connectivity'])
    female=density(female_edges,female_ids,{'contra':720575940660219265,'ipsi':720575940618238523})
    ratios={'all':{measure:male['all'][measure]/female['all'][measure] for measure in ('mean','median')}}
    ratios['by_side']={side:{measure:male['neighborhoods'][side]['partner_indegree'][measure]/female['neighborhoods'][side]['partner_indegree'][measure] for measure in ('mean','median')} for side in ('contra','ipsi')}
    alternative=sum(male['neighborhoods'][s]['partner_indegree']['mean'] for s in ('contra','ipsi'))/sum(female['neighborhoods'][s]['partner_indegree']['mean'] for s in ('contra','ipsi'))
    full={'trials':trials, 'male_density':male, 'female_density':female}
    full_path=OUT/'full_diagnosis.json'
    write_json(full_path,full)
    result={'stage':'M1b_saved_spikes_only','simulation_runs':0,
            'split':{'threshold_spikes':THRESHOLD,'rule':'quiet < 500000; runaway >= 500000 in 1 s; descriptive analyst label, not a model/biological gate',
                     'sensitivity':{str(t):{name:sum(r['spikes']>=t for r in trials if r['condition']==name) for name in selected} for t in (300000,500000,750000)}},
            'region_proxy':{'source_field':'superclass','missing_requested_field':'region',
                            'mapping':{s:region(s) for s in sorted(roster.superclass.unique())},
                            'roster_counts':labels.value_counts().to_dict(),
                            'caveat':'Neuron-class proxy, not synapse locations; crossing/ENS not forced into brain or VNC'},
            'conditions':summaries,'groups':groups,
            'runaway_by_condition':[{'condition':c['id'], 'n':len(rs),
                                    'first_1000_ms':stats([r['first_1000_ms'] for r in rs]),
                                    'windows':{w:{k:{m:stats([r[w][k][m] for r in rs]) for m in ('spikes','neurons')} for k in REGIONS} for w in ('early','late')}}
                                   for c in conditions() if (rs:=[r for r in trials if r['condition']==c['id'] and r['group']=='runaway'])],
            'density':{'definition':'unsigned sum of incoming Connectivity counts, including zero-input roster neurons; strongest means synapses from partner to MN9, tie-break numeric body ID; measure ALL incoming synapses of selected partners. Exact 200-per-side comparison unavailable: male R has only 137. Available-neighborhood diagnostic uses 137 male R, 200 male L and 200 each female, NOT silently padded to 200.',
                       'male':{k:v for k,v in male.items() if k!='neighborhoods'},
                       'female':{k:v for k,v in female.items() if k!='neighborhoods'},'ratios':ratios},
            'proposed_candidates':{'status':'awaiting M1b owner confirmation; no simulation',
                                   'base_w_syn_mV':female_protocol['model']['w_syn_mV'],
                                   'r_all':ratios['all']['mean'], 'r_mn9':None,
                                   'all_w_syn_mV':female_protocol['model']['w_syn_mV']/ratios['all']['mean'],
                                   'mn9_w_syn_mV':None,
                                   'alternative_needs_owner_approval':{'definition':'min(200, available) per MN9; ratio of equally weighted side mean indegrees (not pooled 337 vs 400 sample mean)',
                                                                     'ratio':alternative, 'w_syn_mV':female_protocol['model']['w_syn_mV']/alternative}},
            'sources':inputs+[file_record(ROOT/female_protocol[k]) for k in ('connectivity_file','completeness_file')]+[file_record(DATA/'phase0_results.json'),file_record(Path(__file__))],
            'full_ledger':file_record(full_path)}
    write_json(final,result)
    print(json.dumps(result['density']['ratios'],indent=2))
    print(json.dumps(result['proposed_candidates'],indent=2))


if __name__=='__main__':
    main()
