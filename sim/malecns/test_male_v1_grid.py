"""File-only grid checks and synthetic ledgers; never construct a network."""
import copy
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

import numpy as np
from sim.grid import expand_grid_conditions, load_grid_levels
from sim.malecns import male_v1_adapter as adapter
from sim.malecns import male_v1_grid as grid
from sim.malecns.male_v1_phase1 import event_readouts


def synthetic_results():
    p = adapter.read(adapter.PROTOCOL)
    values = event_readouts(np.array([], dtype='int64'), np.array([]), p, [])
    results = []
    for c in grid.conditions(p):
        rows = []
        for t, seed in enumerate(grid.seeds_for(c['global_index'])):
            row = dict(condition=c['cond_id'], global_index=c['global_index'],
                       trial=t, seed=seed, **copy.deepcopy(values))
            row.update(L_hz=float(t), L_latency_ms=float(t) if t else None,
                       whole_network_spikes=t, neurons_fired=int(t > 0))
            rows.append(row)
        results.append(dict(condition=c, rows=rows))
    return results, p


class GridTests(unittest.TestCase):
    def test_check_without_brian(self):
        code = ("import sys, runpy; sys.modules['brian2']=None; "
                "sys.argv=['male_v1_grid', '--check']; "
                "runpy.run_module('sim.malecns.male_v1_grid', run_name='__main__')")
        result = subprocess.run([sys.executable, '-c', code], cwd=adapter.ROOT,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        check = json.loads(result.stdout)
        self.assertEqual(len(check['conditions']), 400)
        self.assertEqual(check['total_trials'], 12000)
        self.assertEqual(check['seeds'], [grid.seeds_for(g) for g in range(400)])

    def test_female_order(self):
        cs = grid.conditions(adapter.read(adapter.PROTOCOL))
        expanded = expand_grid_conditions(load_grid_levels())
        female = adapter.read(adapter.ROOT / 'data/lookup_table_v1_2.json')['cells']
        self.assertEqual(len(cs), 400)
        self.assertEqual([c['global_index'] for c in cs], list(range(400)))
        self.assertEqual(len({c['cond_id'] for c in cs}), 400)
        for c, e, f in zip(cs, expanded, female):
            for key in ('cond_id', 'global_index', 'levels', 'alias_levels'):
                self.assertEqual(c[key], e[key])
            self.assertEqual(c['hz'], f['hz'])
            self.assertEqual({ch: c[ch + '_hz'] for ch in adapter.CHANNELS}, f['hz'])

    def test_seeds(self):
        self.assertEqual(grid.seeds_for(0)[0], 20260910)
        self.assertEqual(grid.seeds_for(41)[3], 20261913)
        self.assertEqual(grid.seeds_for(399)[29], 20260910 + 1000 * 39 + 29)
        assignments = {(g, t): s for g in range(400) for t, s in enumerate(grid.seeds_for(g))}
        self.assertEqual(len(assignments), 12000)
        self.assertEqual(len(set(assignments.values())), 1200)
        groups = {}
        for (g, t), seed in assignments.items():
            groups.setdefault(seed, set()).add((g % 40, t))
        self.assertTrue(all(len(identities) == 1 for identities in groups.values()))

    def test_source_rates(self):
        c = next(c for c in grid.conditions(adapter.read(adapter.PROTOCOL))
                 if c['hz'] == dict(sugar=60, bitter=30, water=180, ir94e=120))
        self.assertEqual(adapter.source_rates(c, adapter.read(adapter.CELLS)),
                         [60]*34 + [30]*38 + [180]*17 + [120]*19)

    def test_grid_protocol_tampering(self):
        p, cells, slots = adapter.load_configuration()
        for field, value in [('levels', {}), ('seed_rule', '20260910 + trial'),
                             ('grid_levels_record', {}), ('n_unique_cells', 399)]:
            with self.subTest(field=field):
                changed = copy.deepcopy(p)
                changed['grid'][field] = value
                with patch.object(adapter, 'load_configuration', return_value=(changed, cells, slots)):
                    with self.assertRaises(ValueError):
                        grid.check()

    def test_female_order_tampering(self):
        read = adapter.read
        def changed(path):
            value = read(path)
            if Path(path) == adapter.ROOT / 'data/lookup_table_v1_2.json':
                value['cells'][0], value['cells'][1] = value['cells'][1], value['cells'][0]
            return value
        with patch.object(adapter, 'read', side_effect=changed):
            with self.assertRaises(ValueError):
                grid.conditions(adapter.read(adapter.PROTOCOL))

    def test_summary_statistics(self):
        raw, p = synthetic_results()
        result = grid.summarize(raw, p)
        self.assertEqual(len(result['cells']), 400)
        first = result['cells'][0]
        self.assertEqual(first['L_mean'], 14.5)
        self.assertAlmostEqual(first['L_sd'], np.std(np.arange(30), ddof=0))
        self.assertEqual(first['L_firing_trials'], 29)
        self.assertEqual(first['L_latency_median_ms'], 15)
        self.assertIsNone(first['R_latency_median_ms'])
        self.assertEqual(first['whole_network_spikes_median'], 14.5)
        self.assertEqual(first['whole_network_spikes_min'], 0)
        self.assertEqual(first['whole_network_spikes_max'], 29)
        for key in event_readouts(np.array([], dtype='int64'), np.array([]), p, []):
            if key.endswith('_hz'):
                for suffix in ('_mean', '_sd', '_firing_trials', '_latency_median_ms'):
                    self.assertIn(key[:-3] + suffix, first)

    def test_summary_rejects_corrupt_ledgers(self):
        raw, p = synthetic_results()
        mutations = [lambda r: r[0]['rows'][0].update(seed=0),
                     lambda r: r[0]['rows'].pop(),
                     lambda r: r.reverse(),
                     lambda r: r.pop(),
                     lambda r: r.append(r[0]),
                     lambda r: r[0]['rows'].reverse(),
                     lambda r: r[0]['rows'][0].update(global_index=1),
                     lambda r: r[0]['rows'][0].update(condition='wrong')]
        for i, mutate in enumerate(mutations):
            with self.subTest(mutation=i):
                changed = copy.deepcopy(raw)
                mutate(changed)
                with self.assertRaises(ValueError):
                    grid.summarize(changed, p)

    def test_existing_outputs_refused(self):
        with tempfile.TemporaryDirectory(dir=adapter.ROOT / 'results') as directory:
            root = Path(directory)
            for out, result in [(root, root / 'absent.json'), (root / 'absent', root)]:
                with patch.object(grid, 'OUT', out), patch.object(grid, 'RESULT', result), \
                     patch.object(grid.sys, 'platform', 'linux'), patch.object(grid, 'check_plan') as check:
                    with self.assertRaises(FileExistsError):
                        grid.run(1)
                    check.assert_not_called()
            with patch.object(grid, 'PLAN', root), patch.object(grid.sys, 'platform', 'linux'):
                with self.assertRaises(FileExistsError):
                    grid.make_plan(1)

    def test_windows_plan_and_run_refused(self):
        with patch.object(grid.sys, 'platform', 'win32'):
            for action in (grid.make_plan, grid.run):
                with self.assertRaisesRegex(RuntimeError, 'WSL'):
                    action(1)

    def test_declared_rules_match_document(self):
        doc = (adapter.ROOT / 'docs/male_fly_v2.md').read_text(encoding='utf-8')
        section = doc.split('## Phase 2\n')[1].split('## Phase 3\n')[0]
        rules = re.findall(r'^- (R[1-8]) (.*?)(?=\n\n|\Z)', section, re.M | re.S)
        rules = [(rid, ' '.join(text.split())) for rid, text in rules]
        self.assertEqual([rid for rid, _ in rules], [f'R{i}' for i in range(1, 9)])
        self.assertEqual(grid.COMPARISON_RULES, rules)
        self.assertEqual(grid.REPLAY_RULE, 'R8 ' + rules[-1][1])

    def test_memory_uses_larger_peak(self):
        with patch.object(adapter.phase0, 'mem_available_gib', return_value=32), \
             patch.object(adapter.os, 'cpu_count', return_value=32):
            memory = grid.memory_plan(32 * 1024**2)
        peaks = [(adapter.read(adapter.DATA / name)['metadata']['peak_worker_rss_gib'], name)
                 for name in ('m1j_male_results.json', 'male_v1_phase1_results.json')]
        peak, name = max(peaks)
        self.assertEqual(memory['reference_peak_gib'], peak)
        self.assertIn(name, memory['peak_source'])
        self.assertGreaterEqual(memory['worker_budget_gib'], peak * 1.25)

    def test_source_inventory(self):
        records = grid.grid_source_records()
        paths = [r['path'] for r in records]
        p = adapter.read(adapter.PROTOCOL)
        required = ['sim/network.py', 'sim/malecns/phase0.py', 'sim/malecns/substrate.py',
                    'sim/malecns/male_v1_adapter.py', 'sim/malecns/male_v1_phase1.py',
                    'sim/malecns/male_v1_grid.py', 'sim/grid.py', 'data/grid_levels.json',
                    'data/lookup_table_v1_2.json', 'data/dishes.json',
                    'data/malecns/male_v1_phase1_results.json', 'data/malecns/male_v1_phase1_audit.json',
                    p['connectivity_file'], p['completeness_file'], p['substrate_record']['path'],
                    'data/malecns/stim_protocol_male_v1.json', 'data/malecns/cells_male_v1.json']
        self.assertTrue(set(required) <= set(paths))
        self.assertEqual(len(paths), len(set(paths)))
        for record in records:
            adapter.check_file(record)

    def test_plan_validation(self):
        check = grid.check()
        sources = grid.grid_source_records()
        plan = dict(check, sources=sources, compile_only=dict(network_builds=1,
                    elapsed_simulated_seconds=0, spikes=0), brian2_version='test',
                    comparison_rules=[f'{rid} {text}' for rid, text in grid.COMPARISON_RULES],
                    replay_rule=grid.REPLAY_RULE)
        with patch.object(adapter, 'read', return_value=plan), \
             patch.object(grid, 'check', return_value=check), \
             patch.object(grid, 'grid_source_records', return_value=sources), \
             patch.object(grid, 'memory_plan', return_value={'workers': 1}), \
             patch.dict(sys.modules, brian2=types.SimpleNamespace(__version__='test')):
            self.assertEqual(grid.check_plan(1), (plan, {'workers': 1}))
            for key, bad in [('sources', []), ('total_trials', 1), ('compile_only', {}),
                             ('brian2_version', 'wrong'), ('comparison_rules', []), ('replay_rule', '')]:
                with self.subTest(key=key):
                    changed = dict(plan, **{key: bad})
                    with patch.object(adapter, 'read', return_value=changed):
                        with self.assertRaises(ValueError):
                            grid.check_plan(1)


if __name__ == '__main__':
    unittest.main()
