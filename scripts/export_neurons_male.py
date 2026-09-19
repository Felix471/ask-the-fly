# SPDX-License-Identifier: MIT
"""Export MaleCNS soma positions in the existing neurons_v1 format; no simulation."""
import argparse
import base64
import json
from pathlib import Path
import re
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts.export_male_site import current_commit, read

SOURCE = ('MaleCNS v1.0 body annotations (Janelia FlyEM, CC BY 4.0): soma positions in the '
          'MaleCNS 8 nm voxel space, anterior view, aspect preserved; VNC somas below the brain')


def position(value):
    if not value.strip():
        return [np.nan] * 3
    if not re.fullmatch(r'\[\s*-?\d+(?:\.\d+)?\s+-?\d+(?:\.\d+)?\s+-?\d+(?:\.\d+)?\s*\]', value.strip()):
        raise ValueError('Malformed soma coordinate: ' + value)
    return [float(v) for v in value.strip()[1:-1].split()]


def positions(table, centroids=None):
    soma = np.array([position(v) for v in table.somaLocation])
    towards = np.array([position(v) for v in table.tosomaLocation])
    sources = np.where(np.isfinite(soma[:, 0]), 'soma',
                       np.where(np.isfinite(towards[:, 0]), 'tosoma', 'synapse_centroid'))
    xyz = np.where(np.isfinite(soma), soma, towards)
    for i, body in enumerate(table.index):
        if not np.isfinite(xyz[i]).all() and centroids and str(body) in centroids:
            record = centroids[str(body)]
            point = [record[axis] for axis in 'xyz']
            if not np.isfinite(point).all() or record['n_all'] <= 0:
                raise ValueError(f'Invalid synapse centroid: {body}')
            xyz[i] = point
    return xyz, sources


def separation(xyz, first, second):
    """Absolute difference in group medians / pooled population SD, per axis."""
    a, b = xyz[first], xyz[second]
    if len(a) < 2 or len(b) < 2:
        raise ValueError('Insufficient positioned annotations to determine anterior axes')
    delta = np.median(b, axis=0) - np.median(a, axis=0)
    scale = np.sqrt((a.var(axis=0) + b.var(axis=0)) / 2)
    return np.abs(delta) / np.maximum(scale, 1e-9), delta


def project(table, xyz, sources, selected):
    brain = table.somaNeuromere.eq('').to_numpy()
    measured = (sources != 'synapse_centroid') & np.isfinite(xyz).all(axis=1)
    lateral, delta_lr = separation(xyz, measured & brain & table.somaSide.eq('L').to_numpy(),
                                  measured & brain & table.somaSide.eq('R').to_numpy())
    # FlyEM anterior view is x-y. Brain/VNC separation along z reflects depth,
    # not dorsoventral position; only the horizontal orientation is inferred.
    signs = np.array([1 if delta_lr[0] > 0 else -1, 1])
    oriented = xyz[:, [0, 1]] * signs
    # Preserve the anatomical brain-only frame and bottom VNC strip.
    brain_xy = oriented[brain & measured]
    lo, hi = brain_xy.min(axis=0), brain_xy.max(axis=0)
    span = float(max(hi - lo))
    if span <= 0:
        raise ValueError('Degenerate brain frame')
    scale = .88 / span
    offset = (np.array([1., .88]) - (hi - lo) * scale) / 2
    chosen = oriented[selected]
    xy = (chosen - lo) * scale + offset
    is_vnc = ~brain[selected]
    if not np.isfinite(chosen).all():
        raise ValueError('Selected neuron has no soma, entry point or synaptic sites')
    strip = is_vnc
    # Compression of VNC y is explicit; x retains the brain mediolateral scale.
    if strip.any():
        v = chosen[strip, 1]
        xy[strip, 1] = .96 + .04 * (v - v.min()) / max(float(np.ptp(v)), 1e-9)
    axes = ['x', 'y']
    frame = dict(axes=axes, flip=[bool(s < 0) for s in signs],
                 dropped_axis='z',
                 lo=lo.tolist(), span=span, scale=scale, offset=offset.tolist(),
                 voxel_nm=[8., 8.], units='MaleCNS v1.0 8 nm voxel coordinates',
                 brain_y=[0., .88], vnc_y=[.96, 1.],
                 axis_rule='FlyEM convention: x mediolateral, y dorsoventral (increasing ventrally), '
                           'z anteroposterior; anterior view is x–y',
                 lateral_separation=lateral.tolist())
    return np.clip(xy, 0, 1), frame, is_vnc


def build(index, table, cells, commit, background=20000, centroids=None):
    if not table.index.is_unique:
        raise ValueError('Duplicate annotation body IDs')
    root_ids = index['root_ids']
    if len(set(root_ids)) != len(root_ids) or len(root_ids) != index['n_neurons'] or len(index['flags']) != len(root_ids):
        raise ValueError('Invalid frozen replay index')
    indexed_ids = [int(b) for b in root_ids]
    readout_ids = [b for group in cells['readouts'].values() for b in group['ids']]
    missing_readouts = sorted(set(readout_ids) - set(indexed_ids))
    # Silent readouts absent from trial-0 index get non-replay display slots. Never
    # insert into or alter the frozen prefix; flags remain exactly as recorded.
    xyz, sources = positions(table, centroids)
    extras = table[table.somaNeuromere.eq('') & (sources != 'synapse_centroid')].drop(
        index=indexed_ids + missing_readouts, errors='ignore')
    if len(extras) < background:
        raise ValueError('Not enough non-indexed brain neurons for background sample')
    background_ids = extras.sample(n=background, random_state=783).index.tolist()
    ids = indexed_ids + missing_readouts + background_ids
    selected = table.index.get_indexer(ids)
    if (selected < 0).any():
        raise ValueError('Selected body absent from MaleCNS annotations')
    xy, frame, is_vnc = project(table, xyz, sources, selected)
    by_id = {str(b): i for i, b in enumerate(ids)}
    named = []
    for key, label in [('mn9', 'MN9'), ('mn11d', 'MN11D'), ('mn11v', 'MN11V'), ('cem', 'CEM')]:
        group = cells['readouts'][key]
        rows = group['source_rows']
        labels = {r['Target_Muscle'] for r in rows}
        if len(labels) != 1:
            raise ValueError('Inconsistent Target_Muscle labels')
        named.append(dict(key=key, label=label, code=None, cells=[dict(index=by_id[r['Body_ID']],
                          root_id=r['Body_ID'], side=table.loc[int(r['Body_ID']), 'somaSide']) for r in rows]))
    def counts(values):
        return {key: int(np.count_nonzero(values == key)) for key in ('soma', 'tosoma', 'synapse_centroid')}
    indexed_counts = counts(sources[selected[:len(root_ids)]])
    flags = np.concatenate([np.asarray(index['flags'], dtype=np.uint8), np.zeros(len(ids)-len(root_ids), dtype=np.uint8)])
    q = np.round(xy * 65535).astype('<u2')
    return dict(schema_version='neurons_v1', layout='malecns_v1_soma', n=len(ids), n_indexed=len(root_ids),
                frame=frame, flag_bits=index['flag_bits'], git_commit=commit,
                source=SOURCE + f"; canvas axes {frame['axes']}, flip {frame['flip']}; "
                       'missing soma/entry points use cached median synaptic site coordinates',
                named=named, named_side_source='MaleCNS v1.0 annotation somaSide',
                non_replay_readouts=[str(b) for b in missing_readouts], n_background=background,
                position_sources=indexed_counts, position_sources_scope='indexed neurons',
                position_sources_all=counts(sources[selected]), vnc_indexed=int(is_vnc[:len(root_ids)].sum()),
                synapse_centroid_indexed=indexed_counts['synapse_centroid'],
                vnc_positioned_indexed=int(is_vnc[:len(root_ids)].sum()),
                layout_note=f"{indexed_counts['synapse_centroid']} indexed neurons have no soma or entry point recorded in the "
                            'MaleCNS v1.0 annotations; they are placed at their synapse centroid (median of postsynaptic '
                            'sites, or of all sites when none). VNC somas are drawn in the strip at the bottom edge.',
                xy_b64=base64.b64encode(q.tobytes()).decode('ascii'),
                flags_b64=base64.b64encode(flags.tobytes()).decode('ascii'))


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    table = pd.read_csv(ROOT / 'data/malecns/derived/neuron_index.csv', keep_default_na=False,
                        low_memory=False).set_index('bodyId')
    payload = build(read(ROOT / 'data/replay_neurons_male.json'), table,
                    read(ROOT / 'data/malecns/cells_male_v1.json'), current_commit(ROOT),
                    centroids=read(ROOT / 'data/malecns/derived/male_synapse_centroids.json')['bodies'])
    blob = (json.dumps(payload, separators=(',', ':'), ensure_ascii=False, allow_nan=False) + '\n').encode('utf-8')
    if len(blob) >= 300000:
        raise ValueError('Male neuron layout exceeds 300 KB')
    out = ROOT / 'site/data/neurons_male.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(blob)
    print(f"Indexed position sources: {payload['position_sources']}; all displayed: {payload['position_sources_all']}")
    print(f"VNC indexed: {payload['vnc_indexed']}; axes: {payload['frame']['axes']}; flip: {payload['frame']['flip']}")
    print(f"Non-replay readouts: {payload['non_replay_readouts']}; background: {payload['n_background']}")
    print(f'Wrote {out}: {len(blob)} bytes')


if __name__ == '__main__':
    main()
