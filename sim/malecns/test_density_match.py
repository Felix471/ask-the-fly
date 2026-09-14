import unittest
import numpy as np
from sim.malecns.density_match_substrate import choose_cutoff, loss_row


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


if __name__ == '__main__':
    unittest.main()
