"""Synthetic-only Phase 2 outputs tests; never inspect an active grid run."""
import copy
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from sim.malecns import build_lookup_male as builder
from sim.malecns import male_female_comparison as comparison
from sim.malecns import audit_male_v1_grid as audit
from sim.malecns import report_male_v1_grid as report
from scripts import pack_replay_male as pack
from sim.grid import expand_grid_conditions
from sim.lookup import LookupTable, _cells_sha256
from sim.lookup_v1_2 import state_for
from sim.malecns import male_v1_adapter as adapter, male_v1_grid as grid
from sim.malecns.male_v1_phase1 import event_readouts
from sim.malecns.substrate import ROOT, file_record, write_json
from sim.malecns.test_male_v1_grid import synthetic_results


def small_comparison():
    """Six pairs: AB water, BC/BD ir94e, AC only-both, AD neither, CD tie."""
    dimensions = ['sugar', 'bitter', 'water', 'ir94e']
    levels = dict(sugar=dict(none=0, low=60, medium=80, high=120), bitter=dict(none=0),
                  water=dict(none=0, low=60, medium=60), ir94e=dict(none=0, low=60))
    coordinates = expand_grid_conditions(dict(dimensions=dimensions, levels=levels))
    female, male = [dict(dimensions=dimensions, levels=copy.deepcopy(levels), cells=[]) for _ in range(2)]
    fs = [8., 6., 4., 4.]
    original, water, ir94e, both = [0., 2., 4., 4.], [6., 4., 8., 8.], [2., 6., 4., 4.], [6., 4., 2., 8.]
    for c in coordinates:
        d = list(levels['sugar']).index(c['levels']['sugar'])
        for table, score, mn11 in [(female, fs[d], 6 if d in (0, 2) else 0),
                (male, (original if c['rates']['water'] and c['rates']['ir94e'] else
                        water if not c['rates']['water'] and c['rates']['ir94e'] else
                        ir94e if c['rates']['water'] else both)[d],
                 6 if c['rates']['water'] and c['rates']['ir94e'] and d in (0, 2) else 0)]:
            table['cells'].append(dict(c['levels'], hz=c['rates'], mn9_left_mean=score,
                                       mn9_mean=score, state=state_for(score, mn11)))
    dishes = [dict(key=key, display=dict(en=key, zh='菜'+key), sugar=sugar, bitter='none',
                   water='medium', ir94e='low') for key, sugar in zip('ABCD', levels['sugar'])]
    return female, male, dishes


def save_trial(directory, c, p, cells, slots, trial=0):
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f'trial_{trial:02d}.npz'
    body = np.array([10331, 11269, 16949, 10331], dtype='int64')
    times = np.array([.01235, .1, .2, .9999])
    seed = 20260910+1000*(c['global_index'] % 40)+trial
    dt = p['model']['dt_ms']/1000
    ticks, indices = np.nonzero(np.random.RandomState(seed).random_sample((10000, len(slots))) <
                                np.asarray(adapter.source_rates(c, cells))*dt)
    np.savez(path, body_id=body, time_s=times, poisson_index=indices, poisson_time_s=ticks*dt)
    row = dict(condition=c['cond_id'], global_index=c['global_index'], trial=trial, seed=seed,
               trial_wall_s=1., worker_peak_rss_kib=100, spikes=file_record(path),
               **event_readouts(body, times, p, slots))
    write_json(path.with_suffix('.json'), row)
    return row


class OutputTests(unittest.TestCase):
    def test_site_tie_boundary(self):
        self.assertEqual(comparison.outcome(0., 0.), 'tie')
        self.assertEqual(comparison.outcome(0., 1e-9), 'second')

    def test_all_comparison_numbers_by_hand(self):
        f, m, dishes = small_comparison()
        result = comparison.compare(f, m, dishes)
        self.assertEqual((result['n_dishes'], result['n_pairs'], result['n_distinct_female_cells'],
                          result['n_distinct_male_cells']), (4, 6, 4, 4))
        states = ('eats', 'mouth_moves', 'proboscis_only', 'no_response')
        cross = {s: dict.fromkeys(states, 0) for s in states}
        cross['eats']['mouth_moves'] = cross['mouth_moves']['mouth_moves'] = 1
        cross['proboscis_only']['no_response'] = cross['no_response']['no_response'] = 1
        self.assertEqual(result['distributions'], dict(
            female=dict(dishes=dict(zip(states, [1, 1, 1, 1])), cells=dict(zip(states, [4, 4, 4, 4]))),
            male=dict(dishes=dict(zip(states, [0, 2, 0, 2])), cells=dict(zip(states, [0, 2, 6, 8]))),
            below_5hz_dishes=dict(female=2, male=4), cross_table=cross))
        self.assertEqual(result['pairwise'], dict(agreement_rate=1/6, agreeing_pairs=1,
            cross_table=dict(first=dict(first=0, second=5, tie=0), second=dict(first=0, second=0, tie=0),
                             tie=dict(first=0, second=0, tie=1)), strict_pairs=5, strict_agreement_rate=0., both_tie_pairs=1))
        self.assertEqual(result['attribution_pairs'], dict(disagreeing_pairs=5, removed_by_water=1,
            removed_by_ir94e=2, removed_by_either=3, removed_only_by_both=1, removed_by_neither=2))
        self.assertEqual(result['attribution_dishes'], dict(dishes_lower=2, dishes_partly_water=1,
            dishes_fully_water=0, dishes_partly_ir94e=1, dishes_fully_ir94e=1,
            sum_lower=5, sum_lower_water=4, sum_lower_ir94e=3))
        self.assertEqual(result['channel_sign'], dict(
            water=dict(female=dict(lower=0, equal=4, higher=0, n_dishes=4), male=dict(lower=4, equal=0, higher=0, n_dishes=4)),
            ir94e=dict(female=dict(lower=0, equal=4, higher=0, n_dishes=4), male=dict(lower=2, equal=2, higher=0, n_dishes=4))))
        expected = []
        for dish, fs, fr, fst, ms, mr, mst, lost in zip(dishes, [8., 6., 4., 4.], [1, 2, 3, 3],
                ['eats', 'proboscis_only', 'mouth_moves', 'no_response'], [0., 2., 4., 4.], [4, 3, 1, 1],
                ['mouth_moves', 'no_response', 'mouth_moves', 'no_response'], [(3, 2, 3), (2, 2, 0), (0, 0, 0), (0, 0, 0)]):
            expected.append(dict(key=dish['key'], en=dish['display']['en'], zh=dish['display']['zh'],
                **{d: dish[d] for d in ('sugar', 'bitter', 'water', 'ir94e')},
                female_score=fs, female_rank=fr, female_state=fst, male_score=ms, male_rank=mr, male_state=mst,
                lower=lost[0], lower_water=lost[1], lower_ir94e=lost[2]))
        self.assertEqual(result['dishes'], expected)
        self.assertEqual(result['inputs'], dict(female_cells_sha256=_cells_sha256(f['cells']), male_cells_sha256=_cells_sha256(m['cells'])))
        self.assertEqual(result['rules'], [rid+' '+text for rid, text in grid.COMPARISON_RULES])
        audit.audit_comparison(result, f, m, dishes)

    def test_counterfactual_does_not_mutate_and_aliases(self):
        f, m, dishes = small_comparison()
        old = copy.deepcopy((f, m, dishes))
        rows = comparison.r1_dish_set(m, dishes)
        self.assertEqual([r['water'] for r in rows], ['low']*4)
        comparison.compare(f, m, dishes)
        self.assertEqual((f, m, dishes), old)

    def test_r6_counts_newly_lost_pairs(self):
        f, m, dishes = small_comparison()
        fr = comparison.r1_dish_set(f, dishes)
        totals, rows = comparison.r6_attribution_dishes(dishes, fr, fr, [0., 2., 4., 4.], [8., 6., 4., 4.])
        self.assertEqual(totals['sum_lower'], 0)
        self.assertEqual(totals['sum_lower_water'], 5)
        self.assertEqual([r['lower_water'] for r in rows], [3, 2, 0, 0])

    def test_no_strict_pairs_and_empty_channel(self):
        result = comparison.r4_pairwise([0, 0], [0, 1])
        self.assertEqual(result['strict_pairs'], 0)
        self.assertIsNone(result['strict_agreement_rate'])
        f, m, dishes = small_comparison()
        for d in dishes:
            d['water'] = 'none'
        self.assertEqual(comparison.r7_channel_sign(f, m, dishes)['water']['male'],
                         dict(lower=0, equal=0, higher=0, n_dishes=0))

    def test_r5_either_is_union_not_sum(self):
        self.assertEqual(comparison.r5_attribution_pairs([2, 1], [1, 2], [2, 1], [2, 1], [1, 2]),
                         dict(disagreeing_pairs=1, removed_by_water=1, removed_by_ir94e=1,
                              removed_by_either=1, removed_only_by_both=0, removed_by_neither=0))

    def test_imports_without_brian2(self):
        code = ('import sys; sys.modules["brian2"]=None; '
                'from sim.malecns import build_lookup_male, male_female_comparison, audit_male_v1_grid, report_male_v1_grid; '
                'from scripts import pack_replay_male')
        done = subprocess.run([sys.executable, '-c', code], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(done.returncode, 0, done.stderr)

    def test_report_markers_and_later_sections(self):
        block = report.BEGIN+'\nnew\n'+report.END+'\n'
        old = 'before\n'+report.BEGIN+'\nold\n'+report.END+'\nlater\n'
        self.assertEqual(report.replace_block(old, block), 'before\n'+block+'later\n')
        for bad in ('none', report.END+report.BEGIN, old+report.BEGIN, report.END+old):
            with self.assertRaises(ValueError):
                report.replace_block(bad, block)

    def test_memory_arithmetic_and_larger_peak_are_audited(self):
        memory = adapter.phase0.choose_workers(32, 30, 2, 16)
        memory['reference_peak_gib'] = memory.pop('measured_m0_peak_gib')
        memory['rule'] = memory['rule'].replace('M0 peak', 'reference peak')
        memory['peak_source'] = 'data/malecns/male_v1_phase1_results.json metadata.peak_worker_rss_gib'
        memory['peak_selection'] = 'Larger of M1j and male-v1 Phase 1 peak_worker_rss_gib (M1j on equality)'
        audit.audit_memory(memory, 1., 2.)
        for key in ('workers', 'reference_peak_gib', 'reserve_gib', 'worker_budget_gib'):
            bad = dict(memory)
            bad[key] += 1
            with self.assertRaises(ValueError, msg=key):
                audit.audit_memory(bad, 1., 2.)

    def test_audit_rejects_every_changed_comparison_number(self):
        f, m, dishes = small_comparison()
        result = comparison.compare(f, m, dishes)
        # Walk every numeric leaf, including hashes' surrounding input metadata.
        def numeric_paths(value, prefix=()):
            if isinstance(value, dict):
                for k, v in value.items():
                    yield from numeric_paths(v, prefix+(k,))
            elif isinstance(value, list):
                for k, v in enumerate(value):
                    yield from numeric_paths(v, prefix+(k,))
            elif isinstance(value, (int, float)):
                yield prefix
        expected = audit.independent_comparison(f, m, dishes)
        for path in numeric_paths(result):
            bad = copy.deepcopy(result)
            parent = bad
            for key in path[:-1]:
                parent = parent[key]
            parent[path[-1]] += 1
            with patch.object(audit, 'independent_comparison', return_value=expected):
                with self.assertRaises(ValueError, msg=str(path)):
                    audit.audit_comparison(bad, f, m, dishes)


class LookupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(dir=ROOT / 'results')
        cls.directory = Path(cls.temp.name)
        cls.raw, cls.p = synthetic_results()
        cls.cells = adapter.read(adapter.CELLS)
        cls.slots = [b for ch in adapter.CHANNELS for b in cls.cells['sets'][ch]['ids']]
        cls.female = adapter.read(builder.FEMALE)
        # Preserve only the frozen schema/coordinates; replace every female measurement.
        for row in cls.female['cells']:
            for key in row:
                if key not in (*adapter.CHANNELS, 'hz', 'n_trials', 'state'):
                    row[key] = 0.
            row['state'] = 'no_response'
        cls.female['cells_sha256'] = _cells_sha256(cls.female['cells'])
        cls.female_path = cls.directory / 'female.json'
        write_json(cls.female_path, cls.female)
        cls.source_path = cls.directory / 'source.txt'
        cls.source_path.write_text('synthetic source\n', encoding='utf-8')
        plan = cls.directory / 'plan.json'
        write_json(plan, {'synthetic': True})
        cls.summary = grid.summarize(cls.raw, cls.p)
        cls.summary['metadata'] = dict(total_trials=12000, sources=[file_record(cls.source_path)], plan=file_record(plan),
            completed_utc='2026-09-19T00:00:00+00:00', brian2='synthetic', memory={'workers': 1}, walltime_s=1., peak_worker_rss_gib=.001)
        full = cls.directory / 'full.json'
        write_json(full, dict(cls.summary, raw=cls.raw))
        cls.summary['raw_ledger'] = file_record(full)
        cls.result_path = cls.directory / 'compact.json'
        write_json(cls.result_path, cls.summary)
        cls.output = cls.directory / 'male.json'
        with patch.object(adapter, 'load_configuration', return_value=(cls.p, cls.cells, cls.slots)):
            cls.lookup = builder.build(cls.result_path, cls.female_path, cls.output)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_synthetic_400_lookup(self):
        table = LookupTable.load(self.output).data
        self.assertEqual(len(table['cells']), 400)
        self.assertEqual(list(table)[-1], 'cells')
        for row, old in zip(table['cells'], self.female['cells']):
            self.assertEqual(list(row), list(old)[:-1]+['cem_mean', 'cem_sd', 'state'])
            self.assertEqual(row['hz'], old['hz'])
            self.assertEqual(row['mn9_mean'], 14.5)
            self.assertEqual(row['mn9_std'], 8.655)
            self.assertEqual(row['state'], 'proboscis_only')
            self.assertEqual(row['mn9_r_mean'], row['mn9_right_mean'])
        self.assertEqual(table['product_commitments'], self.p['product_commitments'])
        blob = self.output.read_bytes()
        self.assertNotIn(b'\r', blob)
        self.assertEqual(blob, (json.dumps(table, indent=2, ensure_ascii=False, allow_nan=False)+'\n').encode('utf-8'))
        audit.audit_lookup_cells(table, self.raw, self.female)
        audit.audit_lookup_header(table, self.p, self.cells, self.female, self.result_path, self.summary['metadata'], self.female_path)
        self.assertEqual(audit.independent_summary(self.raw, self.p)['cells'], self.summary['cells'])

    def test_builder_refuses_overwrite_before_reading(self):
        with patch.object(adapter, 'load_configuration') as load:
            with self.assertRaises(FileExistsError):
                builder.build(self.directory / 'absent', self.female_path, self.output)
            load.assert_not_called()

    def test_builder_rejects_tampered_source(self):
        self.source_path.write_text('changed\n', encoding='utf-8')
        try:
            with patch.object(adapter, 'load_configuration', return_value=(self.p, self.cells, self.slots)):
                with self.assertRaisesRegex(ValueError, 'Source changed'):
                    builder.build(self.result_path, self.female_path, self.directory / 'rejected.json')
        finally:
            self.source_path.write_text('synthetic source\n', encoding='utf-8')
        self.assertFalse((self.directory / 'rejected.json').exists())

    def test_results_refuse_bad_plan_total_and_raw_record(self):
        for field in ('plan', 'total_trials', 'raw_ledger'):
            bad = copy.deepcopy(self.summary)
            if field == 'total_trials':
                bad['metadata'][field] = 11999
            elif field == 'plan':
                bad['metadata']['plan']['sha256'] = '0'*64
            else:
                bad[field]['sha256'] = '0'*64
            path = self.directory / ('bad_'+field+'.json')
            write_json(path, bad)
            with self.assertRaises(ValueError):
                builder.checked_results(path)

    def test_lookup_rejects_rounding_state_and_order(self):
        summary = copy.deepcopy(self.summary)
        summary['cells'][0]['L_mean'] = 4.9996
        with self.assertRaisesRegex(ValueError, 'rounding'):
            builder.lookup_cells(summary, self.female, grid.conditions(self.p))
        summary['cells'][0]['L_mean'] = 5.
        summary['cells'][0]['mn11d_mean'] = 5.
        cells = builder.lookup_cells(summary, self.female, grid.conditions(self.p))
        self.assertEqual(cells[0]['state'], 'eats')
        summary['cells'].reverse()
        with self.assertRaises(ValueError):
            builder.lookup_cells(summary, self.female, grid.conditions(self.p))

    def test_audit_rejects_every_wrong_lookup_value(self):
        for key in self.lookup['cells'][0]:
            if isinstance(self.lookup['cells'][0][key], (int, float)):
                bad = copy.deepcopy(self.lookup)
                bad['cells'][0][key] += 1
                with self.assertRaises(ValueError, msg=key):
                    audit.audit_lookup_cells(bad, self.raw, self.female)
        bad = copy.deepcopy(self.lookup)
        bad['cells'][0]['state'] = 'no_response'
        with self.assertRaises(ValueError):
            audit.audit_lookup_cells(bad, self.raw, self.female)

    def test_audit_rejects_lookup_header_tampering(self):
        for field, value in [('protocol', {}), ('readouts_recorded', []), ('product_commitments', []),
                             ('grid_levels_sha256', '0'*64), ('state_rule', {}), ('model', 'wrong')]:
            bad = dict(self.lookup, **{field: value})
            with self.assertRaises(ValueError, msg=field):
                audit.audit_lookup_header(bad, self.p, self.cells, self.female, self.result_path,
                                          self.summary['metadata'], self.female_path)

    def test_report_generate_check_and_corruption(self):
        dishes = [dict(key=f'synthetic-{i}', display=dict(en=f'dish {i}', zh=f'菜 {i}'),
                       **{d: row[d] for d in adapter.CHANNELS}) for i, row in enumerate(self.female['cells'][:174])]
        comp = comparison.compare(self.female, self.lookup, dishes)
        comp_path, audit_path = self.directory / 'comparison.json', self.directory / 'audit.json'
        write_json(comp_path, comp)
        audited = dict(status='PASS', raw_trials=12000, readout_neuron_trials=156000, poisson_unit_trials=1296000,
            cells=400, dishes=174, pairs=15051, replays=400,
            sources=[file_record(path) for path in (self.result_path, self.output, comp_path)],
            auditor=file_record(Path(audit.__file__)), dependencies=[],
            replay_sizes=dict(min_bytes=1, median_bytes=2, max_bytes=3, total_bytes=6, index_bytes=10, manifest_bytes=20))
        write_json(audit_path, audited)
        report_path, program_path = self.directory / 'report.md', self.directory / 'program.md'
        original = '# Program\n\n## Phase 2\n\nUntouched declaration.\n\n## Phase 3\n\nLater.\n'
        program_path.write_text(original, encoding='utf-8', newline='\n')
        args = dict(result_path=self.result_path, lookup_path=self.output, comparison_path=comp_path,
                    audit_path=audit_path, report_path=report_path, program_path=program_path)
        with patch.object(adapter, 'load_configuration', return_value=(self.p, self.cells, self.slots)):
            report.generate(**args)
            report.generate(check=True, **args)
            new_program = program_path.read_text(encoding='utf-8')
            self.assertEqual(new_program.split('### Results')[0], original.split('## Phase 3')[0])
            self.assertEqual(new_program.split('## Phase 3')[1], original.split('## Phase 3')[1])
            blob = report_path.read_text(encoding='utf-8')
            self.assertEqual(sum(line.startswith('| synthetic-') for line in blob.splitlines()), 174)
            report_path.write_text(blob.replace('6.000', '6.001') if '6.000' in blob else blob.replace('grid and comparison', 'grid and Comparison'), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'regeneration'):
                report.generate(check=True, **args)
            report_path.write_text(blob, encoding='utf-8')
            program_path.write_text(new_program.replace('Completed', 'completed'), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'regeneration'):
                report.generate(check=True, **args)
            program_path.write_text(new_program, encoding='utf-8')
            comp_path.write_bytes(comp_path.read_bytes()+b' ')
            with self.assertRaisesRegex(ValueError, 'Source changed'):
                report.generate(check=True, **args)


class ReplayTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / 'results')
        self.directory = Path(self.temp.name)
        self.p, self.cells = adapter.read(adapter.PROTOCOL), adapter.read(adapter.CELLS)
        self.slots = [b for ch in adapter.CHANNELS for b in self.cells['sets'][ch]['ids']]
        cs = grid.conditions(self.p)
        self.groups = [dict(condition=c, rows=[save_trial(self.directory / c['cond_id'], c, self.p, self.cells, self.slots)])
                       for c in (cs[0], cs[41])]

    def tearDown(self):
        self.temp.cleanup()

    def test_two_cell_pack_and_audit(self):
        index_path, output = self.directory / 'index.json', self.directory / 'pack'
        stats = pack.pack_trials(dict(raw=self.groups), self.p, self.cells, index_path, output, 'a'*40, 'b'*64, 166700)
        expected = audit.audit_replays(self.groups, self.p, self.cells, index_path, output, 'a'*40, 'b'*64, 166700)
        self.assertEqual(stats, expected)
        index = adapter.read(index_path)
        self.assertEqual(index['replay_run']['n_spikes_total'], 8)
        for group in self.groups:
            blob = (output / (group['condition']['cond_id']+'.bin')).read_bytes()
            self.assertEqual(blob[:4], b'AFR1')
            size = struct.unpack('<I', blob[4:8])[0]
            header = json.loads(blob[8:8+size])
            self.assertEqual(header['seed'], 20260910+1000*(group['condition']['global_index'] % 40))
            self.assertEqual(header['mn9_left_count'], 2)
            self.assertEqual(header['mn9_left_ms'], [12.4, 999.9])
            positions = np.frombuffer(blob, '<u2', count=4, offset=8+size)
            self.assertEqual([index['root_ids'][i] for i in positions], ['10331', '11269', '16949', '10331'])
            np.testing.assert_array_equal(np.frombuffer(blob, '<u2', count=4, offset=8+size+8), [124, 1000, 2000, 9999])
        self.assertEqual(stats['total_bytes'], sum((output / (g['condition']['cond_id']+'.bin')).stat().st_size for g in self.groups))
        with self.assertRaises(FileExistsError):
            pack.pack_trials(dict(raw=self.groups), self.p, self.cells, index_path, output, 'a'*40, 'b'*64, 166700)

    def test_u16_u32_maximum_index_boundary(self):
        c, row = self.groups[0]['condition'], self.groups[0]['rows'][0]
        for size, dtype in [(65535, 'u16'), (65536, 'u16'), (65537, 'u32')]:
            ids = list(range(1, size+1))
            body, times = np.array([size]), np.array([.1])
            blob, header = pack.encode_events(body, times, ids, c, row, 'a'*40, 'b'*64, 166700)
            self.assertEqual(header['idx_dtype'], dtype)
            length = struct.unpack('<I', blob[4:8])[0]
            decoded = np.frombuffer(blob, '<u2' if dtype == 'u16' else '<u4', count=1, offset=8+length)
            self.assertEqual(decoded[0], size-1)

    def test_pack_never_reads_other_trial(self):
        first = self.groups[0]
        first['rows'].append(dict(trial=1, spikes={'path': 'MUST_NOT_OPEN'}))
        index_path, output = self.directory / 'index.json', self.directory / 'pack'
        pack.pack_trials(dict(raw=self.groups), self.p, self.cells, index_path, output, 'a'*40, 'b'*64, 166700)
        self.assertEqual(adapter.read(index_path)['replay_run']['n_cells_run'], 2)

    def test_pack_rejects_wrong_trial_seed_and_source(self):
        for field in ('trial', 'seed'):
            group = copy.deepcopy(self.groups[0])
            group['rows'][0][field] += 1
            with self.assertRaises(ValueError):
                pack.trial_zero(group)
        group = copy.deepcopy(self.groups[0])
        group['rows'][0]['spikes']['sha256'] = '0'*64
        with self.assertRaises(ValueError):
            pack.trial_zero(group)

    def test_audit_corrupt_trial_and_poisson(self):
        group = self.groups[1]
        row, c = group['rows'][0], group['condition']
        path = ROOT / row['spikes']['path']
        ledger = path.with_suffix('.json')
        self.assertEqual(audit.audit_trial(ledger, c, 0, self.p, self.cells, self.slots), row)
        for key in ('L_hz', 'seed', 'global_index', 'whole_network_spikes', 'mn11d_hz'):
            bad = dict(row)
            bad[key] += 1
            ledger.write_text(json.dumps(bad), encoding='utf-8')
            with self.assertRaises(ValueError, msg=key):
                audit.audit_trial(ledger, c, 0, self.p, self.cells, self.slots)
        with np.load(path) as raw:
            data = dict(raw)
        self.assertGreater(len(data['poisson_index']), 0)
        data['poisson_index'] = data['poisson_index'][1:]
        data['poisson_time_s'] = data['poisson_time_s'][1:]
        np.savez(path, **data)
        row['spikes'] = file_record(path)
        ledger.write_text(json.dumps(row), encoding='utf-8')
        with self.assertRaises(AssertionError):
            audit.audit_trial(ledger, c, 0, self.p, self.cells, self.slots)

    def test_audit_corrupt_bin_index_and_manifest(self):
        index_path, output = self.directory / 'index.json', self.directory / 'pack'
        pack.pack_trials(dict(raw=self.groups), self.p, self.cells, index_path, output, 'a'*40, 'b'*64, 166700)
        def check():
            return audit.audit_replays(self.groups, self.p, self.cells, index_path, output, 'a'*40, 'b'*64, 166700)
        binary = output / (self.groups[0]['condition']['cond_id']+'.bin')
        original = binary.read_bytes()
        binary.write_bytes(original[:-1]+bytes([original[-1] ^ 1]))
        with self.assertRaises(AssertionError):
            check()
        binary.write_bytes(original)
        for path in (index_path, output / 'manifest.json'):
            old = path.read_text(encoding='utf-8')
            bad = json.loads(old)
            if path == index_path:
                bad['flags'][0] ^= 1
            else:
                bad['n_cells'] += 1
            path.write_text(json.dumps(bad), encoding='utf-8')
            with self.assertRaises(ValueError):
                check()
            path.write_text(old, encoding='utf-8')


if __name__ == '__main__':
    unittest.main()
