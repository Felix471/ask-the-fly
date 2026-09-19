# SPDX-License-Identifier: MIT
"""File-only checks for the male-v1 protocol; never imports a simulator."""
import copy
import itertools
import json
import unittest
from unittest.mock import patch

from sim.malecns import male_v1_cells as subject


class MaleV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cells = subject.resolve()
        cls.protocol = subject.read_json(subject.PROTOCOL)
        cls.female = subject.read_json(subject.ROOT / 'data/stim_protocol.json')
        cls.lookup = subject.read_json(subject.ROOT / 'data/lookup_table_v1_2.json')

    def test_frozen_cells_reconstruct(self):
        self.assertEqual(self.cells, subject.read_json(subject.OUT))

    def test_sets_and_roster(self):
        roster = subject.roster_ids()
        expected = {'sugar': (34, 17, 17), 'bitter': (38, 19, 19),
                    'water': (17, 9, 8), 'ir94e': (19, 11, 8)}
        for name, (n, left, right) in expected.items():
            row = self.cells['sets'][name]
            self.assertEqual(row['count'], n)
            self.assertEqual(row['sides'], {'L': left, 'R': right})
            self.assertEqual(row['ids'], sorted(set(row['ids'])))
            self.assertTrue(set(row['ids']) <= roster)
            self.assertEqual(row['ids'], [int(r['Body_ID']) for r in row['source_rows']])
        for a, b in itertools.combinations(self.cells['sets'].values(), 2):
            self.assertFalse(set(a['ids']) & set(b['ids']))
        self.assertEqual(sum(r['count'] for r in self.cells['sets'].values()), 108)

    def test_readouts(self):
        expected = {'mn9': [10331, 16949], 'mn11d': [11269, 11393, 551398],
                    'mn11v': [49829, 492462351],
                    'cem': [19823, 20518, 23511, 32852, 34597, 482595]}
        roster = subject.roster_ids()
        for name, ids in expected.items():
            row = self.cells['readouts'][name]
            self.assertEqual(row['ids'], ids)
            self.assertEqual(row['count'], len(ids))
            self.assertTrue(set(ids) <= roster)
        self.assertEqual(self.cells['readouts']['mn9']['primary'], 10331)
        self.assertEqual(self.cells['readouts']['mn9']['secondary'], 16949)

    def test_rejects_workbook_hash_change(self):
        with patch.object(subject, 'WORKBOOK_HASH', 'wrong'):
            with self.assertRaisesRegex(ValueError, 'workbook hash'):
                subject.resolve()

    def test_rejects_missing_roster_id(self):
        with patch.object(subject, 'roster_ids', return_value=set()):
            with self.assertRaisesRegex(ValueError, 'roster'):
                subject.resolve()

    def test_model_trial_and_substrate(self):
        male = copy.deepcopy(self.protocol['model'])
        self.assertEqual(male.pop('w_syn_expression'), '0.65 * 0.275')
        self.assertEqual(male['w_syn_mV'], 0.65 * 0.275)
        male['w_syn_mV'] = self.female['model']['w_syn_mV']
        self.assertEqual(male, self.female['model'])
        self.assertEqual(self.protocol['trial'], self.female['trial'])
        record = self.protocol['substrate_record']
        source = subject.read_json(subject.ROOT / record['path'])
        self.assertEqual(record['counts'], source['counts'])
        self.assertEqual(record['sha256'], subject.file_record(subject.ROOT / record['path'])['sha256'])

    def test_layout_grid_and_seeds(self):
        p = self.protocol
        self.assertEqual(p['stimulus']['type'], self.female['stimulus']['type'])
        self.assertEqual(p['stimulus']['layout']['physical_units'], 108)
        self.assertEqual(p['stimulus']['layout']['channel_order'], ['sugar', 'bitter', 'water', 'ir94e'])
        for name, row in p['stimulus']['channels'].items():
            self.assertEqual(row, {'cell_set': name, 'count': self.cells['sets'][name]['count'], 'sides': 'both'})
        grid = p['grid']
        self.assertEqual(grid['grid_levels_record'], subject.file_record(subject.ROOT / 'data/grid_levels.json'))
        self.assertEqual(grid['grid_levels_record']['sha256'], self.lookup['grid_levels_sha256'])
        self.assertEqual(grid['levels'], self.lookup['levels'])
        self.assertEqual(grid['n_unique_cells'], 400)
        self.assertEqual(grid['seed_rule'], "20260910 + 1000 * (cell_index % 40) + trial, trial 0..29, cell_index in the female grid's cell order")

    def test_state_rule_and_readout(self):
        rule = copy.deepcopy(self.lookup['state_rule'])
        rule['mn9'].update(id='10331', side='XLSX L (primary)')
        rule['mn11']['statistic'] = '30-trial mean of per-trial mean over the male MN11D cells (count 3 from the cells file)'
        rule['meaning'] = 'Owner-designed threshold categories of model outputs; product wording and site integration are Phase 3 decisions.'
        self.assertEqual(self.protocol['state_rule'], rule)
        self.assertEqual(rule['threshold_hz'], 5.0)
        readout = self.protocol['readout']
        self.assertEqual((readout['primary'], readout['secondary'], readout['aggregation']), (10331, 16949, 'primary_only'))
        self.assertEqual(readout['rate_definition'], self.female['readout']['rate_definition'])
        for name in ['mn11d', 'mn11v', 'cem']:
            self.assertEqual(readout['extra_readouts'][name], self.cells['readouts'][name]['ids'])

    def test_phase1_unique_conditions(self):
        plan = self.protocol['phase1_characterization']
        conditions = {(s, 0, w, 0) for s in [0, 60, 80, 120, 200] for w in [0, 60, 180, 240]}
        conditions |= {(s, 0, 0, i) for s in [0, 60, 80, 120, 200] for i in [0, 60, 120, 200]}
        actual = [tuple(c[k] for k in ['sugar_hz', 'bitter_hz', 'water_hz', 'ir94e_hz']) for c in plan['conditions']]
        self.assertEqual(set(actual), conditions)
        self.assertEqual(len(actual), len(conditions))
        self.assertEqual(plan['n_unique_conditions'], 35)
        self.assertEqual(plan['n_trials_per_condition'], 30)
        self.assertEqual(plan['total_trials'], 1050)
        self.assertEqual(plan['seed_rule'], '20260910 + trial, trial 0..29, shared across conditions (M1 seeds)')
        self.assertTrue(plan['record_whole_network_counts'])

    def test_commitments_and_provenance(self):
        self.assertEqual(self.protocol['product_commitments'], subject.PRODUCT_COMMITMENTS)
        doc = (subject.ROOT / 'docs/male_fly_v2.md').read_text(encoding='utf-8')
        for commitment in subject.PRODUCT_COMMITMENTS:
            self.assertIn(commitment, doc)
        provenance = self.protocol['provenance']
        self.assertEqual(provenance['reference_protocol'], subject.file_record(subject.ROOT / 'data/stim_protocol.json'))
        self.assertEqual(provenance['cells'], subject.file_record(subject.OUT))
        self.assertTrue(provenance['frozen_after_owner_go'])
        self.assertIsNone(provenance['owner_go'])
        self.assertEqual(self.protocol['notes'][:-1], self.female['notes'])


if __name__ == '__main__':
    unittest.main()
