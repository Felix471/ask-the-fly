import unittest
from copy import deepcopy
from sim.malecns import density_matched_phase0 as runner, brain_phase0, phase0


class DensityMatchedRunTests(unittest.TestCase):
    def test_one_candidate_480_trials(self):
        self.assertEqual(runner.CANDIDATES, ('density_matched',))
        self.assertEqual(sum(c['n_trials'] for c in phase0.conditions()), 480)
        with self.assertRaises(ValueError):
            runner.protocol_path('another')

    def test_unchanged_dynamics_against_m1f_unscaled(self):
        base = brain_phase0.expected_protocol('unscaled')
        p = runner.expected_protocol('density_matched')
        self.assertEqual(p['model']['w_syn_mV'], .275)
        self.assertEqual(p['density_matched_provenance']['external_kick_mV'], 68.75)
        p.pop('density_matched_provenance')
        base.pop('brain_provenance')
        for key in ['protocol_version', 'data_version', 'connectivity_file', 'completeness_file']:
            p[key] = base[key]
        self.assertEqual(p, base)

    def test_tampering_is_rejected(self):
        p = deepcopy(runner.expected_protocol('density_matched'))
        p['model']['w_syn_mV'] = .274
        with self.assertRaises(ValueError):
            runner.validate('density_matched', p)


if __name__ == '__main__':
    unittest.main()
