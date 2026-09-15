"""Audit saved v1.2 trials and build a new table; never replace the v1 table."""
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from sim.lookup_v1_2 import OUT, SPEC, RULE, design, groups_for, state_for, verify_mn9
from sim.run_mn_readouts import load_json, sha256, published_grid_seed
from sim.grid import EXPECTED_DIMENSIONS, expand_grid_conditions, load_grid_levels
from sim.lookup import LookupTable, _cells_sha256
from scripts.mn_readouts_from_replays import neuron_metrics, aggregate_metrics

MN9_KEYS = ('mn9_mean', 'mn9_std', 'mn9_left_mean', 'mn9_left_std', 'mn9_right_mean', 'mn9_right_std')
STATES = ('eats', 'mouth_moves', 'proboscis_only', 'no_response')


def mn9_tokens(blob):
    pattern = rb'"(?:' + b'|'.join(k.encode() for k in MN9_KEYS) + rb')"\s*:\s*[-+0-9.eE]+'
    return re.findall(pattern, blob)


def verify_projection(old, new, old_bytes, new_bytes):
    if len(old['cells']) != len(new['cells']):
        raise ValueError('STOP: cell count differs')
    projected = [{k: b[k] for k in a} for a, b in zip(old['cells'], new['cells'])]
    if _cells_sha256(projected) != old['cells_sha256']:
        raise ValueError('STOP: original cell projection differs')
    before, after = mn9_tokens(old_bytes), mn9_tokens(new_bytes)
    if len(before) != 400 * 6 or before != after:
        raise ValueError('STOP: literal MN9 field bytes differ')
    return {'literal_mn9_fields_byte_identical': len(before),
            'original_cell_projection_sha256': _cells_sha256(projected)}


def audit_cell(condition, spec, protocol, meta):
    cell_id = condition['cond_id']
    ledger = load_json(OUT / (cell_id + '.json'))
    identity = ledger['identity']
    expected_seeds = [published_grid_seed(condition['global_index'], t) for t in range(30)]
    expected = {k: meta[k] for k in ['source_sha256', 'seed_scheme', 'brian2_version', 'duration_ms', 'channels']}
    expected.update(cell_id=cell_id, global_index=condition['global_index'], input_hz=condition['rates'],
                    seeds=expected_seeds,
                    original_grid_parquet_sha256=sha256(ROOT / 'results/grid/full' / (cell_id + '.parquet')))
    if identity != expected or ledger['completed_trials'] != list(range(30)):
        raise ValueError('Incomplete or mismatched ledger: ' + cell_id)
    raw_path = OUT / (cell_id + '.npz')
    if ledger['spikes_sha256'] != sha256(raw_path) or ledger['mn9_bilateral_exact_spike_match_trials'] != 30:
        raise ValueError('Invalid spike/identity check: ' + cell_id)
    ids = [n['Body_ID'] for n in spec['readout_neurons']]
    individual, grouped = [], []
    with np.load(raw_path, allow_pickle=False) as raw:
        if not np.array_equal(raw['seeds'], expected_seeds) or set(raw['trial']) - set(range(30)):
            raise ValueError('Invalid raw seeds/trials')
        if not set(raw['flywire_id']).issubset({int(i) for i in ids}):
            raise ValueError('Unexpected recorded neuron')
        for trial, seed in enumerate(expected_seeds):
            selected = raw['trial'] == trial
            metrics = neuron_metrics(raw['flywire_id'][selected], raw['t_ms'][selected], ids, 1000)
            prefix = {'cell_id': cell_id, 'global_index': condition['global_index'], 'trial': trial, 'seed': seed}
            individual.extend({**prefix, **n, **metrics[n['Body_ID']]} for n in spec['readout_neurons'])
            grouped.extend({**prefix, 'readout': name, **aggregate_metrics([metrics[i] for i in members])}
                           for name, members in groups_for(spec, protocol).items())
    if individual != ledger['individual'] or grouped != ledger['grouped']:
        raise ValueError('Raw spike reconstruction differs from ledger: ' + cell_id)
    verify_mn9(grouped, condition)
    values = {name: np.array([r['rate_hz'] for r in grouped if r['readout'] == name])
              for name in groups_for(spec, protocol)}
    return values, {'ledger_sha256': sha256(OUT / (cell_id + '.json')),
                    'spikes_sha256': ledger['spikes_sha256'],
                    'original_grid_parquet_sha256': identity['original_grid_parquet_sha256']}


def build():
    for target in [ROOT / 'data/lookup_table_v1_2.json', ROOT / 'data/lookup_v1_2_audit.json', OUT / 'checkpoint.json']:
        if target.exists():
            raise FileExistsError('Refusing to overwrite an existing v1.2 artifact: ' + str(target))
    spec, protocol = design()
    if spec != load_json(SPEC):
        raise ValueError('Frozen recording design differs')
    meta = load_json(OUT / 'run_meta.json')
    if meta['status'] != 'complete' or meta['n_trials_completed'] != 12000 or meta['bilateral_exact_spike_match_trials'] != 12000:
        raise ValueError('Complete 12,000-trial identity-checked run required')
    for name, expected in meta['source_sha256'].items():
        if sha256(ROOT / name) != expected:
            raise ValueError('Run source hash differs: ' + name)
    old_path = ROOT / 'data/lookup_table.json'
    old_bytes = old_path.read_bytes()
    old = json.loads(old_bytes)
    new = deepcopy(old)
    new.update(schema_version='lookup_v1_2', generated_at=datetime.now(timezone.utc).isoformat(),
               git_commit=meta['git_commit'], state_rule=RULE,
               readouts_recorded=spec['readout_neurons'], source_lookup_sha256=sha256(old_path),
               recording_spec_sha256=sha256(SPEC), recording_meta_sha256=sha256(OUT / 'run_meta.json'),
               extra_statistics={'std_ddof': 0, 'decimal_places': 3,
                   'mn11d': 'Mean and population SD over 30 per-trial two-cell mean rates.',
                   'mn11v': 'Mean and population SD over 30 per-trial two-cell mean rates.',
                   'mn9_r': 'Mean and population SD of the right MN9 rate; aliases of the frozen right fields.',
                   'state': 'Threshold applied to unrounded 30-trial means; rounding does not change any state.'},
               recording_note='Re-recording with original batch-40 seeds and unchanged protocol; not 30 additional independent trials. Site integration deferred.')
    cell_artifacts = {}
    for condition, cell in zip(expand_grid_conditions(load_grid_levels()), new['cells']):
        values, artifacts = audit_cell(condition, spec, protocol, meta)
        cell_artifacts[condition['cond_id']] = artifacts
        for name, prefix in [('MN11D', 'mn11d'), ('MN11V', 'mn11v'), ('MN9_R', 'mn9_r')]:
            cell[prefix + '_mean'] = round(float(values[name].mean()), 3)
            cell[prefix + '_sd'] = round(float(values[name].std(ddof=0)), 3)
        cell['state'] = state_for(values['MN9_L'].mean(), values['MN11D'].mean())
        if cell['state'] != state_for(cell['mn9_mean'], cell['mn11d_mean']):
            raise ValueError('Threshold rounding ambiguity')
        if cell['mn9_r_mean'] != cell['mn9_right_mean'] or cell['mn9_r_sd'] != cell['mn9_right_std']:
            raise ValueError('STOP: right MN9 alias mismatch')
    new['cells_sha256'] = _cells_sha256(new['cells'])
    # Keep provenance and the declared state rule in the header, ahead of the large cell array.
    cells = new.pop('cells')
    new['cells'] = cells
    encoded = (json.dumps(new, indent=2, ensure_ascii=False, allow_nan=False) + '\n').encode('utf-8')
    checks = verify_projection(old, new, old_bytes, encoded)
    table = LookupTable(new)
    dishes = load_json(ROOT / 'data/dishes.json')
    if len(dishes) != 174 or len({d['key'] for d in dishes}) != 174:
        raise ValueError('Expected the frozen 174-dish dictionary')
    dish_states = {d['key']: table.get(**{dim: d[dim] for dim in EXPECTED_DIMENSIONS})['state'] for d in dishes}
    cell_counts = Counter(c['state'] for c in new['cells'])
    dish_counts = Counter(dish_states.values())
    report = {**checks, 'mn9_neuron_trials_exact_spike_match': 24000,
              'individual_neuron_trials_reconstructed': 72000, 'grouped_readout_trials_reconstructed': 48000,
              'source_lookup_sha256': sha256(old_path), 'dishes_sha256': sha256(ROOT / 'data/dishes.json'),
              'cell_counts': {s: cell_counts[s] for s in STATES}, 'dish_counts': {s: dish_counts[s] for s in STATES},
              'mouth_moves': [{**{d: c[d] for d in EXPECTED_DIMENSIONS}, 'hz': c['hz'],
                               'mn9_mean': c['mn9_mean'], 'mn11d_mean': c['mn11d_mean']}
                              for c in new['cells'] if c['state'] == 'mouth_moves'], 'dish_states': dish_states}
    output = ROOT / spec['output']
    if old_path.read_bytes() != old_bytes:
        raise ValueError('STOP: old lookup changed during build')
    with output.open('xb') as f:
        f.write(encoded)
    report['lookup_v1_2_sha256'] = sha256(output)
    report['lookup_v1_2_cells_sha256'] = new['cells_sha256']
    with (ROOT / 'data/lookup_v1_2_audit.json').open('x', encoding='utf-8') as f:
        json.dump({'run': meta, 'checkpoint': report, 'trial_artifacts': cell_artifacts,
                   'raw_directory': 'results/grid/v1_2 (local, gitignored)',
                   'builder_sha256': sha256(Path(__file__))}, f, indent=2, ensure_ascii=False); f.write('\n')
    with (OUT / 'checkpoint.json').open('x', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False); f.write('\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'dish_states'}, indent=2))


if __name__ == '__main__':
    build()
