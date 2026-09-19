# SPDX-License-Identifier: MIT
"""Export MaleCNS soma positions in the existing neurons_v1 format; no simulation."""
import argparse
import base64
import hashlib
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


def positions(table):
    soma = np.array([position(v) for v in table.somaLocation])
    towards = np.array([position(v) for v in table.tosomaLocation])
    sources = np.where(np.isfinite(soma[:, 0]), 'soma',
                       np.where(np.isfinite(towards[:, 0]), 'tosoma', 'placeholder'))
    xyz = np.where(np.isfinite(soma), soma, towards)
    return xyz, sources


def placeholder_xy(body_ids):
    """Per-body blake2b uniforms; Box-Muller x spread, independent band y.

    These are explicitly designed display positions, never anatomical estimates.
    """
    xy = []
    for body in body_ids:
        digest = hashlib.blake2b(str(body).encode('ascii'), digest_size=24).digest()
        u, v, w = [(int.from_bytes(digest[i:i+8], 'little') + .5) / 2**64 for i in (0, 8, 16)]
        normal = np.sqrt(-2 * np.log(u)) * np.cos(2 * np.pi * v)
        xy.append([np.clip(.5 + .08 * normal, .15, .85), .90 + .05 * w])
    return np.asarray(xy, dtype=float).reshape(-1, 2)


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
    measured = (sources != 'placeholder') & np.isfinite(xyz).all(axis=1)
    lateral, delta_lr = separation(xyz, measured & brain & table.somaSide.eq('L').to_numpy(),
                                  measured & brain & table.somaSide.eq('R').to_numpy())
    ml = int(np.argmax(lateral))
    vertical, delta_bv = separation(xyz, measured & brain, measured & ~brain)
    remaining = [a for a in range(3) if a != ml]
    dv = max(remaining, key=lambda a: vertical[a])
    signs = np.array([1 if delta_lr[ml] > 0 else -1, 1 if delta_bv[dv] > 0 else -1])
    oriented = xyz[:, [ml, dv]] * signs
    # One scale for both axes; leave a gap above the placeholder and VNC bands.
    brain_xy = oriented[brain & np.isfinite(oriented).all(axis=1)]
    lo, hi = brain_xy.min(axis=0), brain_xy.max(axis=0)
    span = float(max(hi - lo))
    if span <= 0:
        raise ValueError('Degenerate brain frame')
    scale = .88 / span
    offset = (np.array([1., .88]) - (hi - lo) * scale) / 2
    chosen = oriented[selected]
    xy = (chosen - lo) * scale + offset
    is_vnc = ~brain[selected]
    placeholder = ~measured[selected]
    xy[placeholder] = placeholder_xy(table.index.to_numpy()[selected[placeholder]])
    strip = is_vnc & ~placeholder
    # Compression of VNC y is explicit; x retains the brain mediolateral scale.
    if strip.any():
        v = chosen[strip, 1]
        xy[strip, 1] = .96 + .04 * (v - v.min()) / max(float(np.ptp(v)), 1e-9)
    axes = ['xyz'[ml], 'xyz'[dv]]
    frame = dict(axes=axes, flip=[bool(s < 0) for s in signs],
                 dropped_axis=next(a for a in 'xyz' if a not in axes),
                 lo=lo.tolist(), span=span, scale=scale, offset=offset.tolist(),
                 voxel_nm=[8., 8.], units='MaleCNS v1.0 8 nm voxel coordinates',
                 brain_y=[0., .88], placeholder_y=[.90, .95], vnc_y=[.96, 1.],
                 placeholder_rule='blake2b body ID; Box-Muller x mean 0.5 SD 0.08, clipped [0.15,0.85]; uniform band y',
                 axis_rule='largest absolute median separation / pooled population SD; brain L/R then brain/VNC',
                 lateral_separation=lateral.tolist(), vertical_separation=vertical.tolist())
    return np.clip(xy, 0, 1), frame, is_vnc


def build(index, table, cells, commit, background=20000):
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
    xyz, sources = positions(table)
    extras = table[table.somaNeuromere.eq('') & (sources != 'placeholder')].drop(
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
    for key in ('mn9_primary', 'mn9_secondary', 'mn11d', 'mn11v', 'cem'):
        group = cells['readouts']['mn9' if key.startswith('mn9_') else key]
        rows = group['source_rows']
        if key.startswith('mn9_'):
            rows = [r for r in rows if int(r['Body_ID']) == group[key.split('_')[1]]]
        labels = {r['Target_Muscle'] for r in rows}
        if len(labels) != 1:
            raise ValueError('Inconsistent Target_Muscle labels')
        named.append(dict(key=key, label=labels.pop(), cells=[dict(index=by_id[r['Body_ID']],
                          root_id=r['Body_ID'], side=r['Root_Side']) for r in rows]))
    def counts(values):
        return {key: int(np.count_nonzero(values == key)) for key in ('soma', 'tosoma', 'placeholder')}
    indexed_counts = counts(sources[selected[:len(root_ids)]])
    flags = np.concatenate([np.asarray(index['flags'], dtype=np.uint8), np.zeros(len(ids)-len(root_ids), dtype=np.uint8)])
    q = np.round(xy * 65535).astype('<u2')
    return dict(schema_version='neurons_v1', layout='malecns_v1_soma', n=len(ids), n_indexed=len(root_ids),
                frame=frame, flag_bits=index['flag_bits'], git_commit=commit,
                source=SOURCE + f"; canvas axes {frame['axes']}, flip {frame['flip']}; named sides: XLSX Root_Side; "
                       'unpositioned neurons use an explicitly non-anatomical placeholder band',
                named=named, named_side_source='XLSX Root_Side in data/malecns/cells_male_v1.json',
                non_replay_readouts=[str(b) for b in missing_readouts], n_background=background,
                position_sources=indexed_counts, position_sources_scope='indexed neurons',
                position_sources_all=counts(sources[selected]), vnc_indexed=int(is_vnc[:len(root_ids)].sum()),
                placeholder_indexed=indexed_counts['placeholder'],
                vnc_positioned_indexed=int((is_vnc[:len(root_ids)] & (sources[selected[:len(root_ids)]] != 'placeholder')).sum()),
                layout_note=f"{indexed_counts['placeholder']} indexed neurons have no soma or entry point recorded in the "
                            'MaleCNS v1.0 annotations (sensory neurons among them); they are drawn in a band below the '
                            'brain outline and those positions are not anatomical. VNC somas are drawn in the strip '
                            'at the bottom edge.',
                xy_b64=base64.b64encode(q.tobytes()).decode('ascii'),
                flags_b64=base64.b64encode(flags.tobytes()).decode('ascii'))


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    table = pd.read_csv(ROOT / 'data/malecns/derived/neuron_index.csv', keep_default_na=False,
                        low_memory=False).set_index('bodyId')
    payload = build(read(ROOT / 'data/replay_neurons_male.json'), table,
                    read(ROOT / 'data/malecns/cells_male_v1.json'), current_commit(ROOT))
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
