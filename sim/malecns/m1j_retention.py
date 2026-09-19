# SPDX-License-Identifier: MIT
"""M1j outgoing synapses; recorded, not a stop condition."""
import argparse
import json
from pathlib import Path
import sys
if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import pandas as pd
from sim.malecns.substrate import DATA, ROOT, file_record, write_json
from sim.malecns.fbm_substrate import check_file, verify as verify_substrate
from sim.malecns.output_retention import entry

RECORD = DATA / 'm1j_retention.json'
SETS = ('sugar_bilateral', 'sugar_lb3c_bilateral')


def verify():
    record = json.loads(RECORD.read_text(encoding='utf-8'))
    for item in record['sources'] + [record['builder']]:
        check_file(item)
    return record


def build():
    from sim.malecns.m1j_adapter import load_configuration
    if RECORD.exists():
        raise FileExistsError(RECORD)
    verify_substrate()
    mp, male, _ = load_configuration('male')
    fp, female, _ = load_configuration('female')
    old_path = DATA / 'derived/connectivity.parquet'
    new_path = ROOT / mp['connectivity_file']
    female_path = ROOT / fp['connectivity_file']
    source_paths = [old_path, new_path, female_path, ROOT / fp['completeness_file'],
                    DATA / 'derived/neuron_index.csv', DATA / 'substrate_record_fbm.json',
                    ROOT / mp['cells_file'], ROOT / fp['cells_file'],
                    DATA / 'stim_protocol_malecns_m1j.json', ROOT / 'data/stim_protocol_m1j_female.json',
                    ROOT / 'sim/malecns/output_retention.py']
    sources = [file_record(p) for p in source_paths]
    def outgoing(path):
        return pd.read_parquet(path, columns=['Presynaptic_Index', 'Connectivity']).groupby('Presynaptic_Index').Connectivity.sum()
    old, new, frozen = outgoing(old_path), outgoing(new_path), outgoing(female_path)
    idx = pd.read_csv(DATA / 'derived/neuron_index.csv').set_index('bodyId')['index']
    female_ids = pd.read_csv(ROOT / fp['completeness_file'], index_col=0).index
    female_idx = {int(body): i for i, body in enumerate(female_ids)}
    rows, totals, frows, ftotals = [], [], [], []
    for name in SETS:
        group = [entry(body, name, old.get(idx.loc[body], 0), new.get(idx.loc[body], 0))
                 for body in male['sets'][name]['ids']]
        rows.extend(group)
        total = entry(0, name, sum(r['outgoing_0_5'] for r in group), sum(r['outgoing_c_star'] for r in group))
        total.pop('bodyId')
        total['cells'] = len(group)
        totals.append(total)
        fg = [{'bodyId': body, 'label': name, 'outgoing_synapses': int(frozen.get(female_idx[body], 0)),
               'retention_fraction': None} for body in female['sets'][name]['ids']]
        frows.extend(fg)
        ftotals.append({'label': name, 'cells': len(fg), 'outgoing_synapses': sum(r['outgoing_synapses'] for r in fg),
                        'retention_fraction': None})
    for body, label in ((10331, 'MN9_L_primary'), (16949, 'MN9_R_secondary')):
        rows.append(entry(body, label, old.get(idx.loc[body], 0), new.get(idx.loc[body], 0)))
    result = {'scope': 'M1j bilateral labellar sugar and its overlapping LB3c subset; subsets are not added to union totals.',
              'field_meanings': 'Legacy *_0_5 is baseline >=1; *_c_star is >=5 without autapses.',
              'interpretation': 'recorded, not a stop condition; no flag stops anything.',
              'cells': rows, 'set_totals': totals, 'stop_triggered': False,
              'female': {'cells': frows, 'set_totals': ftotals, 'retention_fraction': None,
                         'note': 'Frozen v783 graph has no cut; outgoing synapse totals only, no retention fraction.'},
              'sources': sources, 'builder': file_record(Path(__file__))}
    for source in sources:
        check_file(source)
    write_json(RECORD, result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    r = verify() if args.verify else build()
    print(json.dumps({'male': r['set_totals'], 'female': r['female']['set_totals'],
                      'interpretation': r['interpretation']}, indent=2))
