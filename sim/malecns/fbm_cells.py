# SPDX-License-Identifier: MIT
"""Resolve the M1i declaration's stimulus cells; no substrate build or Brian2.

Run directly to create cells_fbm.json; --verify recomputes without writing.
Existing declarations are never overwritten.
"""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'data/malecns'
ANNOTATIONS = DATA / 'downloads/body-annotations-male-cns-v1.0-minconf-0.5.feather'
OUTPUT = DATA / 'cells_fbm.json'
CONFIGURATION_SOURCE = [
    'https://github.com/blendi-remade/fly-brain-minecraft/blob/main/docs/VALIDATION.md',
    'https://github.com/blendi-remade/fly-brain-minecraft/blob/main/PROVENANCE.md',
]
SET_TYPES = {
    'fbm_sugar_labellar': ['LB3b', 'LB3c'],
    'fbm_sugar_pharyngeal': ['PhG1a', 'PhG1b', 'PhG1c'],
    'fbm_sugar_tarsal': ['LgLG3'],
    'bitter': ['LB1a', 'LB1b', 'LB1c', 'LB1d'],
}
EXPECTED_COUNTS = [34, 8, 162, 38]


def expected_cells():
    annotations = pd.read_feather(ANNOTATIONS)
    original = json.loads((DATA / 'cells.json').read_text(encoding='utf-8'))
    if annotations.bodyId.duplicated().any():
        raise ValueError('Duplicate annotation body IDs')
    sets = {}
    seen = set()
    for (name, types), count in zip(SET_TYPES.items(), EXPECTED_COUNTS):
        rows = annotations.loc[annotations['type'].isin(types)]
        ids = sorted(int(body) for body in rows.bodyId)
        if len(ids) != count or len(set(ids)) != count or seen.intersection(ids):
            raise ValueError(f'Unexpected count, duplicate or overlapping IDs: {name}')
        if rows.rootSide.isna().any() or set(rows.rootSide) != {'L', 'R'}:
            raise ValueError(f'Missing or unexpected rootSide: {name}')
        seen.update(ids)
        # Retain every original bitter field and its exact ID list, adding only
        # the common annotation-derived metadata required by this declaration.
        item = deepcopy(original['sets']['bitter']) if name == 'bitter' else {'ids': ids}
        if item['ids'] != ids:
            raise ValueError('Annotation-resolved bitter differs from frozen bitter IDs')
        item.update(types=types, sides={side: int((rows.rootSide == side).sum())
                                       for side in ('L', 'R')}, count=count)
        sets[name] = item
    if len(seen) != 242:
        raise ValueError('Expected exactly 242 distinct physical units')
    return {
        'source': {
            'path': ANNOTATIONS.relative_to(ROOT).as_posix(),
            'bytes': ANNOTATIONS.stat().st_size,
            'sha256': hashlib.sha256(ANNOTATIONS.read_bytes()).hexdigest(),
            'configuration_source': CONFIGURATION_SOURCE,
        },
        'sets': sets,
        # Historical key labels are preserved verbatim; the M1i protocols
        # explicitly set the post-M1c primary L10331 and secondary R16949.
        'readouts': deepcopy(original['readouts']),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    expected = expected_cells()
    if args.verify:
        if json.loads(OUTPUT.read_text(encoding='utf-8')) != expected:
            raise ValueError('cells_fbm.json differs from the annotation declaration')
    else:
        with OUTPUT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(expected, stream, indent=2, ensure_ascii=False, allow_nan=False)
            stream.write('\n')
    print('M1i cells ' + ('verified' if args.verify else 'created') + ': 242 distinct physical units')
    for name, item in expected['sets'].items():
        print(f"{name}: {item['count']}, rootSide {item['sides']}")


if __name__ == '__main__':
    main()
