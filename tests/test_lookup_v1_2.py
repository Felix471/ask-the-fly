"""Data-only v1.2 safeguards; no Brian2 import or simulation."""
import unittest
from unittest.mock import patch
import numpy as np
from sim.lookup_v1_2 import design, groups_for, state_for, verify_mn9
from sim.run_mn_readouts import published_grid_seed


class LookupV12Tests(unittest.TestCase):
    def test_states_at_threshold(self):
        for a, b, expected in [(5, 5, 'eats'), (4.999, 5, 'mouth_moves'),
                               (5, 4.999, 'proboscis_only'), (0, 0, 'no_response')]:
            self.assertEqual(state_for(a, b), expected)

    def test_invalid_rates(self):
        for value in [-1, float('inf'), float('nan')]:
            with self.assertRaises(ValueError):
                state_for(value, 5)

    def test_frozen_design(self):
        spec, protocol = design()
        self.assertEqual(spec['state_rule']['mn9']['id'], '720575940660219265')
        self.assertEqual([len(v) for v in groups_for(spec, protocol).values()], [1, 1, 2, 2])
        self.assertEqual(spec['trials_per_cell'] * spec['grid_cells'], 12000)

    def test_published_batch_seeds(self):
        self.assertEqual(published_grid_seed(40, 0), 20260910)
        self.assertEqual(published_grid_seed(399, 29), 20299939)

    def test_mn9_mismatch_stops(self):
        condition = {'global_index': 0, 'rates': {}}
        old = {'hz': {}, **{k: 0 for k in ['mn9_mean', 'mn9_std', 'mn9_left_mean',
                                          'mn9_left_std', 'mn9_right_mean', 'mn9_right_std']}}
        grouped = [{'readout': g, 'rate_hz': 0} for g in ['MN9_L', 'MN9_R'] for _ in range(30)]
        with patch('sim.lookup_v1_2.load_json', return_value={'cells': [old]}):
            verify_mn9(grouped, condition)
            grouped[0]['rate_hz'] = 1
            with self.assertRaisesRegex(ValueError, 'STOP'):
                verify_mn9(grouped, condition)


if __name__ == '__main__':
    unittest.main()
