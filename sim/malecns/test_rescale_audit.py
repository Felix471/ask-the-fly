# SPDX-License-Identifier: MIT
import unittest
from sim.malecns.audit_phase0 import raw_gate_checks
from sim.malecns.audit_rescale import require, stats
from sim.malecns.phase0 import conditions


class AuditTests(unittest.TestCase):
    def rows(self, a, b):
        rows=conditions()
        for row in rows:
            value=a.get(row['sugar_hz'],0) if row['gate']=='A' else b.get(row['bitter_hz'],0) if row['gate']=='B' else 0
            row.update(R_mean=value,R_sd=0)
        return rows

    def test_silent_side_does_not_pass(self):
        g=raw_gate_checks(self.rows({},{}),'R')
        self.assertFalse(g['A'])
        self.assertFalse(g['B'])  # strict 0 < 0 fails, never report vacuous suppression
        self.assertFalse(g['overall'])

    def test_historical_adjacent_zeros_allowed(self):
        g=raw_gate_checks(self.rows({200:6},{0:6}),'R')
        self.assertTrue(g['overall'])
        g=raw_gate_checks(self.rows({200:5},{0:5}),'R')
        self.assertFalse(g['A'])  # strict >5, not >=5

    def test_counts_and_fail_closed(self):
        self.assertEqual(stats([0,3,4,8]),{'median':3.5,'min':0,'max':8})
        with self.assertRaises(ValueError):
            require(False,'Do not waive mismatch')


if __name__=='__main__':
    unittest.main()
