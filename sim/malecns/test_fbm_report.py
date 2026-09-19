"""M1i audit failure detection and reproducible report checks; no simulation."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
import numpy as np
from sim.malecns import audit_fbm as audit, report_fbm as report, report_m1h
from sim.malecns.substrate import DATA, ROOT, file_record


class TrialAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT)
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'trial_00.json'
        self.condition = dict(id='synthetic')
        self.protocol = dict(seeds=[20260910], trial=dict(duration_ms=1000), model=dict(dt_ms=.1))
        np.savez(self.path.with_suffix('.npz'), body_id=np.array([10331, 10331, 16949]),
                 time_s=np.array([0., .05, .9999]), poisson_index=np.array([], dtype=np.int32), poisson_time_s=np.array([]))
        self.row = dict(condition='synthetic', trial=0, seed=20260910, whole_network_spikes=3,
                        source_spike_counts=[2, 1], L_hz=2., R_hz=1., L_latency_ms=0., R_latency_ms=999.9,
                        bilateral_mean_hz=1.5, bilateral_bin_hz=[10., 10.] + [0.] * 17 + [10.],
                        spikes=file_record(self.path.with_suffix('.npz')))
        self.save(self.row)

    def save(self, row):
        self.path.write_text(json.dumps(row), encoding='utf-8')

    def check(self):
        return audit.audit_trial(self.path, self.condition, 0, self.protocol, [10331, 16949], [0, 0], True)

    def test_trial_structure_and_bin_boundary(self):
        row, evidence = self.check()
        self.assertEqual(row['neurons_fired'], 2)
        self.assertEqual(evidence['poisson_event_counts'], [0, 0])
        self.assertEqual(len(evidence['unit_hashes']), 2)
        self.assertEqual(sum(row['bilateral_bin_hz']) / 20, row['bilateral_mean_hz'])

    def test_corrupted_trial_json_copy_rejected(self):
        self.check()
        for key, value in [('L_hz', 3.), ('whole_network_spikes', 4), ('L_latency_ms', 1.),
                           ('seed', 20260911), ('source_spike_counts', [3, 1]), ('bilateral_bin_hz', [0.] * 20)]:
            with self.subTest(key=key):
                corrupted = deepcopy(self.row)
                corrupted[key] = value
                self.save(corrupted)
                with self.assertRaisesRegex(ValueError, key):
                    self.check()

    def test_declared_input_mismatch_rejected(self):
        with self.assertRaises(AssertionError):
            audit.audit_trial(self.path, self.condition, 0, self.protocol, [10331, 16949], [120, 0], True)

    def test_nested_summary_mismatch_names_field(self):
        with self.assertRaisesRegex(ValueError, r'summary.gates.L.S1'):
            audit.equal({'gates': {'L': {'S1': True}}}, {'gates': {'L': {'S1': False}}}, 'summary')


class ResultReportTests(unittest.TestCase):
    def test_audit_structure_and_counts(self):
        record = audit.read(DATA / 'm1i_runs_audit.json')
        self.assertEqual(record['status'], 'PASS')
        self.assertEqual((record['raw_trials'], record['MN9_neuron_trials']), (575, 1150))
        for run, trials, units in [('a', 480, 91), ('b', 95, 242)]:
            r = record['runs'][run]
            self.assertEqual(r['raw_trials'], trials)
            self.assertEqual(r['poisson_unit_trials'], trials * units)
            self.assertEqual(len(r['input_trials']), trials)
            for row in r['input_trials']:
                self.assertEqual(len(row['poisson_event_counts']), units)
                self.assertEqual(len(row['declared_rates_hz']), units)
                self.assertEqual(sum(row['poisson_event_counts']), row['poisson_events'])
                self.assertEqual(row['seed'], 20260910 + row['trial'])
                self.assertTrue(all(count == 0 for count, rate in zip(row['poisson_event_counts'], row['declared_rates_hz']) if rate == 0))
        self.assertEqual(record['runs']['b']['kc_identical_input_pairs'], 5)
        self.assertEqual(record['runs']['b']['bilateral_bin_rows'], 1900)
        self.assertEqual(record['runs']['a']['AP_identical_shared_unit_trains'], 360)

    def test_report_regeneration_equality(self):
        text = report.DOCUMENT.read_text(encoding='utf-8')
        self.assertEqual(report.MARKER + text.split(report.MARKER, 1)[1], report.generate())

    def test_historical_ledger_rows_preserved(self):
        old = report_m1h.generate().split('## Male line closing decision — 2026-09-14', 1)[1]
        old_rows = [line for line in old.splitlines() if line.startswith('| [M1')]
        new = report.generate().split(report.LEDGER, 1)[1]
        new_rows = [line for line in new.splitlines() if line.startswith('| [M1')]
        self.assertEqual(len(old_rows), 7)
        self.assertEqual(new_rows[:7], old_rows)
        self.assertEqual(len(new_rows), 8)

    def test_existing_corrupted_report_rejected_without_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'report.md'
            content = report.generate().replace('3/5 positive levels', '4/5 positive levels')
            path.write_text(content, encoding='utf-8')
            with self.assertRaises(ValueError):
                report.check_or_append(path)
            self.assertEqual(path.read_text(encoding='utf-8'), content)

    def test_report_append_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'report.md'
            path.write_text('Prior history\n', encoding='utf-8')
            prefix = path.read_bytes()
            report.check_or_append(path)
            before = path.read_bytes()
            report.check_or_append(path)
            self.assertEqual(path.read_bytes(), before)
            self.assertTrue(before.startswith(prefix))


if __name__ == '__main__':
    unittest.main()
