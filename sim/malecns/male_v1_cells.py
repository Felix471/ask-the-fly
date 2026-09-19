# SPDX-License-Identifier: MIT
"""Resolve male-v1 cells from Table S1, without Brian2 or simulation.

Default: exclusively create cells_male_v1.json. --verify: re-resolve, compare,
and never write. All paths are repository-relative and independent of cwd.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import itertools
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.cross_check_cells import read_xlsx

WORKBOOK = ROOT / 'docs/papers/Tastekin_2025_bioRxiv_v2_SupplTable2_GRN_MN_body_IDs.xlsx'
WORKBOOK_HASH = '7b28d5f3ae45d68c510b8a3616700f0df2a5a6f2e2d2dba490d172939f2b64c9'
ROSTER = ROOT / 'data/malecns/derived/neuron_index.csv'
OUT = ROOT / 'data/malecns/cells_male_v1.json'
PROTOCOL = ROOT / 'data/malecns/stim_protocol_male_v1.json'
SUBTYPES = {'sugar': ['LB3b', 'LB3c'], 'bitter': ['LB1a', 'LB1b', 'LB1c', 'LB1d'],
            'water': ['LB3a'], 'ir94e': ['LB1e']}
EXPECTED_SIDES = {'sugar': {'L': 17, 'R': 17}, 'bitter': {'L': 19, 'R': 19},
                  'water': {'L': 9, 'R': 8}, 'ir94e': {'L': 11, 'R': 8}}
PRODUCT_COMMITMENTS = [
    "The male brain uses MaleCNS v1.0 with connections of >= 5 synapses and a synaptic weight of 0.65 x Shiu's (0.17875 mV), a calibration taken from an independent project (blendi-remade/fly-brain-minecraft) and replicated by us; the female uses FlyWire v783, all connections, Shiu's 0.275 mV.",
    "The male is stimulated bilaterally with Tastekin-typed GRN sets; the female unilaterally with Shiu's sets. The two flies do not share one stimulus protocol.",
    "The male brain misses one of our four behavioural gates: bitter alone at 25 Hz gives 1.07 Hz on MN9 against our 1.0 Hz limit (docs/malecns_phase0.md, M1j); invisible in the product below the 5 Hz activity threshold, but recorded.",
    "When the two flies disagree, the cause may be sex, reconstruction, cell typing, sign assignment, weight, or stimulus protocol; this pipeline cannot separate them. This sentence appears on the result page whenever they disagree, not only in the README.",
]


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def file_record(path):
    path = Path(path)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return {'path': path.relative_to(ROOT).as_posix(), 'bytes': path.stat().st_size, 'sha256': digest}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def roster_ids():
    with ROSTER.open(encoding='utf-8', newline='') as stream:
        ids = [int(r['bodyId']) for r in csv.DictReader(stream)]
    require(len(ids) == len(set(ids)) == 166700, 'M1i roster size or uniqueness mismatch')
    return set(ids)


def summarize(rows, fields, roster):
    rows = sorted(rows, key=lambda r: int(r['Body_ID']))
    ids = [int(r['Body_ID']) for r in rows]
    require(len(ids) == len(set(ids)), 'duplicate workbook Body_ID')
    require(set(ids) <= roster, 'workbook IDs missing from M1i roster')
    sides = dict(sorted(Counter(r['Root_Side'] for r in rows).items()))
    require(set(sides) <= {'L', 'R'}, 'unexpected Root_Side')
    return {'ids': ids, 'sides': sides, 'count': len(ids),
            'source_rows': [{k: r[k] for k in fields} for r in rows]}


def resolve():
    workbook_record = file_record(WORKBOOK)
    require(workbook_record['sha256'] == WORKBOOK_HASH, 'Tastekin workbook hash mismatch')
    roster_record = file_record(ROSTER)
    substrate = read_json(ROOT / 'data/malecns/substrate_record_fbm.json')
    require(roster_record == substrate['artifacts']['neuron_index'], 'M1i roster record mismatch')
    roster = roster_ids()
    sheets = read_xlsx(WORKBOOK)
    grns = [r for r in sheets['GRNs'] if r.get('Connectome') == 'maleCNS']
    mns = [r for r in sheets['MNs'] if r.get('Connectome') == 'maleCNS']
    sets = {}
    for name, subtypes in SUBTYPES.items():
        item = summarize([r for r in grns if r.get('Subtype') in subtypes],
                         ['Body_ID', 'Root_Side', 'Type', 'Subtype', 'Entry_Nerve'], roster)
        item['subtypes'] = subtypes.copy()
        require(item['sides'] == EXPECTED_SIDES[name], f'{name} count/sides mismatch')
        sets[name] = item
    for a, b in itertools.combinations(sets, 2):
        require(not set(sets[a]['ids']) & set(sets[b]['ids']), f'{a}/{b} overlap')
    require(sum(s['count'] for s in sets.values()) == 108, 'physical unit count mismatch')
    original = read_json(ROOT / 'data/malecns/cells.json')
    for name in ['bitter', 'water', 'ir94e']:
        require(sets[name]['ids'] == original['sets'][name]['ids'], f'frozen {name} set mismatch')
    m1j_path = ROOT / 'data/malecns/cells_m1j.json'
    if m1j_path.exists():
        m1j = read_json(m1j_path)
        require(sets['sugar']['ids'] == m1j['sets']['sugar_bilateral']['ids'], 'M1j sugar mismatch')
        m1j_check = {'status': 'matched', 'source': file_record(m1j_path)}
    else:
        m1j_check = {'status': 'skipped', 'reason': 'data/malecns/cells_m1j.json is absent on this branch'}
    readouts = {}
    for name, kind in [('mn9', 'MN9'), ('mn11d', 'MN11D'), ('mn11v', 'MN11V'), ('cem', 'CEM')]:
        rows = [r for r in mns if r.get('Target_Muscle') == 'Crop Entry'] if name == 'cem' else [r for r in mns if r.get('Type') == kind]
        readouts[name] = summarize(rows, ['Body_ID', 'Root_Side', 'Type', 'Target_Muscle'], roster)
        require(readouts[name]['count'] > 0, f'empty {name} readout')
    mn9 = readouts['mn9']
    require([(int(r['Body_ID']), r['Root_Side']) for r in mn9['source_rows']] == [(10331, 'L'), (16949, 'R')], 'MN9 identity/side mismatch')
    mn9.update(primary=10331, secondary=16949)
    return {'source': workbook_record, 'roster': roster_record, 'sets': sets,
            'physical_units': 108, 'readouts': readouts,
            'cross_checks': {'sugar_m1j': m1j_check,
                             'bitter_water_ir94e': {'status': 'matched', 'source': file_record(ROOT / 'data/malecns/cells.json')}}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    resolved = resolve()
    if args.verify:
        require(read_json(OUT) == resolved, 'cells_male_v1.json differs from workbook resolution')
        print('male-v1 cells verified: 108 disjoint units; all stimulus/readout IDs in M1i roster')
    else:
        with OUT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(resolved, stream, indent=2, ensure_ascii=False, allow_nan=False)
            stream.write('\n')
        print(f'Created {OUT.relative_to(ROOT).as_posix()}')
    print('M1j sugar cross-check: ' + resolved['cross_checks']['sugar_m1j']['status'])


if __name__ == '__main__':
    main()
