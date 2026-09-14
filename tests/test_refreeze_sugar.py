# SPDX-License-Identifier: MIT
"""R1 exact-design and result-integrity checks, without simulation."""

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
from tests.test_pharyngeal import synthetic_design

from sim.run_refreeze_sugar import (
    _individual_descriptions,
    candidate_source_rows,
    effective_rates,
    groups_for,
    make_stimulation,
    normalized_statistics,
    paired_statistics,
    phase0_gates,
    phase_r1_seed,
    result_identity,
    select_conditions,
    source_groups,
    validate_paired_inputs,
    validate_result,
)
from scripts.cross_check_cells import FLYWIRE


ROOT = Path(__file__).resolve().parents[1]
DOSES = (0, 60, 80, 120, 200)
DRIVES = ("frozen_sugar23", "candidate33", "LB3c20", "bitter42")
SEED_INDICES = tuple(range(5)) * 2 + tuple(range(5, 16)) + (3,)
CONDITION_IDS = (
    tuple(f"R1_old_{hz}" for hz in DOSES)
    + tuple(f"R1_new_{hz}" for hz in DOSES)
    + tuple(f"R1_A_new_{hz}" for hz in (25, 50, 100))
    + tuple(f"R1_B_new200_bitter{hz}" for hz in (25, 50, 100, 200))
    + tuple(f"R1_C_bitter{hz}" for hz in (25, 50, 100, 200))
    + ("R1_Aprime_LB3c20_120",)
)


def read_json(relative):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def fixture():
    spec, cells = synthetic_design()
    sugar, water = (cells["sets"][key]["ids"] for key in ("sugar", "water"))
    b_ids = sugar[:1] + [720575940000002000 + i for i in range(12)]
    c_ids = sugar[1:12] + water[:7] + [720575940000003000 + i for i in range(2)]
    spec["candidate_neurons"] = [
        {"Body_ID": str(root), "Root_Side": "L", "Type": "LB3", "Subtype": kind,
         "Entry_Nerve": "labial nerve", "in_v783": True}
        for kind, ids in (("LB3b", b_ids), ("LB3c", c_ids)) for root in ids
    ]
    spec["readout_neurons"] = [row for row in read_json("data/mn_readout_ids.json")["neurons"]
                               if row["Type"] in {"MN9", "MN11D", "MN11V"}]
    return spec, read_json("data/stim_protocol.json"), cells


class DesignTests(unittest.TestCase):
    def test_exact_twenty_two_conditions_and_660_runs(self):
        conditions = select_conditions()
        self.assertEqual(tuple(c["cond_id"] for c in conditions), CONDITION_IDS)
        self.assertEqual([c["condition_index"] for c in conditions], list(range(22)))
        self.assertEqual(tuple(c["seed_index"] for c in conditions), SEED_INDICES)
        self.assertEqual(len(conditions) * 30, 660)

    def test_exact_authorised_drives_and_no_extra_benchmark21_runs(self):
        requested = (
            [(hz, 0, 0, 0) for hz in DOSES] + [(0, hz, 0, 0) for hz in DOSES]
            + [(0, hz, 0, 0) for hz in (25, 50, 100)]
            + [(0, 200, 0, hz) for hz in (25, 50, 100, 200)]
            + [(0, 0, 0, hz) for hz in (25, 50, 100, 200)] + [(0, 0, 120, 0)]
        )
        for condition, rates in zip(select_conditions(), requested):
            self.assertEqual(condition["group_rates"], dict(zip(DRIVES, rates)))
        self.assertEqual(sum("Aprime" in c["cond_id"] for c in select_conditions()), 1)
        self.assertFalse(any("bench21" in c["cond_id"] for c in select_conditions()))

    def test_definitions_are_fresh_not_shared_mutable_state(self):
        select_conditions()[8]["group_rates"]["candidate33"] = 999
        self.assertEqual(select_conditions()[8]["group_rates"]["candidate33"], 120)

    def test_no_brian2_import_on_native_validation_path(self):
        result = subprocess.run(
            [sys.executable, "-B", "-c", "import sys; import sim.run_refreeze_sugar; "
             "assert 'brian2' not in sys.modules"], cwd=ROOT, text=True,
            capture_output=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_new_spec_references_frozen_protocol_and_p1_without_redefining_model(self):
        spec = read_json("data/stim_protocol_refreeze_sugar.json")
        self.assertEqual(spec["base_protocol"], "data/stim_protocol.json")
        self.assertEqual(spec["p1_protocol"], "data/stim_protocol_pharyngeal.json")
        self.assertEqual(spec["trial"]["n_trials"], 30)
        self.assertEqual(spec["conditions"], select_conditions())
        self.assertNotIn("model", spec)
        self.assertEqual(len(spec["candidate_neurons"]), 33)
        self.assertEqual({row["Root_Side"] for row in spec["candidate_neurons"]}, {"L"})
        self.assertEqual({row["Type"] for row in spec["candidate_neurons"]}, {"LB3"})
        self.assertTrue(all(row["in_v783"] is True for row in spec["candidate_neurons"]))


class SeedTests(unittest.TestCase):
    def test_paired_grid_formula_660_trials_and_480_unique_seeds(self):
        for index, seed_index in enumerate(SEED_INDICES):
            for trial in range(30):
                self.assertEqual(phase_r1_seed(index, trial), 20260910 + 1000 * seed_index + trial)
        seeds = [phase_r1_seed(i, t) for i in range(22) for t in range(30)]
        self.assertEqual((len(seeds), len(set(seeds))), (660, 480))

    def test_aprime_shares_seed_block_with_both_120_hz_curves(self):
        for trial in range(30):
            self.assertEqual(phase_r1_seed(21, trial), phase_r1_seed(8, trial))
            self.assertEqual(phase_r1_seed(21, trial), phase_r1_seed(3, trial))
        self.assertEqual(phase_r1_seed(21, 29, base_seed=7), 3036)

    def test_seed_rejects_nonintegral_bool_negative_or_out_of_range_values(self):
        for value in (-1, 22, 1.0, True, "1", None):
            with self.subTest(index=value), self.assertRaises((ValueError, TypeError)):
                phase_r1_seed(value, 0)
        for value in (-1, 30, 1.0, True, "1", None):
            with self.subTest(trial=value), self.assertRaises((ValueError, TypeError)):
                phase_r1_seed(0, value)
        for value in (1.0, True, "1", None):
            with self.subTest(base=value), self.assertRaises((ValueError, TypeError)):
                phase_r1_seed(0, 0, base_seed=value)


class MembershipAndLayoutTests(unittest.TestCase):
    def test_xlsx_extraction_keeps_exact_flywire_left_rows_and_literal_columns(self):
        spec, _, _ = fixture()
        expected = spec["candidate_neurons"]
        originals = [{**{key: value for key, value in row.items() if key != "in_v783"},
                      "Connectome": FLYWIRE} for row in expected]
        distractors = [
            {**originals[0], "Body_ID": "720575940000009000", "Root_Side": "R"},
            {**originals[0], "Body_ID": "720575940000009001", "Connectome": "MaleCNS"},
            {**originals[0], "Body_ID": "720575940000009002", "Subtype": "LB3d"},
        ]
        rows = originals + distractors
        before = copy.deepcopy(rows)
        selected = candidate_source_rows(rows, {row["Body_ID"] for row in expected})
        self.assertEqual(selected, expected)
        self.assertEqual(rows, before)

    def test_xlsx_extraction_rejects_incomplete_duplicate_nonexact_or_missing_v783_rows(self):
        spec, _, _ = fixture()
        original = [{**row, "Connectome": FLYWIRE} for row in spec["candidate_neurons"]]
        v783 = {row["Body_ID"] for row in original}
        for mutation in ("missing", "duplicate", "float", "v783"):
            rows, present = copy.deepcopy(original), set(v783)
            if mutation == "missing":
                rows.pop()
            elif mutation == "duplicate":
                rows[1]["Body_ID"] = rows[0]["Body_ID"]
            elif mutation == "float":
                rows[0]["Body_ID"] = float(rows[0]["Body_ID"])
            else:
                present.remove(rows[0]["Body_ID"])
            with self.subTest(mutation=mutation), self.assertRaises((ValueError, TypeError)):
                candidate_source_rows(rows, present)

    def test_candidate_is_13_lb3b_plus_20_lb3c_on_literal_xlsx_left_side(self):
        spec, _, cells = fixture()
        groups = source_groups(spec, cells)
        self.assertEqual({key: len(roots) for key, roots in groups.items()}, {
            "frozen_sugar23": 23, "candidate33": 33, "LB3b13": 13,
            "LB3c20": 20, "shared12": 12, "bitter42": 42,
        })
        for kind, key in (("LB3b", "LB3b13"), ("LB3c", "LB3c20")):
            self.assertEqual(set(groups[key]), {n["Body_ID"] for n in spec["candidate_neurons"] if n["Subtype"] == kind})
        self.assertEqual(set(groups["candidate33"]), set(groups["LB3b13"]) | set(groups["LB3c20"]))
        self.assertTrue(set(groups["LB3b13"]).isdisjoint(groups["LB3c20"]))
        self.assertEqual(set(groups["shared12"]), set(groups["candidate33"]) & set(groups["frozen_sugar23"]))
        self.assertEqual(len(set(groups["candidate33"]) & set(map(str, cells["sets"]["water"]["ids"]))), 7)
        self.assertEqual(len(set(groups["candidate33"]) | set(groups["frozen_sugar23"])), 44)
        self.assertEqual(len(set().union(*map(set, groups.values()))), 86)

    def test_165_singletons_preserve_original_151_order_then_append_14_sorted_roots(self):
        from sim.run_pharyngeal import make_stimulation as p1_stimulation
        spec, _, cells = fixture()
        prior, prior_mapping = p1_stimulation(spec, cells)
        old = [str(root) for name in prior_mapping.values() for root in prior["sets"][name]["ids"]]
        expanded, mapping = make_stimulation(spec, cells)
        roots = [str(expanded["sets"][name]["ids"][0]) for name in mapping.values()]
        self.assertTrue(all(len(expanded["sets"][name]["ids"]) == 1 for name in mapping.values()))
        self.assertEqual(roots[:151], old)
        self.assertEqual(roots[151:], sorted({n["Body_ID"] for n in spec["candidate_neurons"]} - set(old), key=int))
        self.assertEqual((len(roots), len(set(roots))), (165, 165))
        self.assertEqual(list(mapping), [f"r1_{root}" for root in roots])

    def test_source_and_frozen_cells_are_deeply_unchanged(self):
        spec, _, cells = fixture()
        before = copy.deepcopy((spec, cells))
        source_groups(spec, cells)
        expanded, _ = make_stimulation(spec, cells)
        expanded["sets"]["water"]["ids"].clear()
        expanded["unrelated"]["keep"].append(4)
        self.assertEqual((spec, cells), before)

    def test_invalid_source_side_ids_type_counts_v783_and_overlap_are_rejected(self):
        for mutation in ("right_side", "missing", "duplicate", "float", "scientific", "v783", "type", "subtype", "overlap"):
            spec, _, cells = fixture()
            if mutation == "missing":
                spec["candidate_neurons"].pop()
            elif mutation == "duplicate":
                spec["candidate_neurons"][1]["Body_ID"] = spec["candidate_neurons"][0]["Body_ID"]
            elif mutation == "overlap":
                spec["candidate_neurons"][0]["Body_ID"] = "720575940000009999"
            else:
                key, value = {
                    "right_side": ("Root_Side", "R"), "float": ("Body_ID", 720575940000002000.0),
                    "scientific": ("Body_ID", "7.2057594e17"), "v783": ("in_v783", False),
                    "type": ("Type", "LB3c"), "subtype": ("Subtype", "LB3d"),
                }[mutation]
                spec["candidate_neurons"][0][key] = value
            with self.subTest(mutation=mutation), self.assertRaises((ValueError, TypeError)):
                source_groups(spec, cells)

    def test_every_condition_monitors_86_distinct_sources_and_six_literal_mn_readouts(self):
        spec, protocol, cells = fixture()
        first = None
        for condition in select_conditions():
            rows = _individual_descriptions(spec, cells, condition)
            roots = [row["Body_ID"] for row in rows]
            self.assertEqual((len(roots), len(set(roots))), (92, 92))
            self.assertEqual(sum(row["role"] == "source_GRN" for row in rows), 86)
            self.assertEqual(sum(row["role"] == "MN_readout" for row in rows), 6)
            self.assertEqual({row["Target_Muscle"] for row in rows if row["role"] == "MN_readout"}, {"9", "11D", "11V"})
            self.assertEqual(roots, first if first is not None else roots)
            first = roots
            groups = groups_for(spec, protocol, condition, cells)
            self.assertEqual([len(groups[key]) for key in ("MN9_L", "MN9_R", "MN11D", "MN11V")], [1, 1, 2, 2])
            self.assertNotIn("CEM", groups)

    def test_effective_rates_once_per_physical_root_and_inactive_rates_zero(self):
        spec, protocol, cells = fixture()
        sources = source_groups(spec, cells)
        for condition in select_conditions():
            rates = effective_rates(spec, cells, condition)
            expected = {f"r1_{root}": hz for key, hz in condition["group_rates"].items() if hz for root in sources[key]}
            self.assertEqual({key: hz for key, hz in rates.items() if hz}, expected)
            self.assertEqual(len(rates), 165)
            groups = groups_for(spec, protocol, condition, cells)
            if expected:
                self.assertEqual(set(groups["actual_driven_union"]), {key.removeprefix("r1_") for key in expected})
            else:
                self.assertNotIn("actual_driven_union", groups)

    def test_candidate_water_overlap_keeps_120_hz_despite_inactive_water(self):
        spec, _, cells = fixture()
        roots = set(source_groups(spec, cells)["candidate33"]) & set(map(str, cells["sets"]["water"]["ids"]))
        rates = effective_rates(spec, cells, select_conditions()[8])
        self.assertEqual(len(roots), 7)
        self.assertTrue(all(rates[f"r1_{root}"] == 120 for root in roots))

    def test_active_logical_overlap_is_rejected_not_double_driven(self):
        spec, _, cells = fixture()
        for keys in (("frozen_sugar23", "candidate33"), ("candidate33", "LB3c20")):
            condition = copy.deepcopy(select_conditions()[0])
            for key in keys:
                condition["group_rates"][key] = 120
            with self.subTest(keys=keys), self.assertRaises(ValueError):
                effective_rates(spec, cells, condition)


class ComparisonTests(unittest.TestCase):
    def test_per_level_new_over_old_is_ratio_of_means_not_mean_of_ratios(self):
        result = paired_statistics([1.0, 3.0] * 15, [4.0, 6.0] * 15)
        self.assertEqual(result["ratio_of_means"], 2.5)
        self.assertNotEqual(result["ratio_of_means"], 3.0)
        self.assertEqual(result["delta_mean_hz"], 3.0)
        self.assertEqual(result["delta_sd_hz"], 0.0)

    def test_zero_over_zero_and_nonzero_over_zero_are_undefined(self):
        for new in ([0.0] * 30, [1.0] * 30):
            result = paired_statistics([0.0] * 30, new)
            self.assertIsNone(result["ratio_of_means"])

    def test_aprime_subset_minus_candidate_is_paired_mean_and_population_sd(self):
        result = paired_statistics([4.0] * 30, [1.0, 5.0] * 15)
        self.assertEqual(result["delta_mean_hz"], -1.0)
        self.assertEqual(result["delta_sd_hz"], 2.0)

    def test_invalid_incomplete_nonfinite_or_negative_comparison_vectors_fail(self):
        for invalid in ([1.0] * 29, [1.0] * 31, [[1.0]] * 30,
                        [1.0] * 29 + [float("nan")], [1.0] * 29 + [float("inf")],
                        [1.0] * 29 + [-0.1]):
            for arm in range(2):
                args = [[1.0] * 30, [1.0] * 30]
                args[arm] = invalid
                with self.subTest(arm=arm, invalid=repr(invalid[-1])), self.assertRaises((ValueError, TypeError)):
                    paired_statistics(*args)
            for arm in range(4):
                args = [[1.0] * 30 for _ in range(4)]
                args[arm] = invalid
                with self.subTest(normalized_arm=arm, invalid=repr(invalid[-1])), self.assertRaises((ValueError, TypeError)):
                    normalized_statistics(*args)

    def test_endpoint_normalizers_are_fixed_own_mean200_not_trialwise_denominators(self):
        result = normalized_statistics([2.0, 6.0] * 15, [10.0, 14.0] * 15,
                                       [1.0, 7.0] * 15, [2.0, 14.0] * 15)
        self.assertEqual(result["old_200_mean_hz"], 4.0)
        self.assertEqual(result["new_200_mean_hz"], 8.0)
        self.assertEqual(result["old_normalized_mean"], 1.0)
        self.assertEqual(result["old_normalized_sd"], 0.5)
        self.assertEqual(result["new_normalized_mean"], 1.5)
        self.assertEqual(result["new_normalized_sd"], 0.25)
        self.assertEqual(result["delta_values"], [0.75, 0.25] * 15)
        self.assertEqual(result["delta_mean"], 0.5)
        self.assertEqual(result["delta_sd"], 0.25)
        self.assertFalse(result["exceeds_two_sd"])

    def test_two_sd_shape_flag_is_strict_descriptive_threshold_on_paired_delta(self):
        result = normalized_statistics([0.0] * 30, [1.0, 3.0] * 15,
                                       [1.0] * 30, [1.0] * 30)
        self.assertEqual(result["delta_mean"], 2.0)
        self.assertEqual(result["delta_sd"], 1.0)
        self.assertFalse(result["exceeds_two_sd"])
        result = normalized_statistics([0.0] * 30, [2.0, 4.0] * 15,
                                       [1.0] * 30, [1.0] * 30)
        self.assertTrue(result["exceeds_two_sd"])
        result = normalized_statistics([2.0, 4.0] * 15, [0.0] * 30,
                                       [1.0] * 30, [1.0] * 30)
        self.assertTrue(result["exceeds_two_sd"])

    def test_zero_endpoint_mean_makes_normalization_and_shape_comparison_undefined(self):
        for arm in (2, 3):
            args = [[1.0] * 30 for _ in range(4)]
            args[arm] = [0.0] * 30
            result = normalized_statistics(*args)
            prefix = "old" if arm == 2 else "new"
            self.assertIsNone(result[f"{prefix}_normalized_mean"])
            self.assertIsNone(result[f"{prefix}_normalized_sd"])
            self.assertIsNone(result["delta_mean"])
            self.assertIsNone(result["delta_sd"])
            self.assertIsNone(result["exceeds_two_sd"])

    def test_nonzero_endpoint_mean_remains_defined_despite_zero_endpoint_trial(self):
        result = normalized_statistics([1.0] * 30, [1.0] * 30,
                                       [0.0, 2.0] * 15, [0.0, 2.0] * 15)
        self.assertEqual(result["old_normalized_mean"], 1.0)
        self.assertEqual(result["new_normalized_mean"], 1.0)
        self.assertEqual(result["delta_mean"], 0.0)
        self.assertEqual(result["delta_sd"], 0.0)


def gate_fixture():
    means = {"R1_new_200": 80.0, "R1_A_new_25": 10.0,
             "R1_A_new_50": 20.0, "R1_A_new_100": 40.0}
    means.update({f"R1_B_new200_bitter{hz}": value
                  for hz, value in zip((25, 50, 100, 200), (70.0, 50.0, 30.0, 20.0))})
    return [{"cond_id": condition["cond_id"], "readouts": {
        side: {"n_trials": 30, "rate_mean_hz": means.get(condition["cond_id"], 0.0),
               "rate_std_hz": 0.0} for side in ("MN9_L", "MN9_R")
    }} for condition in select_conditions()]


def set_gate_value(rows, name, mean=None, sd=None, n_trials=None, side="MN9_L"):
    readout = next(row for row in rows if row["cond_id"] == name)["readouts"][side]
    for key, value in (("rate_mean_hz", mean), ("rate_std_hz", sd), ("n_trials", n_trials)):
        if value is not None:
            readout[key] = value


class PhaseZeroGateTests(unittest.TestCase):
    def test_complete_original_frequency_coverage_passes_unchanged_thresholds(self):
        result = phase0_gates(gate_fixture())
        self.assertEqual(result["gates"], dict.fromkeys("ABCD", True))
        self.assertTrue(result["overall_pass"])
        self.assertEqual(result["A_doses_hz"], [25, 50, 100, 200])
        self.assertEqual(result["B_doses_hz"], [0, 25, 50, 100, 200])
        self.assertEqual(result["C_doses_hz"], [25, 50, 100, 200])

    def test_every_missing_required_condition_fails_instead_of_passing_partial_grid(self):
        original = gate_fixture()
        for index in range(22):
            rows = copy.deepcopy(original)
            rows.pop(index)
            with self.subTest(missing=CONDITION_IDS[index]), self.assertRaises(ValueError):
                phase0_gates(rows)

    def test_duplicate_or_misnamed_condition_is_rejected(self):
        for duplicate in (True, False):
            rows = gate_fixture()
            rows[-1]["cond_id"] = rows[0]["cond_id"] if duplicate else "A_prime_sugar_bench21_sugar120Hz"
            with self.subTest(duplicate=duplicate), self.assertRaises(ValueError):
                phase0_gates(rows)

    def test_all_gate_readouts_require_30_finite_nonnegative_complete_trials(self):
        for key, value in (("n_trials", 29), ("n_trials", 31), ("rate_mean_hz", float("nan")),
                           ("rate_mean_hz", -1.0), ("rate_std_hz", float("inf")), ("rate_std_hz", -0.1)):
            rows = gate_fixture()
            rows[10]["readouts"]["MN9_L"][key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                phase0_gates(rows)

    def test_a_strict_increase_allows_only_equal_zero_pair(self):
        rows = gate_fixture()
        set_gate_value(rows, "R1_A_new_50", mean=10.0)
        self.assertFalse(phase0_gates(rows)["gates"]["A"])
        set_gate_value(rows, "R1_A_new_25", mean=0.0)
        set_gate_value(rows, "R1_A_new_50", mean=0.0)
        self.assertTrue(phase0_gates(rows)["gates"]["A"])

    def test_a_200_is_strictly_above_baseline_plus_five_sd_plus_five(self):
        rows = gate_fixture()
        set_gate_value(rows, "R1_new_0", mean=2.0, sd=1.0)
        for name, mean in (("R1_A_new_25", 1), ("R1_A_new_50", 2),
                           ("R1_A_new_100", 3), ("R1_new_200", 12)):
            set_gate_value(rows, name, mean=mean)
        self.assertFalse(phase0_gates(rows)["gates"]["A"])
        set_gate_value(rows, "R1_new_200", mean=12.001)
        self.assertTrue(phase0_gates(rows)["gates"]["A"])

    def test_b_is_nonincreasing_and_strictly_below_half_not_soft_70_percent(self):
        rows = gate_fixture()
        set_gate_value(rows, "R1_B_new200_bitter100", mean=50.0)
        set_gate_value(rows, "R1_B_new200_bitter200", mean=40.0)
        self.assertFalse(phase0_gates(rows)["gates"]["B"])
        set_gate_value(rows, "R1_B_new200_bitter200", mean=39.0)
        self.assertTrue(phase0_gates(rows)["gates"]["B"])
        set_gate_value(rows, "R1_B_new200_bitter50", mean=71.0)
        self.assertFalse(phase0_gates(rows)["gates"]["B"])

    def test_c_all_four_points_use_inclusive_baseline_plus_two_sd_plus_one(self):
        for hz in (25, 50, 100, 200):
            rows = gate_fixture()
            set_gate_value(rows, "R1_new_0", mean=2.0, sd=3.0)
            set_gate_value(rows, f"R1_C_bitter{hz}", mean=9.0)
            self.assertTrue(phase0_gates(rows)["gates"]["C"])
            set_gate_value(rows, f"R1_C_bitter{hz}", mean=9.001)
            self.assertFalse(phase0_gates(rows)["gates"]["C"])

    def test_d_requires_complete_baseline_without_inventing_numeric_zero_threshold(self):
        rows = gate_fixture()
        set_gate_value(rows, "R1_new_0", mean=2.0, sd=1.0)
        result = phase0_gates(rows)
        self.assertTrue(result["gates"]["D"])
        self.assertFalse(result["strict_silence"]["D_all_zero_MN9_L"])

    def test_gates_use_frozen_left_mn9_and_report_right_strict_silence_separately(self):
        rows = gate_fixture()
        set_gate_value(rows, "R1_new_0", mean=100.0, side="MN9_R")
        set_gate_value(rows, "R1_C_bitter25", mean=100.0, side="MN9_R")
        result = phase0_gates(rows)
        self.assertTrue(result["overall_pass"])
        self.assertTrue(result["strict_silence"]["D_all_zero_MN9_L"])
        self.assertTrue(result["strict_silence"]["C_all_zero_MN9_L"])
        self.assertFalse(result["strict_silence"]["D_all_zero_MN9_R"])
        self.assertFalse(result["strict_silence"]["C_all_zero_MN9_R"])

    def test_positive_sd_cannot_be_reported_as_exact_zero_even_when_mean_zero(self):
        rows = gate_fixture()
        set_gate_value(rows, "R1_new_0", sd=0.1)
        result = phase0_gates(rows)
        self.assertFalse(result["strict_silence"]["D_all_zero_MN9_L"])

    def test_aprime_subset_comparison_does_not_add_a_gate(self):
        rows = gate_fixture()
        set_gate_value(rows, "R1_Aprime_LB3c20_120", mean=1000.0)
        self.assertEqual(phase0_gates(rows)["gates"], dict.fromkeys("ABCD", True))


class RawValidationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="askfly_refreeze_raw_")
        self.addCleanup(self.temporary.cleanup)
        self.path = Path(self.temporary.name) / "R1_old_0.npz"
        self.spec, self.protocol, self.cells = fixture()
        self.condition = select_conditions()[0]
        self.expected = result_identity(self.condition, {"fixture": "synthetic, no simulation"})
        descriptions = _individual_descriptions(self.spec, self.cells, self.condition)
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
            "poisson_saved_target_ids": np.array([int(row["Body_ID"]) for row in descriptions if row["role"] == "source_GRN"], dtype=np.int64),
        }
        self.saved = {"identity": copy.deepcopy(self.expected), "completed_trials": list(range(30)),
                      "individual": individuals, "grouped": grouped}
        self.write_raw()

    def write_raw(self):
        np.savez_compressed(self.path, **self.raw)
        self.saved["spikes_sha256"] = sha256(self.path)

    def validate(self):
        return validate_result(self.saved, self.path, self.expected, self.spec, self.protocol, self.cells, self.condition)

    def test_complete_silent_trials_keep_all_92_requested_neurons(self):
        self.assertEqual(self.validate(), self.saved)
        self.assertEqual(len(self.saved["individual"]), 2760)

    def test_nonzero_raw_spikes_reconstruct_exact_hz_and_first_spike_latency(self):
        root = str(self.protocol["readout"]["left"])
        self.raw.update(flywire_id=np.array([int(root), int(root)], dtype=np.int64),
                        t_ms=np.array([100.25, 250.5]), trial=np.array([0, 0], dtype=np.int64))
        for row in self.saved["individual"]:
            if row["trial"] == 0 and row["Body_ID"] == root:
                row.update(spike_count=2, rate_hz=2.0, first_spike_ms=100.25)
        for row in self.saved["grouped"]:
            if row["trial"] == 0 and row["readout"] == "MN9_L":
                row.update(spike_count=2, total_rate_hz=2.0, rate_hz=2.0, first_spike_ms=100.25)
        self.write_raw()
        self.assertEqual(self.validate(), self.saved)

    def test_two_cell_mn_readout_averages_members_including_silent_member(self):
        root = next(n["Body_ID"] for n in self.spec["readout_neurons"] if n["Type"] == "MN11D")
        self.raw.update(flywire_id=np.array([int(root), int(root)], dtype=np.int64),
                        t_ms=np.array([12.5, 500.25]), trial=np.array([0, 0], dtype=np.int64))
        for row in self.saved["individual"]:
            if row["trial"] == 0 and row["Body_ID"] == root:
                row.update(spike_count=2, rate_hz=2.0, first_spike_ms=12.5)
        for row in self.saved["grouped"]:
            if row["trial"] == 0 and row["readout"] == "MN11D":
                row.update(spike_count=2, total_rate_hz=2.0, rate_hz=1.0, first_spike_ms=12.5)
        self.write_raw()
        self.assertEqual(self.validate(), self.saved)

    def test_missing_ledger_trial_is_not_replaced_by_silence(self):
        self.saved["completed_trials"].pop()
        with self.assertRaises(ValueError):
            self.validate()

    def test_missing_duplicate_or_float_raw_completion_markers_are_rejected(self):
        for markers in (np.arange(29, dtype=np.int64), np.array(list(range(29)) + [28], dtype=np.int64), np.arange(30, dtype=float)):
            self.raw["completed_trials"] = markers
            self.write_raw()
            with self.subTest(markers=markers.tolist()), self.assertRaises(ValueError):
                self.validate()

    def test_changed_seed_identity_or_group_drive_metadata_is_rejected(self):
        self.raw["seeds"][0] += 1
        self.write_raw()
        with self.assertRaises(ValueError):
            self.validate()
        self.raw["seeds"][0] -= 1
        self.write_raw()
        original = copy.deepcopy(self.saved)
        for key, value in (("condition_id", "R1_new_0"), ("seed_index", 1), ("group_rates", {})):
            self.saved = copy.deepcopy(original)
            self.saved["identity"][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.validate()

    def test_missing_or_repeated_recorded_neuron_or_source_is_rejected(self):
        original = copy.deepcopy(self.raw)
        for key in ("saved_neuron_ids", "poisson_saved_target_ids"):
            for mutation in ("missing", "repeated"):
                self.raw = copy.deepcopy(original)
                self.raw[key] = self.raw[key][:-1] if mutation == "missing" else np.append(self.raw[key], self.raw[key][0])
                self.write_raw()
                with self.subTest(key=key, mutation=mutation), self.assertRaises(ValueError):
                    self.validate()

    def test_no_float_id_rounding_in_any_neuron_or_source_inventory(self):
        original = copy.deepcopy(self.raw)
        for key in ("flywire_id", "saved_neuron_ids", "poisson_target_id", "poisson_saved_target_ids"):
            self.raw = copy.deepcopy(original)
            self.raw[key] = self.raw[key].astype(float)
            self.write_raw()
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.validate()

    def test_saved_rates_latency_and_trial_completeness_are_recomputed_from_raw(self):
        original = copy.deepcopy(self.saved)
        for collection, field, value in (("individual", "rate_hz", 1.0), ("individual", "first_spike_ms", 1.0),
                                          ("grouped", "rate_hz", float("nan")), ("grouped", "trial", 29)):
            self.saved = copy.deepcopy(original)
            self.saved[collection][0][field] = value
            with self.subTest(collection=collection, field=field), self.assertRaises(ValueError):
                self.validate()
        self.saved = copy.deepcopy(original)
        self.saved["individual"].pop()
        with self.assertRaises(ValueError):
            self.validate()

    def test_baseline_inactive_source_cannot_emit_poisson_events(self):
        self.raw["poisson_target_id"] = self.raw["poisson_saved_target_ids"][:1]
        self.raw["poisson_t_ms"] = np.array([10.0])
        self.raw["poisson_trial"] = np.array([0], dtype=np.int64)
        self.write_raw()
        with self.assertRaises(ValueError):
            self.validate()

    def test_out_of_scope_neurons_nonfinite_time_or_invalid_trial_are_rejected(self):
        original = copy.deepcopy(self.raw)
        for root, time, trial in ((720575940999999999, 10.0, 0),
                                  (int(original["saved_neuron_ids"][0]), -0.1, 0),
                                  (int(original["saved_neuron_ids"][0]), 1000.1, 0),
                                  (int(original["saved_neuron_ids"][0]), float("nan"), 0),
                                  (int(original["saved_neuron_ids"][0]), float("inf"), 0),
                                  (int(original["saved_neuron_ids"][0]), 10.0, 30)):
            self.raw = copy.deepcopy(original)
            self.raw.update(flywire_id=np.array([root], dtype=np.int64), t_ms=np.array([time]), trial=np.array([trial], dtype=np.int64))
            self.write_raw()
            with self.subTest(root=root, time=time, trial=trial), self.assertRaises(ValueError):
                self.validate()

    def test_raw_hash_mismatch_is_rejected(self):
        self.saved["spikes_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            self.validate()


class PairedInputTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="askfly_refreeze_paired_")
        self.addCleanup(self.temporary.cleanup)
        self.out = Path(self.temporary.name)
        self.spec, _, self.cells = fixture()
        self.populations = source_groups(self.spec, self.cells)
        roots = sorted(set().union(*map(set, self.populations.values())), key=int)
        self.source_times = {root: 10.0 + i for i, root in enumerate(roots)}
        self.results, self.arrays = [], []
        for condition in select_conditions():
            identity = result_identity(condition, {"fixture": "synthetic, no simulation"})
            descriptions = _individual_descriptions(self.spec, self.cells, condition)
            active = set().union(*(set(self.populations[group]) for group, hz in condition["group_rates"].items() if hz))
            events = [(int(root), self.source_times[root], trial)
                      for trial in range(30) for root in roots if root in active]
            arrays = {
                "poisson_target_id": np.array([r[0] for r in events], dtype=np.int64),
                "poisson_t_ms": np.array([r[1] for r in events], dtype=np.float64),
                "poisson_trial": np.array([r[2] for r in events], dtype=np.int64),
                "poisson_saved_target_ids": np.array([int(r["Body_ID"]) for r in descriptions if r["role"] == "source_GRN"], dtype=np.int64),
                "seeds": np.array(identity["seeds"], dtype=np.int64),
                "completed_trials": np.arange(30, dtype=np.int64),
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

    def test_complete_pairs_match_shared_12_each_dose_and_20_aprime_targets(self):
        result = self.validate()
        self.assertEqual(result, {
            "old_new_shared12_identical": True,
            "old_new_shared_neuron_trials": 1800,
            "old_new_active_shared_neuron_trials": 1440,
            "old_new_zero_drive_shared_neuron_trials": 360,
            "Aprime_shared20_identical": True,
            "Aprime_shared_neuron_trials": 600,
        })

    def test_shared12_event_time_changed_in_each_new_dose_is_rejected(self):
        original = copy.deepcopy(self.arrays)
        root = int(self.populations["shared12"][0])
        for arm in (6, 7, 8, 9):
            self.arrays = copy.deepcopy(original)
            index = np.flatnonzero(self.arrays[arm]["poisson_target_id"] == root)[0]
            self.arrays[arm]["poisson_t_ms"][index] += 0.1
            self.write_raw()
            with self.subTest(arm=arm), self.assertRaises(ValueError):
                self.validate()

    def test_aprime_requires_identical_actual_lb3c20_trains_to_candidate120(self):
        self.arrays[21]["poisson_t_ms"][0] += 0.1
        self.write_raw()
        with self.assertRaises(ValueError):
            self.validate()

    def test_equal_spike_counts_with_different_times_are_not_paired(self):
        self.arrays[3]["poisson_t_ms"] += 0.1
        self.write_raw()
        with self.assertRaises(ValueError):
            self.validate()

    def test_changed_declared_or_raw_paired_seeds_are_rejected(self):
        self.results[21]["identity"]["seeds"][0] += 1
        with self.assertRaises(ValueError):
            self.validate()
        self.results[21]["identity"]["seeds"][0] -= 1
        self.arrays[21]["seeds"][0] += 1
        self.write_raw()
        with self.assertRaises(ValueError):
            self.validate()

    def test_missing_or_duplicate_condition_is_not_accepted(self):
        self.results.append(self.results[-1])
        with self.assertRaises(ValueError):
            self.validate()
        self.results.pop()
        self.results.pop()
        with self.assertRaises(ValueError):
            self.validate()

    def test_incomplete_completion_markers_are_not_filled_as_silence(self):
        self.arrays[21]["completed_trials"] = np.arange(29, dtype=np.int64)
        self.write_raw()
        with self.assertRaises(ValueError):
            self.validate()

    def test_inactive_baseline_or_bitter_source_events_are_rejected(self):
        original = copy.deepcopy(self.arrays)
        for arm in (0, 5, 8):
            self.arrays = copy.deepcopy(original)
            root = int(self.populations["bitter42"][0])
            self.arrays[arm]["poisson_target_id"] = np.append(self.arrays[arm]["poisson_target_id"], root)
            self.arrays[arm]["poisson_t_ms"] = np.append(self.arrays[arm]["poisson_t_ms"], 10.0)
            self.arrays[arm]["poisson_trial"] = np.append(self.arrays[arm]["poisson_trial"], 0)
            self.write_raw()
            with self.subTest(arm=arm), self.assertRaises(ValueError):
                self.validate()

    def test_paired_raw_hash_mismatch_is_rejected(self):
        self.results[21]["spikes_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            self.validate()


if __name__ == "__main__":
    unittest.main()
