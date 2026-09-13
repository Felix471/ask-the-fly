# SPDX-License-Identifier: MIT
"""Synthetic replay-screen checks; no simulation or local research inputs required."""

from __future__ import annotations

import copy
import json
import struct
import tempfile
import unittest
from pathlib import Path

import numpy as np

from scripts.mn_readouts_from_replays import (
    aggregate_metrics,
    neuron_metrics,
    read_replay_header,
    spearman,
    validate_replay,
    verify_mn9,
)


LEFT = 720575940660219265
RIGHT = 720575940618238523
SILENT = 720575940660219266


def replay_fixture():
    condition = {
        "cond_id": "G_s1_b0_w0_i0",
        "global_index": 17,
        "rates": {"sugar": 20.0, "bitter": 0.0, "water": 0.0, "ir94e": 0.0},
        "levels": {"sugar": "low", "bitter": "none", "water": "none", "ir94e": "none"},
    }
    data = {
        "flywire_id": np.array([RIGHT, LEFT, LEFT, SILENT], dtype=np.int64),
        "t_ms": np.array([0.0, 123.44, 999.95, 200.0]),
        "seed": np.int64(700_017),
        "condition_index": np.int64(17),
        "rates": np.array([20.0, 0.0, 0.0, 0.0]),
    }
    return condition, data


def mn9_fixture():
    condition, data = replay_fixture()
    header = {
        "schema_version": "replay_v2",
        "cell_id": condition["cond_id"],
        "variant": "baseline",
        "silenced": None,
        "silenced_root_ids": [],
        "levels": condition["levels"].copy(),
        "hz": condition["rates"].copy(),
        "seed": int(data["seed"]),
        "duration_ms": 1000.0,
        "n_spikes": 4,
        "mn9_left_ms": [123.4, 1000.0],
        "mn9_right_ms": [0.0],
        "mn9_left_first_ms": 123.4,
        "mn9_right_first_ms": 0.0,
        "mn9_left_count": 2,
        "mn9_right_count": 1,
    }
    manifest_cell = {
        "levels": condition["levels"].copy(),
        "n_spikes": 4,
        "mn9_left_count": 2,
    }
    protocol = {"readout": {"left": LEFT, "right": RIGHT}}
    return data, header, manifest_cell, condition, protocol


class NeuronMetricsTests(unittest.TestCase):
    def test_counts_hz_and_first_spike_keep_large_ids_exact(self):
        actual = neuron_metrics(
            np.array([LEFT, RIGHT, LEFT, LEFT], dtype=np.int64),
            np.array([400.0, 0.0, 10.0, 200.0]),
            [str(LEFT), RIGHT, str(SILENT)],
            500.0,
        )
        self.assertEqual(set(actual), {str(LEFT), str(RIGHT), str(SILENT)})
        self.assertEqual(actual[str(LEFT)], {
            "spike_count": 3, "rate_hz": 6.0, "first_spike_ms": 10.0,
        })
        self.assertEqual(actual[str(RIGHT)], {
            "spike_count": 1, "rate_hz": 2.0, "first_spike_ms": 0.0,
        })
        self.assertEqual(actual[str(SILENT)], {
            "spike_count": 0, "rate_hz": 0.0, "first_spike_ms": None,
        })

    def test_empty_spike_table_preserves_silent_readouts(self):
        actual = neuron_metrics(
            np.array([], dtype=np.int64), np.array([], dtype=float), [LEFT], 1000.0,
        )
        self.assertEqual(actual[str(LEFT)], {
            "spike_count": 0, "rate_hz": 0.0, "first_spike_ms": None,
        })

    def test_ignores_spikes_from_other_neurons(self):
        actual = neuron_metrics(
            np.array([RIGHT, RIGHT], dtype=np.int64), np.array([10.0, 20.0]),
            [LEFT], 1000.0,
        )
        self.assertEqual(actual[str(LEFT)]["spike_count"], 0)

    def test_rejects_float_neuron_ids_even_if_integral(self):
        with self.assertRaises(ValueError):
            neuron_metrics(np.array([float(LEFT)]), np.array([1.0]), [LEFT], 1000.0)

    def test_requested_ids_reject_lossy_numeric_and_boolean_coercion(self):
        for root_id in (float(LEFT), np.float64(LEFT), 1.0, True, False, np.bool_(True)):
            with self.subTest(root_id=root_id):
                with self.assertRaises(ValueError):
                    neuron_metrics(
                        np.array([LEFT], dtype=np.int64), np.array([1.0]),
                        [root_id], 1000.0,
                    )

    def test_requested_ids_accept_exact_python_numpy_and_string_integers(self):
        for root_id in (LEFT, np.int64(LEFT), np.uint64(LEFT), str(LEFT)):
            with self.subTest(root_id=root_id):
                actual = neuron_metrics(
                    np.array([LEFT], dtype=np.int64), np.array([1.0]),
                    [root_id], 1000.0,
                )
                self.assertEqual(actual[str(LEFT)]["spike_count"], 1)

    def test_rejects_wrong_shape_or_mismatched_lengths(self):
        for ids, times in (
            (np.array([[LEFT]]), np.array([1.0])),
            (np.array([LEFT]), np.array([[1.0]])),
            (np.array([LEFT, RIGHT]), np.array([1.0])),
            (np.array(LEFT), np.array(1.0)),
        ):
            with self.subTest(ids=ids, times=times):
                with self.assertRaises(ValueError):
                    neuron_metrics(ids, times, [LEFT], 1000.0)

    def test_rejects_times_outside_half_open_trial_window(self):
        for invalid in (-0.1, 1000.0, 1000.1, float("nan"), float("inf"), -float("inf")):
            with self.subTest(time=invalid):
                with self.assertRaises(ValueError):
                    neuron_metrics(np.array([LEFT]), np.array([invalid]), [LEFT], 1000.0)

    def test_rejects_invalid_duration(self):
        for duration in (0.0, -1.0, float("nan"), float("inf")):
            with self.subTest(duration=duration):
                with self.assertRaises(ValueError):
                    neuron_metrics(np.array([LEFT]), np.array([0.0]), [LEFT], duration)


class AggregateMetricsTests(unittest.TestCase):
    def test_mean_includes_silent_neurons_and_latency_is_earliest(self):
        actual = aggregate_metrics([
            {"spike_count": 3, "rate_hz": 6.0, "first_spike_ms": 100.0},
            {"spike_count": 0, "rate_hz": 0.0, "first_spike_ms": None},
            {"spike_count": 1, "rate_hz": 2.0, "first_spike_ms": 0.0},
        ])
        self.assertEqual(actual, {
            "n_neurons": 3,
            "spike_count": 4,
            "total_rate_hz": 8.0,
            "rate_hz": 8.0 / 3.0,
            "first_spike_ms": 0.0,
        })

    def test_all_silent_is_zero_rate_not_missing_data(self):
        actual = aggregate_metrics([
            {"spike_count": 0, "rate_hz": 0.0, "first_spike_ms": None},
            {"spike_count": 0, "rate_hz": 0.0, "first_spike_ms": None},
        ])
        self.assertEqual(actual, {
            "n_neurons": 2,
            "spike_count": 0,
            "total_rate_hz": 0.0,
            "rate_hz": 0.0,
            "first_spike_ms": None,
        })

    def test_rejects_empty_group(self):
        with self.assertRaises(ValueError):
            aggregate_metrics([])


class SpearmanTests(unittest.TestCase):
    def test_identical_and_inverse_rankings(self):
        self.assertAlmostEqual(spearman([0, 1, 4, 100], [1, 2, 3, 4]), 1.0)
        self.assertAlmostEqual(spearman([0, 1, 4, 100], [4, 3, 2, 1]), -1.0)

    def test_ties_use_average_ranks(self):
        # Ranks are [1.5, 1.5, 3] and [1, 2.5, 2.5]; Pearson = 0.5.
        self.assertAlmostEqual(spearman([0, 0, 5], [0, 1, 1]), 0.5)

    def test_zero_spike_ties_are_observations_not_filtered(self):
        self.assertAlmostEqual(spearman([0, 0, 1, 2], [0, 1, 0, 2]), 0.5)

    def test_constant_input_has_undefined_correlation(self):
        self.assertIsNone(spearman([0, 0, 0], [1, 2, 3]))
        self.assertIsNone(spearman([1, 2, 3], [0, 0, 0]))
        self.assertIsNone(spearman([1], [2]))

    def test_rejects_invalid_arrays(self):
        for x, y in (
            ([], []),
            ([1, 2], [1]),
            ([1, float("nan")], [1, 2]),
            ([1, 2], [1, float("inf")]),
            ([[1, 2]], [[1, 2]]),
        ):
            with self.subTest(x=x, y=y):
                with self.assertRaises(ValueError):
                    spearman(x, y)


class ReplayValidationTests(unittest.TestCase):
    def test_valid_replay_and_silent_replay(self):
        condition, data = replay_fixture()
        self.assertIsNone(validate_replay(data, condition, 700_017, 1000.0))
        data["flywire_id"] = np.array([], dtype=np.int64)
        data["t_ms"] = np.array([], dtype=float)
        self.assertIsNone(validate_replay(data, condition, 700_017, 1000.0))

    def test_rejects_missing_required_keys(self):
        for key in ("flywire_id", "t_ms", "seed", "condition_index", "rates"):
            with self.subTest(key=key):
                condition, data = replay_fixture()
                del data[key]
                with self.assertRaises(ValueError):
                    validate_replay(data, condition, 700_017, 1000.0)

    def test_rejects_mismatched_seed_index_and_rates(self):
        for key, value in (
            ("seed", np.int64(700_018)),
            ("condition_index", np.int64(18)),
            ("rates", np.array([0.0, 20.0, 0.0, 0.0])),
            ("rates", np.array([20.0, 0.0, 0.0])),
            ("rates", np.array([[20.0, 0.0, 0.0, 0.0]])),
            ("rates", np.array([20.0, float("nan"), 0.0, 0.0])),
        ):
            with self.subTest(key=key, value=value):
                condition, data = replay_fixture()
                data[key] = value
                with self.assertRaises(ValueError):
                    validate_replay(data, condition, 700_017, 1000.0)

    def test_rejects_lossy_seed_and_index(self):
        for key in ("seed", "condition_index"):
            condition, data = replay_fixture()
            data[key] = np.float64(data[key])
            with self.subTest(key=key):
                with self.assertRaises(ValueError):
                    validate_replay(data, condition, 700_017, 1000.0)

    def test_rejects_malformed_spike_tables(self):
        for key, value in (
            ("flywire_id", np.array([float(LEFT)] * 4)),
            ("flywire_id", np.array([str(LEFT)] * 4)),
            ("flywire_id", np.array([[LEFT, RIGHT, LEFT, SILENT]])),
            ("flywire_id", np.array([LEFT], dtype=np.int64)),
            ("t_ms", np.array([0.0, 1.0, 2.0, 1000.0])),
            ("t_ms", np.array([0.0, 1.0, 2.0, -0.1])),
            ("t_ms", np.array([0.0, 1.0, 2.0, float("nan")])),
            ("t_ms", np.array([[0.0, 1.0, 2.0, 3.0]])),
        ):
            with self.subTest(key=key, value=value):
                condition, data = replay_fixture()
                data[key] = value
                with self.assertRaises(ValueError):
                    validate_replay(data, condition, 700_017, 1000.0)


class ReplayHeaderTests(unittest.TestCase):
    def test_reads_utf8_header_without_conflating_binary_payload(self):
        _, header, _, _, _ = mn9_fixture()
        header["note"] = "Synthetic replay: 果蝇"
        blob = json.dumps(header, ensure_ascii=False).encode("utf-8")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "replay.bin"
            path.write_bytes(b"AFR1" + struct.pack("<I", len(blob)) + blob + b"\xff\x00\x01\x00")
            self.assertEqual(read_replay_header(path), header)

    def test_rejects_magic_length_truncation_and_invalid_json(self):
        for name, contents in (
            ("empty", b""),
            ("bad magic", b"NOPE" + struct.pack("<I", 2) + b"{}"),
            ("short prefix", b"AFR1\x02\x00"),
            ("truncated header", b"AFR1" + struct.pack("<I", 20) + b"{}"),
            ("empty header", b"AFR1" + struct.pack("<I", 0)),
            ("bad json", b"AFR1" + struct.pack("<I", 3) + b"{??"),
            ("bad utf8", b"AFR1" + struct.pack("<I", 1) + b"\xff"),
        ):
            with self.subTest(name=name):
                with tempfile.TemporaryDirectory() as directory:
                    path = Path(directory) / "bad.bin"
                    path.write_bytes(contents)
                    with self.assertRaises(ValueError):
                        read_replay_header(path)


class Mn9SanityTests(unittest.TestCase):
    def test_exact_count_and_rounded_header_latency_checks_keep_raw_result(self):
        data, header, manifest, condition, protocol = mn9_fixture()
        # Rounded stored timestamps may equal 1000 ms; raw timestamps must be <1000.
        actual = verify_mn9(data, header, manifest, condition, protocol, 1000.0)
        self.assertEqual(actual, {
            "left_count": 2,
            "right_count": 1,
            "left_first_ms": 123.44,
            "right_first_ms": 0.0,
        })

    def test_all_silent_mn9_keeps_none_not_zero_latency(self):
        data, header, manifest, condition, protocol = mn9_fixture()
        data["flywire_id"] = np.array([SILENT], dtype=np.int64)
        data["t_ms"] = np.array([200.0])
        header["n_spikes"] = manifest["n_spikes"] = 1
        manifest["mn9_left_count"] = 0
        for side in ("left", "right"):
            header[f"mn9_{side}_count"] = 0
            header[f"mn9_{side}_ms"] = []
            header[f"mn9_{side}_first_ms"] = None
        self.assertEqual(verify_mn9(data, header, manifest, condition, protocol, 1000.0), {
            "left_count": 0,
            "right_count": 0,
            "left_first_ms": None,
            "right_first_ms": None,
        })

    def test_rejects_both_sides_counts_spike_arrays_and_latencies(self):
        for key, value in (
            ("mn9_left_count", 3),
            ("mn9_right_count", 0),
            ("mn9_left_ms", [123.4, 999.9]),
            ("mn9_right_ms", [0.1]),
            ("mn9_left_first_ms", 123.5),
            ("mn9_right_first_ms", None),
        ):
            with self.subTest(key=key):
                data, header, manifest, condition, protocol = mn9_fixture()
                header[key] = value
                with self.assertRaises(ValueError):
                    verify_mn9(data, header, manifest, condition, protocol, 1000.0)

    def test_rejects_wrong_manifest_count(self):
        data, header, manifest, condition, protocol = mn9_fixture()
        manifest["mn9_left_count"] = 3
        with self.assertRaises(ValueError):
            verify_mn9(data, header, manifest, condition, protocol, 1000.0)

    def test_rejects_wrong_header_provenance(self):
        _, base_header, _, _, _ = mn9_fixture()
        changed_rates = copy.deepcopy(base_header["hz"])
        changed_rates["sugar"] = 0.0
        for key, value in (
            ("cell_id", "different-cell"),
            ("seed", 700_018),
            ("duration_ms", 500.0),
            ("hz", changed_rates),
            ("variant", "silence_neuron"),
        ):
            with self.subTest(key=key):
                data, header, manifest, condition, protocol = mn9_fixture()
                header[key] = value
                with self.assertRaises(ValueError):
                    verify_mn9(data, header, manifest, condition, protocol, 1000.0)


if __name__ == "__main__":
    unittest.main()
