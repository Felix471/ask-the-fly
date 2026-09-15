# SPDX-License-Identifier: MIT
"""Pure C2 analysis checks; no Brian2 simulation or vendor inputs required."""

from __future__ import annotations

import math
import subprocess
import sys
import unittest
from pathlib import Path

from sim.grid import EXPECTED_DIMENSIONS, expand_grid_conditions, load_grid_levels
from sim.run_mn_readouts import (
    published_grid_seed,
    ratio_of_means,
    select_conditions,
    summarize_trials,
)


SELECTED_COORDINATES = {
    (0, 0, 0, 0),
    (0, 0, 0, 200),
    (120, 0, 0, 0),
    (120, 60, 0, 0),
    (120, 100, 0, 0),
    (120, 160, 0, 0),
    (120, 0, 0, 200),
    (0, 0, 240, 0),
    (0, 30, 240, 0),
    (200, 100, 60, 200),
    (200, 100, 0, 200),
    (60, 0, 0, 0),
    (80, 0, 0, 0),
}


class AnalysisImportTests(unittest.TestCase):
    def test_import_does_not_load_brian2(self):
        result = subprocess.run(
            [
                sys.executable,
                "-B",
                "-c",
                "import sys; import sim.run_mn_readouts; "
                "assert 'brian2' not in sys.modules, 'Brian2 imported outside worker'",
            ],
            cwd=Path(__file__).resolve().parents[1],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


class PublishedGridSeedTests(unittest.TestCase):
    def test_matches_published_batch_local_scheme_not_new_global_scheme(self):
        self.assertEqual(published_grid_seed(0, 0), 20260910)
        self.assertEqual(published_grid_seed(39, 29), 20299939)
        self.assertEqual(published_grid_seed(40, 0), 20260910)
        self.assertEqual(published_grid_seed(399, 29), 20299939)

    def test_every_batch_reuses_the_corresponding_thirty_seeds(self):
        for batch_start in range(0, 400, 40):
            self.assertEqual(
                [published_grid_seed(batch_start + 17, trial) for trial in range(30)],
                list(range(20277910, 20277940)),
            )

    def test_explicit_base_seed(self):
        self.assertEqual(published_grid_seed(82, 7, base_seed=1000), 3007)

    def test_rejects_indices_outside_frozen_grid(self):
        for index in (-1, 400, 1000):
            with self.subTest(index=index), self.assertRaises((ValueError, TypeError)):
                published_grid_seed(index, 0)

    def test_rejects_trial_indices_outside_thirty_trials(self):
        for trial in (-1, 30, 1000):
            with self.subTest(trial=trial), self.assertRaises((ValueError, TypeError)):
                published_grid_seed(0, trial)

    def test_does_not_silently_coerce_fractional_or_boolean_indices(self):
        for value in (0.0, 1.5, True, False, "1", None):
            with self.subTest(index=value), self.assertRaises((ValueError, TypeError)):
                published_grid_seed(value, 0)
            with self.subTest(trial=value), self.assertRaises((ValueError, TypeError)):
                published_grid_seed(0, value)


class SelectedConditionsTests(unittest.TestCase):
    def test_exactly_all_thirteen_owner_selected_cells(self):
        conditions = select_conditions()
        coordinates = [
            tuple(condition["rates"][dimension] for dimension in EXPECTED_DIMENSIONS)
            for condition in conditions
        ]
        self.assertEqual(len(conditions), 13)
        self.assertEqual(len(set(coordinates)), 13)
        self.assertEqual(set(coordinates), SELECTED_COORDINATES)

    def test_preserves_canonical_cell_ids_and_original_global_indices(self):
        canonical = {
            condition["cond_id"]: condition
            for condition in expand_grid_conditions(load_grid_levels())
        }
        for selected in select_conditions():
            with self.subTest(cell_id=selected["cond_id"]):
                original = canonical[selected["cond_id"]]
                self.assertEqual(selected["global_index"], original["global_index"])
                self.assertEqual(selected["rates"], original["rates"])
                self.assertEqual(selected["levels"], original["levels"])

    def test_selection_is_deterministic(self):
        self.assertEqual(select_conditions(), select_conditions())


class TrialSummaryTests(unittest.TestCase):
    def test_mean_population_sd_and_conditional_latency_median(self):
        actual = summarize_trials([0, 2, 4], [None, 0, 10])
        self.assertEqual(actual["n_trials"], 3)
        self.assertEqual(actual["rate_mean_hz"], 2)
        self.assertAlmostEqual(actual["rate_std_hz"], math.sqrt(8 / 3))
        self.assertEqual(actual["latency_median_ms"], 5)
        self.assertEqual(actual["active_trials"], 2)
        self.assertEqual(actual["silent_trials"], 1)

    def test_all_silent_latency_is_missing_not_zero(self):
        actual = summarize_trials([0] * 30, [None] * 30)
        self.assertEqual(actual["rate_mean_hz"], 0)
        self.assertEqual(actual["rate_std_hz"], 0)
        self.assertIsNone(actual["latency_median_ms"])
        self.assertEqual(actual["active_trials"], 0)
        self.assertEqual(actual["silent_trials"], 30)

    def test_zero_latency_is_a_real_spike_not_a_missing_value(self):
        actual = summarize_trials([1, 0, 1], [0, None, 0])
        self.assertEqual(actual["latency_median_ms"], 0)
        self.assertEqual(actual["active_trials"], 2)
        self.assertEqual(actual["silent_trials"], 1)

    def test_odd_latency_median_excludes_silent_trials_and_sorts(self):
        actual = summarize_trials([1, 0, 1, 1], [900, None, 10, 20])
        self.assertEqual(actual["latency_median_ms"], 20)

    def test_single_trial_population_sd_is_zero(self):
        actual = summarize_trials([2], [999.99])
        self.assertEqual(actual["rate_std_hz"], 0)
        self.assertEqual(actual["latency_median_ms"], 999.99)

    def test_rejects_empty_or_mismatched_input(self):
        for rates, latencies in (([], []), ([1], []), ([], [None]), ([1], [2, 3])):
            with self.subTest(rates=rates, latencies=latencies):
                with self.assertRaises((ValueError, TypeError)):
                    summarize_trials(rates, latencies)

    def test_rejects_negative_or_nonfinite_rates(self):
        for value in (-1, math.inf, -math.inf, math.nan):
            with self.subTest(rate=value), self.assertRaises((ValueError, TypeError)):
                summarize_trials([value], [None])

    def test_rejects_latency_outside_the_half_open_trial_window(self):
        for value in (-0.001, 1000, 1000.1, math.inf, -math.inf, math.nan):
            with self.subTest(latency=value), self.assertRaises((ValueError, TypeError)):
                summarize_trials([1], [value])


class BitterRatioTests(unittest.TestCase):
    def test_ratio_of_means_is_not_mean_of_paired_ratios(self):
        actual = ratio_of_means([1] * 30, [1, 100] * 15)
        self.assertAlmostEqual(actual, 1 / 50.5)
        self.assertNotAlmostEqual(actual, (1 + 0.01) / 2)

    def test_pairing_is_irrelevant_to_ratio_of_means(self):
        numerator = list(range(30))
        baseline = list(range(1, 31))
        self.assertEqual(
            ratio_of_means(numerator, baseline),
            ratio_of_means(list(reversed(numerator)), baseline),
        )

    def test_zero_baseline_mean_is_undefined_even_if_both_silent(self):
        self.assertIsNone(ratio_of_means([1] * 30, [0] * 30))
        self.assertIsNone(ratio_of_means([0] * 30, [0] * 30))

    def test_silent_numerator_and_positive_baseline_has_zero_ratio(self):
        self.assertEqual(ratio_of_means([0] * 30, [2] * 30), 0)

    def test_identical_nonzero_inputs_have_unit_ratio(self):
        self.assertEqual(ratio_of_means(list(range(30)), list(range(30))), 1)

    def test_each_ratio_input_requires_exactly_thirty_trials(self):
        for length in (0, 1, 29, 31):
            with self.subTest(numerator_length=length):
                with self.assertRaises((ValueError, TypeError)):
                    ratio_of_means([1] * length, [1] * 30)
            with self.subTest(baseline_length=length):
                with self.assertRaises((ValueError, TypeError)):
                    ratio_of_means([1] * 30, [1] * length)

    def test_rejects_negative_or_nonfinite_rates_in_either_input(self):
        for value in (-1, math.inf, -math.inf, math.nan):
            invalid = [1] * 29 + [value]
            with self.subTest(numerator=value), self.assertRaises((ValueError, TypeError)):
                ratio_of_means(invalid, [1] * 30)
            with self.subTest(baseline=value), self.assertRaises((ValueError, TypeError)):
                ratio_of_means([1] * 30, invalid)


if __name__ == "__main__":
    unittest.main()
