"""Saved-event audit of M1d; no Brian2 import or simulation."""
import json
import hashlib
import numpy as np
from sim.malecns import split, rescale
from sim.malecns.audit_phase0 import raw_gate_checks
from sim.malecns.substrate import DATA, ROOT, file_record, write_json


def run():
    compact=json.loads((DATA/'split_results.json').read_text())
    ledger=compact['raw_ledger']
    assert file_record(ROOT/ledger['path'])==ledger
    full=json.loads((ROOT/ledger['path']).read_text())
    assert {k:v for k,v in full.items() if k!='raw'}=={k:v for k,v in compact.items() if k!='raw_ledger'}
    plan=json.loads(split.PLAN.read_text()); split.check_sources(plan)
    assert file_record(split.PLAN)==compact['metadata']['plan']
    rebuilt=[]; pairs=0; networks={}; inputs={}
    cells=json.loads((DATA/'cells.json').read_text())['sets']
    slots=[b for c in ['sugar','bitter','water','ir94e'] for b in cells[c]['ids']]
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
                    np.testing.assert_array_equal(pi,old['poisson_index'])
                    np.testing.assert_array_equal(pt,old['poisson_time_s'])
                    pairs+=1
            rows.append(row)
        rebuilt.append(dict(group,rows=rows))
        print(f'M1d audit: {pairs}/480 trials',flush=True)
    summary=rescale.summarize(rebuilt)
    for key in ['conditions','gates','a_prime']:
        assert summary[key]==compact[key]
    for side in ['L','R']:
        for k,v in raw_gate_checks(summary['conditions'],side).items():
            assert compact['gates'][side][k]==v
    sg=split.shape_gate(summary['conditions']); assert sg==compact['shape_gate']
    assert compact['overall_primary']==(compact['gates']['L']['overall'] and sg['S'])
    for trial in range(30):
        assert networks['A_s200_b0',trial]==networks['B_s200_b0',trial]
        for body in cells['sugar_lb3c']['ids']:
            i=slots.index(body)
            assert inputs['AP_sugar_120',trial][i]==inputs['AP_sugar_lb3c_120',trial][i]
    assert pairs==480
    result={'raw_trials':pairs,'MN9_neuron_trials':960,'M1_Poisson_arrays_identical':pairs,
            'AP_shared_trains_identical':360,'A200_B0_network_pairs_identical':30,
            'rates_latencies_source_counts_network_counts_summaries_gates_AP':'PASS',
            'sources':[file_record(DATA/'split_results.json'),ledger,file_record(ROOT/'sim/malecns/audit_split.py')]}
    write_json(DATA/'split_audit.json',result)
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    run()
