# SPDX-License-Identifier: MIT
"""Resolve bilateral female M1j cells; --verify recomputes without writes or simulation."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts.build_mn_readout_ids import read_v783_ids
from scripts.cross_check_cells import FLYWIRE
from sim.malecns.m1j_cells import CHANNELS, physical_layout, record, typed_sets, write_or_verify

OUTPUT = ROOT / 'data/cells_m1j_female.json'


def expected_cells():
    original_path = ROOT / 'data/cells.json'
    original = json.loads(original_path.read_text(encoding='utf-8'))
    protocol_path = ROOT / 'data/stim_protocol.json'
    protocol = json.loads(protocol_path.read_text(encoding='utf-8'))
    source, sets = typed_sets(FLYWIRE, {'LB3b': {'L': 13, 'R': 12}, 'LB3c': {'L': 20, 'R': 12}})
    for key, count in [('bitter', 42), ('water', 18), ('ir94e', 18)]:
        sets[key] = deepcopy(original['sets'][key])
        if len(sets[key]['ids']) != count:
            raise ValueError(f'Unexpected frozen {key} count')
    union = set(sets['sugar_bilateral']['ids'])
    overlaps = {}
    for key, count in [('sugar', 12), ('water', 7), ('bitter', 0), ('ir94e', 0)]:
        ids = sorted(union & set(original['sets'][key]['ids']))
        if len(ids) != count:
            raise ValueError(f'Unexpected frozen {key} overlap')
        overlaps[key] = {'count': count, 'ids': ids}
    layout = physical_layout(sets, dict(zip(CHANNELS, (57, 42, 11, 18))))
    if layout['poisson_units'] != 128:
        raise ValueError('Expected 128 unique physical roots')
    completeness = ROOT / protocol['completeness_file']
    v783 = read_v783_ids(completeness)
    all_ids = {str(body) for item in sets.values() for body in item['ids']}
    all_ids.update(str(protocol['readout'][side]) for side in ('left', 'right'))
    if not all_ids <= v783:
        raise ValueError(f'IDs absent from v783: {sorted(all_ids - v783)}')
    return {'data_version': original['data_version'], 'source': source,
            'original_cells': record(original_path), 'reference_protocol': record(protocol_path),
            'completeness': {**record(completeness), 'all_ids_present': True, 'checked_count': len(all_ids)},
            'sets': sets, 'readout': deepcopy(protocol['readout']), 'overlaps': overlaps, 'layout': layout}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    expected = expected_cells()
    write_or_verify(OUTPUT, expected, args.verify)
    print('Overlaps with frozen sets: ' + str({k: v['count'] for k, v in expected['overlaps'].items()}))
    print('All stimulus and readout IDs present in v783')


if __name__ == '__main__':
    main()
