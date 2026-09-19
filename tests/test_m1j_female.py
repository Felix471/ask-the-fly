# SPDX-License-Identifier: MIT
"""Female M1j declaration/layout and independent historical gate agreement."""
from copy import deepcopy
import json
import subprocess
import sys
import unittest
import numpy as np
from sim.malecns import m1j_adapter as adapter, phase0
from sim.malecns.substrate import ROOT
from sim import m1j_female, run_refreeze_sugar as reference


class FemaleM1jTests(unittest.TestCase):
    def test_layout_and_overlap(self):
        p, cells, channels = adapter.load_configuration('female')
        ids = [body for c in channels for body in cells['sets'][c]['ids']]
        self.assertEqual([len(cells['sets'][c]['ids']) for c in channels], [57, 42, 11, 18])
        self.assertEqual(len(ids), 128)
        self.assertEqual(len(set(ids)), 128)
        declared_cells = adapter.declared_json(ROOT / p['cells_file'])
        overlap = set(declared_cells['sets']['water']['ids']) & set(cells['sets']['sugar']['ids'])
        self.assertEqual(len(overlap), 7)
        self.assertFalse(overlap & set(cells['sets']['water']['ids']))
        self.assertEqual(m1j_female.SIDES, {'L': p['readout']['primary'], 'R': p['readout']['secondary']})

    def test_ap_slots(self):
        p, cells, _ = adapter.load_configuration('female')
        rates = phase0.source_rates(p['conditions'][-1], cells['sets'])
        self.assertEqual(len(rates), 128)
        self.assertEqual(rates.count(120), 32)
        self.assertEqual(rates[:57].count(0), 25)
        self.assertTrue(all(x == 0 for x in rates[57:]))
        union = phase0.source_rates(p['conditions'][-2], cells['sets'])
        self.assertEqual(union.count(120), 57)

    def test_tamper(self):
        p = deepcopy(m1j_female.expected_protocol())
        p['stimulation_layout']['poisson_units'] = 135
        with self.assertRaises(ValueError):
            m1j_female.validate_protocol(p)

    def test_check_cli(self):
        p = subprocess.run([sys.executable, 'sim/m1j_female.py', '--check'], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(json.loads(p.stdout)['poisson_units'], 128)

    def test_historical_gate_equivalence(self):
        # Full independent R1 summary layout. Unused R1 conditions are retained
        # because its completeness gate must not be bypassed for this test.
        conditions = adapter.expected_protocol('female')['conditions']
        rng = np.random.default_rng(109)
        cases = []
        for _ in range(100):
            cases.append([(float(rng.integers(0, 20)), float(rng.integers(0, 3))) for c in conditions])
        cases += [[(0., 0.)] * 16,
                  [(float(c['sugar_hz']) if c['gate'] in ('A', 'AP') else
                    float(200 - c['bitter_hz']) if c['gate'] == 'B' else 0., 0.) for c in conditions]]
        for values in cases:
            rows = []
            for c, (mean, sd) in zip(conditions, values):
                rows.append(dict(c, L_mean=mean, L_sd=sd, R_mean=mean, R_sd=sd))
            # R1 reuses A200 for B0; the M1 design records both with identical
            # rates/layout/seed. Enforce that paired identity in synthetic data.
            a200 = next(r for r in rows if r['id'] == 'A_s200_b0')
            b0 = next(r for r in rows if r['id'] == 'B_s200_b0')
            for k in ('L_mean', 'L_sd', 'R_mean', 'R_sd'):
                b0[k] = a200[k]
            mapped = {}
            for r in rows:
                g, s, b = r['gate'], r['sugar_hz'], r['bitter_hz']
                if g == 'A':
                    key = 'R1_new_200' if s == 200 else f'R1_A_new_{s}'
                elif g == 'B':
                    key = 'R1_new_200' if b == 0 else f'R1_B_new200_bitter{b}'
                elif g == 'C':
                    key = f'R1_C_bitter{b}'
                elif g == 'D':
                    key = 'R1_new_0'
                else:
                    continue
                mapped[key] = r
            summaries = []
            for c in reference.select_conditions():
                r = mapped.get(c['cond_id'], {'L_mean': 0., 'L_sd': 0., 'R_mean': 0., 'R_sd': 0.})
                summaries.append({'cond_id': c['cond_id'], 'readouts': {
                    f'MN9_{side}': {'n_trials': 30, 'rate_mean_hz': r[f'{side}_mean'], 'rate_std_hz': r[f'{side}_sd']}
                    for side in ('L', 'R')}})
            expected = reference.phase0_gates(summaries)
            actual = phase0.evaluate_gates(rows)['L']
            self.assertEqual({g: actual[g] for g in 'ABCD'}, expected['gates'])
            self.assertEqual(actual['overall'], expected['overall_pass'])


if __name__ == '__main__':
    unittest.main()
