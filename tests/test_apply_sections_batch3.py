# SPDX-License-Identifier: MIT
"""The approved taxonomy rebuild survives partial and full dictionary merges."""
import copy
import json
from pathlib import Path
import unittest

from scripts.apply_sections_batch3 import APPROVED_SECTIONS, build_sections

ROOT = Path(__file__).resolve().parents[1]


class Batch3Sections(unittest.TestCase):
    def setUp(self):
        self.dishes = [{'key': key} for section in APPROVED_SECTIONS for key in section['keys']]
        self.batch = json.loads((ROOT / 'encoder/foods_batch3.json').read_text(encoding='utf-8'))
        self.popular = ['pizza', 'water']

    def test_existing_reassignment(self):
        result = build_sections(self.dishes, self.batch, self.popular)
        self.assertEqual([len(s['keys']) for s in result['sections']],
                         [38, 11, 5, 3, 1, 2, 12, 14, 26, 27, 6, 3, 26, 0])
        self.assertEqual(result['popular'], self.popular)
        self.assertEqual(sum(len(s['keys']) for s in result['sections']), 174)

    def test_partial_full_merge_and_idempotence(self):
        for batch in (self.batch[:1], self.batch):
            with self.subTest(count=len(batch)):
                result = build_sections(self.dishes + batch, self.batch, self.popular)
                membership = {key: s for s in result['sections'] for key in s['keys']}
                self.assertEqual(len(membership), 174 + len(batch))
                for item in batch:
                    self.assertEqual(membership[item['key']]['zh'], item['section_zh'])
                    self.assertEqual(membership[item['key']]['en'], item['section_en'])
                self.assertEqual(result, build_sections(self.dishes + batch, self.batch, result['popular']))
        self.assertEqual(len(result['sections'][-1]['keys']), 23)

    def test_unknown_duplicate_missing_or_mismatched_keys_fail(self):
        for dishes in (self.dishes + [{'key': 'unknown'}], self.dishes[:-1], self.dishes + self.dishes[:1]):
            with self.assertRaises(ValueError):
                build_sections(dishes, self.batch, self.popular)
        batch = copy.deepcopy(self.batch)
        batch[0]['section_en'] = 'wrong'
        with self.assertRaises(ValueError):
            build_sections(self.dishes, batch, self.popular)
        with self.assertRaises(ValueError):
            build_sections(self.dishes, self.batch + self.batch[:1], self.popular)


if __name__ == '__main__':
    unittest.main()
