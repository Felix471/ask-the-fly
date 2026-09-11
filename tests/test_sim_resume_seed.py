# SPDX-License-Identifier: MIT
"""D01 + D02: resuming a run validates the per-condition ledger (never zero-fills missing trials);
seeds derive from a stable global condition index (seed scheme v2), not from the batch slice."""

import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from sim import runner
from sim.grid import expand_grid_conditions, load_grid_levels
from sim.readout import mn9_rate

PROTOCOL = {
    "trial": {"duration_ms": 1000.0, "seed_rule": "seed = base_seed + trial + 1000 * condition_index, base_seed = 12345"},
    "readout": {"left": 1, "right": 2, "aggregation": "left_only"},
}
CELLS = {"mn9_left": 1, "mn9_right": 2}


def frame_with(trials, spikes_per_trial):
    return runner.spikes_dataframe([(t, {1: np.linspace(1, 999, spikes_per_trial)}) for t in trials])


class SeedScheme(unittest.TestCase):
    def test_grid_conditions_carry_a_stable_global_index(self):
        conditions = expand_grid_conditions(load_grid_levels())
        self.assertEqual([c["global_index"] for c in conditions], list(range(len(conditions))))

    def test_seed_is_independent_of_batch_size_and_worker_count(self):
        conditions = expand_grid_conditions(load_grid_levels())
        target = conditions[45]
        seeds = set()
        for batch_size in (40, 50, 7, 400):
            batches = [conditions[i:i + batch_size] for i in range(0, len(conditions), batch_size)]
            for batch in batches:
                for local_index, condition in enumerate(batch):
                    if condition is target:
                        seeds.add(runner.seed_for(12345, condition, 0, local_index))
        self.assertEqual(len(seeds), 1, f"seed changed with the batch slice: {seeds}")
        self.assertEqual(seeds.pop(), 12345 + 0 + 1000 * 45)
        self.assertEqual(runner.seed_scheme_for(conditions), "v2")

    def test_legacy_conditions_without_global_index_use_scheme_v1(self):
        legacy = [{"cond_id": "a"}, {"cond_id": "b"}]
        self.assertEqual(runner.seed_scheme_for(legacy), "v1")
        self.assertEqual(runner.seed_for(12345, legacy[1], 2, 1), 12345 + 2 + 1000 * 1)


class Ledger(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.out = Path(self.tmp.name)
        self.condition = {"cond_id": "c", "rates": {"sugar": 100.0}, "global_index": 3}

    def tearDown(self):
        self.tmp.cleanup()

    def expected(self, n_trials, duration=1000.0):
        return runner.ledger_expectation(self.condition, n_trials, duration, PROTOCOL, CELLS, ["sugar"])

    def write_run(self, trials, spikes=60, n_trials=None):
        frame = frame_with(trials, spikes)
        path = self.out / "c.parquet"
        frame.to_parquet(path, index=False)
        ledger = runner.write_ledger(self.out, self.expected(n_trials or len(trials)), sorted(trials), [12345 + t + 3000 for t in trials])
        return path, ledger

    def test_five_trials_reused_as_five_give_the_true_mean(self):
        path, _ = self.write_run([0, 1, 2, 3, 4])
        rates, n = runner.reuse_condition(self.condition, path, self.expected(5))
        self.assertEqual(n, 5)
        self.assertAlmostEqual(rates["left"]["mean"], 60.0)

    def test_five_trials_cannot_be_reused_as_thirty(self):
        path, _ = self.write_run([0, 1, 2, 3, 4])
        with self.assertRaises(runner.ResumeError) as ctx:
            runner.reuse_condition(self.condition, path, self.expected(30))
        self.assertIn("n_trials", str(ctx.exception))

    def test_thirty_trials_cannot_be_reused_as_five(self):
        path, _ = self.write_run(list(range(30)))
        with self.assertRaises(runner.ResumeError):
            runner.reuse_condition(self.condition, path, self.expected(5))

    def test_duration_change_is_rejected(self):
        path, _ = self.write_run([0, 1, 2, 3, 4])
        with self.assertRaises(runner.ResumeError) as ctx:
            runner.reuse_condition(self.condition, path, self.expected(5, duration=500.0))
        self.assertIn("duration", str(ctx.exception))

    def test_missing_ledger_is_rejected(self):
        frame_with([0, 1, 2, 3, 4], 60).to_parquet(self.out / "c.parquet", index=False)
        with self.assertRaises(runner.ResumeError) as ctx:
            runner.reuse_condition(self.condition, self.out / "c.parquet", self.expected(5))
        self.assertIn("ledger", str(ctx.exception))

    def test_incomplete_ledger_is_rejected_not_zero_filled(self):
        frame_with([0, 1, 2], 60).to_parquet(self.out / "c.parquet", index=False)
        runner.write_ledger(self.out, self.expected(5), [0, 1, 2], [1, 2, 3])
        with self.assertRaises(runner.ResumeError) as ctx:
            runner.reuse_condition(self.condition, self.out / "c.parquet", self.expected(5))
        self.assertIn("completed", str(ctx.exception))

    def test_corrupted_parquet_is_rejected(self):
        path, _ = self.write_run([0, 1, 2, 3, 4])
        path.write_bytes(b"not a parquet file")
        with self.assertRaises(runner.ResumeError):
            runner.reuse_condition(self.condition, path, self.expected(5))

    def test_all_zero_spike_trials_with_a_complete_ledger_are_a_valid_zero(self):
        path, _ = self.write_run([0, 1, 2, 3, 4], spikes=0)
        rates, n = runner.reuse_condition(self.condition, path, self.expected(5))
        self.assertEqual(n, 5)
        self.assertEqual(rates["left"]["mean"], 0.0)

    def test_readout_refuses_a_trial_count_the_ledger_does_not_cover(self):
        frame = frame_with([0, 1, 2, 3, 4], 60)
        with self.assertRaises(ValueError):
            mn9_rate(frame, PROTOCOL, 30, completed_trials=[0, 1, 2, 3, 4])
        rates = mn9_rate(frame, PROTOCOL, 5, completed_trials=[0, 1, 2, 3, 4])
        self.assertAlmostEqual(rates["left"]["mean"], 60.0)


if __name__ == "__main__":
    unittest.main()
