"""M1h graph construction only. No simulation imports or activity-based selection."""
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import time

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from sim.malecns.substrate import DATA, ROOT, BASE_URL, file_record, write_json
from sim.malecns.brain_substrate import verify as verify_brain

TARGET = DATA / 'derived/density_matched'
RECORD = DATA / 'substrate_record_density_matched.json'
SOURCE = DATA / 'downloads/syn-partners-male-cns-v1.0-minconf-0.5.feather'
EXPECTED_BYTES = 6777179098


def choose_cutoff(confidence, male_neurons, female_synapses, female_neurons):
    """Closest stored breakpoint by exact integer objective; lower cutoff breaks ties."""
    values, counts = np.unique(confidence, return_counts=True)
    retained = np.cumsum(counts[::-1], dtype=np.int64)[::-1]
    errors = np.abs(retained * female_neurons - female_synapses * male_neurons)
    best = int(np.argmin(errors))
    return float(values[best]), int(retained[best]), {
        'distinct_breakpoints': len(values),
        'absolute_cross_product_error': int(errors[best]),
        'neighbouring_breakpoints': [
            {'cutoff': float(values[i]), 'synapses': int(retained[i]),
             'ratio': float(retained[i] * female_neurons / (female_synapses * male_neurons))}
            for i in range(max(0, best - 1), min(len(values), best + 2))],
    }


def loss_row(body, label, baseline, retained):
    return {'bodyId': int(body), 'label': label, 'incoming_at_0_5': int(baseline),
            'incoming_at_c_star': int(retained),
            'retained_fraction': float(retained / baseline) if baseline else None,
            'loss_gt_half': bool(2 * retained < baseline), 'baseline_zero': baseline == 0}


def main():
    started = time.perf_counter()
    if TARGET.exists() or RECORD.exists():
        raise FileExistsError('Never overwrite the M1h substrate')
    if SOURCE.stat().st_size != EXPECTED_BYTES:
        raise ValueError('Full partner download size differs from release')
    old_record = verify_brain()
    roster = pd.read_csv(DATA / 'derived/brain/neuron_index.csv')
    index = pd.Index(roster.bodyId)
    n = len(roster)
    assert n == old_record['counts']['neurons']
    source_record = file_record(SOURCE)
    reader = pa.ipc.open_file(SOURCE)
    key_chunks, conf_chunks = [], []
    raw_rows = 0
    for i in range(reader.num_record_batches):
        b = reader.get_batch(i)
        pre = index.get_indexer(b.column('body_pre').to_numpy())
        post = index.get_indexer(b.column('body_post').to_numpy())
        confidence = np.minimum(b.column('conf_pre').to_numpy(), b.column('conf_post').to_numpy())
        if not (np.isfinite(confidence).all() and (confidence >= .5).all() and (confidence <= 1).all()):
            raise ValueError('Invalid source confidence')
        keep = (pre >= 0) & (post >= 0)
        key_chunks.append(pre[keep].astype('uint64') * n + post[keep].astype('uint64'))
        conf_chunks.append(confidence[keep])
        raw_rows += len(b)
    keys, confidence = np.concatenate(key_chunks), np.concatenate(conf_chunks)
    del key_chunks, conf_chunks
    print('Full source rows', raw_rows, 'brain contacts', len(keys), flush=True)
    baseline_keys, baseline_weights = np.unique(keys, return_counts=True)
    old = pq.read_table(DATA / 'derived/brain/connectivity.parquet').to_pandas()
    old_keys = old.Presynaptic_Index.to_numpy(dtype='uint64') * n + old.Postsynaptic_Index.to_numpy(dtype='uint64')
    order = np.argsort(old_keys)
    np.testing.assert_array_equal(baseline_keys, old_keys[order])
    np.testing.assert_array_equal(baseline_weights, old.Connectivity.to_numpy()[order])
    baseline_degree = np.bincount((baseline_keys % n).astype('int64'), weights=baseline_weights, minlength=n).astype('int64')
    del old, old_keys, order, baseline_keys, baseline_weights
    female_synapses = old_record['density']['female_synapses']
    female_neurons = old_record['density']['female_neurons']
    cutoff, target_synapses, selection = choose_cutoff(confidence, n, female_synapses, female_neurons)
    ratio = target_synapses * female_neurons / (female_synapses * n)
    if not .98 <= ratio <= 1.02:
        raise ValueError('Closest attainable breakpoint misses declared density tolerance')
    edge_keys, weights = np.unique(keys[confidence >= cutoff], return_counts=True)
    assert int(weights.sum()) == target_synapses
    pre = (edge_keys // n).astype('int32')
    post = (edge_keys % n).astype('int32')
    degree = np.bincount(post, weights=weights, minlength=n).astype('int64')
    signs = roster.sign.to_numpy(dtype='int8')[pre]
    graph = pd.DataFrame({'Presynaptic_Index': pre, 'Postsynaptic_Index': post,
                          'Connectivity': weights.astype('int64'), 'Excitatory': signs,
                          'Excitatory x Connectivity': weights * signs})
    bins, edge_counts = np.unique(weights, return_counts=True)
    histogram = [{'synapses_per_edge': int(w), 'edges': int(count)} for w, count in zip(bins, edge_counts)]
    cells = json.loads((DATA / 'cells.json').read_text())['sets']
    inputs = {int(body): name for name in ['sugar', 'bitter', 'water', 'ir94e'] for body in cells[name]['ids']}
    assert len(inputs) == 91
    rows = []
    for body, label in list(sorted(inputs.items())) + [(10331, 'MN9 L primary'), (16949, 'MN9 R secondary')]:
        pos = index.get_loc(body)
        rows.append(loss_row(body, label, int(baseline_degree[pos]), int(degree[pos])))
    TARGET.mkdir()
    for name in ['neuron_index.csv', 'completeness.csv']:
        shutil.copyfile(DATA / 'derived/brain' / name, TARGET / name)
    graph.to_parquet(TARGET / 'connectivity.parquet', index=False, compression='zstd')
    record = {
        'stage': 'M1h substrate checkpoint; no simulation', 'built_utc': datetime.now(timezone.utc).isoformat(),
        'declaration_commit': 'a8234d3',
        'source': source_record, 'source_url': BASE_URL + SOURCE.name, 'raw_partner_rows': raw_rows,
        'baseline_edge_for_edge_match': 'PASS: full contacts reproduce all M1f brain edge counts',
        'rule': 'Both conf_pre and conf_post >= c_star, float32 source confidence; original M1f roster, signs and endpoint cut; keep isolated neurons.',
        'selection_rule': 'Minimise exact absolute cross-product error retained_synapses*female_neurons - female_synapses*male_neurons over stored confidence breakpoints; lower cutoff breaks ties. No activity read.',
        'c_star': cutoff, 'selection': selection,
        'counts': {'neurons': n, 'edges': len(graph), 'synapses': target_synapses},
        'density': {'female_neurons': female_neurons, 'female_synapses': female_synapses,
                    'female_mean': female_synapses / female_neurons, 'male_mean': target_synapses / n,
                    'ratio': ratio, 'baseline_ratio': old_record['density']['r_brain']},
        'retention': {'contacts_fraction': target_synapses / len(keys), 'interpretation': 'Contact retention is not measured recall.'},
        'synapses_per_edge_histogram': histogram,
        'input_and_readout_degrees': rows,
        'flagged_body_ids': [r['bodyId'] for r in rows if r['loss_gt_half']],
        'zero_baseline_body_ids': [r['bodyId'] for r in rows if r['baseline_zero']],
        'sources': [file_record(DATA / 'substrate_record_brain.json'), file_record(DATA / 'cells.json')],
        'builder': file_record(Path(__file__)),
        'artifacts': {name: file_record(TARGET / name) for name in ['neuron_index.csv', 'completeness.csv', 'connectivity.parquet']},
        'wall_seconds': time.perf_counter() - started,
    }
    write_json(RECORD, record)
    print(json.dumps({k: record[k] for k in ['c_star', 'counts', 'density', 'flagged_body_ids', 'zero_baseline_body_ids', 'wall_seconds']}, indent=2))


if __name__ == '__main__':
    main()
