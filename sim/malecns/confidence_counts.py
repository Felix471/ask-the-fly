"""Research-only confidence distributions; never writes a model substrate."""
import json
import time
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from sim.malecns.substrate import DATA, ROOT, file_record, write_json


def main():
    started = time.perf_counter()
    source = DATA/'downloads/syn-partners-male-cns-v1.0-minconf-0.5-traced-only.feather'
    roster = pd.read_csv(DATA/'derived/neuron_index.csv',usecols=['bodyId'])
    brain = pd.read_csv(DATA/'derived/brain/neuron_index.csv',usecols=['bodyId'])
    index = pd.Index(roster.bodyId)
    brain_mask = roster.bodyId.isin(brain.bodyId).to_numpy()
    n = len(roster)
    keys, confidences = [], []
    reader = pa.ipc.open_file(source)
    raw_count = 0
    for i in range(reader.num_record_batches):
        b = reader.get_batch(i)
        pre = index.get_indexer(b.column('body_pre').to_numpy())
        post = index.get_indexer(b.column('body_post').to_numpy())
        confidence = np.minimum(b.column('conf_pre').to_numpy(), b.column('conf_post').to_numpy())
        assert np.isfinite(confidence).all() and (confidence >= .5).all() and (confidence <= 1).all()
        keep = (pre >= 0) & (post >= 0)
        keys.append(pre[keep].astype('uint64')*n+post[keep].astype('uint64'))
        confidences.append(confidence[keep])
        raw_count += len(b)
    keys = np.concatenate(keys); confidence = np.concatenate(confidences)
    print('Rows read:', raw_count, 'roster retained:', len(keys), flush=True)
    unique, inverse, counts = np.unique(keys, return_inverse=True, return_counts=True)
    max_conf = np.zeros(len(unique), dtype='float32')
    np.maximum.at(max_conf, inverse, confidence)
    expected = pq.read_table(DATA/'derived/connectivity.parquet', columns=['Presynaptic_Index','Postsynaptic_Index','Connectivity']).to_pandas()
    expected_key = expected.Presynaptic_Index.to_numpy(dtype='uint64')*n+expected.Postsynaptic_Index.to_numpy(dtype='uint64')
    order = np.argsort(expected_key)
    locations = np.searchsorted(expected_key[order], unique)
    np.testing.assert_array_equal(unique, expected_key[order][locations])
    np.testing.assert_array_equal(counts, expected.Connectivity.to_numpy()[order][locations])
    # The traced-only export omits edges from our broader original roster.
    # Retain that failed equality as a limitation, not an exact rebuild claim.
    absent = np.ones(len(expected), dtype=bool); absent[locations] = False
    missing_key = expected_key[order][absent]
    missing_count = expected.Connectivity.to_numpy()[order][absent]
    missing_brain = brain_mask[missing_key//n] & brain_mask[missing_key%n]
    omissions = {'whole': {'edges':len(missing_key),'synapses':int(missing_count.sum())},
                 'brain': {'edges':int(missing_brain.sum()),'synapses':int(missing_count[missing_brain].sum())}}
    del expected, expected_key, order, counts, inverse
    syn_brain = brain_mask[keys//n] & brain_mask[keys%n]
    edge_brain = brain_mask[unique//n] & brain_mask[unique%n]
    female_mean = 54492922/138639
    rows = []
    for cutoff in [.5,.6,.7,.8,.9]:
        syn_keep = confidence >= cutoff
        edge_keep = max_conf >= cutoff
        row = {'cutoff': cutoff}
        for name, neurons, sm, em in [('whole',n,np.ones(len(keys),dtype=bool),np.ones(len(unique),dtype=bool)),('brain',len(brain),syn_brain,edge_brain)]:
            synapses = int((syn_keep & sm).sum())
            edges = int((edge_keep & em).sum())
            missing = omissions[name]
            row[name] = {'neurons':neurons,'edges_lower':edges,'edges_upper':edges+missing['edges'],
                         'synapses_lower':synapses,'synapses_upper':synapses+missing['synapses'],
                         'density_ratio_lower':synapses/neurons/female_mean,
                         'density_ratio_upper':(synapses+missing['synapses'])/neurons/female_mean}
        rows.append(row)
        print(row, flush=True)
    result = {'scope':'Read-only counts, no substrate export or simulation; illustrative cutoffs, not candidates.',
              'rule':'Both conf_pre and conf_post >= cutoff; same M0 roster and M1f brain endpoint mask; retain isolated neurons.',
              'source':file_record(source),'source_url':'https://storage.googleapis.com/flyem-male-cns/v1.0/connectome-data/flat-connectome/'+source.name,
              'raw_rows':raw_count,'baseline_full_graph_equality':'FAIL: traced-only export is smaller than original roster graph',
              'retained_edge_weights_match_original':'PASS','omissions':omissions,'rows':rows,
              'sources':[file_record(DATA/'derived/neuron_index.csv'),file_record(DATA/'derived/brain/neuron_index.csv'),file_record(DATA/'derived/connectivity.parquet')],
              'wall_seconds':time.perf_counter()-started,'code':file_record(ROOT/'sim/malecns/confidence_counts.py')}
    write_json(DATA/'confidence_counts.json',result)


if __name__ == '__main__':
    main()
