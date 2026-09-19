# SPDX-License-Identifier: MIT
"""Windows-safe M1j build checks; never construct a Brian2 network."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
from sim.malecns import m0_recheck, m1j_adapter as adapter, m1j_retention, phase0
from sim.malecns.substrate import ROOT


class M0ComparisonTests(unittest.TestCase):
    def compare(self, a, b):
        with tempfile.TemporaryDirectory() as tmp:
            old, new = Path(tmp) / 'old.npz', Path(tmp) / 'new.npz'
            np.savez_compressed(old, **a)
            np.savez_compressed(new, **b)
            return m0_recheck.compare_trial(old, new)

    def test_identical(self):
        data = {'10331': np.array([.1, .2]), '16949': np.array([.3])}
        r = self.compare(data, data)
        self.assertTrue(r['identical'])
        self.assertEqual((r['neurons_compared'], r['spikes_compared']), (2, 3))
        self.assertIsNone(r['first_differing_key'])

    def test_one_altered_array_no_tolerance(self):
        r = self.compare({'10331': [.1]}, {'10331': [np.nextafter(.1, 1)]})
        self.assertFalse(r['identical'])
        self.assertEqual(r['first_differing_key'], '10331')

    def test_key_sets_and_later_arrays(self):
        r = self.compare({'1': [.1], '2': [.2], '3': [.3]}, {'2': [.21], '3': [.31], '4': [.4]})
        self.assertFalse(r['key_sets_identical'])
        self.assertEqual(r['differing_arrays'], 2)
        self.assertEqual(r['missing_keys'], ['1'])
        self.assertEqual(r['extra_keys'], ['4'])

    def test_baseline_empty(self):
        self.assertTrue(self.compare({}, {})['identical'])

    def test_json_row_rates_latencies_counts(self):
        row = {key: 0 for key in m0_recheck.ROW_KEYS}
        self.assertEqual(m0_recheck.compare_rows(row, dict(row)), [])
        for key in m0_recheck.ROW_KEYS:
            other = dict(row, **{key: 1})
            self.assertEqual(m0_recheck.compare_rows(row, other), [key])

    def test_missing_compare_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(m0_recheck, 'OUT', Path(tmp) / 'absent'), patch.object(m0_recheck, 'RECORD', Path(tmp) / 'record.json'):
            with self.assertRaisesRegex(FileNotFoundError, 'directory absent'):
                m0_recheck.compare()
            self.assertFalse(m0_recheck.RECORD.exists())


class M1jBuildTests(unittest.TestCase):
    def test_male_layout(self):
        p, cells, channels = adapter.load_configuration()
        ids = [x for c in channels for x in cells['sets'][c]['ids']]
        self.assertEqual(len(ids), 108)
        self.assertEqual(len(set(ids)), 108)
        self.assertEqual([len(cells['sets'][c]['ids']) for c in channels], [34, 38, 17, 19])
        self.assertEqual(p['model']['w_syn_mV'], .65 * .275)

    def test_male_ap_zeroing(self):
        p, cells, _ = adapter.load_configuration()
        condition = p['conditions'][-1]
        rates = phase0.source_rates(condition, cells['sets'])
        self.assertEqual(len(rates), 108)
        self.assertEqual(rates.count(120), 23)
        self.assertEqual(rates[:34].count(0), 11)
        for body, rate in zip(cells['sets']['sugar']['ids'], rates):
            self.assertEqual(rate, 120 if body in cells['sets']['sugar_lb3c_bilateral']['ids'] else 0)

    def test_tamper_rejected(self):
        for brain in ('male', 'female'):
            for key in ('model', 'conditions', 'shape_gate', 'seeds'):
                p = deepcopy(adapter.expected_protocol(brain))
                p[key] = None
                with self.assertRaisesRegex(ValueError, 'frozen declaration'):
                    adapter.validate_protocol(p, brain)

    def test_cell_tamper_rejected(self):
        original = adapter.declared_json
        def altered(path):
            value = original(path)
            if path.name == 'cells_m1j.json':
                value['sets']['sugar_bilateral']['ids'].pop()
            return value
        with patch.object(adapter, 'declared_json', side_effect=altered):
            with self.assertRaisesRegex(ValueError, 'cells differ'):
                adapter.load_configuration()

    def test_m0_gate_both_runners(self):
        from sim.malecns.m1j_phase0 import run
        from sim.m1j_female import run as female_run
        with patch.object(adapter, 'require_m0', side_effect=ValueError('M0 missing')):
            for runner in (run, female_run):
                with self.assertRaisesRegex(ValueError, 'M0 missing'):
                    runner(100000000)

    def test_m0_verdict_gate(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(adapter, 'DATA', Path(tmp)):
            with self.assertRaises(ValueError):
                adapter.require_m0()
            path = Path(tmp) / 'm0_recheck.json'
            path.write_text(json.dumps({'verdict': 'DIFFERENT'}))
            with self.assertRaises(ValueError):
                adapter.require_m0()

    def test_retention_structure(self):
        r = json.loads(m1j_retention.RECORD.read_text(encoding='utf-8'))
        self.assertEqual([x['cells'] for x in r['set_totals']], [34, 23])
        self.assertEqual([x['cells'] for x in r['female']['set_totals']], [57, 32])
        self.assertEqual(len(r['cells']), 34 + 23 + 2)
        self.assertEqual(len(r['female']['cells']), 57 + 32)
        self.assertFalse(r['stop_triggered'])
        self.assertIn('no cut', r['female']['note'])
        for row in r['cells']:
            self.assertEqual(row['below_half'], 2 * row['outgoing_c_star'] < row['outgoing_0_5'])
        for total in r['set_totals']:
            rows = [x for x in r['cells'] if x['label'] == total['label']]
            for key in ('outgoing_0_5', 'outgoing_c_star'):
                self.assertEqual(total[key], sum(x[key] for x in rows))
        for row in r['female']['cells'] + r['female']['set_totals']:
            self.assertIsNone(row['retention_fraction'])

    def test_male_check_cli(self):
        p = subprocess.run([sys.executable, 'sim/malecns/m1j_phase0.py', '--check'], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(json.loads(p.stdout)['poisson_units'], 108)

    def test_physical_rate_refractory_rule_in_reused_trial(self):
        # Inspect the unchanged routine that both runners actually call: ordinary
        # refractory for all targets, then zero only positive-rate targets.
        import inspect
        source = inspect.getsource(phase0.run_condition)
        self.assertIn('model.neurons.rfc[model.target_indices] = model.t_rfc', source)
        self.assertIn('model.neurons.rfc[model.target_indices[rates>0]] = 0*ms', source)


if __name__ == '__main__':
    unittest.main()
