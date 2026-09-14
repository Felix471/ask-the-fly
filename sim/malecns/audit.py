# SPDX-License-Identifier: MIT
"""Read-only M0 verification against raw downloads and recorded spikes; no simulation."""
import argparse
import json

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from sim.malecns.substrate import DATA, ROOT, FILENAMES, file_record, verify_record


def audit_substrate():
    record = verify_record()
    a = pd.read_feather(DATA / 'downloads' / FILENAMES['annotations'])
    nt = pd.read_feather(DATA / 'downloads' / FILENAMES['neurotransmitters'])
    ids = np.sort(a.loc[a.superclass.notna(), 'bodyId'].to_numpy())
    index = pd.read_csv(DATA / 'derived/neuron_index.csv', low_memory=False)
    completeness = pd.read_csv(DATA / 'derived/completeness.csv')
    np.testing.assert_array_equal(index.bodyId, ids)
    np.testing.assert_array_equal(index['index'], np.arange(len(ids)))
    np.testing.assert_array_equal(completeness.bodyId, ids)
    labels = nt.set_index('body').consensus_nt.reindex(ids).fillna('missing').to_numpy()
    signs = np.ones(len(ids), dtype='int8')
    signs[(labels == 'gaba') | (labels == 'glutamate')] = -1
    np.testing.assert_array_equal(index.sign, signs)
    raw = pa.ipc.open_file(pa.memory_map(str(DATA / 'downloads' / FILENAMES['weights']), 'r'))
    graph = pq.ParquetFile(DATA / 'derived/connectivity.parquet')
    if graph.num_row_groups != raw.num_record_batches:
        raise ValueError('source batch / output row-group alignment differs')
    edges = synapses = raw_edges = 0
    outgoing = np.zeros(len(ids), dtype=bool)
    incoming = np.zeros(len(ids), dtype=bool)
    for i in range(raw.num_record_batches):
        batch = raw.get_batch(i)
        pre_ids = batch.column('body_pre').to_numpy()
        post_ids = batch.column('body_post').to_numpy()
        weights = batch.column('weight').to_numpy()
        # Independent endpoint lookup, not the builder's pandas indexer.
        pre = np.searchsorted(ids, pre_ids)
        post = np.searchsorted(ids, post_ids)
        mask = (pre < len(ids)) & (post < len(ids))
        mask &= (ids[np.minimum(pre, len(ids)-1)] == pre_ids)
        mask &= (ids[np.minimum(post, len(ids)-1)] == post_ids)
        expected = {'Presynaptic_Index': pre[mask], 'Postsynaptic_Index': post[mask],
                    'Connectivity': weights[mask], 'Excitatory': signs[pre[mask]],
                    'Excitatory x Connectivity': weights[mask] * signs[pre[mask]]}
        actual = graph.read_row_group(i)
        for column, values in expected.items():
            np.testing.assert_array_equal(actual[column].to_numpy(), values)
        outgoing[pre[mask]] = True
        incoming[post[mask]] = True
        raw_edges += len(weights)
        edges += int(mask.sum())
        synapses += int(weights[mask].sum())
    expected_counts = {'neurons': len(ids), 'raw_edges': raw_edges, 'edges': edges, 'synapses': synapses,
                       'positive_neurons': int((signs == 1).sum()), 'negative_neurons': int((signs == -1).sum()),
                       'default_positive_neurons': int(np.isin(labels, ['unclear', 'missing']).sum()),
                       'default_positive_with_outgoing_edges': int((np.isin(labels, ['unclear', 'missing']) & outgoing).sum()),
                       'neurons_with_outgoing_edges': int(outgoing.sum()),
                       'neurons_with_any_edges': int((outgoing | incoming).sum()),
                       'isolated_neurons': int((~(outgoing | incoming)).sum())}
    for key, value in expected_counts.items():
        if record['counts'][key] != value:
            raise ValueError(f'substrate count mismatch: {key}')
    for label in ('unclear', 'missing'):
        if record['counts']['unresolved_by_label'][label] != {
                'neurons': int((labels == label).sum()), 'with_outgoing_edges': int(((labels == label) & outgoing).sum())}:
            raise ValueError(f'unresolved label count mismatch: {label}')
    print(f'PASS: all {edges:,} retained edges match raw endpoints/counts/signs; index and counts match', flush=True)


def audit_benchmark():
    record = json.loads((DATA / 'benchmark_m0.json').read_text(encoding='utf-8'))
    cells = json.loads((DATA / 'cells.json').read_text(encoding='utf-8'))
    for source in record['sources']:
        if file_record(ROOT / source['path']) != source:
            raise ValueError(f'benchmark source changed: {source["path"]}')
    for row in record['trials']:
        spike = row['spikes']
        if file_record(ROOT / spike['path']) != spike:
            raise ValueError('raw spike hash mismatch')
        with np.load(ROOT / spike['path'], allow_pickle=False) as raw:
            total = sum(len(raw[k]) for k in raw.files)
            if total != row['whole_network_spikes']:
                raise ValueError('whole-network spike count mismatch')
            for body, rate, latency in ((16949, 'MN9_R_primary_hz', 'MN9_R_latency_ms'),
                                        (10331, 'MN9_L_secondary_hz', 'MN9_L_latency_ms')):
                times = raw[str(body)] if str(body) in raw.files else np.array([])
                if row[rate] != len(times) or row[latency] != (float(times[0]*1000) if len(times) else None):
                    raise ValueError('MN9 rate/latency mismatch')
            if row['condition'] == 'baseline' and total != 0:
                raise ValueError('nonzero baseline observed')
            if row['condition'] == 'sugar200':
                source_rates = [len(raw[str(i)]) if str(i) in raw.files else 0 for i in cells['sets']['sugar']['ids']]
                if row['driven_sugar_mean_hz'] != float(np.mean(source_rates)):
                    raise ValueError('driven cell rate mismatch')
    for name, summary in record['summary'].items():
        rows = [r for r in record['trials'] if r['condition'] == name]
        if len(rows) != 5 or [r['seed'] for r in rows] != list(range(20260910, 20260915)):
            raise ValueError('incorrect benchmark design')
        times = [r['trial_wall_s'] for r in rows]
        if summary['mean_wall_s'] != float(np.mean(times)):
            raise ValueError('benchmark timing mean mismatch')
        worker = next(w for w in record['workers'] if w['condition'] == name)
        if summary['peak_worker_rss_gib'] != worker['peak_worker_rss_kib'] / 1024**2:
            raise ValueError('peak memory mismatch')
    print('PASS: ten benchmark trials, seeds, raw spike rates/latencies, timing and memory summaries', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--substrate', action='store_true')
    parser.add_argument('--benchmark', action='store_true')
    args = parser.parse_args()
    if not (args.substrate or args.benchmark):
        parser.error('select --substrate and/or --benchmark')
    if args.substrate:
        audit_substrate()
    if args.benchmark:
        audit_benchmark()
