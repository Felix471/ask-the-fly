"""Independent edge retention and saved-event checks for M1h; no simulation."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from sim.malecns import density_matched_phase0 as brain_phase0, rescale, split
from sim.malecns.audit_phase0 import raw_gate_checks
from sim.malecns.substrate import DATA,ROOT,file_record,write_json


def audit_runs():
    brain_phase0.verify_substrate()
    plan=json.loads(brain_phase0.PLAN.read_text()); brain_phase0.check_sources(plan)
    outputs={}
    cells=json.loads((DATA/'cells.json').read_text())['sets']
    slots=[b for c in ['sugar','bitter','water','ir94e'] for b in cells[c]['ids']]
    for candidate in brain_phase0.CANDIDATES:
        compact=json.loads((DATA/'m1h_results.json').read_text())
        assert file_record(ROOT/compact['raw_ledger']['path'])==compact['raw_ledger']
        full=json.loads((ROOT/compact['raw_ledger']['path']).read_text())
        assert {k:v for k,v in full.items() if k!='raw'}=={k:v for k,v in compact.items() if k!='raw_ledger'}
        assert file_record(brain_phase0.PLAN)==compact['metadata']['plan']
        rebuilt=[]; checked=0; networks={}; inputs={}
        for group in full['raw']:
            c=group['condition']; rows=[]
            for row in group['rows']:
                assert row['seed']==20260910+row['trial']
                assert file_record(ROOT/row['spikes']['path'])==row['spikes']
                with np.load(ROOT/row['spikes']['path'],allow_pickle=False) as z:
                    body,t=z['body_id'],z['time_s']; pi,pt=z['poisson_index'],z['poisson_time_s']
                    for times in [t,pt]:
                        assert np.isfinite(times).all() and (times>=0).all() and (times<1).all() and (np.diff(times)>=0).all()
                    for side,b in [('L',10331),('R',16949)]:
                        st=t[body==b]
                        assert row[side+'_hz']==len(st)
                        assert row[side+'_latency_ms']==(float(st[0]*1000) if len(st) else None)
                    ids,counts=np.unique(body,return_counts=True); cm=dict(zip(ids,counts))
                    assert row['source_spike_counts']==[cm.get(b,0) for b in slots]
                    assert row['whole_network_spikes']==len(t) and row['neurons_fired']==len(ids)
                    key=(c['id'],row['trial'])
                    networks[key]=hashlib.sha256(body.tobytes()+t.tobytes()).hexdigest()
                    inputs[key]=[hashlib.sha256(pt[pi==i].tobytes()).hexdigest() for i in range(91)]
                    with np.load(DATA/'runs/m1'/c['id']/f'trial_{row["trial"]:02d}.npz',allow_pickle=False) as old:
                        np.testing.assert_array_equal(pi,old['poisson_index']); np.testing.assert_array_equal(pt,old['poisson_time_s'])
                    checked+=1
                rows.append(row)
            rebuilt.append(dict(group,rows=rows))
            print(f'M1h audit {candidate}: {checked}/480',flush=True)
        summary=rescale.summarize(rebuilt)
        for key in ['conditions','gates','a_prime']:
            assert summary[key]==compact[key]
        for side in ['L','R']:
            for k,v in raw_gate_checks(summary['conditions'],side).items():
                assert compact['gates'][side][k]==v
        assert split.shape_gate(summary['conditions'])==compact['shape_gate']
        assert compact['overall_primary']==(compact['gates']['L']['overall'] and compact['shape_gate']['S'])
        for trial in range(30):
            assert networks['A_s200_b0',trial]==networks['B_s200_b0',trial]
            for b in cells['sugar_lb3c']['ids']:
                i=slots.index(b)
                assert inputs['AP_sugar_120',trial][i]==inputs['AP_sugar_lb3c_120',trial][i]
        assert checked==480
        p=json.loads(brain_phase0.protocol_path(candidate).read_text())
        for f in compact['metadata']['weight_logs']:
            assert file_record(ROOT/f['path'])==f
            log=json.loads((ROOT/f['path']).read_text())
            assert log['candidate']==candidate
            for observation in log['weights']:
                for key in ['stimulus_mV_min','stimulus_mV_max']:
                    assert observation[key]==68.75
                for key in ['recurrent_unit_mV_min','recurrent_unit_mV_max']:
                    assert abs(observation[key]-p['model']['w_syn_mV'])<1e-12
        outputs[candidate]={'raw_trials':checked,'MN9_neuron_trials':960,'M1_input_arrays_identical':checked,
                            'A200_B0_network_pairs_identical':30,'AP_shared_trains_identical':360,
                            'runtime_weight_logs':len(compact['metadata']['weight_logs']),
                            'raw_stats_gates_AP_source_and_weight_checks':'PASS',
                            'sources':[file_record(DATA/'m1h_results.json'),compact['raw_ledger']]}
    write_json(DATA/'m1h_runs_audit.json',{'candidates':outputs,'cross_candidate_comparison':'Not applicable: one M1h candidate',
                                           'auditor':file_record(Path(__file__))})
    print(json.dumps(outputs,indent=2))


if __name__=='__main__':
    audit_runs()
