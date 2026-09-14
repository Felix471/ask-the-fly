# SPDX-License-Identifier: MIT
"""Read-only source extraction for MN9 cross-brain mapping and ROI capture."""
import csv
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'data/malecns'
COMMIT='67767d2233657983993ff6c2be48e836a935863c'
BASE=f'https://github.com/flyconnectome/2025malecns/blob/{COMMIT}/'


def source(path,url=None):
    b=path.read_bytes()
    r={'path':path.relative_to(ROOT).as_posix(),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
    if url:
        r['url']=url
    return r


def extract():
    mapping_path=DATA/'downloads/mcns_fw_edge_comp_mappings.json'
    capture_path=DATA/'downloads/male-cns-v1.0-traced-synapse-capture-by-roi.csv'
    neuprint_path=DATA/'runs/m1c_preflight/neuprint.json'
    mapping=json.loads(mapping_path.read_text())
    female=['720575940660219265','720575940618238523']
    labels={mapping[i] for i in female}
    if len(labels)!=1:
        raise ValueError('Female MN9 IDs do not share one mapping label')
    label=next(iter(labels))
    matches={i:v for i,v in mapping.items() if v==label}
    male=sorted(int(i) for i in matches if i not in female)
    # Protect against accidentally treating an additional FlyWire ID as male.
    if male!=[10331,16949]:
        raise ValueError('Mapping membership changed; inspect substrate identity before classifying')
    with capture_path.open(newline='',encoding='utf-8') as f:
        capture=list(csv.DictReader(f))
    saved=json.loads(neuprint_path.read_text())
    bodies=[]
    all_rois=set()
    for wrapped in saved['response']['data']:
        n=wrapped[0]
        roi=json.loads(n['roiInfo'])
        all_rois.update(roi)
        if roi['GNG']['post']+roi['CentralBrain-unspecified']['post']!=n['post']:
            raise ValueError('Leaf ROI post counts do not reconcile')
        bodies.append({'body_id':n['bodyId'],'side':n['somaSide'],'status':n['status'],
                       'statusLabel':n['statusLabel'],'flywireType':n['flywireType'],
                       'mapping_label':mapping.get(str(n['bodyId'])),'roiInfo':roi,
                       'total_post':n['post']})
    rows=[]
    for roi in sorted(all_rois):
        selected=[(i+2,r) for i,r in enumerate(capture) if r['roi']==roi]
        if not selected:
            rows.append({'roi':roi,'capture':None,'reason':'No row with this ROI in the requested CSV'})
            continue
        if len(selected)!=1:
            raise ValueError('Duplicate ROI capture row')
        line,r=selected[0]
        typed={k:int(v) if k in ['PreSyn','PostSyn'] else float(v) if k.endswith('_frac') else v for k,v in r.items()}
        rows.append({'roi':roi,'csv_line':line,'capture':typed})
    return {'scope':'Requested mapping/capture additions only; no simulation or conclusion',
            'source_commit':COMMIT,'cross_matched_label':label,'female_MN9_ids':female,
            'all_label_members':matches,'male_body_ids':male,'16949_in_mapping':16949 in male,
            'mapping_semantics':'Neuron-to-cross-matched-group labels for the edge comparison; not one-to-one body pairing.',
            'neuprint_retrieved_utc':saved['retrieved_utc'],'neuprint_dataset':saved['query']['dataset'],
            'bodies':bodies,'roi_capture':rows,
            'roi_limit':'Local body-annotation export has no dendrite ROI field. neuPrint roiInfo localizes postsynapses, not segmented dendritic arbors. GNG and CentralBrain-unspecified are disjoint here; CentralBrain is their parent and must not be added again.',
            'capture_definitions':{'presyn_traced_frac':'Fraction of ROI presynapses belonging to proofread neurons.',
                'postsyn_traced_frac':'Fraction of ROI postsynapses belonging to proofread neurons.',
                'conn_traced_frac':'Fraction of ROI synaptic connections with both endpoints proofread.'},
            'capture_limit':'ROI-wide population fractions, not a completeness fraction for either MN9. No GNG side-specific rows; no CentralBrain-unspecified row; do not substitute the parent fraction.',
            'sources':[source(mapping_path,BASE+'supplemental_data/'+mapping_path.name),
                       source(capture_path,BASE+'supplemental_data/'+capture_path.name),
                       source(neuprint_path,'https://neuprint.janelia.org/'),
                       source(DATA/'downloads/body-annotations-male-cns-v1.0-minconf-0.5.feather')],
            'definitions_source':BASE+'README.md#synapse-capture'}


def render():
    d=json.loads((DATA/'mn9_mapping_capture.json').read_text())
    lines=['### Additional mapping and ROI-capture check', '',
           '**Source check only; no new conclusion.** In the '
           f"[cross-brain mapping]({d['sources'][0]['url']}), both female MN9 IDs "
           '`720575940660219265` and `720575940618238523` have the label **CB0701**. '
           'Exactly two male bodies share that label: **10331 and 16949**. Thus **16949 is included**. '
           'These four IDs are the complete label group; this mapping is a cross-matched group '
           'assignment, not a one-to-one left/right pairing.', '',
           'The saved neuPrint response (`male-cns:v1.0`, retrieved '+d['neuprint_retrieved_utc']+') '
           'gives the following status and postsynaptic ROI counts. The local body-annotation export '
           'has no dendrite-ROI field; `roiInfo.post` identifies input locations, **not explicitly '
           'segmented dendritic arbors**.', '',
           '| Male body / side | status | statusLabel | Mapping label | GNG postsynapses | CentralBrain-unspecified postsynapses |',
           '|---|---|---|---|---:|---:|']
    for n in sorted(d['bodies'],key=lambda n:n['side'],reverse=True):
        lines.append(f"| {n['body_id']} / {n['side']} | {n['status']} | {n['statusLabel']} | {n['mapping_label']} | {n['roiInfo']['GNG']['post']:,} | {n['roiInfo']['CentralBrain-unspecified']['post']:,} |")
    lines += ['', 'These leaf counts sum to 633 (R) and 6,358 (L). `CentralBrain` is the parent ROI, '
              'not an additional disjoint compartment. Both leaf ROIs contain postsynapses in both bodies.', '',
              f"The requested [capture CSV]({d['sources'][1]['url']}) reports ROI-wide fractions:", '',
              '| ROI | Presynapses on proofread neurons | Postsynapses on proofread neurons | Connections with both endpoints proofread |',
              '|---|---:|---:|---:|']
    rows={r['roi']:r for r in d['roi_capture']}
    for roi in ['GNG','CentralBrain-unspecified','CentralBrain']:
        r=rows[roi]['capture']
        label=roi+' (parent, context only)' if roi=='CentralBrain' else roi
        values=['not reported']*3 if r is None else [f'{100*r[k]:.4f}%' for k in ['presyn_traced_frac','postsyn_traced_frac','conn_traced_frac']]
        lines.append('| '+label+' | '+' | '.join(values)+' |')
    lines += ['', 'GNG is CSV line 31; CentralBrain is line 3 (header counted). There is no '
              '`CentralBrain-unspecified` row and no left/right GNG breakdown. The parent fraction '
              'is not substituted for the missing leaf fraction. These are **ROI-wide capture '
              'fractions, not either MN9’s tracing-completeness percentage**. '
              f"[Source definitions]({d['definitions_source']}); "
              '[extracted fields, source commit, sizes and SHA256 hashes](../data/malecns/mn9_mapping_capture.json). '
              'No simulation, body substitution, verdict or causal conclusion is added.', '']
    return '\n'.join(lines)


if __name__=='__main__':
    result=extract()
    with (DATA/'mn9_mapping_capture.json').open('x',encoding='utf-8',newline='\n') as f:
        json.dump(result,f,ensure_ascii=False,indent=2)
        f.write('\n')
    print(json.dumps(result,indent=2))
