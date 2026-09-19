"""M1i structural and dry-run checks; never execute a simulation trial."""
from copy import deepcopy
import json
import subprocess
import sys
import unittest
from unittest.mock import patch
import numpy as np
import pandas as pd
from sim.malecns import fbm_substrate as substrate, fbm_adapter as adapter
from sim.malecns import fbm_replication as replication, fbm_phase0 as runner
from sim.malecns import fbm_output_retention as retention, fbm_cells, phase0
from sim.malecns.substrate import DATA, ROOT


class DeclarationTests(unittest.TestCase):
    def test_protocol_equality(self):
        for module, run in [(runner, 'a'), (replication, 'b')]:
            p = json.loads(adapter.protocol_path(run).read_text(encoding='utf-8'))
            self.assertEqual(module.validate_protocol(p), module.expected_protocol())

    def test_protocol_tampering_rejected(self):
        for module in (runner, replication):
            for key in ('model', 'seeds', 'conditions'):
                p = deepcopy(module.expected_protocol())
                p[key] = None
                with self.assertRaises(ValueError):
                    module.validate_protocol(p)

    def test_input_counts_disjoint_order(self):
        cells = adapter.declared_json(DATA / 'cells_fbm.json')
        ids = []
        for channel, count in zip(adapter.CHANNELS_B, [34, 8, 162, 38]):
            values = cells['sets'][channel]['ids']
            self.assertEqual(len(values), count)
            self.assertEqual(values, sorted(values))
            ids.extend(values)
        self.assertEqual(len(set(ids)), 242)

    def test_seed_and_condition_design(self):
        a, b = runner.expected_protocol(), replication.expected_protocol()
        self.assertEqual(a['conditions'], phase0.conditions())
        self.assertEqual(sum(c['n_trials'] for c in a['conditions']), 480)
        self.assertEqual([c['id'] for c in b['conditions']], ['fbm_sugar', 'fbm_bitter', 'fbm_both', 'fbm_sugar_kc'])
        self.assertEqual([c['n_trials'] for c in b['conditions']], [30, 30, 30, 5])
        for c in b['conditions']:
            self.assertEqual(c['seeds'], list(range(20260910, 20260910 + c['n_trials'])))

    def test_bilateral_bin_boundaries_and_normalization(self):
        body = np.array([10331, 16949, 10331, 42, 16949])
        times = np.array([0., .0499, .05, .08, .9999])
        metrics = replication.bilateral_metrics(body, times)
        self.assertEqual(metrics['bilateral_mean_hz'], 2.)
        self.assertEqual(metrics['bilateral_bin_hz'], [20., 10.] + [0.] * 17 + [10.])
        self.assertEqual(np.mean(metrics['bilateral_bin_hz']), 2.)

    def test_incomplete_replication_rejected(self):
        with self.assertRaises(ValueError):
            replication.summarize([])

    def test_compile_plan_never_calls_trial_runner(self):
        with patch.object(adapter.sys, 'platform', 'win32'):
            with self.assertRaises(RuntimeError):
                adapter.make_plan('a', 64 * 1024**2)

    def test_memory_plan_uses_supplied_host_and_live_wsl_memory(self):
        with patch.object(phase0, 'mem_available_gib', side_effect=[64., 48.]) as available, \
                patch.object(adapter.subprocess, 'check_output', side_effect=AssertionError('No host subprocess')):
            planned = adapter.memory_plan(32 * 1024**2)
            launched = adapter.memory_plan(24 * 1024**2)
        self.assertEqual(available.call_count, 2)
        self.assertEqual((planned['wsl_available_gib'], planned['host_free_gib']), (64., 32.))
        self.assertEqual((launched['wsl_available_gib'], launched['host_free_gib']), (48., 24.))

    def test_cli_forwards_host_memory(self):
        for module, run in [(runner, 'a'), (replication, 'b')]:
            with patch.object(sys, 'argv', ['runner', '--plan', '--host-free-kib', '67108864']), \
                    patch.object(adapter, 'make_plan', return_value={}) as plan, patch('builtins.print'):
                module.main()
                plan.assert_called_once_with(run, 67108864)
            with patch.object(sys, 'argv', ['runner', '--run', '--host-free-kib', '33554432']), \
                    patch.object(sys, 'platform', 'linux'), patch.object(module, 'run') as execute:
                module.main()
                execute.assert_called_once_with(33554432)


@unittest.skipUnless((DATA / 'derived/fbm/connectivity.parquet').exists(), 'Local ignored M1i graphs required')
class ArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.record = substrate.verify()
        cls.old = pd.read_parquet(DATA / 'derived/connectivity.parquet')
        cls.graph = pd.read_parquet(DATA / 'derived/fbm/connectivity.parquet')
        cls.kc = pd.read_parquet(DATA / 'derived/fbm_kc/connectivity.parquet')

    def test_exact_filter_counts_schema_signs(self):
        expected = self.old.loc[self.old.Connectivity.ge(5) & self.old.Presynaptic_Index.ne(self.old.Postsynaptic_Index)].reset_index(drop=True)
        pd.testing.assert_frame_equal(self.graph, expected)
        self.assertEqual(len(self.graph), 6242085)
        self.assertEqual(int(self.graph.Connectivity.sum()), 89859938)
        self.assertFalse(self.graph.Presynaptic_Index.eq(self.graph.Postsynaptic_Index).any())
        self.assertEqual(self.record['counts']['autapses_removed'], 33)

    def test_kc_only_signed_column_and_target_rows_change(self):
        annotations = pd.read_feather(fbm_cells.ANNOTATIONS)
        roster = pd.read_csv(DATA / 'derived/neuron_index.csv', usecols=['bodyId', 'index'])
        indices = roster.loc[roster.bodyId.isin(annotations.loc[annotations['class'].eq('Kenyon_Cell'), 'bodyId']), 'index']
        self.assertEqual(len(indices), 4064)
        mask = self.graph.Postsynaptic_Index.isin(indices)
        self.assertEqual(int(mask.sum()), 70931)
        self.assertEqual(int(self.graph.loc[mask, 'Connectivity'].sum()), 906584)
        signed = 'Excitatory x Connectivity'
        self.assertEqual(str(self.kc[signed].dtype), 'float64')
        for column in self.graph.columns:
            if column != signed:
                pd.testing.assert_series_equal(self.kc[column], self.graph[column])
        np.testing.assert_array_equal(self.kc[signed], self.graph[signed] * np.where(mask, .25, 1.))

    def test_completeness_and_index_unchanged(self):
        original = (DATA / 'derived/completeness.csv').read_bytes()
        for name in ('fbm', 'fbm_kc'):
            self.assertEqual((DATA / f'derived/{name}/completeness.csv').read_bytes(), original)
        self.assertEqual(self.record['artifacts']['neuron_index']['sha256'],
                         json.loads((DATA / 'substrate_record.json').read_text())['artifacts']['neuron_index']['sha256'])

    def test_histogram_totals(self):
        h = self.record['synapses_per_edge_histogram']
        self.assertEqual(sum(r['edges'] for r in h), len(self.old))
        self.assertEqual(sum(r['edges'] for r in h if r['synapses_per_edge'] >= 5), 6242118)
        self.assertEqual(sum(r['edges'] * r['synapses_per_edge'] for r in h), int(self.old.Connectivity.sum()))

    def test_annotation_cells(self):
        self.assertEqual(json.loads((DATA / 'cells_fbm.json').read_text()), fbm_cells.expected_cells())

    def test_retention_structure_and_values(self):
        r = retention.verify()
        self.assertFalse(r['stop_triggered'])
        self.assertIn('recorded, not a stop condition', r['interpretation'])
        self.assertEqual(len(r['cells']), 93)
        self.assertEqual(len(r['fbm_cells']), 242)
        self.assertEqual(len(r['partners']), 20)
        roster = pd.read_csv(DATA / 'derived/neuron_index.csv', usecols=['bodyId', 'index']).set_index('bodyId')['index']
        old = self.old.groupby('Presynaptic_Index').Connectivity.sum()
        new = self.graph.groupby('Presynaptic_Index').Connectivity.sum()
        for row in r['cells'] + r['fbm_cells']:
            i = roster.loc[row['bodyId']]
            self.assertEqual(row['outgoing_0_5'], int(old.get(i, 0)))
            self.assertEqual(row['outgoing_c_star'], int(new.get(i, 0)))
        for rows, totals in [(r['cells'][:91], r['set_totals']), (r['fbm_cells'], r['fbm_set_totals'])]:
            for total in totals:
                group = [x for x in rows if x['label'] == total['label']]
                for key in ('outgoing_0_5', 'outgoing_c_star'):
                    self.assertEqual(total[key], sum(x[key] for x in group))
                self.assertEqual(total['below_half'], 2 * total['outgoing_c_star'] < total['outgoing_0_5'])

    def test_fixed_top20(self):
        r = retention.verify()
        roster = pd.read_csv(DATA / 'derived/neuron_index.csv', usecols=['bodyId', 'index'])
        target = int(roster.loc[roster.bodyId.eq(10331), 'index'].iloc[0])
        old = self.old.loc[self.old.Postsynaptic_Index.eq(target)].copy()
        old['bodyId'] = roster.bodyId.to_numpy()[old.Presynaptic_Index]
        old = old.sort_values(['Connectivity', 'bodyId'], ascending=[False, True]).head(20)
        new = self.graph.loc[self.graph.Postsynaptic_Index.eq(target)].set_index('Presynaptic_Index').Connectivity
        self.assertEqual([p['bodyId'] for p in r['partners']], old.bodyId.tolist())
        for partner, row in zip(r['partners'], old.itertuples()):
            self.assertEqual(partner['into_L10331_c_star'], int(new.get(row.Presynaptic_Index, 0)))

    def test_check_cli_without_brian2(self):
        for filename, units, trials in [('fbm_replication.py', 242, 95), ('fbm_phase0.py', 91, 480)]:
            command = [sys.executable, str(ROOT / 'sim/malecns' / filename)]
            value = subprocess.check_output(command + ['--check'], cwd=ROOT, text=True)
            plan = json.loads(value)
            self.assertEqual(plan['poisson_units'], units)
            self.assertEqual(plan['total_trials'], trials)
            for mode in ('--plan', '--run'):
                missing = subprocess.run(command + [mode], cwd=ROOT, text=True, capture_output=True)
                self.assertEqual(missing.returncode, 2)
                self.assertIn('--host-free-kib', missing.stderr)
            conflicting = subprocess.run(command + ['--check', '--plan'], cwd=ROOT, text=True, capture_output=True)
            self.assertEqual(conflicting.returncode, 2)
        self.assertNotIn('brian2', sys.modules)


if __name__ == '__main__':
    unittest.main()
