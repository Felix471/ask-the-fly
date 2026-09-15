# SPDX-License-Identifier: MIT
"""Phase P design checks only: no Brian2, WSL, or simulation required."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

from sim.run_pharyngeal import (
    groups_for,
    make_stimulation,
    phase_p_seed,
    result_identity,
    select_conditions,
    validate_result,
)
from sim.run_mn_readouts import sha256


ROOT = Path(__file__).resolve().parents[1]
LABELLAR = ("sugar", "bitter", "water", "ir94e")
PHG_TYPES = tuple(f"PhG{i}" for i in range(1, 17))
CHANNELS = LABELLAR + PHG_TYPES
PHG_COUNTS = (8, 5, 2, 4, 2, 2, 5, 4, 4, 2, 2, 2, 2, 2, 2, 2)


def synthetic_design():
    """Use large, exactly represented IDs and realistic cardinalities."""
    neurons = []
    for kind, count in zip(PHG_TYPES, PHG_COUNTS):
        for member in range(count):
            neurons.append({
                "Body_ID": str(720575940000000001 + len(neurons)),
                "Root_Side": "L" if member % 2 else "R",
                "Type": kind,
                "Subtype": kind,
                "Entry_Nerve": "aPhN",
                "in_v783": True,
            })
    sets, index = {}, 1000
    for channel, count in zip(LABELLAR, (23, 42, 18, 18)):
        sets[channel] = {"ids": [720575940000000001 + index + i for i in range(count)],
                         "note": {"must_remain": "unchanged"}}
        index += count
    return {"pharyngeal_neurons": neurons}, {"sets": sets, "unrelated": {"keep": [1, 2, 3]}}


class ImportTests(unittest.TestCase):
    def test_import_does_not_load_brian2(self):
        result = subprocess.run(
            [sys.executable, "-B", "-c",
             "import sys; import sim.run_pharyngeal; "
             "assert 'brian2' not in sys.modules, 'Brian2 imported outside worker'"],
            cwd=ROOT, text=True, capture_output=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


class ConditionTests(unittest.TestCase):
    def setUp(self):
        self.conditions = select_conditions()

    def test_exactly_nineteen_conditions_with_fixed_identity_and_order(self):
        expected = (["P_baseline"] + [f"P_{kind}" for kind in PHG_TYPES]
                    + ["P_all_pharyngeal", "P_PhG1_sugar_high"])
        self.assertEqual([c["cond_id"] for c in self.conditions], expected)
        self.assertEqual([c["condition_index"] for c in self.conditions], list(range(19)))
        self.assertEqual(len(self.conditions) * 10, 190)

    def test_every_condition_uses_same_twenty_ordered_channels(self):
        for condition in self.conditions:
            with self.subTest(condition=condition["cond_id"]):
                self.assertEqual(tuple(condition["rates"]), CHANNELS)
                self.assertNotIn("all_pharyngeal", condition["rates"])

    def test_baseline_drives_nothing(self):
        baseline = self.conditions[0]
        self.assertEqual(set(baseline["rates"].values()), {0})
        self.assertEqual(baseline["driven_types"], [])

    def test_each_single_type_drives_only_its_members_at_100_hz(self):
        for kind, condition in zip(PHG_TYPES, self.conditions[1:17]):
            with self.subTest(kind=kind):
                self.assertEqual(condition["driven_types"], [kind])
                self.assertEqual(condition["rates"], {
                    channel: 100 if channel == kind else 0 for channel in CHANNELS
                })

    def test_all_pharyngeal_condition_drives_each_of_sixteen_channels_once(self):
        condition = self.conditions[17]
        self.assertEqual(condition["driven_types"], list(PHG_TYPES))
        self.assertEqual(condition["rates"], {
            channel: 0 if channel in LABELLAR else 100 for channel in CHANNELS
        })

    def test_combined_condition_is_only_phg1_and_sugar_high(self):
        condition = self.conditions[18]
        self.assertEqual(condition["driven_types"], ["PhG1"])
        expected = {channel: 0 for channel in CHANNELS}
        expected.update({"PhG1": 100, "sugar": 120})
        self.assertEqual(condition["rates"], expected)

    def test_calls_return_fresh_condition_dictionaries(self):
        self.conditions[1]["rates"]["PhG1"] = 500
        self.conditions[1]["driven_types"].append("PhG2")
        fresh = select_conditions()
        self.assertEqual(fresh[1]["rates"]["PhG1"], 100)
        self.assertEqual(fresh[1]["driven_types"], ["PhG1"])


class SeedTests(unittest.TestCase):
    def test_grid_formula_with_explicit_new_phase_p_condition_indices(self):
        for index in range(19):
            for trial in range(10):
                self.assertEqual(phase_p_seed(index, trial), 20260910 + 1000 * index + trial)

    def test_nineteen_by_ten_seeds_are_unique_and_never_extra_replay_seeds(self):
        seeds = [phase_p_seed(i, trial) for i in range(19) for trial in range(10)]
        self.assertEqual(len(set(seeds)), 190)
        self.assertLess(max(seeds), 20260910 + 700000)

    def test_custom_base_seed_preserves_the_grid_formula(self):
        self.assertEqual(phase_p_seed(18, 9, base_seed=7), 18016)

    def test_rejects_indices_outside_authorised_conditions(self):
        for index in (-1, 19, 39, 40, 400):
            with self.subTest(index=index), self.assertRaises((ValueError, TypeError)):
                phase_p_seed(index, 0)

    def test_rejects_trial_indices_outside_ten_trials(self):
        for trial in (-1, 10, 29, 30):
            with self.subTest(trial=trial), self.assertRaises((ValueError, TypeError)):
                phase_p_seed(0, trial)

    def test_rejects_lossy_or_boolean_seed_arguments(self):
        for value in (0.0, 1.5, True, False, "1", None):
            with self.subTest(index=value), self.assertRaises((ValueError, TypeError)):
                phase_p_seed(value, 0)
            with self.subTest(trial=value), self.assertRaises((ValueError, TypeError)):
                phase_p_seed(0, value)
            with self.subTest(base_seed=value), self.assertRaises((ValueError, TypeError)):
                phase_p_seed(0, 0, base_seed=value)


class StimulationTests(unittest.TestCase):
    def test_stimulation_uses_fixed_151_nonduplicated_targets(self):
        spec, cells = synthetic_design()
        expanded, channels = make_stimulation(spec, cells)
        self.assertEqual(tuple(channels), CHANNELS)
        self.assertEqual([channels[k] for k in PHG_TYPES], [f"phase_p_{k}" for k in PHG_TYPES])
        targets = [str(i) for name in channels.values() for i in expanded["sets"][name]["ids"]]
        self.assertEqual(len(targets), 151)
        self.assertEqual(len(set(targets)), 151)
        for kind, count in zip(PHG_TYPES, PHG_COUNTS):
            self.assertEqual(len(expanded["sets"][channels[kind]]["ids"]), count)

    def test_each_type_contains_all_exact_source_ids_both_sides(self):
        spec, cells = synthetic_design()
        expanded, channels = make_stimulation(spec, cells)
        for kind in PHG_TYPES:
            expected = {row["Body_ID"] for row in spec["pharyngeal_neurons"] if row["Type"] == kind}
            actual = {str(i) for i in expanded["sets"][channels[kind]]["ids"]}
            self.assertEqual(actual, expected)

    def test_inputs_are_not_mutated_or_nested_aliases_returned(self):
        spec, cells = synthetic_design()
        before_spec, before_cells = copy.deepcopy(spec), copy.deepcopy(cells)
        expanded, channels = make_stimulation(spec, cells)
        self.assertEqual(spec, before_spec)
        self.assertEqual(cells, before_cells)
        expanded["sets"]["sugar"]["note"]["must_remain"] = "changed"
        expanded["unrelated"]["keep"].append(4)
        expanded["sets"][channels["PhG1"]]["ids"].clear()
        self.assertEqual(spec, before_spec)
        self.assertEqual(cells, before_cells)

    def test_source_row_order_cannot_lexically_reorder_channels(self):
        spec, cells = synthetic_design()
        spec["pharyngeal_neurons"].reverse()
        _, channels = make_stimulation(spec, cells)
        self.assertEqual(tuple(channels), CHANNELS)

    def test_rejects_duplicate_pharyngeal_ids(self):
        spec, cells = synthetic_design()
        spec["pharyngeal_neurons"][1]["Body_ID"] = spec["pharyngeal_neurons"][0]["Body_ID"]
        with self.assertRaises((ValueError, TypeError)):
            make_stimulation(spec, cells)

    def test_rejects_overlap_with_frozen_labellar_stimulation(self):
        spec, cells = synthetic_design()
        spec["pharyngeal_neurons"][0]["Body_ID"] = str(cells["sets"]["sugar"]["ids"][0])
        with self.assertRaises((ValueError, TypeError)):
            make_stimulation(spec, cells)

    def test_rejects_missing_extra_or_wrong_type_counts(self):
        for mutation in ("missing", "extra", "wrong_type"):
            spec, cells = synthetic_design()
            if mutation == "missing":
                spec["pharyngeal_neurons"].pop()
            elif mutation == "extra":
                extra = dict(spec["pharyngeal_neurons"][0])
                extra["Body_ID"] = "720575940000000500"
                spec["pharyngeal_neurons"].append(extra)
            else:
                spec["pharyngeal_neurons"][0]["Type"] = "PhG17"
            with self.subTest(mutation=mutation), self.assertRaises((ValueError, TypeError)):
                make_stimulation(spec, cells)

    def test_rejects_pharyngeal_ids_with_lost_precision(self):
        for value in (720575940000000001.0, True, "7.20575940000000001e17", "0720575940000000001"):
            spec, cells = synthetic_design()
            spec["pharyngeal_neurons"][0]["Body_ID"] = value
            with self.subTest(value=value), self.assertRaises((ValueError, TypeError)):
                make_stimulation(spec, cells)


class ReferencingProtocolTests(unittest.TestCase):
    def test_new_protocol_references_frozen_model_and_ten_trials(self):
        spec = json.loads((ROOT / "data/stim_protocol_pharyngeal.json").read_text(encoding="utf-8"))
        self.assertEqual(spec["base_protocol"], "data/stim_protocol.json")
        self.assertEqual(spec["trial"]["n_trials"], 10)
        self.assertNotIn("model", spec)
        self.assertEqual(len(spec["pharyngeal_neurons"]), 50)
        self.assertTrue(all(row["in_v783"] for row in spec["pharyngeal_neurons"]))

    def test_mn9_preserves_frozen_sides_and_twelve_readout_neurons(self):
        protocol = json.loads((ROOT / "data/stim_protocol.json").read_text(encoding="utf-8"))
        spec = json.loads((ROOT / "data/stim_protocol_pharyngeal.json").read_text(encoding="utf-8"))
        inventory = json.loads((ROOT / "data/mn_readout_ids.json").read_text(encoding="utf-8"))
        self.assertEqual(spec["readout_neurons"], [
            row for row in inventory["neurons"] if row["Type"] in {"MN9", "MN11D", "MN11V", "CEM"}
        ])
        groups = groups_for(spec, protocol)
        self.assertEqual(groups["MN9_L"], [str(protocol["readout"]["left"])])
        self.assertEqual(groups["MN9_R"], [str(protocol["readout"]["right"])])
        self.assertEqual([len(groups[k]) for k in ("MN9_L", "MN9_R", "MN11D", "MN11V", "CEM")],
                         [1, 1, 2, 2, 6])
        self.assertEqual(len(set(i for ids in groups.values() for i in ids)), 12)

    def test_baseline_does_not_invent_a_driven_neuron_group(self):
        protocol = json.loads((ROOT / "data/stim_protocol.json").read_text(encoding="utf-8"))
        spec = json.loads((ROOT / "data/stim_protocol_pharyngeal.json").read_text(encoding="utf-8"))
        cells = json.loads((ROOT / "data/cells.json").read_text(encoding="utf-8"))
        groups = groups_for(spec, protocol, select_conditions()[0], cells)
        self.assertNotIn("driven_pharyngeal", groups)
        self.assertNotIn("driven_sugar", groups)

    def test_combined_sanity_groups_cover_all_eight_phg1_and_twenty_three_sugar_cells(self):
        protocol = json.loads((ROOT / "data/stim_protocol.json").read_text(encoding="utf-8"))
        spec = json.loads((ROOT / "data/stim_protocol_pharyngeal.json").read_text(encoding="utf-8"))
        cells = json.loads((ROOT / "data/cells.json").read_text(encoding="utf-8"))
        groups = groups_for(spec, protocol, select_conditions()[18], cells)
        self.assertEqual(len(groups["driven_pharyngeal"]), 8)
        self.assertEqual(set(groups["driven_pharyngeal"]), {
            row["Body_ID"] for row in spec["pharyngeal_neurons"] if row["Type"] == "PhG1"
        })
        self.assertEqual(len(groups["driven_sugar"]), 23)
        self.assertEqual(set(groups["driven_sugar"]), {str(i) for i in cells["sets"]["sugar"]["ids"]})
        self.assertTrue(set(groups["driven_pharyngeal"]).isdisjoint(groups["driven_sugar"]))


class RawResultValidationTests(unittest.TestCase):
    """An empty spike array is valid only with explicit, complete trial coverage."""

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="askfly_phg_test_")
        self.addCleanup(self.temporary.cleanup)
        self.path = Path(self.temporary.name) / "P_baseline.npz"
        self.protocol = json.loads((ROOT / "data/stim_protocol.json").read_text(encoding="utf-8"))
        self.spec = json.loads((ROOT / "data/stim_protocol_pharyngeal.json").read_text(encoding="utf-8"))
        self.cells = json.loads((ROOT / "data/cells.json").read_text(encoding="utf-8"))
        self.condition = select_conditions()[0]
        self.expected = result_identity(self.condition, {"fixture": "synthetic, no simulation"})
        descriptions = [{
            "Body_ID": row["Body_ID"], "Root_Side": row["Root_Side"], "Type": row["Type"],
            "Target_Muscle": row["Target_Muscle"], "role": "MN_readout",
        } for row in self.spec["readout_neurons"]]
        groups = groups_for(self.spec, self.protocol, self.condition, self.cells)
        individuals, grouped = [], []
        for trial in range(10):
            prefix = {"condition_id": "P_baseline", "condition_index": 0,
                      "trial": trial, "seed": 20260910 + trial}
            individuals.extend({**prefix, **row, "spike_count": 0,
                                "rate_hz": 0.0, "first_spike_ms": None} for row in descriptions)
            grouped.extend({**prefix, "readout": name, "n_neurons": len(roots),
                            "spike_count": 0, "total_rate_hz": 0.0, "rate_hz": 0.0,
                            "first_spike_ms": None} for name, roots in groups.items())
        self.raw = {
            "flywire_id": np.array([], dtype=np.int64),
            "t_ms": np.array([], dtype=np.float64),
            "trial": np.array([], dtype=np.int64),
            "seeds": np.array(self.expected["seeds"], dtype=np.int64),
            "completed_trials": np.arange(10, dtype=np.int64),
            "saved_neuron_ids": np.array([int(row["Body_ID"]) for row in descriptions], dtype=np.int64),
        }
        self.saved = {"identity": copy.deepcopy(self.expected), "completed_trials": list(range(10)),
                      "individual": individuals, "grouped": grouped}
        self.write_raw()

    def write_raw(self):
        np.savez_compressed(self.path, **self.raw)
        self.saved["spikes_sha256"] = sha256(self.path)

    def validate(self):
        return validate_result(self.saved, self.path, self.expected, self.spec,
                               self.protocol, self.cells, self.condition)

    def test_complete_all_silent_trials_are_valid_not_missing(self):
        self.assertEqual(self.validate(), self.saved)
        self.assertEqual(len(self.saved["individual"]), 120)

    def test_missing_ledger_trial_is_not_filled_as_silence(self):
        self.saved["completed_trials"].pop()
        with self.assertRaisesRegex(ValueError, "completion"):
            self.validate()

    def test_missing_raw_trial_marker_is_not_filled_as_silence(self):
        self.raw["completed_trials"] = np.arange(9, dtype=np.int64)
        self.write_raw()
        with self.assertRaisesRegex(ValueError, "completed_trials"):
            self.validate()

    def test_duplicate_raw_trial_marker_is_not_complete(self):
        self.raw["completed_trials"][-1] = 8
        self.write_raw()
        with self.assertRaisesRegex(ValueError, "completed_trials"):
            self.validate()

    def test_missing_individual_rows_are_not_filled_as_silence(self):
        self.saved["individual"] = self.saved["individual"][:-12]
        with self.assertRaisesRegex(ValueError, "metrics"):
            self.validate()

    def test_changed_derived_rate_is_rejected_against_raw_spikes(self):
        self.saved["grouped"][0]["rate_hz"] = 1.0
        with self.assertRaisesRegex(ValueError, "metrics"):
            self.validate()

    def test_wrong_raw_seed_is_rejected_even_when_file_hash_matches(self):
        self.raw["seeds"][0] += 1
        self.write_raw()
        with self.assertRaisesRegex(ValueError, "seeds"):
            self.validate()

    def test_saved_neuron_inventory_cannot_omit_a_silent_neuron(self):
        self.raw["saved_neuron_ids"] = self.raw["saved_neuron_ids"][:-1]
        self.write_raw()
        with self.assertRaisesRegex(ValueError, "saved_neuron_ids"):
            self.validate()

    def test_raw_spikes_cannot_include_an_unrequested_neuron(self):
        self.raw["flywire_id"] = np.array([720575940000000001], dtype=np.int64)
        self.raw["t_ms"] = np.array([100.0], dtype=np.float64)
        self.raw["trial"] = np.array([0], dtype=np.int64)
        self.write_raw()
        with self.assertRaisesRegex(ValueError, "unrequested"):
            self.validate()

    def test_trial_indices_cannot_exceed_the_ten_authorised_trials(self):
        self.raw["flywire_id"] = self.raw["saved_neuron_ids"][:1]
        self.raw["t_ms"] = np.array([100.0], dtype=np.float64)
        self.raw["trial"] = np.array([10], dtype=np.int64)
        self.write_raw()
        with self.assertRaisesRegex(ValueError, "trial indices"):
            self.validate()

    def test_file_hash_mismatch_is_not_ignored(self):
        self.saved["spikes_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "hash"):
            self.validate()


if __name__ == "__main__":
    unittest.main()
