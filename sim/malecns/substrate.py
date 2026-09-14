# SPDX-License-Identifier: MIT
"""Build/freeze the isolated MaleCNS v1.0 substrate; no Brian2 imports.

Run once: python -m sim.malecns.substrate
Verify without rewriting: python -m sim.malecns.substrate --verify
Large sources/derived files are ignored; small manifests and cell sets are versioned.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'data/malecns'
BASE_URL = 'https://storage.googleapis.com/flyem-male-cns/v1.0/connectome-data/flat-connectome/'
FILENAMES = {
    'weights': 'connectome-weights-male-cns-v1.0-minconf-0.5.feather',
    'annotations': 'body-annotations-male-cns-v1.0-minconf-0.5.feather',
    'neurotransmitters': 'body-neurotransmitters-male-cns-v1.0.feather',
}
WORKBOOK = ROOT / 'docs/papers/Tastekin_2025_bioRxiv_v2_SupplTable2_GRN_MN_body_IDs.xlsx'
WORKBOOK_HASH = '7b28d5f3ae45d68c510b8a3616700f0df2a5a6f2e2d2dba490d172939f2b64c9'
LABELS = {'acetylcholine', 'gaba', 'glutamate', 'histamine', 'dopamine', 'octopamine',
          'serotonin', 'unclear', 'missing'}


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def file_record(path):
    path = Path(path)
    return {'path': path.relative_to(ROOT).as_posix(), 'bytes': path.stat().st_size, 'sha256': sha256(path)}


def write_json(path, value):
    """Never overwrite a frozen record or previously recorded run."""
    with Path(path).open('x', encoding='utf-8', newline='\n') as f:
        json.dump(value, f, indent=2, ensure_ascii=False, allow_nan=False)
        f.write('\n')


def make_roster(annotations, nt):
    if annotations.bodyId.duplicated().any() or nt.body.duplicated().any():
        raise ValueError('duplicate source body ID')
    roster = annotations.loc[annotations.superclass.notna()].sort_values('bodyId').copy()
    if roster.bodyId.isna().any() or (roster.bodyId <= 0).any():
        raise ValueError('invalid roster body IDs')
    roster = roster.merge(nt[['body', 'consensus_nt']], left_on='bodyId', right_on='body',
                          how='left', validate='one_to_one').drop(columns='body')
    roster['consensus_nt'] = roster.consensus_nt.fillna('missing')
    unknown = set(roster.consensus_nt) - LABELS
    if unknown:
        raise ValueError(f'unrecognised consensus labels: {unknown}')
    roster['sign'] = np.where(roster.consensus_nt.isin(['gaba', 'glutamate']), -1, 1).astype('int8')
    roster['default_positive'] = roster.consensus_nt.isin(['unclear', 'missing'])
    roster.insert(0, 'index', np.arange(len(roster), dtype='int32'))
    return roster


def signed_batch(raw, roster):
    weights = raw.weight.to_numpy()
    if not np.isfinite(weights).all() or (weights <= 0).any() or (weights != np.floor(weights)).any():
        raise ValueError('weights must be positive integer synapse counts')
    index = pd.Index(roster.bodyId)
    pre = index.get_indexer(raw.body_pre)
    post = index.get_indexer(raw.body_post)
    keep = (pre >= 0) & (post >= 0)
    pre, post, weights = pre[keep].astype('int32'), post[keep].astype('int32'), weights[keep].astype('int64')
    signs = roster.sign.to_numpy()[pre]
    return pd.DataFrame({'Presynaptic_Index': pre, 'Postsynaptic_Index': post,
                         'Connectivity': weights, 'Excitatory': signs,
                         'Excitatory x Connectivity': weights * signs})


def select_cells(rows):
    rules = {'sugar': ({'LB3b', 'LB3c'}, {'L'}), 'bitter': ({'LB1a', 'LB1b', 'LB1c', 'LB1d'}, {'L', 'R'}),
             'water': ({'LB3a'}, {'L', 'R'}), 'ir94e': ({'LB1e'}, {'L', 'R'}),
             'sugar_lb3c': ({'LB3c'}, {'L'})}
    sets = {}
    for name, (subtypes, sides) in rules.items():
        selected = [r for r in rows if r.get('Connectome') == 'maleCNS'
                    and r.get('Subtype') in subtypes and r.get('Root_Side') in sides]
        selected.sort(key=lambda r: int(r['Body_ID']))
        ids = [int(r['Body_ID']) for r in selected]
        if len(ids) != len(set(ids)):
            raise ValueError(f'duplicate IDs in {name}')
        fields = ['Body_ID', 'Root_Side', 'Type', 'Subtype', 'Entry_Nerve']
        sets[name] = {'ids': ids, 'subtypes': sorted(subtypes), 'xlsx_sides': sorted(sides),
                      'source_rows': [{k: r.get(k, '') for k in fields} for r in selected]}
    return sets


def derived_protocol(base, sets):
    p = deepcopy(base)
    p['protocol_version'] = 'malecns-phase0-1.0'
    p['data_version'] = 'male-cns:v1.0'
    p['connectivity_file'] = 'data/malecns/derived/connectivity.parquet'
    p['completeness_file'] = 'data/malecns/derived/completeness.csv'
    for k, channel in p['stimulus']['channels'].items():
        channel['count'] = len(sets[k]['ids'])
    p['readout'] = {'neuron': 'MN9', 'primary': 16949, 'secondary': 10331,
                    'primary_xlsx_side': 'R', 'secondary_xlsx_side': 'L', 'aggregation': 'primary_only',
                    'aggregation_rationale': 'Stimulate XLSX Root_Side L sugar, mirroring the female frozen set side. '
                    'Read contralateral XLSX R MN9 (16949); also record XLSX L MN9 (10331). '
                    'Shiu historical left/right aliases are not XLSX side labels.',
                    'rate_definition': base['readout']['rate_definition']}
    del p['phase0_conditions']['A_prime_sugar_bench21']
    p['phase0_conditions']['A_prime_sugar_lb3c'] = {
        'reference_cell_set': 'sugar', 'cell_set': 'sugar_lb3c', 'sugar_hz': [120], 'bitter_hz': 0,
        'trials_each': 30, 'paired_seeds': True,
        'note': 'Two fresh 120 Hz conditions; neither is in the A-D 420 trials. Not executed at M0.'}
    p['male_provenance'] = {
        'reference_protocol': 'data/stim_protocol.json', 'reference_protocol_sha256': sha256(ROOT / 'data/stim_protocol.json'),
        'substrate_record': 'data/malecns/substrate_record.json', 'cells_file': 'data/malecns/cells.json',
        'model_parameters': 'Inherited byte-for-value unchanged, including model.source attribution.',
        'adapter': 'sim/malecns/adapter.py',
        'rederived_fields': ['protocol_version', 'data_version', 'connectivity_file', 'completeness_file',
                             'stimulus.channels.*.count', 'readout identifiers/side aliases/aggregation/rationale',
                             'phase0_conditions.A_prime_sugar_bench21 -> A_prime_sugar_lb3c'],
        'unchanged_fields': ['model', 'trial', 'stimulus.type', 'stimulus.channels.*.cell_set',
                             'stimulus.channels.water.phase', 'stimulus.channels.ir94e.phase',
                             'readout.neuron', 'readout.rate_definition', 'phase0_conditions.A-D',
                             'phase1_characterization', 'notes'],
        'seed_scheme': {'base_seed': 20260910, 'formula': '20260910 + trial_index',
                        'same_seeds_across_conditions': True, 'trial_index_base': 0},
        'stimulation_layout': {'channel_order': ['sugar', 'bitter', 'water', 'ir94e'],
                               'within_channel_order': 'ascending numeric Body_ID', 'poisson_units': 91},
        'scope': 'Whole CNS; M0 only baseline and sugar200 five-trial benchmarks. M1/M2 require checkpoints.',
        'calibration': 'Transfer is a model assumption, not male behavioural calibration.'}
    return p


def audit_sets(sets, roster):
    indexed = roster.set_index('bodyId')
    audit = {}
    for name in ('sugar', 'bitter', 'water', 'ir94e'):
        cells = indexed.loc[sets[name]['ids']]
        audit[name] = {'cells': len(cells), 'negative': int((cells.sign == -1).sum()),
                       'positive': int((cells.sign == 1).sum()),
                       'default_positive': int(cells.default_positive.sum()),
                       'negative_ids': [int(i) for i in cells.index[cells.sign == -1]],
                       'consensus_labels': {k: int(v) for k, v in cells.consensus_nt.value_counts().items()}}
    return audit


def verify_record():
    record = json.loads((DATA / 'substrate_record.json').read_text(encoding='utf-8'))
    entries = list(record['sources'].values()) + list(record['artifacts'].values()) + [record['builder']]
    for entry in entries:
        actual = file_record(ROOT / entry['path'])
        if actual['sha256'] != entry['sha256'] or actual['bytes'] != entry['bytes']:
            raise ValueError(f'frozen hash/size mismatch: {entry["path"]}')
    print('MaleCNS frozen record: all source, builder and artifact hashes/sizes match', flush=True)
    return record


def build():
    if (DATA / 'substrate_record.json').exists() or (DATA / 'derived').exists():
        raise FileExistsError('substrate/derived directory already exists; use --verify, never overwrite a freeze')
    sources = {key: dict(file_record(DATA / 'downloads' / filename), url=BASE_URL + filename)
               for key, filename in FILENAMES.items()}
    if sha256(WORKBOOK) != WORKBOOK_HASH:
        raise ValueError('Table S1 workbook differs from the inspected source')
    sources['tastekin_table_s1'] = dict(file_record(WORKBOOK), url='https://doi.org/10.1016/j.cell.2026.08.016')
    sources['female_reference_protocol'] = file_record(ROOT / 'data/stim_protocol.json')
    sources['shared_shiu_implementation'] = file_record(ROOT / 'sim/network.py')
    a = pd.read_feather(DATA / 'downloads' / FILENAMES['annotations'])
    nt = pd.read_feather(DATA / 'downloads' / FILENAMES['neurotransmitters'])
    roster = make_roster(a, nt)
    if len(roster) != 166700:
        raise ValueError(f'roster count differs from v1.0 paper: {len(roster)}')
    from scripts.cross_check_cells import read_xlsx
    sheets = read_xlsx(WORKBOOK)
    sets = select_cells(sheets['GRNs'])
    if {k: len(v['ids']) for k, v in sets.items()} != {'sugar': 17, 'bitter': 38, 'water': 17, 'ir94e': 19, 'sugar_lb3c': 12}:
        raise ValueError('typed cell sets differ from approved counts')
    drives = [i for k in ('sugar', 'bitter', 'water', 'ir94e') for i in sets[k]['ids']]
    if len(drives) != len(set(drives)) or not set(drives).issubset(set(roster.bodyId)):
        raise ValueError('drive sets overlap or contain neurons outside the roster')
    mn9 = [r for r in sheets['MNs'] if r.get('Connectome') == 'maleCNS' and r.get('Type') == 'MN9']
    if {(int(r['Body_ID']), r['Root_Side']) for r in mn9} != {(16949, 'R'), (10331, 'L')}:
        raise ValueError('MN9 identities or sides differ from approval')
    if not {16949, 10331}.issubset(set(roster.bodyId)):
        raise ValueError('MN9 absent from proofread roster')
    target = DATA / 'derived'
    target.mkdir()
    roster.to_csv(target / 'neuron_index.csv', index=False, lineterminator='\n')
    pd.DataFrame(index=pd.Index(roster.bodyId, name='bodyId')).to_csv(target / 'completeness.csv', lineterminator='\n')
    outgoing = np.zeros(len(roster), dtype=bool)
    incoming = np.zeros(len(roster), dtype=bool)
    raw_count = edge_count = synapses = 0
    keys = []
    reader = pa.ipc.open_file(pa.memory_map(str(DATA / 'downloads' / FILENAMES['weights']), 'r'))
    writer = None
    try:
        for i in range(reader.num_record_batches):
            raw = reader.get_batch(i).to_pandas()
            raw_count += len(raw)
            signed = signed_batch(raw, roster)
            table = pa.Table.from_pandas(signed, preserve_index=False)
            if writer is None:
                writer = pq.ParquetWriter(target / 'connectivity.parquet', table.schema, compression='zstd')
            writer.write_table(table)
            pre, post = signed.Presynaptic_Index.to_numpy(), signed.Postsynaptic_Index.to_numpy()
            outgoing[pre] = True
            incoming[post] = True
            keys.append(pre.astype('int64') * len(roster) + post)
            edge_count += len(signed)
            synapses += int(signed.Connectivity.sum())
            if i % 200 == 0:
                print(f'batch {i}/{reader.num_record_batches}: retained {edge_count:,} edges', flush=True)
    finally:
        if writer is not None:
            writer.close()
    packed = np.concatenate(keys)
    if len(np.unique(packed)) != len(packed):
        raise ValueError('duplicate retained directed edges; no freeze written')
    labels = {k: int(v) for k, v in roster.consensus_nt.value_counts().items()}
    unresolved = {}
    for label in ('unclear', 'missing'):
        mask = roster.consensus_nt.to_numpy() == label
        unresolved[label] = {'neurons': int(mask.sum()), 'with_outgoing_edges': int((mask & outgoing).sum())}
    cells = {'source': sources['tastekin_table_s1'], 'sets': sets,
             'readouts': {'MN9_R_primary': 16949, 'MN9_L_secondary': 10331}, 'mn9_source_rows': mn9}
    write_json(DATA / 'cells.json', cells)
    base = json.loads((ROOT / 'data/stim_protocol.json').read_text(encoding='utf-8'))
    protocol = derived_protocol(base, sets)
    write_json(DATA / 'stim_protocol_malecns.json', protocol)
    artifacts = {k: file_record(DATA / path) for k, path in {
        'neuron_index': 'derived/neuron_index.csv', 'completeness': 'derived/completeness.csv',
        'signed_connectivity': 'derived/connectivity.parquet', 'cells': 'cells.json',
        'protocol': 'stim_protocol_malecns.json'}.items()}
    record = {'schema_version': 1, 'substrate_version': 'male-cns-v1.0-shiu-signs-1',
              'built_utc': datetime.now(timezone.utc).isoformat(), 'scope': 'whole CNS',
              'licence': {'data': 'CC BY 4.0', 'url': 'https://creativecommons.org/licenses/by/4.0/',
                          'attribution': 'Berg et al. 2026 / MaleCNS collaboration',
                          'paper': 'https://doi.org/10.1016/j.cell.2026.08.015',
                          'adaptation': 'Proofread endpoint filtering; contiguous indices; model sign assignment.'},
              'sources': sources, 'builder': file_record(Path(__file__)), 'artifacts': artifacts,
              'roster_rule': 'body annotations superclass is non-null; ascending numeric bodyId; '
                             'retain isolated neurons; both edge endpoints must belong to this roster',
              'edge_rule': 'Release minconf-0.5 weights, every positive-count directed edge; no additional cutoff; '
                           'source order retained; duplicate pairs rejected',
              'sign_rule': {'column': 'consensus_nt (neuPrint consensusNt)', 'join': 'bodyId = body',
                            'negative': ['gaba', 'glutamate'], 'positive': 'all other consensus labels',
                            'default_positive': ['unclear', 'missing'],
                            'authority': 'Owner decision; Tastekin GABA/glutamate negative, otherwise positive'},
              'counts': {'neurons': len(roster), 'raw_edges': raw_count, 'edges': edge_count,
                         'synapses': synapses, 'positive_neurons': int((roster.sign == 1).sum()),
                         'negative_neurons': int((roster.sign == -1).sum()),
                         'default_positive_neurons': int(roster.default_positive.sum()),
                         'default_positive_with_outgoing_edges': int((roster.default_positive & outgoing).sum()),
                         'unresolved_by_label': unresolved, 'consensus_labels': labels,
                         'neurons_with_outgoing_edges': int(outgoing.sum()),
                         'neurons_with_any_edges': int((outgoing | incoming).sum()),
                         'isolated_neurons': int((~(outgoing | incoming)).sum())},
              'input_sign_audit': audit_sets(sets, roster), 'readout': protocol['readout'],
              'female_comparison': 'Female frozen LB3d: 27/29 positive despite Tastekin glutamatergic class. '
                                   'Male typed sugar is LB3b/LB3c, not LB3d; this is not a matched-class comparison.'}
    write_json(DATA / 'substrate_record.json', record)
    print(json.dumps(record['counts'], indent=2), flush=True)
    print(json.dumps(record['input_sign_audit'], indent=2), flush=True)
    verify_record()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    verify_record() if args.verify else build()
