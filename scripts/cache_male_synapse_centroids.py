# SPDX-License-Identifier: MIT
"""One batched scan of the full MaleCNS synapse file; cache display positions."""
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts.export_neurons_male import positions

SOURCE = ROOT / 'data/malecns/downloads/syn-partners-male-cns-v1.0-minconf-0.5.feather'
OUT = ROOT / 'data/malecns/derived/male_synapse_centroids.json'
RULE = ('Median of postsynaptic site coordinates (x_post, y_post, z_post) per body; '
        'when no postsynaptic rows exist, median of all its post and pre site rows. '
        'Rows are used as recorded, without deduplication or additional confidence filtering; '
        'coordinates are MaleCNS 8 nm voxels.')


def scan_batches(batches, targets, progress=False):
    import pyarrow as pa
    import pyarrow.compute as pc
    targets = sorted(set(map(int, targets)))
    target_set = pa.array(targets, type=pa.int64())
    sites = {side: {body: [] for body in targets} for side in ('post', 'pre')}
    count = 0
    for number, batch in enumerate(batches):
        count += batch.num_rows
        for side in ('post', 'pre'):
            filtered = batch.filter(pc.is_in(batch.column('body_'+side), value_set=target_set))
            if not filtered.num_rows:
                continue
            bodies = filtered.column('body_'+side).to_numpy()
            xyz = np.column_stack([filtered.column(axis+'_'+side).to_numpy() for axis in 'xyz'])
            order = np.argsort(bodies, kind='stable')
            bodies, xyz = bodies[order], xyz[order]
            boundaries = np.r_[0, np.flatnonzero(np.diff(bodies))+1, len(bodies)]
            for start, end in zip(boundaries[:-1], boundaries[1:]):
                sites[side][int(bodies[start])].append(xyz[start:end].copy())
        if progress and number % 250 == 0:
            print(f'Scanned {number+1} batches / {count:,} rows', flush=True)
    result = {}
    missing = []
    for body in targets:
        post, pre = sites['post'][body], sites['pre'][body]
        n_post = sum(len(a) for a in post)
        n_all = n_post + sum(len(a) for a in pre)
        if not n_all:
            missing.append(body)
            continue
        xyz = np.median(np.concatenate(post if n_post else post+pre), axis=0)
        result[str(body)] = dict(zip('xyz', map(float, xyz)), n_post=n_post, n_all=n_all,
                                 used='post' if n_post else 'all')
    if missing:
        raise ValueError(f'Bodies with no synaptic sites: {missing}')
    return result, count


def main():
    import pyarrow as pa
    if OUT.exists():
        raise FileExistsError(f'Refusing to overwrite existing cache: {OUT}')
    table = pd.read_csv(ROOT/'data/malecns/derived/neuron_index.csv', keep_default_na=False,
                        low_memory=False).set_index('bodyId')
    xyz, sources = positions(table)
    index = json.loads((ROOT/'data/replay_neurons_male.json').read_text())
    cells = json.loads((ROOT/'data/malecns/cells_male_v1.json').read_text())
    wanted = set(map(int, index['root_ids'])) | {b for g in cells['readouts'].values() for b in g['ids']}
    missing = sorted(body for body in wanted if not np.isfinite(xyz[table.index.get_loc(body)]).all())
    # Reproducible random sample from all annotations WITH a recorded soma.
    sample = table[sources == 'soma'].sample(n=50, random_state=783).index.tolist()
    before = SOURCE.stat()
    with pa.memory_map(str(SOURCE), 'r') as source:
        reader = pa.ipc.open_file(source)
        bodies, rows = scan_batches((reader.get_batch(i) for i in range(reader.num_record_batches)), missing+sample, True)
    if rows != 311833243:
        raise ValueError(f'Expected the full 311,833,243-row synapse source, got {rows:,}')
    with SOURCE.open('rb') as source:
        digest = hashlib.file_digest(source, 'sha256').hexdigest()
    after = SOURCE.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise ValueError('Synapse source changed during scan/hash')
    checks = []
    for body in sample:
        soma = xyz[table.index.get_loc(body)]
        centroid = [bodies[str(body)][axis] for axis in 'xyz']
        checks.append(dict(body_id=str(body), soma=soma.tolist(), centroid=centroid,
                           distance_voxels=float(np.linalg.norm(soma-centroid))))
    median = float(np.median([r['distance_voxels'] for r in checks]))
    # Broad display-coordinate sanity check, not a physiological/model gate.
    if not 0 < median < 50000:
        raise ValueError(f'Implausible soma/centroid median distance in 8 nm voxels: {median}')
    payload = dict(schema_version='male_synapse_centroids_v1', rule=RULE,
        source=dict(path=SOURCE.relative_to(ROOT).as_posix(), bytes=before.st_size, sha256=digest),
        counts=dict(rows_scanned=rows, targets=len(missing), validation_sample=50,
                    post=sum(bodies[str(b)]['used']=='post' for b in missing),
                    all=sum(bodies[str(b)]['used']=='all' for b in missing), no_sites=0),
        bodies={str(body): bodies[str(body)] for body in missing},
        coordinate_check=dict(seed=783, sample_rule='50 random annotations with somaLocation',
            median_distance_voxels=median, median_distance_um=median*.008, samples=checks))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open('x', encoding='utf-8', newline='\n') as out:
        out.write(json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
    print(json.dumps(dict(counts=payload['counts'], median_distance_voxels=median), indent=2))


if __name__ == '__main__':
    main()
