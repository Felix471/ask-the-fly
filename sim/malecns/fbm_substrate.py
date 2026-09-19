# SPDX-License-Identifier: MIT
"""M1i write-once >=5 substrate and KC input scaling; no simulation imports."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import sys

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np
import pandas as pd
from sim.malecns.substrate import DATA, ROOT, file_record, write_json
from sim.malecns.fbm_cells import CONFIGURATION_SOURCE

RECORD = DATA / 'substrate_record_fbm.json'
TARGET = DATA / 'derived/fbm'
KC_TARGET = DATA / 'derived/fbm_kc'
DECL_HASH = 'db7ae6e8e249a3bda7722da1b15a4dd67a6fc2ef'


def check_file(record):
    actual = file_record(ROOT / record['path'])
    if any(actual[k] != record[k] for k in actual):
        raise ValueError('Frozen file changed: ' + record['path'])


def verify():
    record = json.loads(RECORD.read_text(encoding='utf-8'))
    for item in list(record['artifacts'].values()) + record['sources'] + [record['builder']]:
        check_file(item)
    return record


def filter_graph(graph):
    return graph.loc[graph.Connectivity.ge(5) &
                     graph.Presynaptic_Index.ne(graph.Postsynaptic_Index)].reset_index(drop=True)


def scale_kc(graph, kc_indices):
    mask = graph.Postsynaptic_Index.isin(kc_indices)
    scaled = graph.copy()
    column = 'Excitatory x Connectivity'
    scaled[column] = scaled[column].astype('float64')
    scaled.loc[mask, column] *= .25
    return scaled, mask


def build():
    if any(p.exists() for p in (RECORD, TARGET, KC_TARGET)):
        raise FileExistsError('Never overwrite the M1i substrate or partial build')
    baseline = json.loads((DATA / 'substrate_record.json').read_text(encoding='utf-8'))
    sources = [baseline['sources'][k] for k in ('weights', 'annotations', 'neurotransmitters')]
    sources += [baseline['artifacts'][k] for k in ('signed_connectivity', 'neuron_index', 'completeness')]
    for item in sources:
        check_file(item)
    sources += [file_record(DATA / 'substrate_record.json')]
    roster = pd.read_csv(DATA / 'derived/neuron_index.csv')
    if len(roster) != 166700 or roster['index'].tolist() != list(range(166700)):
        raise ValueError('M0 roster or indices differ')
    old = pd.read_parquet(DATA / 'derived/connectivity.parquet')
    ge5 = old.Connectivity.ge(5)
    if int(ge5.sum()) != 6242118:
        raise ValueError('Declared >=5 count differs')
    histogram = [{'synapses_per_edge': int(w), 'edges': int(n),
                  'threshold_action': 'removed' if w < 5 else 'kept before autapse removal'}
                 for w, n in old.Connectivity.value_counts().sort_index().items()]
    graph = filter_graph(old)
    counts = {'neurons': len(roster), 'ge5_before_autapse_removal': int(ge5.sum()),
              'autapses_removed': int(ge5.sum()) - len(graph), 'edges': len(graph),
              'synapses': int(graph.Connectivity.sum())}
    del old
    raw = pd.read_feather(ROOT / baseline['sources']['weights']['path'])
    raw = raw.loc[raw.weight.ge(5)]
    on = raw.body_pre.isin(roster.bodyId) & raw.body_post.isin(roster.bodyId)
    autapse = raw.body_pre.eq(raw.body_post)
    retained = raw.loc[on & ~autapse]
    # Exact endpoint/weight reconciliation, not merely matching aggregate counts.
    index = pd.Series(roster['index'].to_numpy(), index=roster.bodyId)
    np.testing.assert_array_equal(retained.body_pre.map(index), graph.Presynaptic_Index)
    np.testing.assert_array_equal(retained.body_post.map(index), graph.Postsynaptic_Index)
    np.testing.assert_array_equal(retained.weight, graph.Connectivity)
    comparison = {'their_neurons': 176422, 'our_neurons': len(roster),
                  'roster_difference_theirs_minus_ours': 176422 - len(roster),
                  'their_edges': 6287749, 'their_synapses': 90296905,
                  'raw_ge5_edges': len(raw), 'raw_ge5_synapses': int(raw.weight.sum()),
                  'raw_ge5_outside_roster_edges': int((~on).sum()),
                  'raw_ge5_autapses_all': int(autapse.sum()),
                  'raw_ge5_on_roster_autapses': int((on & autapse).sum()),
                  'raw_ge5_on_roster_non_autapse_edges': len(retained),
                  'raw_ge5_on_roster_non_autapse_synapses': int(retained.weight.sum()),
                  'reconciliation': 'Exact retained endpoints, order and weights equal our graph.',
                  'residual_theirs_minus_raw_ge5_non_autapse_edges': 6287749 - int((~autapse).sum()),
                  'residual_theirs_minus_raw_ge5_non_autapse_synapses': 90296905 - int(raw.loc[~autapse, 'weight'].sum()),
                  'final_difference_theirs_minus_ours_edges': 6287749 - len(graph),
                  'final_difference_theirs_minus_ours_synapses': 90296905 - counts['synapses'],
                  'residual_label': 'Their neuPrint fetch versus the GCS flat file; no explanation assigned.'}
    del raw, retained
    annotations = pd.read_feather(ROOT / baseline['sources']['annotations']['path'])
    comparison['superclass_null_by_status'] = {str(k): int(v) for k, v in
        annotations.loc[annotations.superclass.isna(), 'status'].fillna('(missing)').value_counts().items()}
    nt = pd.read_feather(ROOT / baseline['sources']['neurotransmitters']['path']).set_index('body').reindex(roster.bodyId)
    consensus = nt.consensus_nt.fillna('missing')
    unresolved = consensus.isin(['unclear', 'missing'])
    predicted = unresolved & nt.predicted_nt_confidence.ge(.5) & nt.predicted_nt.notna() & nt.predicted_nt.ne('unclear')
    celltype = unresolved & ~predicted & nt.celltype_predicted_nt.notna() & nt.celltype_predicted_nt.ne('unclear')
    resolved = consensus.copy()
    resolved.loc[predicted] = nt.loc[predicted, 'predicted_nt']
    resolved.loc[celltype] = nt.loc[celltype, 'celltype_predicted_nt']
    negative = resolved.isin(['gaba', 'glutamate', 'histamine'])
    signs = {'histamine_sign_differences': int(consensus.eq('histamine').sum()),
             'consensus_unclear_or_missing': int(unresolved.sum()),
             'predicted_fallback_labels': {str(k): int(v) for k, v in nt.loc[predicted, 'predicted_nt'].value_counts().items()},
             'celltype_fallback_labels': {str(k): int(v) for k, v in nt.loc[celltype, 'celltype_predicted_nt'].value_counts().items()},
             'fallback_sign_differences': int((unresolved & negative).sum()),
             'total_sign_differences': int((np.where(negative, -1, 1) != roster.sign.to_numpy()).sum()),
             'applied': False, 'our_rule': baseline['sign_rule']}
    kc_bodies = annotations.loc[annotations['class'].eq('Kenyon_Cell') & annotations.bodyId.isin(roster.bodyId), 'bodyId']
    if len(kc_bodies) != 4064:
        raise ValueError('Declared KC count differs')
    scaled, mask = scale_kc(graph, index.loc[kc_bodies].to_numpy())
    for directory, table in ((TARGET, graph), (KC_TARGET, scaled)):
        directory.mkdir()
        shutil.copyfile(DATA / 'derived/completeness.csv', directory / 'completeness.csv')
        table.to_parquet(directory / 'connectivity.parquet', index=False, compression='zstd')
    artifacts = {'neuron_index': file_record(DATA / 'derived/neuron_index.csv')}
    for label, directory in [('fbm', TARGET), ('fbm_kc', KC_TARGET)]:
        for name in ('connectivity.parquet', 'completeness.csv'):
            artifacts[label + '/' + name] = file_record(directory / name)
    record = {'substrate_version': 'male-cns-v1.0-fbm-ge5-1', 'declaration_commit': DECL_HASH,
              'built_utc': datetime.now(timezone.utc).isoformat(), 'stage': 'M1i substrate only; no trials',
              'scope': 'whole CNS; unchanged M0 roster and consensus signs', 'counts': counts,
              'synapses_per_edge_histogram': histogram, 'their_graph_comparison': comparison,
              'sign_rule_comparison': signs, 'w_syn_mV': .65 * .275, 'w_syn_expression': '0.65 * 0.275',
              'external_kick_mV': (.65 * .275) * 250,
              'kc': {'bodies': len(kc_bodies), 'affected_edges': int(mask.sum()),
                     'affected_synapses': int(graph.loc[mask, 'Connectivity'].sum()), 'gain': .25,
                     'column': 'Excitatory x Connectivity', 'dtype': 'float64'},
              'dt_ms': {'ours': .1, 'theirs': .5},
              'readouts': {'ours': 'L10331 and R16949 over 1 s; b also two-cell mean and 20 x 50 ms bin means; a gates on L10331.',
                           'theirs': 'MN9 two-cell population mean per 50 ms tick, one 600 ms run; 30-90 / 0 / 0 Hz.'},
              'licence': baseline['licence'], 'configuration_source': CONFIGURATION_SOURCE,
              'sources': sources, 'builder': file_record(Path(__file__)), 'artifacts': artifacts}
    write_json(RECORD, record)
    return record


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    result = verify() if args.verify else build()
    print(json.dumps({k: result[k] for k in ('counts', 'their_graph_comparison', 'sign_rule_comparison', 'kc')}, indent=2))
