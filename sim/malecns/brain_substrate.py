"""M1f endpoint-based brain-only substrate and mean in-degree; no simulation."""
from datetime import datetime, timezone
import json
from pathlib import Path
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from sim.malecns.substrate import DATA, ROOT, file_record, write_json, verify_record, FILENAMES, make_roster

TARGET=DATA/'derived/brain'
RECORD=DATA/'substrate_record_brain.json'
RATIONALE=('Female FlyWire contains no VNC and Shiu parameters were calibrated brain-only. '
           'A male brain-only endpoint cut is a structural substrate comparison, not a fitted weight. '
           'Hypnagogia reports about80Hz male MN9 at200Hz with brain-only scope and0.581 count scaling; '
           'that different design motivates testing scope but does not set our weight or prove equivalence.')


def brain_mask(roster):
    return ~roster.superclass.str.startswith('vnc_') & roster.superclass.ne('ENS')


def verify():
    record=json.loads(RECORD.read_text())
    for f in record['sources']+list(record['artifacts'].values())+[record['builder']]:
        actual=file_record(ROOT/f['path'])
        if any(actual[k]!=f[k] for k in actual):
            raise ValueError('Brain freeze changed: '+f['path'])
    return record


def build():
    original=verify_record()
    if TARGET.exists() or RECORD.exists():
        raise FileExistsError('Do not overwrite brain freeze')
    a=pd.read_feather(DATA/'downloads'/FILENAMES['annotations'])
    nt=pd.read_feather(DATA/'downloads'/FILENAMES['neurotransmitters'])
    roster=make_roster(a,nt); mask=brain_mask(roster)
    kept=roster.loc[mask].copy().reset_index(drop=True)
    mapping=np.full(len(roster),-1,dtype='int32'); mapping[np.flatnonzero(mask)]=np.arange(len(kept),dtype='int32')
    kept['index']=np.arange(len(kept),dtype='int32')
    cells=json.loads((DATA/'cells.json').read_text())['sets']
    required={16949,10331}|{b for s in cells.values() for b in s['ids']}
    if not required.issubset(set(kept.bodyId)):
        raise ValueError('Brain cut removes required input/readout')
    TARGET.mkdir()
    kept.to_csv(TARGET/'neuron_index.csv',index=False,lineterminator='\n')
    pd.DataFrame(index=pd.Index(kept.bodyId,name='bodyId')).to_csv(TARGET/'completeness.csv',lineterminator='\n')
    degree=np.zeros(len(kept),dtype='int64'); edges=synapses=0
    reader=pq.ParquetFile(DATA/'derived/connectivity.parquet'); writer=None
    try:
        for batch in reader.iter_batches(batch_size=500000):
            df=batch.to_pandas(); pre=mapping[df.Presynaptic_Index.to_numpy()]; post=mapping[df.Postsynaptic_Index.to_numpy()]
            good=(pre>=0)&(post>=0); df=df.loc[good].copy()
            df['Presynaptic_Index']=pre[good]; df['Postsynaptic_Index']=post[good]
            table=pa.Table.from_pandas(df,preserve_index=False)
            if writer is None:
                writer=pq.ParquetWriter(TARGET/'connectivity.parquet',table.schema,compression='zstd')
            writer.write_table(table)
            np.add.at(degree,post[good],df.Connectivity.to_numpy())
            edges+=len(df); synapses+=int(df.Connectivity.sum())
    finally:
        if writer is not None:
            writer.close()
    assert degree.sum()==synapses
    female=json.loads((ROOT/'data/stim_protocol.json').read_text())
    fids=pd.read_csv(ROOT/female['completeness_file'],index_col=0).index
    fdegree=np.zeros(len(fids),dtype='int64')
    for batch in pq.ParquetFile(ROOT/female['connectivity_file']).iter_batches(columns=['Postsynaptic_Index','Connectivity']):
        df=batch.to_pandas(); np.add.at(fdegree,df.Postsynaptic_Index.to_numpy(),df.Connectivity.to_numpy())
    ratio=float(degree.mean()/fdegree.mean())
    r_all=json.loads((DATA/'m1b_diagnosis.json').read_text())['proposed_candidates']['r_all']
    counts={'neurons':len(kept),'edges':edges,'synapses':synapses,
            'removed_neurons':len(roster)-len(kept),'removed_edges':original['counts']['edges']-edges,
            'removed_synapses':original['counts']['synapses']-synapses,
            'retained_superclasses':{k:int(v) for k,v in kept.superclass.value_counts().items()},
            'dropped_superclasses':{k:int(v) for k,v in roster.loc[~mask].superclass.value_counts().items()},
            'positive_neurons':int((kept.sign==1).sum()),'negative_neurons':int((kept.sign==-1).sum()),
            'default_positive_neurons':int(kept.default_positive.sum())}
    record={'stage':'M1f','built_utc':datetime.now(timezone.utc).isoformat(),'structural_rationale':RATIONALE,
            'scope':'Brain-only endpoint approximation, retaining crossing neurons',
            'cut':'Original superclass-nonnull roster; drop vnc_* and ENS, retain every other class including ascending/descending; no new status filter.',
            'synapse_location':'Unavailable in aggregate weights (only body_pre/body_post/weight). No partner-file download. Remove edges incident on any dropped body; retain all counts between retained bodies. VNC-local contacts between retained crossing bodies remain; brain contacts on removed bodies are also lost.',
            'hypnagogia':{'source':'https://github.com/ankthba/hypnagogia/blob/86da5f93e25a2f1ac78c2fa810f34a4a57992b66/src/hypnagogia/connectome.py#L342-L371',
                          'same':'drop vnc_* and ENS; retain crossing cells; endpoint rather than synapse-location cut',
                          'different':'They additionally require status Traced, report144209neurons, use histamine negative/DPM correction/gradedAPL and0.581scaling. We retain original roster/sign rule and compute r_brain, not adopt0.581.'},
            'counts':counts,'density':{'definition':'Mean unsigned incoming synapse counts over every retained neuron, including isolated; female frozen roster denominator.',
                                      'male_mean':float(degree.mean()),'male_median':float(np.median(degree)),
                                      'female_neurons':len(fdegree),'female_synapses':int(fdegree.sum()),
                                      'female_mean':float(fdegree.mean()),'female_median':float(np.median(fdegree)),
                                      'r_brain':ratio,'r_all':r_all,'scaled_w_syn_rec_mV':0.275/ratio},
            'sign_rule':original['sign_rule'],
            'sources':[file_record(DATA/'substrate_record.json'),original['artifacts']['signed_connectivity'],
                       original['sources']['annotations'],original['sources']['neurotransmitters'],
                       file_record(ROOT/female['connectivity_file']),file_record(ROOT/female['completeness_file'])],
            'builder':file_record(Path(__file__)),
            'artifacts':{name:file_record(TARGET/name) for name in ['neuron_index.csv','completeness.csv','connectivity.parquet']}}
    write_json(RECORD,record)
    print(json.dumps({'counts':counts,'density':record['density']},indent=2))
    verify()


if __name__=='__main__':
    build()
