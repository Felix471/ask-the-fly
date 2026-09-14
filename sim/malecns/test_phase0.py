"""M1 synthetic design/gate tests; no simulations."""
import unittest
from sim.malecns.phase0 import conditions, choose_workers, evaluate_gates, source_rates


class Phase0Tests(unittest.TestCase):
    def test_exact_design(self):
        cs = conditions()
        self.assertEqual(len(cs), 16)
        self.assertEqual(sum(c['n_trials'] for c in cs if c['gate'] in 'ABCD'), 420)
        self.assertEqual(sum(c['n_trials'] for c in cs), 480)
        self.assertEqual([c['sugar_hz'] for c in cs if c['gate']=='A'], [25,50,100,200])
        self.assertEqual([c['bitter_hz'] for c in cs if c['gate']=='B'], [0,25,50,100,200])
        self.assertEqual([c['sugar_hz'] for c in cs if c['gate']=='AP'], [120,120])

    def test_memory_headroom(self):
        p = choose_workers(60, 80, 3.038, 32)
        self.assertLess(p['workers'], 14)
        self.assertGreaterEqual(p['reserve_gib'], 15)
        self.assertGreaterEqual(p['worker_budget_gib'], 1.5*3.038)
        self.assertLessEqual(p['workers']*p['worker_budget_gib']+p['reserve_gib'], 60)
        with self.assertRaises(ValueError):
            choose_workers(5, 80, 3.038, 32)

    def test_subset_preserves_physical_slots(self):
        sets = {'sugar':{'ids':[1,2,3]}, 'sugar_lb3c':{'ids':[2,3]},
                'bitter':{'ids':[4]}, 'water':{'ids':[5]}, 'ir94e':{'ids':[6]}}
        a, b = conditions()[-2:]
        self.assertEqual(source_rates(a, sets), [120,120,120,0,0,0])
        self.assertEqual(source_rates(b, sets), [0,120,120,0,0,0])

    def fixture(self):
        rows = []
        for c in conditions():
            value = c['sugar_hz']/2 if c['gate']=='A' else (100-c['bitter_hz']*.4 if c['gate']=='B' else 0)
            rows.append(dict(c, R_mean=value, R_sd=0, L_mean=value, L_sd=0))
        return rows

    def test_independent_sides(self):
        rows = self.fixture()
        rows[3]['L_mean'] = 0
        g = evaluate_gates(rows)
        self.assertTrue(g['R']['A'])
        self.assertFalse(g['L']['A'])
        self.assertTrue(g['R']['B'])

    def test_bitter_monotonicity_not_just_endpoint(self):
        rows = self.fixture()
        rows[5]['R_mean'] = 101
        self.assertFalse(evaluate_gates(rows)['R']['B'])

    def test_historical_D_and_literal_zero_are_separate(self):
        rows = self.fixture()
        next(r for r in rows if r['gate']=='D')['R_mean'] = 2
        gates = evaluate_gates(rows)
        self.assertTrue(gates['R']['D'])
        self.assertFalse(gates['R']['D_literal_zero'])
        self.assertTrue(gates['L']['D_literal_zero'])

    def test_incomplete_design_rejected(self):
        with self.assertRaises(ValueError):
            evaluate_gates(self.fixture()[:-1])


if __name__ == '__main__':
    unittest.main()
