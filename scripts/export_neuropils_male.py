# SPDX-License-Identifier: MIT
"""Export verified local MaleCNS ROI meshes in the male neuron anterior frame."""
import hashlib
import json
from pathlib import Path
import struct
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts.export_neuropils import GROUPS, convex_hull
from scripts.fetch_malecns_rois import BASE, DEST, local_path, match_groups, roi_names


def mesh_vertices(blob):
    if len(blob) < 4:
        raise ValueError('Truncated legacy mesh header')
    n = struct.unpack_from('<I', blob)[0]
    end = 4+12*n
    if n < 3 or end > len(blob) or (len(blob)-end) % 12:
        raise ValueError('Invalid legacy mesh vertices/triangles')
    vertices = np.frombuffer(blob, dtype='<f4', count=3*n, offset=4).reshape(-1, 3)
    triangles = np.frombuffer(blob, dtype='<u4', offset=end)
    if not np.isfinite(vertices).all() or not len(triangles) or (triangles >= n).any():
        raise ValueError('Invalid mesh coordinates or triangle indices')
    return vertices.astype(np.float64)


def project_vertices(vertices, frame):
    if frame['axes'] != ['x', 'y'] or frame['voxel_nm'] != [8, 8]:
        raise ValueError('Expected MaleCNS anterior 8 nm frame')
    xy = vertices[:, :2]/8 * np.where(frame['flip'], -1, 1)
    return (xy-np.asarray(frame['lo']))*frame['scale']+np.asarray(frame['offset'])


def build(root, frame):
    manifest = json.loads((root/'manifest.json').read_text(encoding='utf-8'))
    if manifest['source'] != BASE:
        raise ValueError('Unexpected ROI source')
    def read(relative):
        blob = local_path(root, relative).read_bytes()
        record = manifest['files'][relative]
        if record['bytes'] != len(blob) or record['sha256'] != hashlib.sha256(blob).hexdigest():
            raise ValueError(f'ROI cache hash/size mismatch: {relative}')
        return blob
    names = roi_names(json.loads(read('segment_properties/info')))
    matched, missing = match_groups(names)
    if manifest['groups'] != matched or manifest['unmatched'] != missing:
        raise ValueError('ROI matching differs from downloaded manifest')
    groups = []
    for key, en, zh, _ in GROUPS:
        if key not in matched:
            continue
        parts = []
        for name in matched[key]:
            mesh = manifest['meshes'][name]
            if mesh['segment_id'] != str(names[name]):
                raise ValueError(f'ROI segment ID mismatch: {name}')
            fragments = json.loads(read('mesh/'+mesh['segment_id']+':0'))['fragments']
            if fragments != mesh['fragments']:
                raise ValueError(f'ROI fragment mismatch: {name}')
            parts.extend(mesh_vertices(read('mesh/'+f)) for f in fragments)
        xy = project_vertices(np.vstack(parts), frame)
        if not np.isfinite(xy).all() or (xy < 0).any() or (xy > 1).any():
            raise ValueError(f'ROI {key} falls outside the male frame; refusing clipping')
        hull = convex_hull(xy)
        if len(hull) < 3:
            raise ValueError(f'Degenerate ROI polygon: {key}')
        label_at = xy.mean(axis=0)
        if key == 'sez':
            # The male GRN cluster sits on the SEZ centroid; keep the label clear of it.
            label_at = np.array([label_at[0], hull[:, 1].max() - 0.03])
        groups.append(dict(key=key, polygon=np.round(hull, 6).tolist(),
            label_at=np.round(label_at, 6).tolist(), label_en=en, label_zh=zh, members=matched[key]))
    if len(groups) < 5:
        raise ValueError(f'Only {len(groups)} complete ROI groups matched; unmatched: {missing}')
    return dict(schema_version='neuropils_v1',
        view='anterior (x mediolateral, y dorsoventral), same frame as neurons_male.json',
        source='MaleCNS v1.0 brain ROI meshes (fullbrain-roi-v4, Janelia FlyEM, CC BY 4.0); '
               'nanometres converted to 8 nm voxels; 2D convex hull per group in the male anterior frame',
        source_url=BASE, groups=groups, unmatched=missing)


def main():
    frame = json.loads((ROOT/'site/data/neurons_male.json').read_text(encoding='utf-8'))['frame']
    payload = build(DEST, frame)
    out = ROOT/'site/data/neuropils_male.json'
    out.write_text(json.dumps(payload, ensure_ascii=False, separators=(',', ':'))+'\n', encoding='utf-8')
    print(json.dumps(dict(matched={g['key']: g['members'] for g in payload['groups']}, unmatched=payload['unmatched']), indent=2))
    print(f'Wrote {out}: {out.stat().st_size} bytes')


if __name__ == '__main__':
    main()
