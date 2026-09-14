"""M1d construction/state and saved-event verification; no new trial."""
import json
import numpy as np
import pandas as pd
from sim.malecns import split, phase0
from sim.malecns.substrate import DATA, ROOT, file_record, write_json


def run():
    from brian2 import mV
    plan=json.loads(split.PLAN.read_text()); split.check_sources(plan)
    split.init_worker()  # reconstruct frozen build; only its zero-duration compile
    model=phase0._MODEL
    p=json.loads(split.PROTOCOL.read_text())
    signed=pd.read_parquet(DATA/'derived/connectivity.parquet',columns=['Excitatory x Connectivity']).iloc[:,0].to_numpy()
    observations=[]
    for state in ['constructed','restored']:
        if state=='restored':
            model.net.restore('m1_init')
        stim=np.asarray(model.net['stimulus_synapses'].w_stim[:]/mV)
        rec=np.asarray(model.net['default_synapses'].w[:]/mV)
        np.testing.assert_allclose(stim,68.75,rtol=0,atol=1e-12)
        np.testing.assert_allclose(rec,signed*p['model']['w_syn_mV'],rtol=1e-14,atol=1e-12)
        observations.append({'state':state,'stimulus_mV_min':float(stim.min()),'stimulus_mV_max':float(stim.max()),
                             'recurrent_mV_per_signed_count_min':float((rec/signed).min()),
                             'recurrent_mV_per_signed_count_max':float((rec/signed).max())})
    d=json.loads((DATA/'split_results.json').read_text()); old=json.loads((DATA/'rescale_all_results.json').read_text())
    assert d['conditions']==old['conditions'] and d['gates']==old['gates'] and d['a_prime']==old['a_prime']
    full=json.loads((ROOT/d['raw_ledger']['path']).read_text())
    cells=json.loads((DATA/'cells.json').read_text())['sets']
    slots=[b for c in phase0.CHANNELS for b in cells[c]['ids']]
    exact=driven=equal=timing_equal=0; differences=[]
    for group in full['raw']:
        c=group['condition']; rates=phase0.source_rates(c,cells)
        for row in group['rows']:
            with np.load(ROOT/row['spikes']['path'],allow_pickle=False) as z, np.load(DATA/'runs/m1c/all'/c['id']/f'trial_{row["trial"]:02d}.npz',allow_pickle=False) as prev:
                for key in ['body_id','time_s','poisson_index','poisson_time_s']:
                    np.testing.assert_array_equal(z[key],prev[key])
                exact+=1
                for i,rate in enumerate(rates):
                    if rate<=0:
                        continue
                    driven+=1
                    events=z['poisson_time_s'][z['poisson_index']==i]
                    spikes=z['time_s'][z['body_id']==slots[i]]
                    equal+=int(len(events)==len(spikes))
                    predicted=events+0.0001
                    predicted=predicted[predicted<1-1e-12]
                    matched=len(predicted)==len(spikes) and np.allclose(predicted,spikes,rtol=0,atol=1e-10)
                    timing_equal+=int(matched)
                    if not matched:
                        differences.append({'condition':c['id'],'trial':row['trial'],'body':slots[i],'events':len(events),'spikes':len(spikes)})
    result={'scope':'Post-run reconstruction of frozen construction and restore; no historical runtime weight dump existed; no new positive-duration run.',
            'sources':[file_record(split.PROTOCOL),file_record(split.PLAN),file_record(DATA/'split_results.json'),file_record(DATA/'rescale_all_results.json')],
            'observed_weights':observations,'M1c_all_protocol':old['metadata']['protocol']['path'],
            'historical_M1c_all_external_kick_mV':json.loads((DATA/'stim_protocol_malecns_all.json').read_text())['model']['w_syn_mV']*250,
            'exact_whole_network_and_input_trial_pairs':exact,'driven_cell_trials':driven,
            'equal_input_output_counts':equal,'event_plus_dt_exact_driven_trains':timing_equal,
            'exceptions':differences,'simulation_trials':0}
    fullpath=DATA/'runs/m1d/split_weight_verification_full.json'
    write_json(fullpath,result)
    result['full_ledger']=file_record(fullpath)
    result['exception_summary']={'more_spikes_than_events':sum(x['spikes']>x['events'] for x in differences),
                                 'fewer_spikes_than_events':sum(x['spikes']<x['events'] for x in differences)}
    del result['exceptions']
    write_json(DATA/'split_weight_verification.json',result)
    print(json.dumps({k:v for k,v in result.items() if k!='exceptions'},indent=2))


if __name__=='__main__':
    run()
