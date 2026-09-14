"""Checks of the saved research-only counts; no downloads or simulations."""
import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]


class ConfidenceCountsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.record = json.loads((ROOT / 'data/malecns/confidence_counts.json').read_text())

    def test_count_source_hash(self):
        source = self.record['code']
        data = (ROOT / source['path']).read_bytes()
        # Git may normalize text line endings on checkout.
        variants = [data, data.replace(b'\r\n', b'\n'), data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')]
        self.assertTrue(any(hashlib.sha256(v).hexdigest() == source['sha256'] for v in variants))

    def test_original_graph_counts_recovered_at_baseline(self):
        row = self.record['rows'][0]
        self.assertEqual(row['cutoff'], .5)
        for name, edges, synapses, neurons in [('whole', 25582938, 124177617, 166700), ('brain', 21884935, 101220515, 146221)]:
            self.assertEqual(row[name]['edges_upper'], edges)
            self.assertEqual(row[name]['synapses_upper'], synapses)
            self.assertEqual(row[name]['neurons'], neurons)
        self.assertTrue(self.record['baseline_full_graph_equality'].startswith('FAIL'))
        self.assertEqual(self.record['retained_edge_weights_match_original'], 'PASS')

    def test_bounds_and_density_arithmetic(self):
        female_mean = 54492922 / 138639
        for row in self.record['rows']:
            for name in ['whole', 'brain']:
                d = row[name]
                for unit in ['edges', 'synapses']:
                    self.assertEqual(d[unit + '_upper'] - d[unit + '_lower'], self.record['omissions'][name][unit])
                for bound in ['lower', 'upper']:
                    self.assertAlmostEqual(d['density_ratio_' + bound], d['synapses_' + bound] / d['neurons'] / female_mean, places=12)
                    self.assertLessEqual(d['edges_' + bound], d['synapses_' + bound])

    def test_retention_monotonic_and_brain_subset(self):
        rows = self.record['rows']
        self.assertEqual([r['cutoff'] for r in rows], [.5, .6, .7, .8, .9])
        for row in rows:
            for unit in ['edges', 'synapses']:
                for bound in ['lower', 'upper']:
                    self.assertLessEqual(row['brain'][unit + '_' + bound], row['whole'][unit + '_' + bound])
        for a, b in zip(rows, rows[1:]):
            for name in ['whole', 'brain']:
                for unit in ['edges', 'synapses']:
                    for bound in ['lower', 'upper']:
                        self.assertLessEqual(b[name][unit + '_' + bound], a[name][unit + '_' + bound])


if __name__ == '__main__':
    unittest.main()
