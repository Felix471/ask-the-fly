"""Stage 400 baseline replays with explicit MN11D/V rows, outside site/."""
from copy import deepcopy
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from sim.lookup_v1_2 import design, OUT
from sim.run_mn_readouts import load_json, sha256
from sim.grid import EXPECTED_DIMENSIONS, expand_grid_conditions, load_grid_levels
from scripts.mn_readouts_from_replays import validate_replay


def unpack(blob):
    if blob[:4] != b'AFR1' or len(blob) < 8:
        raise ValueError('Invalid AFR1 file')
    length = struct.unpack('<I', blob[4:8])[0]
    header_bytes, body = blob[8:8+length], blob[8+length:]
    header = json.loads(header_bytes)
    width = {'u16': 2, 'u32': 4}[header['idx_dtype']]
    if len(body) != header['n_spikes'] * (width + 2):
        raise ValueError('Invalid binary body length')
    return header, header_bytes, body


def expand(blob, raw, condition, neurons, index, protocol):
    header, original_header, body = unpack(blob)
    seed_match = re.search(r'base_seed\s*=\s*(\d+)', protocol['trial']['seed_rule'])
    if seed_match is None:
        raise ValueError('Unrecognized frozen seed rule')
    validate_replay(raw, condition, int(seed_match.group(1)) + 700000 + condition['global_index'], 1000)
    if header['cell_id'] != condition['cond_id'] or header['variant'] != 'baseline' or header['schema_version'] != 'replay_v2':
        raise ValueError('Unexpected source header')
    if header['hz'] != condition['rates'] or header['seed'] != int(raw['seed']):
        raise ValueError('Source header provenance mismatch')
    ids, times = raw['flywire_id'], raw['t_ms']
    position = {int(r): i for i, r in enumerate(index['root_ids'])}
    idx = np.array([position[int(r)] for r in ids], dtype='<u2' if header['idx_dtype'] == 'u16' else '<u4')
    t_units = np.clip(np.round(times * 10), 0, 10000).astype('<u2')
    if idx.tobytes() + t_units.tobytes() != body:
        raise ValueError('STOP: whole-network replay body differs from the raw recording')
    for side in ['left', 'right']:
        ts = np.round(times[ids == int(protocol['readout'][side])], 1).tolist()
        if ts != header['mn9_'+side+'_ms'] or len(ts) != header['mn9_'+side+'_count']:
            raise ValueError('STOP: original packed MN9 differs from raw recording')
    additions = {'readout_rows': {}}
    for kind in ['MN11D', 'MN11V']:
        rows = []
        for n in neurons:
            if n['Type'] != kind:
                continue
            root = n['Body_ID']
            ts = np.round(times[ids == int(root)], 1).tolist()
            rows.append({'root_id': root, 'root_side': n['Root_Side'], 'target_muscle': n['Target_Muscle'],
                         'neuron_index': position[int(root)], 'spike_ms': ts, 'count': len(ts),
                         'rate_hz': float(len(ts)), 'first_ms': min(ts) if ts else None})
        if len(rows) != 2:
            raise ValueError('Expected two cells per MN11 type')
        additions['readout_rows'][kind] = {'cells': rows, 'two_cell_mean_hz': sum(r['rate_hz'] for r in rows) / 2}
    if not original_header.endswith(b'}'):
        raise ValueError('Unexpected header serialization')
    # Preserve every existing header field byte-for-byte except the explicit schema version.
    amended = original_header.replace(b'"replay_v2"', b'"replay_v3"', 1)
    amended = amended[:-1] + b',' + json.dumps(additions, separators=(',', ':'), ensure_ascii=False).encode('utf-8')[1:]
    result = b'AFR1' + struct.pack('<I', len(amended)) + amended + body
    new, _, new_body = unpack(result)
    projected = deepcopy(new)
    del projected['readout_rows']
    projected['schema_version'] = 'replay_v2'
    if projected != header or new_body != body:
        raise ValueError('STOP: original replay fields changed')
    return result, additions['readout_rows'], hashlib.sha256(body).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-only', action='store_true', help='Verify raw and packed source data without writing')
    args = parser.parse_args()
    spec, protocol = design()
    if not args.check_only:
        checkpoint = load_json(OUT / 'checkpoint.json')
        if checkpoint['lookup_v1_2_sha256'] != sha256(ROOT / 'data/lookup_table_v1_2.json'):
            raise ValueError('Completed identity-checked table required first')
    destination = ROOT / spec['replay_output']
    if destination.exists() and not args.check_only:
        raise FileExistsError('Refusing to overwrite a staged replay pack')
    source = ROOT / 'site/data/replay'
    index_path = ROOT / 'data/replay_neurons.json'
    index = load_json(index_path)
    source_manifest = load_json(source / 'manifest.json')
    conditions = expand_grid_conditions(load_grid_levels())
    outputs, entries = {}, {}
    for c in conditions:
        name = c['cond_id'] + '.bin'
        raw_path = ROOT / 'results/replay' / (c['cond_id'] + '.npz')
        original_blob = (source / name).read_bytes()
        original_header, _, _ = unpack(original_blob)
        if original_header['protocol_sha256'] != spec['base_protocol_sha256']:
            raise ValueError('Source replay protocol differs')
        with np.load(raw_path, allow_pickle=False) as raw:
            packed, rows, body_hash = expand(original_blob, raw, c, spec['readout_neurons'], index, protocol)
        outputs[name] = packed
        old_entry = source_manifest['cells'][c['cond_id']]
        if any(old_entry[k] != original_header[k] for k in ['levels', 'n_spikes', 'mn9_left_count']):
            raise ValueError('Source manifest differs from replay header')
        entries[c['cond_id']] = {k: old_entry[k] for k in ['levels', 'n_spikes', 'mn9_left_count']}
        entries[c['cond_id']].update(file=name, sha256=hashlib.sha256(packed).hexdigest(),
                                    source_packed_sha256=sha256(source / name), raw_replay_sha256=sha256(raw_path),
                                    unchanged_binary_body_sha256=body_hash,
                                    mn11d_mean=rows['MN11D']['two_cell_mean_hz'], mn11v_mean=rows['MN11V']['two_cell_mean_hz'])
    manifest = {'schema_version': 'replay_manifest_v2', 'replay_schema_version': 'replay_v3',
                'packed_at': datetime.now(timezone.utc).isoformat(),
                'packing_git_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                'packer_sha256': sha256(Path(__file__)),
                'n_cells': 400, 'variants': ['baseline'],
                'scope': 'Staged baseline pack only; all live site files and existing silencing variants remain unchanged.',
                'not_repacked_variants': [v for v in source_manifest['variants'] if v != 'baseline'],
                'source_manifest_sha256': sha256(source / 'manifest.json'),
                'git_commit': source_manifest['git_commit'], 'protocol_sha256': spec['base_protocol_sha256'],
                'index_file': 'replay_neurons.json', 'index_sha256': sha256(index_path),
                'recorded_readout_neurons': spec['readout_neurons'],
                'identity_check': 'All 400 whole-network binary bodies and original MN9 header bytes unchanged; verified against raw recordings.',
                'trial_note': 'One extra replay trial per cell, not a lookup-table trial and not the 30-trial mean used for state.',
                'cells': entries}
    if args.check_only:
        print('PASS: all 400 raw/binary bodies agree; MN9 rows unchanged; 1,600 MN11 rows available. No files written.')
        return
    # Do not write a partial pack if any source check fails.
    destination.mkdir()
    for name, blob in outputs.items():
        with (destination / name).open('xb') as f:
            f.write(blob)
    with (destination / 'replay_neurons.json').open('xb') as f:
        f.write(index_path.read_bytes())
    with (destination / 'manifest.json').open('x', encoding='utf-8') as f:
        json.dump(manifest, f, separators=(',', ':'), ensure_ascii=False); f.write('\n')
    print(json.dumps({'repacked_baseline_cells': len(outputs), 'mn9_rows_byte_identical': 800,
                      'whole_binary_bodies_byte_identical': 400, 'mn11_individual_rows_added': 1600,
                      'manifest_sha256': sha256(destination / 'manifest.json')}, indent=2))


if __name__ == '__main__':
    main()
