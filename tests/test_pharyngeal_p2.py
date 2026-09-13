# SPDX-License-Identifier: MIT
"""P2 design, paired statistics, and complete raw-record checks; no simulation."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

from sim.run_mn_readouts import sha256
from sim.run_pharyngeal_p2 import (
    groups_for,
    load_design,
    make_stimulation,
    paired_statistics,
    phase_p2_seed,
    result_identity,
    select_conditions,
    validate_paired_inputs,
    validate_result,
)


ROOT = Path(__file__).resolve().parents[1]
CHANNELS = ("sugar", "bitter", "water", "ir94e") + tuple(f"PhG{i}" for i in range(1, 17))
DOSES = (0, 60, 80, 120, 200)


def read_json(relative):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


class DesignTests(unittest.TestCase):
    def test_import_keeps_brian2_out_of_native_process(self):
        result = subprocess.run(
            [sys.executable, "-B", "-c", "import sys; import sim.run_pharyngeal_p2; "
             "assert 'brian2' not in sys.modules"],
            cwd=ROOT, text=True, capture_output=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_exact_thirteen_condition_design_is_390_not_330_runs(self):
        conditions = select_conditions()
        expected = [f"P2_{kind}_{dose}" for kind in ("PhG1", "PhG4") for dose in DOSES]
        expected += ["P2_pair_a_sugar", "P2_pair_b_PhG1", "P2_pair_c_both"]
        self.assertEqual([c["cond_id"] for c in conditions], expected)
        self.assertEqual([c["condition_index"] for c in conditions], list(range(13)))
        self.assertEqual([c["seed_index"] for c in conditions], list(range(10)) + [10, 10, 10])
        self.assertEqual(len(conditions) * 30, 390)

    def test_dose_conditions_only_drive_requested_type_at_requested_level(self):
        for condition, (kind, dose) in zip(
            select_conditions()[:10], ((k, d) for k in ("PhG1", "PhG4") for d in DOSES)
        ):
            with self.subTest(condition=condition["cond_id"]):
                self.assertEqual(tuple(condition["rates"]), CHANNELS)
                self.assertEqual(condition["rates"], {ch: dose if ch == kind else 0 for ch in CHANNELS})
                self.assertEqual(condition["monitored_types"], [kind])
                self.assertEqual(condition["driven_types"], [kind] if dose else [])
                self.assertFalse(condition["monitor_sugar"])

    def test_paired_three_conditions_have_both_source_sets_monitored(self):
        for condition, (sugar, phg1) in zip(select_conditions()[10:], ((120, 0), (0, 100), (120, 100))):
            with self.subTest(condition=condition["cond_id"]):
                expected = {ch: 0 for ch in CHANNELS}
                expected.update(sugar=sugar, PhG1=phg1)
                self.assertEqual(condition["rates"], expected)
                self.assertEqual(condition["monitored_types"], ["PhG1"])
                self.assertTrue(condition["monitor_sugar"])
                self.assertEqual(condition["driven_types"], ["PhG1"] if phg1 else [])

    def test_condition_definitions_have_no_shared_mutable_state(self):
        first = select_conditions()
        first[0]["rates"]["sugar"] = 1000
        first[0]["monitored_types"].clear()
        fresh = select_conditions()[0]
        self.assertEqual(fresh["rates"]["sugar"], 0)
        self.assertEqual(fresh["monitored_types"], ["PhG1"])

    def test_new_protocol_references_both_frozen_model_and_p1_inventory(self):
        spec = read_json("data/stim_protocol_pharyngeal_p2.json")
        self.assertEqual(spec["base_protocol"], "data/stim_protocol.json")
        self.assertEqual(spec["trial"]["n_trials"], 30)
        self.assertEqual(spec["conditions"], select_conditions())
        self.assertEqual(spec["n_poisson_units"], 151)
        self.assertNotIn("model", spec)

    def test_same_fixed_151_targets_and_order_as_p1_without_mutating_inputs(self):
        from sim.run_pharyngeal import make_stimulation as p1_stimulation
        spec = read_json("data/stim_protocol_pharyngeal.json")
        cells = read_json("data/cells.json")
        before_spec, before_cells = copy.deepcopy(spec), copy.deepcopy(cells)
        expanded, mapping = make_stimulation(spec, cells)
        prior_expanded, prior_mapping = p1_stimulation(spec, cells)
        self.assertEqual((expanded, mapping), (prior_expanded, prior_mapping))
        targets = [str(root) for name in mapping.values() for root in expanded["sets"][name]["ids"]]
        self.assertEqual((len(targets), len(set(targets))), (151, 151))
        self.assertEqual(tuple(mapping), CHANNELS)
        self.assertEqual((spec, cells), (before_spec, before_cells))

    def test_readonly_design_rejects_dose_levels_that_differ_from_frozen_grid(self):
        from sim import run_pharyngeal_p2 as runner
        original_load = runner.load_json
        grid = read_json("data/grid_levels.json")
        grid["levels"]["sugar"]["low"] = 61
        inherited = (read_json("data/stim_protocol_pharyngeal.json"),
                     read_json("data/stim_protocol.json"), read_json("data/cells.json"))

        def altered_grid(path):
            return grid if Path(path).name == "grid_levels.json" else original_load(path)

        with patch.object(runner.p1, "load_design", return_value=inherited), \
                patch.object(runner, "load_json", side_effect=altered_grid):
            with self.assertRaises(ValueError):
                load_design()

    def test_zero_dose_has_monitored_source_sanity_but_no_driven_group(self):
        p1 = read_json("data/stim_protocol_pharyngeal.json")
        protocol = read_json("data/stim_protocol.json")
        cells = read_json("data/cells.json")
        for index, count in ((0, 8), (5, 4)):
            groups = groups_for(p1, protocol, select_conditions()[index], cells)
            self.assertEqual(len(groups["monitored_pharyngeal"]), count)
            self.assertNotIn("driven_pharyngeal", groups)
            self.assertNotIn("driven_sugar", groups)
            self.assertNotIn("monitored_sugar", groups)
            self.assertEqual(sum(len(groups[f"CEM_{s}{i}"]) for s in ("L", "R") for i in range(1, 4)), 6)

    def test_paired_inventory_keeps_both_31_sources_in_all_three_conditions(self):
        p1 = read_json("data/stim_protocol_pharyngeal.json")
        protocol = read_json("data/stim_protocol.json")
        cells = read_json("data/cells.json")
        inventories = []
        for condition in select_conditions()[10:]:
            groups = groups_for(p1, protocol, condition, cells)
            self.assertEqual(len(groups["monitored_pharyngeal"]), 8)
            self.assertEqual(len(groups["monitored_sugar"]), 23)
            inventories.append(groups["monitored_pharyngeal"] + groups["monitored_sugar"])
        self.assertEqual(inventories[0], inventories[1])
        self.assertEqual(inventories[0], inventories[2])
        self.assertEqual(len(set(inventories[0])), 31)


class SeedTests(unittest.TestCase):
    def test_dose_and_paired_seeds_follow_explicit_published_grid_formula(self):
        for index in range(13):
            for trial in range(30):
                self.assertEqual(phase_p2_seed(index, trial), 20260910 + 1000 * min(index, 10) + trial)

    def test_same_thirty_seeds_in_each_paired_arm(self):
        arms = [[phase_p2_seed(index, trial) for trial in range(30)] for index in (10, 11, 12)]
        self.assertEqual(arms[0], arms[1])
        self.assertEqual(arms[0], arms[2])
        self.assertEqual(len(set(arms[0])), 30)

    def test_390_runs_use_330_unique_seeds_because_three_arms_are_paired(self):
        seeds = [phase_p2_seed(index, trial) for index in range(13) for trial in range(30)]
        self.assertEqual(len(seeds), 390)
        self.assertEqual(len(set(seeds)), 330)

    def test_rejects_invalid_condition_trial_or_seed(self):
        for value in (-1, 13, 19, 400, 1.0, True, "1", None):
            with self.subTest(condition=value), self.assertRaises((ValueError, TypeError)):
                phase_p2_seed(value, 0)
        for value in (-1, 30, 1.0, True, "1", None):
            with self.subTest(trial=value), self.assertRaises((ValueError, TypeError)):
                phase_p2_seed(0, value)
        for value in (1.0, True, "1", None):
            with self.subTest(seed=value), self.assertRaises((ValueError, TypeError)):
                phase_p2_seed(0, 0, base_seed=value)

    def test_custom_base_seed(self):
        self.assertEqual(phase_p2_seed(12, 29, base_seed=7), 10036)


class PairedStatisticsTests(unittest.TestCase):
    def test_ratio_is_mean_of_thirty_trial_ratios_not_ratio_of_means(self):
        a = [1.0, 3.0] * 15
        b = [2.0] * 30
        c = [4.0, 6.0] * 15
        result = paired_statistics(a, b, c)
        self.assertEqual(result["ratio_values"], [4.0, 2.0] * 15)
        self.assertAlmostEqual(result["ratio_mean"], 3.0)
        self.assertAlmostEqual(result["ratio_sd"], 1.0)
        self.assertNotAlmostEqual(result["ratio_mean"], np.mean(c) / np.mean(a))
        self.assertEqual(result["ratio_defined_trials"], 30)
        self.assertEqual(result["ratio_total_trials"], 30)

    def test_any_zero_denominator_marks_overall_ratio_undefined_without_epsilon(self):
        a = [1.0] * 29 + [0.0]
        result = paired_statistics(a, [1.0] * 30, [2.0] * 30)
        self.assertIsNone(result["ratio_mean"])
        self.assertIsNone(result["ratio_sd"])
        self.assertEqual(result["ratio_defined_trials"], 29)
        self.assertEqual(result["ratio_total_trials"], 30)
        self.assertEqual(result["ratio_values"], [2.0] * 29 + [None])

    def test_all_silent_cem_ratio_is_undefined_and_zero_delta_is_only_numerical_equality(self):
        result = paired_statistics([0.0] * 30, [0.0] * 30, [0.0] * 30)
        self.assertIsNone(result["ratio_mean"])
        self.assertIsNone(result["ratio_sd"])
        self.assertEqual(result["ratio_defined_trials"], 0)
        self.assertEqual(result["delta_mean_hz"], 0.0)
        self.assertEqual(result["delta_sd_hz"], 0.0)
        self.assertEqual(result["relation"], "equal")
        self.assertEqual(result["equal_sum_trials"], 30)

    def test_delta_population_sd_and_all_trial_sign_counts(self):
        a, b = [2.0] * 30, [1.0] * 30
        c = [2.0, 3.0, 7.0] * 10
        result = paired_statistics(a, b, c)
        self.assertEqual(result["delta_values_hz"], [-1.0, 0.0, 4.0] * 10)
        self.assertAlmostEqual(result["delta_mean_hz"], 1.0)
        self.assertAlmostEqual(result["delta_sd_hz"], np.std([-1.0, 0.0, 4.0], ddof=0))
        self.assertEqual((result["above_sum_trials"], result["equal_sum_trials"], result["below_sum_trials"]), (10, 10, 10))
        self.assertEqual(result["relation"], "superadditive")

    def test_negative_and_exact_equal_mean_relations_are_not_significance_tests(self):
        short = paired_statistics([2.0] * 30, [2.0] * 30, [3.0] * 30)
        equal = paired_statistics([2.0] * 30, [1.0] * 30, [2.0, 4.0] * 15)
        self.assertEqual(short["relation"], "falls short")
        self.assertEqual(short["below_sum_trials"], 30)
        self.assertEqual(equal["relation"], "equal")
        self.assertEqual(equal["equal_sum_trials"], 0)
        self.assertEqual(equal["delta_sd_hz"], 1.0)

    def test_rejects_any_incomplete_misaligned_nonfinite_or_negative_vector(self):
        invalid = ([1.0] * 29, [1.0] * 31, [[1.0]] * 30,
                   [1.0] * 29 + [float("nan")], [1.0] * 29 + [float("inf")],
                   [1.0] * 29 + [-1.0])
        for values in invalid:
            for arm in range(3):
                inputs = [[1.0] * 30 for _ in range(3)]
                inputs[arm] = values
                with self.subTest(arm=arm, values=repr(values[-1])), self.assertRaises((ValueError, TypeError)):
                    paired_statistics(*inputs)


class RawResultTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="askfly_phg_p2_test_")
        self.addCleanup(self.temporary.cleanup)
        self.path = Path(self.temporary.name) / "P2_PhG1_0.npz"
        self.spec = read_json("data/stim_protocol_pharyngeal.json")
        self.protocol = read_json("data/stim_protocol.json")
        self.cells = read_json("data/cells.json")
        self.condition = select_conditions()[0]
        self.expected = result_identity(self.condition, {"fixture": "synthetic, no simulation"})
        self.mn_rows = [{"Body_ID": row["Body_ID"], "Root_Side": row["Root_Side"],
                         "Type": row["Type"], "Target_Muscle": row["Target_Muscle"],
                         "role": "MN_readout", "input_hz": 0} for row in self.spec["readout_neurons"]]
        self.source_rows = [{"Body_ID": row["Body_ID"], "Root_Side": row["Root_Side"],
                             "Type": row["Type"], "Target_Muscle": "", "role": "monitored_pharyngeal", "input_hz": 0}
                            for row in self.spec["pharyngeal_neurons"] if row["Type"] == "PhG1"]
        descriptions = self.mn_rows + self.source_rows
        groups = groups_for(self.spec, self.protocol, self.condition, self.cells)
        individuals, grouped = [], []
        for trial in range(30):
            prefix = {"condition_id": self.condition["cond_id"], "condition_index": 0,
                      "trial": trial, "seed": 20260910 + trial}
            individuals.extend({**prefix, **row, "spike_count": 0, "rate_hz": 0.0,
                                "first_spike_ms": None} for row in descriptions)
            grouped.extend({**prefix, "readout": name, "n_neurons": len(roots),
                            "spike_count": 0, "total_rate_hz": 0.0, "rate_hz": 0.0,
                            "first_spike_ms": None} for name, roots in groups.items())
        self.raw = {
            "flywire_id": np.array([], dtype=np.int64), "t_ms": np.array([], dtype=np.float64),
            "trial": np.array([], dtype=np.int64), "seeds": np.array(self.expected["seeds"], dtype=np.int64),
            "completed_trials": np.arange(30, dtype=np.int64),
            "saved_neuron_ids": np.array([int(row["Body_ID"]) for row in descriptions], dtype=np.int64),
            "poisson_target_id": np.array([], dtype=np.int64), "poisson_t_ms": np.array([], dtype=np.float64),
            "poisson_trial": np.array([], dtype=np.int64),
            "poisson_saved_target_ids": np.array([int(row["Body_ID"]) for row in self.source_rows], dtype=np.int64),
        }
        self.saved = {"identity": copy.deepcopy(self.expected), "completed_trials": list(range(30)),
                      "individual": individuals, "grouped": grouped}
        self.write_raw()

    def write_raw(self):
        np.savez_compressed(self.path, **self.raw)
        self.saved["spikes_sha256"] = sha256(self.path)

    def validate(self):
        return validate_result(self.saved, self.path, self.expected, self.spec,
                               self.protocol, self.cells, self.condition)

    def test_complete_zero_dose_is_silence_not_missing_data(self):
        self.assertEqual(self.validate(), self.saved)
        self.assertEqual(len(self.saved["individual"]), 30 * (12 + 8))

    def test_missing_trial_from_ledger_is_not_silence(self):
        self.saved["completed_trials"].pop()
        with self.assertRaises(ValueError):
            self.validate()

    def test_missing_or_duplicate_raw_completion_marker_is_rejected(self):
        for markers in (np.arange(29, dtype=np.int64), np.array(list(range(29)) + [28], dtype=np.int64)):
            self.raw["completed_trials"] = markers
            self.write_raw()
            with self.subTest(markers=markers.tolist()), self.assertRaises(ValueError):
                self.validate()

    def test_wrong_seed_is_rejected_even_with_updated_hash(self):
        self.raw["seeds"][0] += 1
        self.write_raw()
        with self.assertRaises(ValueError):
            self.validate()

    def test_identity_tampering_is_rejected(self):
        self.saved["identity"]["condition_id"] = "P2_PhG4_0"
        with self.assertRaises(ValueError):
            self.validate()

    def test_missing_silent_neuron_or_source_inventory_is_rejected(self):
        original = copy.deepcopy(self.raw)
        for key in ("saved_neuron_ids", "poisson_saved_target_ids"):
            self.raw = copy.deepcopy(original)
            self.raw[key] = self.raw[key][:-1]
            self.write_raw()
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.validate()

    def test_float_id_arrays_are_rejected_even_when_all_trials_are_silent(self):
        original = copy.deepcopy(self.raw)
        for key in ("flywire_id", "saved_neuron_ids", "poisson_target_id", "poisson_saved_target_ids"):
            self.raw = copy.deepcopy(original)
            self.raw[key] = self.raw[key].astype(np.float64)
            self.write_raw()
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.validate()

    def test_missing_or_changed_derived_metrics_are_rejected(self):
        original = copy.deepcopy(self.saved)
        self.saved["individual"].pop()
        with self.assertRaises(ValueError):
            self.validate()
        self.saved = original
        self.saved["grouped"][0]["rate_hz"] = 1.0
        with self.assertRaises(ValueError):
            self.validate()

    def test_poisson_event_on_zero_driven_channel_is_rejected(self):
        self.raw["poisson_target_id"] = self.raw["poisson_saved_target_ids"][:1]
        self.raw["poisson_t_ms"] = np.array([100.0], dtype=np.float64)
        self.raw["poisson_trial"] = np.array([0], dtype=np.int64)
        self.write_raw()
        with self.assertRaises(ValueError):
            self.validate()

    def test_out_of_range_neuron_and_poisson_event_times_are_rejected(self):
        original = copy.deepcopy(self.raw)
        for ids_key, times_key, trial_key, saved_key in (
            ("flywire_id", "t_ms", "trial", "saved_neuron_ids"),
            ("poisson_target_id", "poisson_t_ms", "poisson_trial", "poisson_saved_target_ids"),
        ):
            for bad_time in (-0.1, 1000.1, float("nan"), float("inf")):
                self.raw = copy.deepcopy(original)
                self.raw[ids_key] = self.raw[saved_key][:1]
                self.raw[times_key] = np.array([bad_time], dtype=np.float64)
                self.raw[trial_key] = np.array([0], dtype=np.int64)
                self.write_raw()
                with self.subTest(key=times_key, time=bad_time), self.assertRaises(ValueError):
                    self.validate()

    def test_spike_trial_index_cannot_exceed_thirty_trials(self):
        self.raw["flywire_id"] = self.raw["saved_neuron_ids"][:1]
        self.raw["t_ms"] = np.array([100.0], dtype=np.float64)
        self.raw["trial"] = np.array([30], dtype=np.int64)
        self.write_raw()
        with self.assertRaises(ValueError):
            self.validate()

    def test_hash_mismatch_is_not_swallowed(self):
        self.saved["spikes_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            self.validate()


class PairedInputTests(unittest.TestCase):
    """Same seed labels alone are insufficient: recorded source events must match."""

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="askfly_phg_p2_paired_")
        self.addCleanup(self.temporary.cleanup)
        self.out = Path(self.temporary.name)
        spec = read_json("data/stim_protocol_pharyngeal.json")
        cells = read_json("data/cells.json")
        self.phg_ids = [row["Body_ID"] for row in spec["pharyngeal_neurons"] if row["Type"] == "PhG1"]
        self.sugar_ids = [str(root) for root in cells["sets"]["sugar"]["ids"]]
        self.results, self.arrays = [], []
        for condition in select_conditions()[10:]:
            identity = result_identity(condition, {"fixture": "synthetic, no simulation"})
            rows = [{"Body_ID": root, "role": role}
                    for roots, role in ((self.phg_ids, "monitored_pharyngeal"),
                                        (self.sugar_ids, "monitored_sugar")) for root in roots]
            events = []
            for trial in range(30):
                if condition["rates"]["sugar"]:
                    events += [(int(root), 10.0 + index, trial) for index, root in enumerate(self.sugar_ids)]
                if condition["rates"]["PhG1"]:
                    events += [(int(root), 50.0 + index, trial) for index, root in enumerate(self.phg_ids)]
            array = {
                "poisson_target_id": np.array([r[0] for r in events], dtype=np.int64),
                "poisson_t_ms": np.array([r[1] for r in events], dtype=np.float64),
                "poisson_trial": np.array([r[2] for r in events], dtype=np.int64),
                "poisson_saved_target_ids": np.array(self.phg_ids + self.sugar_ids, dtype=np.int64),
                "seeds": np.array(identity["seeds"], dtype=np.int64),
                "completed_trials": np.arange(30, dtype=np.int64),
            }
            self.results.append({"identity": identity, "individual": rows})
            self.arrays.append(array)
        self.write_raw()

    def write_raw(self):
        for result, arrays in zip(self.results, self.arrays):
            path = self.out / f"{result['identity']['condition_id']}.npz"
            np.savez_compressed(path, **arrays)
            result["spikes_sha256"] = sha256(path)

    def validate(self):
        return validate_paired_inputs(self.results, self.out)

    def test_all_930_target_trials_have_identical_active_source_events(self):
        result = self.validate()
        self.assertEqual(result["n_paired_trials"], 30)
        self.assertIs(result["sugar_a_c_identical"], True)
        self.assertIs(result["PhG1_b_c_identical"], True)
        self.assertEqual(result["n_sugar_neuron_trials"], 690)
        self.assertEqual(result["n_PhG1_neuron_trials"], 240)

    def test_changed_sugar_event_in_combined_arm_is_rejected(self):
        self.arrays[2]["poisson_t_ms"][0] += 0.1
        self.write_raw()
        with self.assertRaises(ValueError):
            self.validate()

    def test_changed_phg_event_in_combined_arm_is_rejected(self):
        index = np.flatnonzero(self.arrays[2]["poisson_target_id"] == int(self.phg_ids[0]))[0]
        self.arrays[2]["poisson_t_ms"][index] += 0.1
        self.write_raw()
        with self.assertRaises(ValueError):
            self.validate()

    def test_matching_event_counts_without_matching_times_are_not_paired(self):
        self.arrays[0]["poisson_t_ms"] += 0.1
        self.write_raw()
        with self.assertRaises(ValueError):
            self.validate()

    def test_same_sources_with_different_declared_seeds_are_rejected(self):
        self.results[1]["identity"]["seeds"][0] += 1
        self.write_raw()
        with self.assertRaises(ValueError):
            self.validate()

    def test_inactive_phg_input_in_sugar_only_arm_is_rejected(self):
        array = self.arrays[0]
        array["poisson_target_id"] = np.append(array["poisson_target_id"], int(self.phg_ids[0]))
        array["poisson_t_ms"] = np.append(array["poisson_t_ms"], 100.0)
        array["poisson_trial"] = np.append(array["poisson_trial"], 0)
        self.write_raw()
        with self.assertRaises(ValueError):
            self.validate()

    def test_missing_paired_arm_is_rejected(self):
        self.results.pop()
        with self.assertRaises(ValueError):
            self.validate()


if __name__ == "__main__":
    unittest.main()
