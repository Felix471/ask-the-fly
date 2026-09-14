# SPDX-License-Identifier: MIT
"""Read saved female replays, Table S1 and live neuPrint metadata; no simulation."""
import json
import argparse
import subprocess
from datetime import datetime, timezone
import numpy as np
import pandas as pd
from urllib.request import Request, urlopen
from sim.malecns.substrate import ROOT, DATA, WORKBOOK, file_record, write_json


def main(workbook_python):
    out=DATA/'runs/m1c_preflight'
    out.mkdir(parents=True,exist_ok=True)
    query={'dataset':'male-cns:v1.0',
           'cypher':"MATCH (n:Neuron) WHERE n.type = 'MN9' OR n.bodyId IN [16949,10331] RETURN properties(n) ORDER BY n.bodyId"}
    request=Request('https://neuprint.janelia.org/api/custom/custom',data=json.dumps(query).encode(),headers={'Content-Type':'application/json'})
    saved=out/'neuprint.json'
    if saved.exists():
        prior=json.loads(saved.read_text())
        assert prior['query']==query
        payload=prior['response']
    else:
        with urlopen(request,timeout=45) as response:
            payload=json.load(response)
        write_json(saved,{'retrieved_utc':datetime.now(timezone.utc).isoformat(),'query':query,'response':payload})
    live=[row[0] for row in payload['data']]
    annotations=pd.read_feather(DATA/'downloads/body-annotations-male-cns-v1.0-minconf-0.5.feather')
    release=annotations[annotations['type'].eq('MN9') | annotations.bodyId.isin([16949,10331])]
    # Use the bundled spreadsheet reader; this process supplies parquet support.
    code="import pandas as p,sys; a=p.read_excel(sys.argv[1],sheet_name='MNs'); a['xlsx_row']=a.index+2; print(a.to_json(orient='records'))"
    workbook=pd.DataFrame(json.loads(subprocess.check_output([workbook_python,'-c',code,str(WORKBOOK)],text=True)))
    mn9=workbook[workbook.Connectome.eq('maleCNS') & workbook.Type.eq('MN9')]
    columns=['bodyId','type','instance','somaSide','status','statusLabel','cropped','pre','post','size','statusConfidence','tracingCompleteness','matchingNotes','dimorphism','rootSide','somaNeuromere','exitNerve','group']
    rows=[]
    for _,r in mn9.iterrows():
        b=int(r.Body_ID)
        a=release[release.bodyId==b].iloc[0]
        n=next(n for n in live if n['bodyId']==b)
        rows.append({'body_id':b,'xlsx_row':int(r.xlsx_row),'xlsx_side':r.Root_Side,
                     'live':{k:n.get(k) for k in columns},'live_property_keys':sorted(n),
                     'release_status':a.status,'release_statusLabel':a.statusLabel,
                     'missing_metadata_policy':'Absent/cropped null is unknown, not proof of complete tracing; no numerical tracing completeness available in these fields.'})
    targets=[('A_s25_b0',None,[25,0,0,0]),
             ('A_s200_b0','G_svery_high_bnone_wnone_inone',[200,0,0,0]),
             ('B_s200_b100','G_svery_high_bhigh_wnone_inone',[200,100,0,0]),
             ('C_s0_b25',None,[0,25,0,0]),
             ('D_s0_b0','G_snone_bnone_wnone_inone',[0,0,0,0])]
    comparisons=[]
    for condition,cell,rates in targets:
        r={'male_condition':condition,'requested_rates_hz':rates,'female_cell':cell,'n_trials':0}
        if cell is None:
            r.update(status='unavailable: 25 Hz is not a frozen female grid level',network_spikes=None,neurons_fired=None)
        else:
            path=ROOT/f'results/replay/{cell}.npz'
            with np.load(path,allow_pickle=False) as z:
                assert np.array_equal(z['rates'],rates)
                assert len(z['flywire_id'])==len(z['t_ms'])
                assert np.all((z['t_ms']>=0)&(z['t_ms']<1000))
                r.update(status='saved full-network replay, n=1, not paired with male seeds',n_trials=1,
                         network_spikes=len(z['flywire_id']),neurons_fired=len(np.unique(z['flywire_id'])),
                         seed=int(z['seed']),condition_index=int(z['condition_index']),source=file_record(path))
        comparisons.append(r)
    record={'stage':'M1c additions, no simulation','female_activity':comparisons,
            'mn9_status':rows,'all_release_mn9_ids':release.bodyId.astype(int).tolist(),
            'all_live_mn9_ids':[n['bodyId'] for n in live],
            'all_workbook_mn9_ids':mn9.Body_ID.astype(int).tolist(),
            'workbook_sheet':'MNs','workbook_range':'A66:G67',
            'sources':[file_record(WORKBOOK),file_record(DATA/'downloads/body-annotations-male-cns-v1.0-minconf-0.5.feather'),
                       file_record(out/'neuprint.json'),file_record(ROOT/'data/grid_levels.json'),file_record(ROOT/'results/replay/run_meta.json')],
            'interpretation':'R16949 hard-to-trace status and 556 vs 6012 proofread-substrate input synapses make reconstruction incompleteness a likely cause of laterality reversal; hypothesis, not established, pending bilateral M1c. No substitute MN9 identified.'}
    write_json(DATA/'rescale_preflight.json',record)
    print(json.dumps(record,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workbook-python',required=True)
    main(parser.parse_args().workbook_python)
