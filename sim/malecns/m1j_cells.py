# SPDX-License-Identifier: MIT
"""Resolve M1j Table S1 cells without Brian2; --verify reads without writing.

Creation is exclusive: existing declarations are never overwritten.
"""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts.cross_check_cells import XLSX, read_xlsx

WORKBOOK_SHA256 = '7b28d5f3ae45d68c510b8a3616700f0df2a5a6f2e2d2dba490d172939f2b64c9'
OUTPUT = ROOT / 'data/malecns/cells_m1j.json'
CHANNELS = ('sugar', 'bitter', 'water', 'ir94e')


def record(path):
    return {'path': path.relative_to(ROOT).as_posix(), 'bytes': path.stat().st_size,
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def typed_sets(connectome, expected_sides):
    source = record(XLSX)
    if source['sha256'] != WORKBOOK_SHA256:
        raise ValueError('Table S1 workbook hash differs from declaration')
    rows = [r for r in read_xlsx(XLSX)['GRNs']
            if r.get('Connectome') == connectome and r.get('Subtype') in {'LB3b', 'LB3c'}]
    seen = set()
    for row in rows:
        body = row.get('Body_ID', '')
        if (not isinstance(body, str) or not re.fullmatch(r'[1-9][0-9]*', body)
                or body in seen or row.get('Root_Side') not in {'L', 'R'}
                or row.get('Type') != 'LB3'):
            raise ValueError('Invalid or duplicate typed sugar source row')
        seen.add(body)
    rows.sort(key=lambda r: int(r['Body_ID']))
    for subtype, sides in expected_sides.items():
        actual = {side: sum(r['Subtype'] == subtype and r['Root_Side'] == side for r in rows)
                  for side in ('L', 'R')}
        if actual != sides:
            raise ValueError(f'{subtype} side counts differ: {actual}')
    sets = {}
    for name, subtypes in [('sugar_bilateral', ['LB3b', 'LB3c']),
                           ('sugar_lb3c_bilateral', ['LB3c'])]:
        selected = [r for r in rows if r['Subtype'] in subtypes]
        sets[name] = {'ids': [int(r['Body_ID']) for r in selected], 'count': len(selected),
                      'subtypes': subtypes, 'xlsx_sides': ['L', 'R'],
                      'sides': {s: sum(r['Root_Side'] == s for r in selected) for s in ('L', 'R')},
                      'source_rows': [{k: r.get(k, '') for k in
                                       ('Body_ID', 'Root_Side', 'Type', 'Subtype', 'Entry_Nerve')}
                                      for r in selected]}
    source.update(sheet='GRNs', connectome=connectome,
                  selection='Subtype LB3b or LB3c; both Root_Side L and R; labellar only.')
    return source, sets


def physical_layout(sets, expected_counts):
    seen, channels = set(), {}
    for channel in CHANNELS:
        key = 'sugar_bilateral' if channel == 'sugar' else channel
        ids = sets[key]['ids']
        if len(ids) != len(set(ids)):
            raise ValueError(f'Duplicate IDs in {key}')
        physical = sorted(set(ids) - seen)
        if len(physical) != expected_counts[channel]:
            raise ValueError(f'Unexpected physical count for {channel}')
        channels[channel] = {'cell_set': key, 'logical_count': len(ids),
                             'physical_count': len(physical), 'ids': physical}
        seen.update(physical)
    return {'channel_order': list(CHANNELS), 'within_channel_order': 'ascending numeric Body_ID',
            'poisson_units': len(seen), 'channels': channels,
            'dedup_rule': 'Each physical root appears once. A root in sugar_bilateral and water is assigned to sugar.',
            'refractory_rule': 'Inactive units retain ordinary model refractory; driven units have refractory 0.',
            'inactive_channels_hz': {'water': 0, 'ir94e': 0}}


def expected_cells():
    original_path = ROOT / 'data/malecns/cells.json'
    original = json.loads(original_path.read_text(encoding='utf-8'))
    source, sets = typed_sets('maleCNS', {'LB3b': {'L': 5, 'R': 6}, 'LB3c': {'L': 12, 'R': 11}})
    for key, count in [('bitter', 38), ('water', 17), ('ir94e', 19)]:
        sets[key] = deepcopy(original['sets'][key])
        if len(sets[key]['ids']) != count:
            raise ValueError(f'Unexpected frozen {key} count')
    layout = physical_layout(sets, dict(zip(CHANNELS, (34, 38, 17, 19))))
    if layout['poisson_units'] != 108:
        raise ValueError('Expected 108 disjoint physical units')
    return {'source': source, 'original_cells': record(original_path), 'sets': sets,
            'readouts': deepcopy(original['readouts']), 'layout': layout}


def write_or_verify(output, expected, verify):
    if verify:
        if json.loads(output.read_text(encoding='utf-8')) != expected:
            raise ValueError(f'{output.name} differs from resolved declaration')
    else:
        with output.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(expected, stream, indent=2, ensure_ascii=False, allow_nan=False)
            stream.write('\n')
    print(f"{output.name}: {'verified' if verify else 'created'}, {expected['layout']['poisson_units']} physical units")
    for key in ('sugar_bilateral', 'sugar_lb3c_bilateral'):
        print(f"{key}: {expected['sets'][key]['count']}, sides {expected['sets'][key]['sides']}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    write_or_verify(OUTPUT, expected_cells(), args.verify)


if __name__ == '__main__':
    main()
