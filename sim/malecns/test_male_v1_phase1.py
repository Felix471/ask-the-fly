"""File-only Phase 1 checks; synthetic events never construct a network."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from sim.malecns import male_v1_adapter as adapter
from sim.malecns import male_v1_phase1 as runner
from sim.malecns import audit_male_v1_phase1 as audit
from sim.malecns import report_male_v1_phase1 as report


class Phase1Tests(unittest.TestCase):
    def test_check_without_brian(self):
        code = "import sys; sys.modules['brian2']=None; from sim.malecns.male_v1_adapter import check; print(check()['total_trials'])"
        p = subprocess.run([sys.executable, '-c', code], cwd=adapter.ROOT, capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(p.stdout.strip(), '1050')

    def test_layout(self):
        p, cells, slots = adapter.load_configuration()
        self.assertEqual(len(set(slots)), 108)
        self.assertEqual(slots, [b for c in adapter.CHANNELS for b in sorted(cells['sets'][c]['ids'])])
        self.assertEqual(p['model']['w_syn_mV'], .17875)

    def test_conditions_seeds_rates(self):
        p, cells, slots = adapter.load_configuration()
        cs = adapter.conditions(p)
        self.assertEqual(len({c['id'] for c in cs}), 35)
        self.assertEqual(sum(c['n_trials'] for c in cs), 1050)
        self.assertEqual(adapter.SEEDS, list(range(20260910, 20260940)))
        c = dict(sugar_hz=60, bitter_hz=30, water_hz=180, ir94e_hz=120)
        self.assertEqual(adapter.source_rates(c, cells), [60]*34+[30]*38+[180]*17+[120]*19)

    def test_protocol_tamper(self):
        p = adapter.read(adapter.PROTOCOL)
        p['model']['w_syn_mV'] += .001
        with self.assertRaisesRegex(ValueError, 'frozen'):
            adapter.validate_protocol(p)

    def test_cells_tamper(self):
        original = adapter.read
        def changed(path):
            value = original(path)
            if path == adapter.CELLS:
                value['sets']['water']['ids'][0] += 1
            return value
        with patch.object(adapter, 'read', side_effect=changed):
            with self.assertRaisesRegex(ValueError, 'frozen'):
                adapter.load_configuration()

    def test_corrupt_trial(self):
        p, cells, slots = adapter.load_configuration()
        c = adapter.conditions(p)[0]
        with tempfile.TemporaryDirectory(dir=adapter.ROOT / 'results') as directory:
            path = Path(directory) / 'trial_00.json'
            npz = path.with_suffix('.npz')
            body = np.array([10331, 11269, 19823], dtype='int64')
            t = np.array([.1, .2, .3])
            np.savez(npz, body_id=body, time_s=t, poisson_index=np.array([], dtype='int32'), poisson_time_s=np.array([]))
            row = dict(condition=c['id'], trial=0, seed=adapter.SEEDS[0], trial_wall_s=1., worker_peak_rss_kib=100,
                       spikes=adapter.file_record(npz), **runner.event_readouts(body, t, p, slots))
            path.write_text(json.dumps(row), encoding='utf-8')
            rebuilt = audit.audit_trial(path, c, 0, p, cells, slots)
            self.assertEqual(rebuilt, row)
            self.assertEqual(row['mn11d_hz'], 1/3)
            for key in ('L_hz', 'mn11d_hz', 'cem_19823_hz', 'neurons_fired', 'seed'):
                bad = dict(row)
                bad[key] += 1
                path.write_text(json.dumps(bad), encoding='utf-8')
                with self.assertRaises((ValueError, AssertionError)):
                    audit.audit_trial(path, c, 0, p, cells, slots)

    def test_summary_inventory(self):
        with self.assertRaises(ValueError):
            runner.summarize([], adapter.read(adapter.PROTOCOL))

    def test_independent_summary_and_group_sd(self):
        p = adapter.read(adapter.PROTOCOL)
        cells = adapter.read(adapter.CELLS)
        slots = [b for c in adapter.CHANNELS for b in cells['sets'][c]['ids']]
        raw = []
        for c in adapter.conditions(p):
            rows = []
            for trial, seed in enumerate(adapter.SEEDS):
                body = np.array([10331,11269,11393,551398,49829,19823]*trial,dtype='int64')
                times = np.arange(len(body))*.0001
                rows.append(dict(condition=c['id'],trial=trial,seed=seed,
                                 **runner.event_readouts(body,times,p,slots)))
            raw.append(dict(condition=c,rows=rows))
        result = runner.summarize(raw,p)
        self.assertEqual(result,audit.independent_summary(raw,p))
        self.assertEqual(result['conditions'][0]['mn11d_mean'],14.5)
        self.assertEqual(result['conditions'][0]['mn11d_firing_trials'],29)
        self.assertAlmostEqual(result['conditions'][0]['mn11d_sd'],np.std(np.arange(30),ddof=0))
        self.assertEqual([len(result['tables'][k]) for k in ('water_alone','water_x_sugar','ir94e_alone','ir94e_x_sugar')],[4,20,4,20])
        raw[0]['rows'][1]['seed'] += 1
        with self.assertRaises(ValueError):
            runner.summarize(raw,p)

    def test_nonzero_poisson_reconstruction_and_corruption(self):
        p, cells, slots = adapter.load_configuration()
        c = next(c for c in adapter.conditions(p) if c['id'] == 's60_b0_w180_i0')
        dt = p['model']['dt_ms']/1000
        ticks, indices = np.nonzero(np.random.RandomState(adapter.SEEDS[0]).random_sample((10000,108)) <
                                    np.array(adapter.source_rates(c,cells))*dt)
        with tempfile.TemporaryDirectory(dir=adapter.ROOT / 'results') as directory:
            path = Path(directory)/'trial_00.json'
            body, times = np.array([],dtype='int64'), np.array([])
            values = runner.event_readouts(body,times,p,slots)
            def save(pi,pt):
                np.savez(path.with_suffix('.npz'),body_id=body,time_s=times,poisson_index=pi,poisson_time_s=pt)
                row = dict(condition=c['id'],trial=0,seed=adapter.SEEDS[0],trial_wall_s=1.,worker_peak_rss_kib=100,
                           spikes=adapter.file_record(path.with_suffix('.npz')),**values)
                path.write_text(json.dumps(row),encoding='utf-8')
            save(indices,ticks*dt)
            audit.audit_trial(path,c,0,p,cells,slots)
            # Re-hash the corrupt archive so the event comparison itself must reject it.
            save(indices[1:],(ticks*dt)[1:])
            with self.assertRaises(AssertionError):
                audit.audit_trial(path,c,0,p,cells,slots)

    def test_memory_reference(self):
        peak = adapter.read(adapter.DATA/'m1j_male_results.json')['metadata']['peak_worker_rss_gib']
        with patch.object(adapter.phase0,'mem_available_gib',return_value=32), patch.object(adapter.os,'cpu_count',return_value=32):
            memory = adapter.memory_plan(32*1024**2)
        self.assertEqual(memory['reference_peak_gib'],peak)
        self.assertEqual(memory['worker_budget_gib'],1.5)
        self.assertIn('m1j_male_results.json',memory['peak_source'])

    def test_existing_outputs_refused(self):
        with tempfile.TemporaryDirectory(dir=adapter.ROOT/'results') as directory:
            with patch.object(runner,'OUT',Path(directory)), patch.object(runner.sys,'platform','linux'):
                with self.assertRaises(FileExistsError):
                    runner.run(1)
            with patch.object(adapter,'PLAN',Path(directory)), patch.object(adapter.sys,'platform','linux'):
                with self.assertRaises(FileExistsError):
                    adapter.make_plan(1)

    def test_verdicts(self):
        rows = synthetic_summary()['conditions']
        self.assertIn('not observed as', report.verdicts(rows)[0])
        self.assertIn('no monotone suppression', report.verdicts(rows)[1])
        by_id = {r['id']:r for r in rows}
        by_id['s0_b0_w240_i0']['L_mean'] = 5.001
        self.assertIn('an appetitive driver', report.verdicts(rows)[0])
        for i, value in zip((0,60,120,200), (20,15,10,5)):
            by_id[f's200_b0_w0_i{i}']['L_mean'] = value
        self.assertIn('Ir94e suppresses', report.verdicts(rows)[1])
        by_id['s200_b0_w0_i120']['L_mean'] = 21
        by_id['s0_b0_w0_i60']['L_mean'] = 6
        self.assertIn('excites MN9', report.verdicts(rows)[1])

    def test_verdict_boundaries(self):
        rows = synthetic_summary()['conditions']
        by_id = {r['id']:r for r in rows}
        by_id['s0_b0_w240_i0']['L_mean'] = 5
        by_id['s60_b0_w60_i0']['L_mean'] = 5
        self.assertIn('not observed as',report.verdicts(rows)[0])
        by_id['s60_b0_w60_i0']['L_mean'] = 5.001
        self.assertIn('an appetitive driver',report.verdicts(rows)[0])
        for i,value in zip((0,60,120,200),(20,15,15,5)):
            by_id[f's200_b0_w0_i{i}']['L_mean'] = value
        by_id['s0_b0_w0_i200']['L_mean'] = 5
        self.assertIn('no monotone suppression',report.verdicts(rows)[1])
        by_id['s0_b0_w0_i200']['L_mean'] = 4.999
        self.assertIn('Ir94e suppresses',report.verdicts(rows)[1])

    def test_report_regeneration(self):
        summary = synthetic_summary()
        female = adapter.read(adapter.ROOT / 'data/lookup_table_v1_2.json')
        block = report.render(summary, female)
        self.assertEqual(block, report.render(summary, female))
        self.assertEqual(report.replace_block(block+'\n## Later\nPreserved\n', block), block+'\n## Later\nPreserved\n')
        with self.assertRaises(ValueError):
            report.verify_block(block.replace('1,050', '1,049'), block)
        self.assertEqual(block.count('### Table '), 4)
        self.assertIn('not recorded in the female grid', block)

    def test_program_section_preserved(self):
        original = report.PROGRAM.read_text(encoding='utf-8')
        updated = report.program_text(original,synthetic_summary())
        self.assertEqual(original.split('## Phase 1\n')[0],updated.split('## Phase 1\n')[0])
        self.assertEqual(original.split('## Phase 2\n')[1],updated.split('## Phase 2\n')[1])
        self.assertEqual(updated,report.program_text(updated,synthetic_summary()))

    def test_female_low_coordinate(self):
        female = adapter.read(adapter.ROOT / 'data/lookup_table_v1_2.json')
        row = report.female_cell(female, dict(sugar_hz=60,bitter_hz=0,water_hz=60,ir94e_hz=0))
        self.assertEqual(row['water'], 'low')


def synthetic_summary():
    p = adapter.read(adapter.PROTOCOL)
    slots = [b for c in adapter.CHANNELS for b in adapter.read(adapter.CELLS)['sets'][c]['ids']]
    values = runner.event_readouts(np.array([], dtype='int64'), np.array([]), p, slots)
    raw = [dict(condition=c, rows=[dict(condition=c['id'],trial=t,seed=seed,**copy.deepcopy(values))
                                  for t,seed in enumerate(adapter.SEEDS)]) for c in adapter.conditions(p)]
    summary = runner.summarize(raw, p)
    summary['metadata'] = dict(completed_utc='SYNTHETIC',brian2='test',memory={'workers':1},total_trials=1050,
                               walltime_s=0.,peak_worker_rss_gib=0.,sources=[])
    return summary


if __name__ == '__main__':
    unittest.main()
