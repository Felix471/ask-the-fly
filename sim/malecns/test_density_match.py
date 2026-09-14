import unittest
import json
import numpy as np
from sim.malecns.density_match_substrate import choose_cutoff, loss_row, RECORD


class DensityMatchTests(unittest.TestCase):
    def test_target_chosen_from_counts_only(self):
        c, count, _ = choose_cutoff(np.array([.5, .6, .7, .8], dtype='float32'), 2, 2, 2)
        self.assertEqual(c, float(np.float32(.7)))
        self.assertEqual(count, 2)

    def test_tie_goes_to_lower_cutoff(self):
        c, count, _ = choose_cutoff(np.array([.5, .5, .8, .8], dtype='float32'), 1, 3, 1)
        self.assertEqual(c, .5)
        self.assertEqual(count, 4)

    def test_repeated_scores_never_partially_retained(self):
        c, count, _ = choose_cutoff(np.array([.5, .8, .8, .8], dtype='float32'), 1, 2, 1)
        self.assertEqual(c, float(np.float32(.8)))
        self.assertEqual(count, 3)

    def test_loss_strict_boundary_and_zero(self):
        self.assertFalse(loss_row(1, 'x', 10, 5)['loss_gt_half'])
        self.assertTrue(loss_row(1, 'x', 10, 4)['loss_gt_half'])
        self.assertIsNone(loss_row(1, 'x', 0, 0)['retained_fraction'])
        self.assertTrue(loss_row(1, 'x', 0, 0)['baseline_zero'])

    def test_record_histogram_and_density(self):
        r = json.loads(RECORD.read_text())
        hist = r['synapses_per_edge_histogram']
        self.assertEqual(sum(x['edges'] for x in hist), r['counts']['edges'])
        self.assertEqual(sum(x['edges'] * x['synapses_per_edge'] for x in hist), r['counts']['synapses'])
        d = r['density']
        self.assertAlmostEqual(d['ratio'], r['counts']['synapses'] / r['counts']['neurons'] / d['female_mean'], places=12)
        self.assertTrue(.98 <= d['ratio'] <= 1.02)

    def test_record_all_input_and_readout_flags(self):
        r = json.loads(RECORD.read_text())
        rows = r['input_and_readout_degrees']
        self.assertEqual(len(rows), 93)
        self.assertEqual(len({x['bodyId'] for x in rows}), 93)
        self.assertEqual(rows[-2]['bodyId'], 10331)
        self.assertEqual(rows[-1]['bodyId'], 16949)
        self.assertEqual(r['flagged_body_ids'], [x['bodyId'] for x in rows if x['loss_gt_half']])
        for x in rows:
            self.assertEqual(x, loss_row(x['bodyId'], x['label'], x['incoming_at_0_5'], x['incoming_at_c_star']))
            self.assertLessEqual(x['incoming_at_c_star'], x['incoming_at_0_5'])


if __name__ == '__main__':
    unittest.main()
