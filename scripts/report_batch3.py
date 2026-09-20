#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Regenerate or exactly check the batch-3 dictionary tables; no encoder/simulation calls."""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from sim.lookup import DIMENSIONS, LookupTable

BEGIN = '<!-- batch3-tables:begin -->'
END = '<!-- batch3-tables:end -->'
STATES = ('eats', 'mouth_moves', 'proboscis_only', 'no_response')


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def table(headers, rows):
    def escape(value):
        return str(value).replace('|', '\\|').replace('\n', ' ')
    return '\n'.join('| ' + ' | '.join(map(escape, row)) + ' |'
                     for row in [headers, ['---'] * len(headers), *rows])


def name(dish):
    return f"{dish['display']['zh']} / {dish['display']['en']}"


def ranked_groups(rows, *, bottom=False, limit=None):
    """Competition ranks by exact stored score; include every boundary tie.

    Rows sharing a score but having different states get separate table rows
    with the same rank range. Names are sorted by key, never used to break ties.
    """
    ordered = sorted(rows, key=lambda r: (r['score'] if bottom else -r['score'], r['key']))
    result, offset = [], 0
    for score in sorted({r['score'] for r in ordered}, reverse=not bottom):
        if limit is not None and offset >= limit:
            break
        tied = [r for r in ordered if r['score'] == score]
        rank = str(offset + 1) if len(tied) == 1 else f'{offset + 1}–{offset + len(tied)}'
        for state in STATES:
            group = [r for r in tied if r['state'] == state]
            if group:
                result.append([rank, f'{score:.6f}', state, '; '.join(name(r) for r in group)])
        offset += len(tied)
    return result


def render(root=ROOT):
    dishes = load(root / 'data/dishes.json')
    by_key = {d['key']: d for d in dishes}
    reference = {d[0] for d in load(root / 'site/test/fixtures/female_v1_2_1_decisions.json')['dishes']}
    batch = {d['key'] for d in load(root / 'encoder/foods_batch3.json')}
    new = set(by_key) - reference
    if len(by_key) != len(dishes) or len(dishes) != 279 or len(reference) != 174 or not reference <= set(by_key):
        raise ValueError('Expected 279 unique dishes including all 174 reference keys')
    if len(new) != 105 or new != batch - {'umeboshi'}:
        raise ValueError('Batch must contain exactly 105 new entries, with only umeboshi dropped')
    sections = load(root / 'data/dish_sections.json')['sections']
    members = [key for s in sections for key in s['keys']]
    if len(sections) != 14 or Counter(members) != Counter(by_key.keys()):
        raise ValueError('Expected 14 sections partitioning all 279 entries')
    not_food = {k for s in sections if s.get('not_food') is True for k in s['keys']}
    addendum = {d['key'] for d in dishes if d.get('encoder_addendum') == 'addendum_not_food_v1'}
    if len(not_food) != 23 or not_food != addendum or not not_food <= new:
        raise ValueError('All 23 new not-food entries must record the addendum')
    reviewed = sorted((by_key[k] for k in new if by_key[k]['review'] == 'human_checked'), key=lambda d: d['key'])
    if len(reviewed) != 12 or any(by_key[k]['review'] == 'needs_review' for k in new):
        raise ValueError('Expected 12 hand-checked entries and no unresolved review')
    lines = [BEGIN, '## Taxonomy and additions', '',
             table(['Section (zh / en)', 'Full menu', 'New entries'],
                   [[f"{s['zh']} / {s['en']}", len(s['keys']), len(set(s['keys']) & new)] for s in sections]), '',
             'Total: 279 entries, including 105 additions; 23 additions are in Not food.', '']
    for section in sections:
        additions = sorted(set(section['keys']) & new)
        lines += [f"### {section['zh']} / {section['en']} ({len(additions)} new)", '',
                  table(['Key', '中文', 'English'], [[k, by_key[k]['display']['zh'], by_key[k]['display']['en']] for k in additions])
                  if additions else 'No new entries.', '']
    lines += ['## Hand-checked entries', '',
              'All twelve are `human_checked`. Levels below are the final owner-reviewed mappings, '
              'in sugar / bitter / water / Ir94e order; the original encoder version is retained.', '',
              table(['Entry', 'Final levels', 'Decision'], [[name(d), ' / '.join(d[x] for x in DIMENSIONS),
                     'Override; see reasons above.' if d['key'] in ('ketchup', 'rotting-tomato') else 'Arbitrated levels accepted unchanged.']
                     for d in reviewed]), '', '## Scores from the frozen lookup tables', '',
              'MN9 Hz is the stored 30-trial primary-readout mean, shown to six decimal places. '
              'States are the stored designed labels, using our existing >=5 Hz MN9/MN11D rule; '
              'they are not measured feeding or an edibility judgment. Female and male are independent experiments.', '',
              'Top/bottom 10 means the first/last ten entries by exact stored MN9, including **all** '
              'ties at the cutoff. Rank ranges count entries from the indicated end; tied names are '
              'alphabetical by key, not tie-broken. Equal scores with different states have separate rows.', '']
    scores = {}
    for fly, filename in [('female', 'lookup_table_v1_2.json'), ('male', 'lookup_table_male.json')]:
        lookup = LookupTable.load(root / 'data' / filename)
        scores[fly] = []
        for dish in dishes:
            cell = lookup.get(**{d: dish[d] for d in DIMENSIONS})
            scores[fly].append({**dish, 'score': cell['mn9_mean'], 'state': cell['state']})
        for bottom in (False, True):
            lines += [f"### {fly.title()} — {'bottom' if bottom else 'top'} 10 (including ties)", '',
                      table(['Positions from ' + ('bottom' if bottom else 'top'), 'MN9 Hz', 'State', 'Entries (zh / en)'],
                            ranked_groups(scores[fly], bottom=bottom, limit=10)), '']
    lines += ['### State distribution of the 105 additions', '',
              table(['State', 'Female', 'Male'], [[state, *[sum(r['key'] in new and r['state'] == state for r in scores[fly])
                     for fly in ('female', 'male')]] for state in STATES]), '']
    for fly in ('female', 'male'):
        lines += [f'### {fly.title()} — Not food ranking (23 entries)', '',
                  table(['Positions from top', 'MN9 Hz', 'State', 'Entries (zh / en)'],
                        ranked_groups([r for r in scores[fly] if r['key'] in not_food])), '']
    return '\n'.join(lines) + END


def update(text, block):
    if text.count(BEGIN) != 1 or text.count(END) != 1:
        raise ValueError('Report must contain exactly one start/end marker pair')
    start, end = text.index(BEGIN), text.index(END)
    if end < start:
        raise ValueError('Report markers are reversed')
    return text[:start] + block + text[end + len(END):]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    path = ROOT / 'docs/dictionary_batch3.md'
    existing = path.read_text(encoding='utf-8')
    expected = update(existing, render())
    if args.check:
        if expected != existing:
            print('Batch-3 report tables are stale; run scripts/report_batch3.py')
            return 1
        print('Batch-3 report tables match: 279 entries, 105 new, 14 sections, both flies')
    else:
        path.write_text(expected, encoding='utf-8', newline='\n')
        print(f'Wrote {path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
