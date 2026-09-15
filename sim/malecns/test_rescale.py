# SPDX-License-Identifier: MIT
"""Pre-run safeguards; no Brian2 imports or simulations."""
from copy import deepcopy
import json
import unittest
from sim.malecns import phase0, rescale
from sim.malecns.substrate import DATA


class RescaleTests(unittest.TestCase):
    def test_exact_two_weights(self):
        self.assertEqual(rescale.CANDIDATES, ('all','mn9'))
        for name, weight in [('all',0.14510408910416958),('mn9',0.13850350171906808)]:
            p=rescale.expected_protocol(name)
            self.assertAlmostEqual(p['model']['w_syn_mV'],weight,places=14)
            self.assertEqual(p,json.loads(rescale.protocol_path(name).read_text()))

    def test_only_weight_changes(self):
        base=json.loads((DATA/'stim_protocol_malecns.json').read_text())
        for name in rescale.CANDIDATES:
            p=rescale.expected_protocol(name)
            p.pop('rescale_provenance')
            p['protocol_version']=base['protocol_version']
            p['model']['w_syn_mV']=base['model']['w_syn_mV']
            self.assertEqual(p,base)

    def test_reject_other_weights_and_protocol_changes(self):
        for key in ('w_syn_mV','f_poi','dt_ms','t_rfc_ms'):
            p=rescale.expected_protocol('all')
            p['model'][key]+=0.001
            with self.assertRaises(ValueError):
                rescale.validate_protocol('all',p)
        with self.assertRaises(ValueError):
            rescale.expected_protocol('third')

    def test_design_960_with_unchanged_seeds_and_gates(self):
        conditions=phase0.conditions()
        self.assertEqual(sum(c['n_trials'] for c in conditions)*2,960)
        self.assertEqual(sum(c['n_trials'] for c in conditions if c['gate']!='AP'),420)
        rows=deepcopy(json.loads((DATA/'phase0_results.json').read_text())['conditions'])
        g=phase0.evaluate_gates(rows)
        self.assertFalse(g['R']['overall'])
        self.assertFalse(g['L']['overall'])
        self.assertTrue(g['R']['B'])
        self.assertFalse(g['L']['B'])

    def test_subset_fixed_layout(self):
        cells=json.loads((DATA/'cells.json').read_text())
        c=next(c for c in phase0.conditions() if c['id']=='AP_sugar_lb3c_120')
        rates=phase0.source_rates(c,cells['sets'])
        self.assertEqual(len(rates),91)
        self.assertEqual(sum(r>0 for r in rates),12)
        self.assertEqual(set(rates),{0,120})

    def test_activity_and_memory(self):
        self.assertEqual(rescale.activity_stats([0,2,10]),{'median':2.,'min':0,'max':10})
        m=phase0.choose_workers(60,85,3.578,32)
        self.assertEqual(m['workers'],8)
        self.assertEqual(m['worker_budget_gib'],5.4)
        self.assertGreaterEqual(m['reserve_gib'],15)

    def test_preflight_limits_and_ids(self):
        p=json.loads((DATA/'rescale_preflight.json').read_text())
        rows={r['male_condition']:r for r in p['female_activity']}
        for key in ['A_s25_b0','C_s0_b25']:
            self.assertEqual(rows[key]['n_trials'],0)
            self.assertIsNone(rows[key]['network_spikes'])
        for key in ['all_release_mn9_ids','all_live_mn9_ids','all_workbook_mn9_ids']:
            self.assertEqual(set(p[key]),{16949,10331})


if __name__=='__main__':
    unittest.main()
