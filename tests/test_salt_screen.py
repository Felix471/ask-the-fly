# SPDX-License-Identifier: MIT
"""S1 source, layout, paired-input, and raw-record checks; never simulate."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

from sim.run_mn_readouts import sha256
from sim.run_salt_screen import (
    _individual_descriptions,
    effective_rates,
    groups_for,
    make_stimulation,
    paired_statistics,
    phase_s1_seed,
    result_identity,
    select_conditions,
    source_groups,
    validate_paired_inputs,
    validate_result,
)
from tests.test_pharyngeal import synthetic_design


ROOT = Path(__file__).resolve().parents[1]
CONDITION_IDS = ("S1_baseline", "S1_LB3b_25", "S1_LB3d_29", "S1_LB3d_22",
                 "S1_sugar_120", "S1_sugar_120_LB3d_22")
SOURCE_CHANNELS = ("LB3b25", "LB3d29", "LB3d22", "frozen_sugar23")


def read_json(relative):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def fixture():
    spec, cells = synthetic_design()
    sugar = cells["sets"]["sugar"]["ids"]
    b_ids = [sugar[0]] + [720575940000002000 + i for i in range(24)]
    d_ids = sugar[1:8] + [720575940000003000 + i for i in range(22)]
    rows = []
    for kind, ids, left_count in (("LB3b", b_ids, 13), ("LB3d", d_ids, 15)):
        rows += [{"Body_ID": str(root), "Root_Side": "L" if i < left_count else "R",
                  "Type": "LB3", "Subtype": kind, "Entry_Nerve": "labial nerve",
                  "in_v783": True} for i, root in enumerate(ids)]
    spec["salt_neurons"] = rows
    spec["readout_neurons"] = [row for row in read_json("data/mn_readout_ids.json")["neurons"]
                               if row["Type"] in {"MN9", "MN11D", "MN11V"}]
    return spec, read_json("data/stim_protocol.json"), cells


class ConditionTests(unittest.TestCase):
    def test_native_import_does_not_load_brian2(self):
        result = subprocess.run(
            [sys.executable, "-B", "-c", "import sys; import sim.run_salt_screen; "
             "assert 'brian2' not in sys.modules"], cwd=ROOT, text=True,
            capture_output=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_exact_six_condition_order_and_sixty_trials(self):
        conditions = select_conditions()
        self.assertEqual(tuple(c["cond_id"] for c in conditions), CONDITION_IDS)
        self.assertEqual([c["condition_index"] for c in conditions], list(range(6)))
        self.assertEqual([c["seed_index"] for c in conditions], [0, 1, 2, 2, 3, 3])
        self.assertEqual(len(conditions) * 10, 60)

    def test_each_condition_has_exact_authorised_logical_drive(self):
        active = ({}, {"LB3b25": 100}, {"LB3d29": 100}, {"LB3d22": 100},
                  {"frozen_sugar23": 120}, {"frozen_sugar23": 120, "LB3d22": 100})
        for condition, selected in zip(select_conditions(), active):
            expected = dict.fromkeys(SOURCE_CHANNELS, 0)
            expected.update(selected)
            self.assertEqual(condition["group_rates"], expected)

    def test_definitions_are_not_mutably_shared(self):
        conditions = select_conditions()
        conditions[1]["group_rates"]["LB3b25"] = 300
        self.assertEqual(select_conditions()[1]["group_rates"]["LB3b25"], 100)

    def test_referencing_protocol_uses_unchanged_base_and_ten_trials(self):
        spec = read_json("data/stim_protocol_salt.json")
        self.assertEqual(spec["base_protocol"], "data/stim_protocol.json")
        self.assertEqual(spec["p1_protocol"], "data/stim_protocol_pharyngeal.json")
        self.assertEqual(spec["trial"]["n_trials"], 10)
        self.assertEqual(spec["conditions"], select_conditions())
        self.assertNotIn("model", spec)
        self.assertEqual(len(spec["salt_neurons"]), 54)
        self.assertEqual({r["Type"] for r in spec["salt_neurons"]}, {"LB3"})
        self.assertEqual({r["Subtype"] for r in spec["salt_neurons"]}, {"LB3b", "LB3d"})


class SeedTests(unittest.TestCase):
    def test_exact_grid_formula_and_shared_pair_indices(self):
        for index, seed_index in enumerate((0, 1, 2, 2, 3, 3)):
            for trial in range(10):
                self.assertEqual(phase_s1_seed(index, trial), 20260910 + 1000 * seed_index + trial)
        seeds = [phase_s1_seed(i, t) for i in range(6) for t in range(10)]
        self.assertEqual((len(seeds), len(set(seeds))), (60, 40))

    def test_custom_base_seed(self):
        self.assertEqual(phase_s1_seed(5, 9, base_seed=7), 3016)

    def test_rejects_out_of_range_or_lossy_arguments(self):
        for value in (-1, 6, 10, 1.0, True, "1", None):
            with self.subTest(condition=value), self.assertRaises((ValueError, TypeError)):
                phase_s1_seed(value, 0)
        for value in (-1, 10, 30, 1.0, True, "1", None):
            with self.subTest(trial=value), self.assertRaises((ValueError, TypeError)):
                phase_s1_seed(0, value)
        for value in (1.0, True, "1", None):
            with self.subTest(base=value), self.assertRaises((ValueError, TypeError)):
                phase_s1_seed(0, 0, base_seed=value)


class MembershipAndLayoutTests(unittest.TestCase):
    def test_exact_source_groups_and_removed_overlap(self):
        spec, _, cells = fixture()
        groups = source_groups(spec, cells)
        self.assertEqual({key: len(groups[key]) for key in SOURCE_CHANNELS + ("overlap7",)},
                         {"LB3b25": 25, "LB3d29": 29, "LB3d22": 22, "frozen_sugar23": 23, "overlap7": 7})
        self.assertEqual(set(groups["overlap7"]), set(map(str, cells["sets"]["sugar"]["ids"][1:8])))
        self.assertEqual(set(groups["LB3d22"]), set(groups["LB3d29"]) - set(groups["frozen_sugar23"]))
        self.assertTrue(set(groups["LB3d22"]).isdisjoint(groups["frozen_sugar23"]))
        self.assertEqual(len(set(groups["LB3b25"]) & set(groups["frozen_sugar23"])), 1)
        self.assertEqual(len(set().union(*(set(v) for v in groups.values()))), 69)

    def test_all_exact_bilateral_source_ids_are_preserved(self):
        spec, _, cells = fixture()
        groups = source_groups(spec, cells)
        for kind, key, expected in (("LB3b", "LB3b25", {"L": 13, "R": 12}),
                                    ("LB3d", "LB3d29", {"L": 15, "R": 14})):
            selected = [r for r in spec["salt_neurons"] if r["Subtype"] == kind]
            self.assertEqual(set(groups[key]), {r["Body_ID"] for r in selected})
            self.assertEqual({side: sum(r["Root_Side"] == side for r in selected) for side in expected}, expected)

    def test_layout_is_197_unique_singleton_units_with_p1_first_151_unchanged(self):
        from sim.run_pharyngeal import make_stimulation as p1_stimulation
        spec, _, cells = fixture()
        prior_cells, prior_channels = p1_stimulation(spec, cells)
        prior_roots = [str(root) for name in prior_channels.values() for root in prior_cells["sets"][name]["ids"]]
        expanded, channels = make_stimulation(spec, cells)
        self.assertEqual(len(channels), 197)
        self.assertTrue(all(len(expanded["sets"][name]["ids"]) == 1 for name in channels.values()))
        roots = [str(expanded["sets"][name]["ids"][0]) for name in channels.values()]
        self.assertEqual(roots[:151], prior_roots)
        self.assertEqual(roots[151:], sorted(set(r["Body_ID"] for r in spec["salt_neurons"]) - set(prior_roots), key=int))
        self.assertEqual(len(set(roots)), 197)
        self.assertEqual(list(channels), [f"s1_{root}" for root in roots])

    def test_layout_and_grouping_do_not_modify_source_or_frozen_nested_values(self):
        spec, _, cells = fixture()
        before = copy.deepcopy((spec, cells))
        source_groups(spec, cells)
        expanded, _ = make_stimulation(spec, cells)
        expanded["sets"]["sugar"]["ids"].clear()
        expanded["unrelated"]["keep"].append(100)
        self.assertEqual((spec, cells), before)

    def test_all_silent_baseline_still_monitors_69_sources_and_six_mns_once(self):
        spec, protocol, cells = fixture()
        rows = _individual_descriptions(spec, cells, select_conditions()[0])
        self.assertEqual(len(rows), 75)
        self.assertEqual(len({r["Body_ID"] for r in rows}), 75)
        self.assertEqual(sum(r["role"] == "MN_readout" for r in rows), 6)
        self.assertEqual(sum(r["role"] == "source_GRN" for r in rows), 69)
        self.assertTrue(all(r["input_hz"] == 0 for r in rows))
        self.assertEqual({r["Target_Muscle"] for r in rows if r["role"] == "MN_readout"}, {"9", "11D", "11V"})
        groups = groups_for(spec, protocol, select_conditions()[0], cells)
        self.assertNotIn("CEM", groups)
        self.assertNotIn("actual_driven_union", groups)
        self.assertEqual([len(groups[g]) for g in ("MN9_L", "MN9_R", "MN11D", "MN11V")], [1, 1, 2, 2])

    def test_source_inventory_remains_identical_across_all_six_conditions(self):
        spec, _, cells = fixture()
        inventories = [[r["Body_ID"] for r in _individual_descriptions(spec, cells, c)] for c in select_conditions()]
        self.assertTrue(all(roots == inventories[0] for roots in inventories))

    def test_invalid_source_ids_counts_duplicates_or_absence_from_v783_are_rejected(self):
        for mutation in ("missing", "duplicate", "float", "scientific", "missing_v783", "wrong_subtype"):
            spec, _, cells = fixture()
            if mutation == "missing":
                spec["salt_neurons"].pop()
            elif mutation == "duplicate":
                spec["salt_neurons"][1]["Body_ID"] = spec["salt_neurons"][0]["Body_ID"]
            elif mutation == "float":
                spec["salt_neurons"][0]["Body_ID"] = float(spec["salt_neurons"][0]["Body_ID"])
            elif mutation == "scientific":
                spec["salt_neurons"][0]["Body_ID"] = "7.20575940000001e17"
            elif mutation == "missing_v783":
                spec["salt_neurons"][0]["in_v783"] = False
            else:
                spec["salt_neurons"][0]["Subtype"] = "LB3c"
            with self.subTest(mutation=mutation), self.assertRaises((ValueError, TypeError)):
                source_groups(spec, cells)

    def test_effective_singleton_rates_activate_only_the_authorised_union(self):
        spec, protocol, cells = fixture()
        populations = source_groups(spec, cells)
        expected_counts = (0, 25, 29, 22, 23, 45)
        for condition, count in zip(select_conditions(), expected_counts):
            expected = {}
            for group, hz in condition["group_rates"].items():
                if hz:
                    expected.update({f"s1_{root}": hz for root in populations[group]})
            rates = effective_rates(spec, cells, condition)
            self.assertEqual(len(rates), 197)
            self.assertEqual({key: value for key, value in rates.items() if value}, expected)
            self.assertEqual(sum(value > 0 for value in rates.values()), count)
            groups = groups_for(spec, protocol, condition, cells)
            if count:
                self.assertEqual(len(groups["actual_driven_union"]), count)
                self.assertEqual(len(set(groups["actual_driven_union"])), count)

    def test_combo_gives_sugar_overlap7_only_sugar120_not_double_drive_or_zero_refractory(self):
        spec, _, cells = fixture()
        populations = source_groups(spec, cells)
        rates = effective_rates(spec, cells, select_conditions()[5])
        self.assertTrue(all(rates[f"s1_{root}"] == 120 for root in populations["overlap7"]))
        self.assertTrue(all(rates[f"s1_{root}"] == 100 for root in populations["LB3d22"]))

    def test_unauthorised_positive_overlap_is_rejected_not_summed_or_last_writer_wins(self):
        spec, _, cells = fixture()
        for active in (("frozen_sugar23", "LB3d29"), ("frozen_sugar23", "LB3b25"), ("LB3d22", "LB3d29")):
            condition = copy.deepcopy(select_conditions()[0])
            for key in active:
                condition["group_rates"][key] = 100
            with self.subTest(active=active), self.assertRaises(ValueError):
                effective_rates(spec, cells, condition)


class PairStatisticsTests(unittest.TestCase):
    def test_trialwise_ratio_mean_population_sd_and_ratio_of_means_are_distinguished(self):
        result = paired_statistics([1.0, 3.0] * 5, [4.0, 6.0] * 5)
        self.assertEqual(result["ratio_mean"], 3.0)
        self.assertEqual(result["ratio_sd"], 1.0)
        self.assertEqual(result["ratio_of_means"], 2.5)
        self.assertEqual(result["ratio_defined_trials"], 10)
        self.assertEqual(result["delta_mean_hz"], 3.0)
        self.assertEqual(result["delta_sd_hz"], 0.0)

    def test_any_zero_trial_denominator_makes_trialwise_summary_undefined(self):
        result = paired_statistics([1.0] * 9 + [0.0], [2.0] * 10)
        self.assertIsNone(result["ratio_mean"])
        self.assertIsNone(result["ratio_sd"])
        self.assertEqual(result["ratio_defined_trials"], 9)
        self.assertAlmostEqual(result["ratio_of_means"], 2.0 / 0.9)

    def test_zero_over_zero_is_undefined_not_zero_or_epsilon(self):
        result = paired_statistics([0.0] * 10, [0.0] * 10)
        self.assertIsNone(result["ratio_mean"])
        self.assertIsNone(result["ratio_sd"])
        self.assertIsNone(result["ratio_of_means"])
        self.assertEqual(result["ratio_defined_trials"], 0)

    def test_delta_uses_paired_trials_and_population_sd(self):
        result = paired_statistics([2.0] * 10, [1.0, 5.0] * 5)
        self.assertEqual(result["delta_mean_hz"], 1.0)
        self.assertEqual(result["delta_sd_hz"], 2.0)

    def test_rejects_incomplete_nonfinite_negative_or_nonscalar_rate_vectors(self):
        for invalid in ([1.0] * 9, [1.0] * 11, [[1.0]] * 10,
                        [1.0] * 9 + [float("nan")], [1.0] * 9 + [float("inf")], [1.0] * 9 + [-1.0]):
            for arm in (0, 1):
                args = [[1.0] * 10, [1.0] * 10]
                args[arm] = invalid
                with self.subTest(arm=arm, invalid=repr(invalid[-1])), self.assertRaises((ValueError, TypeError)):
                    paired_statistics(*args)


class RawValidationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="askfly_salt_raw_")
        self.addCleanup(self.temporary.cleanup)
        self.path = Path(self.temporary.name) / "S1_baseline.npz"
        self.spec, self.protocol, self.cells = fixture()
        self.condition = select_conditions()[0]
        self.expected = result_identity(self.condition, {"fixture": "synthetic, no simulation"})
        descriptions = _individual_descriptions(self.spec, self.cells, self.condition)
        groups = groups_for(self.spec, self.protocol, self.condition, self.cells)
        individuals, grouped = [], []
        for trial in range(10):
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
            "completed_trials": np.arange(10, dtype=np.int64),
            "saved_neuron_ids": np.array([int(row["Body_ID"]) for row in descriptions], dtype=np.int64),
            "poisson_target_id": np.array([], dtype=np.int64), "poisson_t_ms": np.array([], dtype=np.float64),
            "poisson_trial": np.array([], dtype=np.int64),
            "poisson_saved_target_ids": np.array([int(row["Body_ID"]) for row in descriptions if row["role"] == "source_GRN"], dtype=np.int64),
        }
        self.saved = {"identity": copy.deepcopy(self.expected), "completed_trials": list(range(10)),
                      "individual": individuals, "grouped": grouped}
        self.write_raw()

    def write_raw(self):
        np.savez_compressed(self.path, **self.raw)
        self.saved["spikes_sha256"] = sha256(self.path)

    def validate(self):
        return validate_result(self.saved, self.path, self.expected, self.spec, self.protocol, self.cells, self.condition)

    def test_complete_silent_trials_are_valid_with_all_75_neurons_saved(self):
        self.assertEqual(self.validate(), self.saved)
        self.assertEqual(len(self.saved["individual"]), 750)

    def test_missing_ledger_trial_is_not_filled_as_silence(self):
        self.saved["completed_trials"].pop()
        with self.assertRaises(ValueError):
            self.validate()

    def test_missing_or_duplicate_completion_markers_are_rejected(self):
        for markers in (np.arange(9, dtype=np.int64), np.array(list(range(9)) + [8], dtype=np.int64)):
            self.raw["completed_trials"] = markers
            self.write_raw()
            with self.subTest(markers=markers.tolist()), self.assertRaises(ValueError):
                self.validate()

    def test_changed_raw_seed_or_identity_is_rejected(self):
        self.raw["seeds"][0] += 1
        self.write_raw()
        with self.assertRaises(ValueError):
            self.validate()
        self.raw["seeds"][0] -= 1
        self.write_raw()
        self.saved["identity"]["condition_id"] = "S1_LB3d_22"
        with self.assertRaises(ValueError):
            self.validate()

    def test_missing_saved_neuron_or_source_never_becomes_a_silent_row(self):
        original = copy.deepcopy(self.raw)
        for key in ("saved_neuron_ids", "poisson_saved_target_ids"):
            self.raw = copy.deepcopy(original)
            self.raw[key] = self.raw[key][:-1]
            self.write_raw()
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.validate()

    def test_float_id_arrays_lose_precision_and_are_rejected(self):
        original = copy.deepcopy(self.raw)
        for key in ("flywire_id", "saved_neuron_ids", "poisson_target_id", "poisson_saved_target_ids"):
            self.raw = copy.deepcopy(original)
            self.raw[key] = self.raw[key].astype(float)
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

    def test_inactive_poisson_source_event_is_rejected(self):
        self.raw["poisson_target_id"] = self.raw["poisson_saved_target_ids"][:1]
        self.raw["poisson_t_ms"] = np.array([100.0])
        self.raw["poisson_trial"] = np.array([0], dtype=np.int64)
        self.write_raw()
        with self.assertRaises(ValueError):
            self.validate()

    def test_extra_neuron_invalid_time_and_trial_are_rejected(self):
        original = copy.deepcopy(self.raw)
        for root, time, trial in ((720575940999999999, 100.0, 0),
                                  (int(original["saved_neuron_ids"][0]), -0.1, 0),
                                  (int(original["saved_neuron_ids"][0]), 1000.1, 0),
                                  (int(original["saved_neuron_ids"][0]), float("nan"), 0),
                                  (int(original["saved_neuron_ids"][0]), 100.0, 10)):
            self.raw = copy.deepcopy(original)
            self.raw.update(flywire_id=np.array([root], dtype=np.int64), t_ms=np.array([time]), trial=np.array([trial], dtype=np.int64))
            self.write_raw()
            with self.subTest(root=root, time=time, trial=trial), self.assertRaises(ValueError):
                self.validate()

    def test_hash_mismatch_is_rejected(self):
        self.saved["spikes_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            self.validate()


class PairedInputTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="askfly_salt_paired_")
        self.addCleanup(self.temporary.cleanup)
        self.out = Path(self.temporary.name)
        self.spec, _, self.cells = fixture()
        self.populations = source_groups(self.spec, self.cells)
        roots = sorted(set().union(*(set(v) for v in self.populations.values())), key=int)
        self.source_times = {root: 10.0 + i for i, root in enumerate(roots)}
        self.results, self.arrays = [], []
        for condition in select_conditions():
            identity = result_identity(condition, {"fixture": "synthetic, no simulation"})
            descriptions = _individual_descriptions(self.spec, self.cells, condition)
            active = set().union(*(set(self.populations[group]) for group, hz in condition["group_rates"].items() if hz))
            events = [(int(root), self.source_times[root], trial)
                      for trial in range(10) for root in roots if root in active]
            arrays = {
                "poisson_target_id": np.array([r[0] for r in events], dtype=np.int64),
                "poisson_t_ms": np.array([r[1] for r in events], dtype=np.float64),
                "poisson_trial": np.array([r[2] for r in events], dtype=np.int64),
                "poisson_saved_target_ids": np.array([int(r["Body_ID"]) for r in descriptions if r["role"] == "source_GRN"], dtype=np.int64),
                "seeds": np.array(identity["seeds"], dtype=np.int64),
                "completed_trials": np.arange(10, dtype=np.int64),
            }
            self.results.append({"identity": identity, "individual": descriptions})
            self.arrays.append(arrays)
        self.write_raw()

    def write_raw(self):
        for result, arrays in zip(self.results, self.arrays):
            path = self.out / f"{result['identity']['condition_id']}.npz"
            np.savez_compressed(path, **arrays)
            result["spikes_sha256"] = sha256(path)

    def validate(self):
        return validate_paired_inputs(self.results, self.out, self.spec, self.cells)

    def test_shared_residual22_and_sugar23_have_identical_source_events(self):
        result = self.validate()
        self.assertEqual(result, {
            "LB3d22_29_vs22_identical": True,
            "sugar23_alone_vs_combo_identical": True,
            "LB3d22_neuron_trials": 220,
            "sugar23_neuron_trials": 230,
        })

    def test_changed_residual_source_time_in_22_cell_arm_is_rejected(self):
        self.arrays[3]["poisson_t_ms"][0] += 0.1
        self.write_raw()
        with self.assertRaises(ValueError):
            self.validate()

    def test_changed_sugar_source_time_in_combination_is_rejected(self):
        root = int(self.populations["frozen_sugar23"][0])
        index = np.flatnonzero(self.arrays[5]["poisson_target_id"] == root)[0]
        self.arrays[5]["poisson_t_ms"][index] += 0.1
        self.write_raw()
        with self.assertRaises(ValueError):
            self.validate()

    def test_matching_counts_without_matching_spike_times_are_not_paired(self):
        self.arrays[4]["poisson_t_ms"] += 0.1
        self.write_raw()
        with self.assertRaises(ValueError):
            self.validate()

    def test_identical_sources_but_changed_paired_seed_metadata_are_rejected(self):
        self.results[3]["identity"]["seeds"][0] += 1
        self.write_raw()
        with self.assertRaises(ValueError):
            self.validate()

    def test_missing_paired_arm_is_rejected(self):
        self.results.pop()
        with self.assertRaises(ValueError):
            self.validate()

    def test_incomplete_raw_trial_markers_are_not_accepted_as_paired(self):
        self.arrays[3]["completed_trials"] = np.arange(9, dtype=np.int64)
        self.write_raw()
        with self.assertRaises(ValueError):
            self.validate()

    def test_raw_seed_change_is_rejected_even_when_event_arrays_match(self):
        self.arrays[3]["seeds"][0] += 1
        self.write_raw()
        with self.assertRaises(ValueError):
            self.validate()


if __name__ == "__main__":
    unittest.main()
