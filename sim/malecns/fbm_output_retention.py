# SPDX-License-Identifier: MIT
"""M1i outgoing retention: recorded, not a stop condition."""
import argparse
import json
from pathlib import Path
import sys
if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import pandas as pd
from sim.malecns.substrate import DATA, ROOT, file_record, write_json
from sim.malecns.fbm_substrate import verify as verify_substrate, check_file
from sim.malecns.output_retention import entry

RECORD = DATA / 'm1i_output_retention.json'


def verify():
    r = json.loads(RECORD.read_text(encoding='utf-8'))
    for item in r['sources'] + [r['builder']]:
        check_file(item)
    return r


def build():
    if RECORD.exists():
        raise FileExistsError(RECORD)
    verify_substrate()
    roster = pd.read_csv(DATA / 'derived/neuron_index.csv', low_memory=False)
    old_path, new_path = DATA / 'derived/connectivity.parquet', DATA / 'derived/fbm/connectivity.parquet'
    old, new = pd.read_parquet(old_path), pd.read_parquet(new_path)
    out_old = old.groupby('Presynaptic_Index').Connectivity.sum()
    out_new = new.groupby('Presynaptic_Index').Connectivity.sum()
    idx = roster.set_index('bodyId')['index']

    def table(filename, channels, count):
        sets = json.loads((DATA / filename).read_text(encoding='utf-8'))['sets']
        rows, totals = [], []
        for name in channels:
            group = [entry(body, name, out_old.get(idx.loc[body], 0), out_new.get(idx.loc[body], 0))
                     for body in sets[name]['ids']]
            rows.extend(group)
            total = entry(0, name, sum(x['outgoing_0_5'] for x in group), sum(x['outgoing_c_star'] for x in group))
            total.pop('bodyId')
            total['cells'] = len(group)
            totals.append(total)
        if len(rows) != count or len({x['bodyId'] for x in rows}) != count:
            raise ValueError('Retention layout mismatch')
        return rows, totals

    rows, totals = table('cells.json', ['sugar', 'bitter', 'water', 'ir94e'], 91)
    fbm_rows, fbm_totals = table('cells_fbm.json', ['fbm_sugar_labellar', 'fbm_sugar_pharyngeal', 'fbm_sugar_tarsal', 'bitter'], 242)
    for body, label in [(10331, 'MN9_L_primary'), (16949, 'MN9_R_secondary')]:
        rows.append(entry(body, label, out_old.get(idx.loc[body], 0), out_new.get(idx.loc[body], 0)))
    last_old = old.loc[old.Postsynaptic_Index.eq(idx.loc[10331])].copy()
    last_old['bodyId'] = roster.bodyId.to_numpy()[last_old.Presynaptic_Index]
    last_old = last_old.sort_values(['Connectivity', 'bodyId'], ascending=[False, True]).head(20)
    last_new = new.loc[new.Postsynaptic_Index.eq(idx.loc[10331])].set_index('Presynaptic_Index').Connectivity
    partners = []
    for rank, row in enumerate(last_old.itertuples(), 1):
        i = row.Presynaptic_Index
        item = entry(row.bodyId, 'L10331 baseline top20 presynaptic partner', out_old.get(i, 0), out_new.get(i, 0))
        item.update(rank=rank, into_L10331_0_5=int(row.Connectivity), into_L10331_c_star=int(last_new.get(i, 0)),
                    last_hop_retained_fraction=float(last_new.get(i, 0) / row.Connectivity))
        partners.append(item)
    result = {'scope': 'M1i whole-CNS >=1 to >=5 outgoing retention; autapses removed in retained graph.',
              'field_meanings': 'Legacy *_0_5 fields mean baseline >=1; *_c_star fields mean >=5 without autapses. No confidence cutoff changed.',
              'interpretation': 'recorded, not a stop condition; no flag stops anything.',
              'partner_selection': 'Top20 by baseline >=1 synapses directly into L10331, ties by ascending bodyId; fixed membership.',
              'cells': rows, 'set_totals': totals, 'partners': partners,
              'fbm_cells': fbm_rows, 'fbm_set_totals': fbm_totals, 'stop_triggered': False,
              'sources': [file_record(p) for p in [old_path, new_path, DATA / 'cells.json', DATA / 'cells_fbm.json',
                          DATA / 'derived/neuron_index.csv', DATA / 'substrate_record_fbm.json']],
              'builder': file_record(Path(__file__))}
    write_json(RECORD, result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    result = verify() if args.verify else build()
    print(json.dumps({k: result[k] for k in ('set_totals', 'fbm_set_totals', 'interpretation', 'stop_triggered')}, indent=2))
