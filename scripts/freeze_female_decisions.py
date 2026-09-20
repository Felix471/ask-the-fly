# SPDX-License-Identifier: MIT
"""Freeze v1.2.1 female decisions once, independently of the live JavaScript.

Inputs were compared to the v1.2.1 tag. Canonical JSON hashes ignore checkout
line endings; their contents must never change. Existing fixtures are refused.
The 174-dish guard is the frozen v1.2.1 reference set, not today's dictionary.
Do not rerun this generator against an expanded dictionary.
Pair order is i<j in dictionary order; each pair has ask then opposite outcomes.
An outcome is [winner, flyPick, tie, flyTies, humanSet]: first two are local
indices 0/1 (-1 means no winner); sets are bit masks (1=first, 2=second).
"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    'data/lookup_table_v1_2.json': 'c1fe37fdc35c5540da1bc495363bcf18676bdfb65f2a4bd817657f071ee7e663',
    'data/dishes.json': '48cf7ed2d66122fcd0683a5a43c5a8c68f6c3e3314a15a190ad0b3f111f4f58a',
}


def freeze(output):
    if output.exists():
        raise FileExistsError(f'Refusing to overwrite frozen fixture: {output}')
    sources = []
    for name, expected in SOURCES.items():
        value = json.loads((ROOT / name).read_text(encoding='utf-8'))
        canonical = json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()
        if hashlib.sha256(canonical).hexdigest() != expected:
            raise ValueError(f'Frozen v1.2.1 source changed: {name}')
        sources.append(value)
    table, dictionary = sources
    assert len(dictionary) == 174 and len(table['cells']) == 400
    dimensions = ('sugar', 'bitter', 'water', 'ir94e')
    by_hz = {tuple(c['hz'][d] for d in dimensions): c for c in table['cells']}
    dishes = []
    for dish in dictionary:
        hz = tuple(table['levels'][d][dish.get(d, 'none')] for d in dimensions)
        cell = by_hz[hz]
        cell_id = 'G_' + '_'.join(d[0] + cell[d] for d in dimensions)
        dishes.append([dish['key'], cell_id, cell['mn9_mean'], cell['state']])
    pairs = []
    for i, first in enumerate(dishes):
        for second in dishes[i + 1:]:
            a, b = first[2], second[2]
            if abs(a - b) < 1e-9:
                pairs.append([[0, 0, 3, 3, 0], [-1, 0, 3, 3, 0]])
            else:
                high = 0 if a > b else 1
                low = 1 - high
                pairs.append([[high, high, 0, 0, 0], [low, high, 0, 0, 1 << low]])
    fixture = dict(version='v1.2.1', source_sha256=SOURCES,
                   encoding='pairs: i<j; modes ask,opposite; outcome [winner,flyPick,tie,flyTies,humanSet]; local indices -1/0/1; sets bitmask 1/2',
                   dishes=dishes, pairs=pairs)
    payload = (json.dumps(fixture, ensure_ascii=False, separators=(',', ':')) + '\n').encode()
    assert len(pairs) == 15051 and len(payload) < 1_000_000
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('xb') as stream:
        stream.write(payload)
    print(f'{len(payload)} bytes; sha256 {hashlib.sha256(payload).hexdigest()}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=ROOT / 'site/test/fixtures/female_v1_2_1_decisions.json')
    freeze(parser.parse_args().out)
