"""M0 adapter/benchmark tests with synthetic results; no Brian2 execution."""
import unittest
from unittest.mock import patch
from types import SimpleNamespace

from sim.malecns import adapter
from sim.malecns.benchmark import summarise


class AdapterTests(unittest.TestCase):
    def test_native_windows_simulation_rejected(self):
        with patch.object(adapter.sys, 'platform', 'win32'), self.assertRaises(RuntimeError):
            adapter.build_male_network()

    def test_shared_builder_used_without_model_reimplementation(self):
        p = {'male_provenance': {'stimulation_layout': {'channel_order': ['sugar', 'bitter', 'water', 'ir94e']}}}
        cells = {'sets': {}}
        calls = []
        stub = SimpleNamespace(build_network=lambda *args: calls.append(args) or 'mock-network')
        with patch.object(adapter.sys, 'platform', 'linux'), patch.object(adapter, 'load_configuration', return_value=(p, cells)), patch.dict('sys.modules', {'sim.network': stub}):
            net, actual_p, actual_cells = adapter.build_male_network()
        self.assertEqual(net, 'mock-network')
        self.assertIs(actual_p, p)
        self.assertIs(actual_cells, cells)
        self.assertEqual(calls, [(p, cells, ['sugar', 'bitter', 'water', 'ir94e'])])

    def rows(self):
        return [{'condition': c, 'trial': i, 'seed': 20260910+i, 'trial_wall_s': i+1,
                 'peak_worker_rss_kib': 1048576, 'MN9_R_primary_hz': 10, 'MN9_L_secondary_hz': 20,
                 'driven_sugar_mean_hz': 200 if c == 'sugar200' else None}
                for c in ('baseline', 'sugar200') for i in range(5)]

    def test_benchmark_summary_uses_five_actual_trials(self):
        result = summarise(self.rows())
        self.assertEqual(result['baseline']['mean_wall_s'], 3)
        self.assertEqual(result['sugar200']['peak_worker_rss_gib'], 1)
        self.assertIsNone(result['baseline']['driven_sugar_mean_hz'])
        self.assertEqual(result['sugar200']['MN9_R_primary_hz']['mean'], 10)

    def test_incomplete_or_duplicate_benchmark_fails(self):
        rows = self.rows()
        with self.assertRaises(ValueError):
            summarise(rows[:-1])
        rows[-1] = rows[-2]
        with self.assertRaises(ValueError):
            summarise(rows)

    def test_wrong_seed_fails(self):
        rows = self.rows()
        rows[0]['seed'] = 123
        with self.assertRaises(ValueError):
            summarise(rows)


if __name__ == '__main__':
    unittest.main()
