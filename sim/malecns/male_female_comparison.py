# SPDX-License-Identifier: MIT
"""The frozen R1-R7 dish comparison, using stored scores; no simulation."""
import argparse
from itertools import combinations
from pathlib import Path
import sys

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from sim.grid import EXPECTED_DIMENSIONS as DIMS, resolve_levels
from sim.lookup import LookupTable, _cells_sha256
from scripts.build_lookup_v1_2 import STATES
from sim.malecns import male_v1_adapter as adapter
from sim.malecns.male_v1_grid import COMPARISON_RULES, REPLAY_RULE
from sim.malecns.substrate import DATA, ROOT, file_record, write_json

FEMALE = ROOT / 'data/lookup_table_v1_2.json'
MALE = ROOT / 'data/lookup_table_male.json'
DISHES = ROOT / 'data/dishes.json'
OUTPUT = DATA / 'male_female_comparison.json'
OUTCOMES = ('first', 'second', 'tie')


def outcome(a, b):
    return 'tie' if abs(a-b) < 1e-9 else 'first' if a > b else 'second'


def r1_dish_set(table, dishes, channels=()):
    """Resolve original or counterfactual coordinates, preserving dictionary order."""
    lookup = LookupTable(table)
    cache = {}
    rows = []
    for dish in dishes:
        selected = {d: ('none' if d in channels else dish[d]) for d in DIMS}
        key = tuple(selected.values())
        if key not in cache:
            cache[key] = lookup.get(**resolve_levels(table, selected))
        rows.append(cache[key])
    return rows


def r2_scores_states(rows):
    return [r['mn9_left_mean'] for r in rows], [r['state'] for r in rows]


def r3_distributions(female_table, male_table, dishes):
    cross = {f: dict.fromkeys(STATES, 0) for f in STATES}
    result = {}
    states = []
    for fly, table in [('female', female_table), ('male', male_table)]:
        scores, ds = r2_scores_states(r1_dish_set(table, dishes))
        states.append(ds)
        result[fly] = dict(dishes={s: ds.count(s) for s in STATES},
                           cells={s: sum(c['state'] == s for c in table['cells']) for s in STATES})
        result.setdefault('below_5hz_dishes', {})[fly] = sum(s < 5.0 for s in scores)
    for f, m in zip(*states):
        cross[f][m] += 1
    result['cross_table'] = cross
    return result


def r4_pairwise(female_scores, male_scores):
    cross = {s: dict.fromkeys(OUTCOMES, 0) for s in OUTCOMES}
    for a, b in combinations(range(len(female_scores)), 2):
        cross[outcome(female_scores[a], female_scores[b])][outcome(male_scores[a], male_scores[b])] += 1
    n = sum(sum(r.values()) for r in cross.values())
    agree = sum(cross[s][s] for s in OUTCOMES)
    strict = sum(cross[a][b] for a in OUTCOMES[:2] for b in OUTCOMES[:2])
    return dict(agreement_rate=agree/n if n else None, agreeing_pairs=agree, cross_table=cross,
                strict_pairs=strict,
                strict_agreement_rate=(cross['first']['first']+cross['second']['second'])/strict if strict else None,
                both_tie_pairs=cross['tie']['tie'])


def r5_attribution_pairs(female_scores, male_scores, water_scores, ir94e_scores, both_scores):
    result = dict.fromkeys(('disagreeing_pairs', 'removed_by_water', 'removed_by_ir94e',
                           'removed_by_either', 'removed_only_by_both', 'removed_by_neither'), 0)
    for a, b in combinations(range(len(female_scores)), 2):
        f = outcome(female_scores[a], female_scores[b])
        if f == outcome(male_scores[a], male_scores[b]):
            continue
        w, i, both = [outcome(s[a], s[b]) == f for s in (water_scores, ir94e_scores, both_scores)]
        result['disagreeing_pairs'] += 1
        result['removed_by_water'] += w
        result['removed_by_ir94e'] += i
        result['removed_by_either'] += w or i
        result['removed_only_by_both'] += both and not (w or i)
        # Literal "neither" of the two single-channel interventions. This includes
        # the separately reported only-by-both subset; the categories overlap.
        result['removed_by_neither'] += not (w or i)
    return result


def r6_attribution_dishes(dishes, female_rows, male_rows, water_scores, ir94e_scores):
    fs, _ = r2_scores_states(female_rows)
    ms, _ = r2_scores_states(male_rows)
    rows = []
    for d, dish in enumerate(dishes):
        lost = []
        for scores in (ms, water_scores, ir94e_scores):
            lost.append(sum(x != d and outcome(fs[d], fs[x]) == 'first'
                            and outcome(scores[d], scores[x]) != 'first' for x in range(len(dishes))))
        rows.append(dict(key=dish['key'], en=dish['display']['en'], zh=dish['display']['zh'],
                         **{dim: dish[dim] for dim in DIMS},
                         female_score=fs[d], female_rank=1+sum(s > fs[d] for s in fs),
                         female_state=female_rows[d]['state'],
                         male_score=ms[d], male_rank=1+sum(s > ms[d] for s in ms),
                         male_state=male_rows[d]['state'],
                         lower=lost[0], lower_water=lost[1], lower_ir94e=lost[2]))
    result = dict(dishes_lower=sum(r['lower'] > 0 for r in rows))
    for channel in ('water', 'ir94e'):
        result['dishes_partly_'+channel] = sum(r['lower_'+channel] < r['lower'] for r in rows)
        result['dishes_fully_'+channel] = sum(r['lower_'+channel] == 0 < r['lower'] for r in rows)
    for key in ('lower', 'lower_water', 'lower_ir94e'):
        result['sum_'+key] = sum(r[key] for r in rows)
    return result, rows


def r7_channel_sign(female_table, male_table, dishes):
    result = {}
    for channel in ('water', 'ir94e'):
        result[channel] = {}
        selected = [d for d in dishes if d[channel] != 'none']
        for fly, table in [('female', female_table), ('male', male_table)]:
            actual, _ = r2_scores_states(r1_dish_set(table, selected))
            counter, _ = r2_scores_states(r1_dish_set(table, selected, (channel,)))
            signs = [outcome(a, b) for a, b in zip(actual, counter)]
            result[channel][fly] = dict(lower=signs.count('second'), equal=signs.count('tie'),
                                        higher=signs.count('first'), n_dishes=len(selected))
    return result


def compare(female_table, male_table, dishes):
    if len({d['key'] for d in dishes}) != len(dishes):
        raise ValueError('Duplicate dish key')
    frows = r1_dish_set(female_table, dishes)
    mrows = r1_dish_set(male_table, dishes)
    fs, _ = r2_scores_states(frows)
    ms, _ = r2_scores_states(mrows)
    ws, ins, both = [r2_scores_states(r1_dish_set(male_table, dishes, channels))[0]
                     for channels in [('water',), ('ir94e',), ('water', 'ir94e')]]
    attribution, rows = r6_attribution_dishes(dishes, frows, mrows, ws, ins)
    return dict(rules=[f'{rid} {text}' for rid, text in COMPARISON_RULES[:-1]]+[REPLAY_RULE],
                inputs=dict(female_cells_sha256=_cells_sha256(female_table['cells']),
                            male_cells_sha256=_cells_sha256(male_table['cells'])),
                n_dishes=len(dishes), n_pairs=len(dishes)*(len(dishes)-1)//2,
                n_distinct_female_cells=len({tuple(r['hz'][d] for d in DIMS) for r in frows}),
                n_distinct_male_cells=len({tuple(r['hz'][d] for d in DIMS) for r in mrows}),
                distributions=r3_distributions(female_table, male_table, dishes),
                pairwise=r4_pairwise(fs, ms), attribution_pairs=r5_attribution_pairs(fs, ms, ws, ins, both),
                attribution_dishes=attribution, channel_sign=r7_channel_sign(female_table, male_table, dishes),
                dishes=rows)


def build(female_path=FEMALE, male_path=MALE, dishes_path=DISHES, output=OUTPUT):
    if output.exists():
        raise FileExistsError(output)
    female, male = LookupTable.load(female_path).data, LookupTable.load(male_path).data
    dishes = adapter.read(dishes_path)
    if len(dishes) != 174 or len(female['cells']) != 400 or len(male['cells']) != 400:
        raise ValueError('Expected 174 dishes and two 400-cell tables')
    result = compare(female, male, dishes)
    result['inputs'].update(female=file_record(female_path), male=file_record(male_path), dishes=file_record(dishes_path))
    write_json(output, result)
    return result


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    result = build()
    print(f"Compared {result['n_dishes']} dishes / {result['n_pairs']} pairs")


if __name__ == '__main__':
    main()
