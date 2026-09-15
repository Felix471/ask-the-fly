"""Offline reference resolver for the review-only speech copy; no site integration."""
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEVELS = json.loads((ROOT / 'data/grid_levels.json').read_text())['levels']


def canonical_levels(levels):
    result = {axis: levels[axis] for axis in LEVELS}
    for axis, value in result.items():
        if value not in LEVELS[axis]:
            raise ValueError(f'Invalid {axis} level: {value}')
    if result['water'] == 'medium':
        result['water'] = 'low'
    return result


def matches(bucket, levels):
    return all(levels[axis] in allowed for axis, allowed in bucket['when'].items())


def resolve(data, state, levels):
    levels = canonical_levels(levels)
    for bucket in data['buckets']:
        if bucket['state'] == state and matches(bucket, levels):
            return bucket
    raise ValueError(f'No speech bucket for state {state}')


def line_for(data, state, levels, share_seed, lang):
    if type(share_seed) is not int or not 0 <= share_seed <= 2**53 - 1:
        raise ValueError('share_seed must be a non-negative safe integer')
    if lang not in ('zh', 'en'):
        raise ValueError('Unsupported language')
    return resolve(data, state, levels)[lang][share_seed % 3]


def main():
    data = json.loads((ROOT / 'copy/fly_lines.json').read_text(encoding='utf-8'))
    cells = json.loads((ROOT / 'data/lookup_table_v1_2.json').read_text())['cells']
    counts = Counter(resolve(data, cell['state'], cell)['id'] for cell in cells)
    print(json.dumps({'cells': len(cells), 'bucket_counts': dict(counts)}, indent=2))


if __name__ == '__main__':
    main()
