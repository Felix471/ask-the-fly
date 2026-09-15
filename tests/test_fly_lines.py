"""Review copy contract: exhaustive frozen-cell coverage and ordered selection."""
import json
from itertools import product
import unittest

from scripts.check_fly_lines import ROOT, LEVELS, canonical_levels, matches, resolve, line_for


class FlyLinesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / 'copy/fly_lines.json').read_text(encoding='utf-8'))
        cls.cells = json.loads((ROOT / 'data/lookup_table_v1_2.json').read_text())['cells']

    def test_schema_and_three_distinct_short_lines(self):
        self.assertEqual([b['id'] for b in self.data['buckets']], list(range(1, 15)) + ['tie', 'eats_first'])
        for bucket in self.data['buckets']:
            self.assertTrue(bucket['context'])
            for axis, allowed in bucket['when'].items():
                self.assertIn(axis, LEVELS)
                self.assertTrue(allowed)
                self.assertLessEqual(set(allowed), set(LEVELS[axis]))
            for lang in ('zh', 'en'):
                self.assertEqual(len(bucket[lang]), 3)
                self.assertEqual(len(set(bucket[lang])), 3)
            for line in bucket['zh']:
                self.assertLessEqual(len(line), 14)
                for banned in ('Hz', '神经元', '放电', 'MN9', 'MN11'):
                    self.assertNotIn(banned, line)

    def test_400_cells_exactly_one_effective_bucket(self):
        self.assertEqual(len(self.cells), 400)
        for cell in self.cells:
            buckets = [b for b in self.data['buckets'] if b['state'] == cell['state']]
            raw = [matches(b, canonical_levels(cell)) for b in buckets]
            # Predicates intentionally overlap; effective rules exclude all earlier matches.
            effective = [hit and not any(raw[:i]) for i, hit in enumerate(raw)]
            self.assertEqual(sum(effective), 1, cell)
            self.assertEqual(resolve(self.data, cell['state'], cell), buckets[effective.index(True)])

    def test_exhaustive_level_aliases_and_state_fallbacks(self):
        for values in product(*(LEVELS[a] for a in LEVELS)):
            levels = dict(zip(LEVELS, values))
            for state in ('eats', 'mouth_moves', 'proboscis_only', 'no_response'):
                self.assertEqual(resolve(self.data, state, levels)['state'], state)
                self.assertEqual(resolve(self.data, state, levels), resolve(self.data, state, canonical_levels(levels)))

    def test_priorities_and_boundaries(self):
        cases = [
            ('eats', 'high', 'none', 'high', 'none', 1),
            ('eats', 'high', 'low', 'none', 'high', 2),
            ('eats', 'high', 'none', 'none', 'low', 3),
            ('eats', 'low', 'none', 'high', 'none', 4),
            ('eats', 'none', 'none', 'high', 'none', 5),
            ('eats', 'none', 'none', 'none', 'none', 6),
            ('mouth_moves', 'none', 'medium', 'none', 'high', 7),
            ('mouth_moves', 'none', 'low', 'none', 'medium', 8),
            ('mouth_moves', 'none', 'low', 'none', 'low', 9),
            ('no_response', 'none', 'high', 'none', 'high', 11),
            ('no_response', 'none', 'medium', 'none', 'medium', 12),
            ('no_response', 'none', 'low', 'medium', 'low', 13),
            ('no_response', 'none', 'medium', 'none', 'low', 14),
        ]
        for state, s, b, w, i, expected in cases:
            self.assertEqual(resolve(self.data, state, dict(zip(LEVELS, [s, b, w, i])))['id'], expected)

    def test_seed_modulo_and_language_pairing(self):
        for bucket in self.data['buckets']:
            levels = {axis: bucket['when'].get(axis, ['none'])[0] for axis in LEVELS}
            selected = resolve(self.data, bucket['state'], levels)
            for seed in (0, 1, 2, 3, 4, 5, 123456, 2**53 - 1):
                for lang in ('zh', 'en'):
                    self.assertEqual(line_for(self.data, bucket['state'], levels, seed, lang), selected[lang][seed % 3])

    def test_invalid_inputs_rejected(self):
        levels = dict.fromkeys(LEVELS, 'none')
        for seed in (-1, True, 1.5, '3', 2**53):
            with self.assertRaises(ValueError):
                line_for(self.data, 'eats', levels, seed, 'zh')
        with self.assertRaises(ValueError):
            resolve(self.data, 'unknown', levels)
        with self.assertRaises(ValueError):
            resolve(self.data, 'eats', dict(levels, sugar='invalid'))


if __name__ == '__main__':
    unittest.main()
