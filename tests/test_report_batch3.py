# SPDX-License-Identifier: MIT
"""Tie handling and exact regeneration of the batch report."""
import unittest
from scripts.report_batch3 import BEGIN, END, ROOT, ranked_groups, render, update


class BatchReportTests(unittest.TestCase):
    def test_boundary_ties_include_every_entry_and_keep_states_separate(self):
        rows = [dict(key=str(i), display={'en': str(i), 'zh': str(i)}, score=score,
                     state='eats' if i != 2 else 'proboscis_only')
                for i, score in enumerate([9, 8, 8, 8, 0])]
        groups = ranked_groups(rows, limit=2)
        self.assertEqual([r[:3] for r in groups], [
            ['1', '9.000000', 'eats'], ['2–4', '8.000000', 'eats'],
            ['2–4', '8.000000', 'proboscis_only']])
        self.assertEqual(groups[1][3], '1 / 1; 3 / 3')
        self.assertEqual(ranked_groups(rows, bottom=True, limit=1)[0][:2], ['1', '0.000000'])

    def test_marked_block_replaces_only_generated_content_and_rejects_bad_markers(self):
        text = f'prefix\n{BEGIN}\nold\n{END}\nsuffix'
        new = f'{BEGIN}\nnew\n{END}'
        self.assertEqual(update(text, new), f'prefix\n{new}\nsuffix')
        for invalid in ('', text + END, END + BEGIN):
            with self.assertRaises(ValueError):
                update(invalid, new)

    def test_checked_in_report_matches_current_sources(self):
        text = (ROOT / 'docs/dictionary_batch3.md').read_text(encoding='utf-8')
        self.assertEqual(update(text, render()), text)
