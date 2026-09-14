"""M1h outgoing/last-hop audit. No simulation or substrate mutation."""
import json
import numpy as np
import pandas as pd
from sim.malecns.substrate import DATA, file_record, write_json


def entry(body, label, old, new):
    return {'bodyId': int(body), 'label': label, 'outgoing_0_5': int(old),
            'outgoing_c_star': int(new), 'retained_fraction': float(new / old) if old else None,
            'below_half': bool(2 * new < old)}


def main():
    roster = pd.read_csv(DATA / 'derived/brain/neuron_index.csv')
    old_path = DATA / 'derived/brain/connectivity.parquet'
    new_path = DATA / 'derived/density_matched/connectivity.parquet'
    old, new = pd.read_parquet(old_path), pd.read_parquet(new_path)
    out_old = old.groupby('Presynaptic_Index').Connectivity.sum()
    out_new = new.groupby('Presynaptic_Index').Connectivity.sum()
    idx = roster.set_index('bodyId')['index']
    cells = json.loads((DATA / 'cells.json').read_text())['sets']
    rows, totals = [], []
    for name in ['sugar', 'bitter', 'water', 'ir94e']:
        start = len(rows)
        for body in cells[name]['ids']:
            i = idx.loc[body]
            rows.append(entry(body, name, out_old.get(i, 0), out_new.get(i, 0)))
        group = rows[start:]
        total = entry(0, name, sum(x['outgoing_0_5'] for x in group), sum(x['outgoing_c_star'] for x in group))
        total.pop('bodyId')
        total['cells'] = len(group)
        totals.append(total)
    assert len(rows) == 91 and len({x['bodyId'] for x in rows}) == 91
    for body, name in [(10331, 'MN9 L primary'), (16949, 'MN9 R secondary')]:
        i = idx.loc[body]
        rows.append(entry(body, name, out_old.get(i, 0), out_new.get(i, 0)))
    # Fix partners by strongest baseline direct input to L10331; never rerank after pruning.
    target = idx.loc[10331]
    last_old = old.loc[old.Postsynaptic_Index.eq(target)].copy()
    last_old['bodyId'] = roster.bodyId.to_numpy()[last_old.Presynaptic_Index]
    last_old = last_old.sort_values(['Connectivity', 'bodyId'], ascending=[False, True]).head(20)
    last_new = new.loc[new.Postsynaptic_Index.eq(target)].set_index('Presynaptic_Index').Connectivity
    partners = []
    for rank, x in enumerate(last_old.itertuples(), 1):
        i = x.Presynaptic_Index
        p = entry(x.bodyId, 'L10331 baseline top20 presynaptic partner', out_old.get(i, 0), out_new.get(i, 0))
        p.update(rank=rank, into_L10331_0_5=int(x.Connectivity), into_L10331_c_star=int(last_new.get(i, 0)),
                 last_hop_retained_fraction=float(last_new.get(i, 0) / x.Connectivity))
        partners.append(p)
    result = {'scope': 'Read-only M1h outgoing audit before simulation; same brain endpoint roster.',
              'partner_selection': 'Top20 by baseline0.5 synapses directly into L10331, tie by ascending bodyId; fixed membership.',
              'set_totals': totals, 'cells': rows, 'partners': partners,
              'stop_triggered': any(x['below_half'] for x in totals),
              'cost': 'At c*=0.869 the graph keeps56.8% of brain contacts. Recall at this cutoff is unknown (0.81 at0.5 per Berg S8E). This is a heavily pruned graph, density-matched by construction.',
              'sources': [file_record(old_path), file_record(new_path), file_record(DATA / 'cells.json'),
                          file_record(DATA / 'derived/brain/neuron_index.csv')],
              'builder': file_record(__file__)}
    write_json(DATA / 'm1h_output_retention.json', result)
    print(json.dumps({'set_totals': totals, 'MN9': rows[-2:], 'top20_last_hop': [sum(x[k] for x in partners) for k in ['into_L10331_0_5', 'into_L10331_c_star']], 'stop_triggered': result['stop_triggered']}, indent=2))


def report():
    r = json.loads((DATA / 'm1h_output_retention.json').read_text())
    lines = ['## M1h outgoing-retention checkpoint — 2026-09-14', '',
             '**STOP: all four input sets retain less than half their outgoing synapses. The owner’s conditional run criterion fails. No M1h trials are run; no A–D/S result is assigned.**', '',
             'At `c* = 0.869` the graph keeps **56.8% of brain contacts**; recall at that cutoff is unknown (**0.81 at0.5 per Berg S8E**). This is a **heavily pruned graph, density-matched by construction**. The previous incoming-loss flags are not the run criterion for these Poisson-driven inputs; the owner instead requires each input set to retain at least half its outputs.', '',
             '[Hashed outgoing audit and all values](../data/malecns/m1h_output_retention.json). Counts are unsigned synapse totals within the same M1f brain endpoint cut, not unique partners or signed net drive. Set retention is a ratio of totals, not the average of per-cell fractions.', '',
             '| Set | Cells | Outgoing at0.5 | Outgoing at `c*` | Retained | Below half |', '|---|---:|---:|---:|---:|---|']
    for x in r['set_totals']:
        lines.append(f"| {x['label']} | {x['cells']} | {x['outgoing_0_5']:,} | {x['outgoing_c_star']:,} | {x['retained_fraction']:.2%} | {'FLAG' if x['below_half'] else 'No'} |")
    lines += ['', '### Both MN9s and all91 input cells', '', '| Cell / set | Body ID | Outgoing at0.5 | Outgoing at `c*` | Retained |', '|---|---:|---:|---:|---:|']
    for x in r['cells'][-2:] + r['cells'][:-2]:
        fraction = f"{x['retained_fraction']:.2%}" if x['retained_fraction'] is not None else 'n.a. (baseline zero)'
        lines.append(f"| {x['label']} | {x['bodyId']} | {x['outgoing_0_5']:,} | {x['outgoing_c_star']:,} | {fraction} |")
    lines += ['', '### L10331 top20 direct presynaptic partners', '',
              'Rank fixed using the0.5 graph: strongest direct synapse count into L10331, ties by ascending body ID. Total outgoing retention alone does not establish last-hop retention, so both are shown; zero surviving direct contacts would be explicit. These rows do not select or adjust `c*`.', '',
              '| Rank | Partner body | All outputs0.5 | All outputs `c*` | Retained | Into L10331 at0.5 | Into L10331 at `c*` | Last-hop retained |', '|---:|---:|---:|---:|---:|---:|---:|---:|']
    for x in r['partners']:
        lines.append(f"| {x['rank']} | {x['bodyId']} | {x['outgoing_0_5']:,} | {x['outgoing_c_star']:,} | {x['retained_fraction']:.2%} | {x['into_L10331_0_5']:,} | {x['into_L10331_c_star']:,} | {x['last_hop_retained_fraction']:.2%} |")
    old = sum(x['into_L10331_0_5'] for x in r['partners'])
    new = sum(x['into_L10331_c_star'] for x in r['partners'])
    lines += ['', f"These fixed20 partners retain {new:,}/{old:,} direct synapses into L10331 ({new/old:.2%}). This does not override the input-set stop condition. The experiment remains stopped before simulation, awaiting the owner’s decision.", '']
    return '\n'.join(lines)


if __name__ == '__main__':
    import sys
    if '--report' in sys.argv:
        print(report())
    else:
        main()
