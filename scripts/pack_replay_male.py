# SPDX-License-Identifier: MIT
"""Pack existing male grid trial 0 events as AFR1; never simulate an extra trial."""
import argparse
import json
from pathlib import Path
import struct
import sys

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
from scripts.run_replay import FLAG_BITS, MAGIC
from sim.malecns import male_v1_adapter as adapter, male_v1_grid as grid
from sim.malecns.audit_male_v1_phase1 import equal, require
from sim.malecns.build_lookup_male import checked_results, current_commit
from sim.malecns.substrate import ROOT, file_record, write_json

INDEX = ROOT / 'data/replay_neurons_male.json'
OUTPUT = ROOT / 'data/replay_male'
NOTE = ('recorded output of grid trial 0 of the male model; one of the 30 trials behind the score; '
        'not a live simulation')


def flag_map(cells, p):
    flags = {}
    for channel in adapter.CHANNELS:
        for body in cells['sets'][channel]['ids']:
            flags[body] = flags.get(body, 0) | FLAG_BITS[channel]
    for side, name in [('primary', 'mn9_left'), ('secondary', 'mn9_right')]:
        body = p['readout'][side]
        flags[body] = flags.get(body, 0) | FLAG_BITS[name]
    return flags


def trial_zero(group):
    row = group['rows'][0]
    c = group['condition']
    equal((row['condition'], row['global_index'], row['trial'], row['seed']),
          (c['cond_id'], c['global_index'], 0, grid.seeds_for(c['global_index'])[0]), 'Replay identity')
    path = ROOT / row['spikes']['path']
    equal(path.name, 'trial_00.npz', 'Only grid trial 0 may be packed')
    equal(path.parent.name, c['cond_id'], 'Replay cell path')
    adapter.check_file(row['spikes'])
    with np.load(path, allow_pickle=False) as raw:
        body, times = raw['body_id'], raw['time_s']
    require(body.ndim == times.ndim == 1 and len(body) == len(times), 'Replay event shape')
    require(np.issubdtype(body.dtype, np.integer) and (body > 0).all(), 'Replay body IDs')
    require(np.isfinite(times).all() and (times >= 0).all() and (times < 1).all()
            and (np.diff(times) >= 0).all(), 'Replay times')
    for side, body_id in [('L', 10331), ('R', 16949)]:
        equal(int(np.count_nonzero(body == body_id)), row[side+'_hz'], 'Trial 0 MN9 count/rate')
    equal(len(body), row['whole_network_spikes'], 'Trial 0 network count')
    return body, times


def encode_events(body, times, index_ids, condition, row, commit, protocol_sha256, n_model_neurons):
    position = {int(b): i for i, b in enumerate(index_ids)}
    # The largest index, not the neuron count, determines whether u16 fits.
    dtype = np.dtype('<u2' if len(index_ids) <= 65536 else '<u4')
    idx = np.fromiter((position[int(b)] for b in body), dtype=dtype, count=len(body))
    units = np.rint(times*10000).astype('<u2')
    left = np.round(times[body == 10331]*1000, 1).tolist()
    right = np.round(times[body == 16949]*1000, 1).tolist()
    header = dict(schema_version='replay_v2', fly='male', cell_id=condition['cond_id'], variant='baseline',
                  n_model_neurons=n_model_neurons, seed=row['seed'], seed_rule=grid.REPLAY_RULE, trial=0,
                  mn9_left_ms=left, mn9_right_ms=right, mn9_left_count=len(left), mn9_right_count=len(right),
                  mn9_left_first_ms=left[0] if left else None, mn9_right_first_ms=right[0] if right else None,
                  n_spikes=len(body), n_neurons_active=len(np.unique(body)), levels=condition['levels'],
                  hz=condition['hz'], git_commit=commit, protocol_sha256=protocol_sha256,
                  duration_ms=1000.0, t_unit_ms=0.1, idx_dtype='u16' if dtype.itemsize == 2 else 'u32', note=NOTE)
    blob = json.dumps(header, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode('utf-8')
    return MAGIC+struct.pack('<I', len(blob))+blob+idx.tobytes()+units.tobytes(), header


def pack_trials(full, p, cells, index_path, output, commit, protocol_sha256, n_model_neurons):
    """Two streaming passes over trial 0 only; also usable with tiny synthetic ledgers."""
    if output.exists() or index_path.exists():
        raise FileExistsError('Male replay index or folder already exists')
    groups = full['raw']
    require(bool(groups), 'Empty replay inventory')
    names = [g['condition']['cond_id'] for g in groups]
    require(len(set(names)) == len(names), 'Duplicate replay cell')
    flags = flag_map(cells, p)
    spiking = set(flags)
    total = 0
    for group in groups:
        body, _ = trial_zero(group)
        spiking.update(int(b) for b in np.unique(body))
        total += len(body)
    ids = sorted(spiking)
    index = dict(schema_version='replay_neurons_v1', fly='male', id_space='MaleCNS v1.0 body id',
                 git_commit=commit, replay_run=dict(seed_rule=grid.REPLAY_RULE,
                 path=str(Path(groups[0]['rows'][0]['spikes']['path']).parent.parent.as_posix()),
                 n_cells_run=len(groups), n_spikes_total=total, trial='grid trial 0'),
                 flag_bits=FLAG_BITS, n_neurons=len(ids), root_ids=[str(b) for b in ids],
                 flags=[flags.get(b, 0) for b in ids], readouts=p['readout']['extra_readouts'])
    output.mkdir(parents=True)
    write_json(index_path, index)
    manifest = dict(schema_version='replay_manifest_v1', fly='male', git_commit=commit,
                    n_cells=len(groups), cells={})
    sizes = []
    for group in groups:
        body, times = trial_zero(group)
        c, row = group['condition'], group['rows'][0]
        payload, header = encode_events(body, times, ids, c, row, commit, protocol_sha256, n_model_neurons)
        with (output / (c['cond_id']+'.bin')).open('xb') as stream:
            stream.write(payload)
        sizes.append(len(payload))
        manifest['cells'][c['cond_id']] = dict(levels=c['levels'], n_spikes=len(body),
                                              mn9_left_count=header['mn9_left_count'])
    write_json(output / 'manifest.json', manifest)
    stats = dict(min_bytes=min(sizes), median_bytes=float(np.median(sizes)), max_bytes=max(sizes),
                 total_bytes=sum(sizes), n_cells=len(groups), n_neurons=len(ids),
                 index_bytes=index_path.stat().st_size, manifest_bytes=(output / 'manifest.json').stat().st_size)
    print(json.dumps(stats, sort_keys=True), flush=True)
    return stats


def pack(result_path=None, index_path=INDEX, output=OUTPUT):
    if output.exists() or index_path.exists():
        raise FileExistsError('Male replay index or folder already exists')
    p, cells, _ = adapter.load_configuration()
    result, full = checked_results(grid.RESULT if result_path is None else result_path)
    equal([g['condition'] for g in full['raw']], grid.conditions(p), '400-cell replay inventory')
    substrate = adapter.read(ROOT / p['substrate_record']['path'])
    equal(substrate['counts']['neurons'], 166700, 'Male model neuron count')
    return pack_trials(full, p, cells, index_path, output, current_commit(),
                       file_record(adapter.PROTOCOL)['sha256'], substrate['counts']['neurons'])


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    pack()


if __name__ == '__main__':
    main()
