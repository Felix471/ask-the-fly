"""Synthetic, source-free tests for the connectome-only CEM input audit."""

import unittest

import pandas as pd

from scripts.cem_inputs import exact_id, input_metrics, select_pharyngeal_rows, validate_edges
from scripts.cross_check_cells import FLYWIRE


PRE = "Presynaptic_ID"
POST = "Postsynaptic_ID"
SYN = "Connectivity"
SIGN = "Excitatory"
WEIGHT = "Excitatory x Connectivity"


def edges(rows):
    return pd.DataFrame([(a, b, n, sign, n * sign) for a, b, n, sign in rows],
                        columns=[PRE, POST, SYN, SIGN, WEIGHT])


class InputMetricsTests(unittest.TestCase):
    def test_direct_and_two_hop_count_real_edges_not_path_products(self):
        graph = edges([(1, 10, 3, 1), (2, 10, 5, -1), (10, 90, 7, 1),
                       (10, 91, 11, 1), (1, 90, 2, 1), (50, 90, 13, -1)])
        result = input_metrics(graph, {1, 2}, {90})
        self.assertEqual(result["direct_synapses"], 2)
        self.assertEqual(result["two_hop_first_leg_synapses"], 8)
        self.assertEqual(result["two_hop_last_leg_synapses"], 7)
        self.assertEqual(result["two_hop_intermediates"], 1)
        self.assertEqual(result["total_presynaptic_partners"], 3)
        self.assertEqual(result["total_input_synapses"], 22)
        self.assertEqual(result["two_hop_first_leg_negative_synapses"], 5)
        self.assertEqual(result["total_negative_synapses"], 13)

    def test_union_deduplicates_first_leg_across_convergent_target_paths(self):
        graph = edges([(1, 10, 3, 1), (2, 10, 5, -1), (10, 90, 7, 1), (10, 91, 11, 1)])
        result = input_metrics(graph, {1, 2}, {90, 91})
        self.assertEqual(result["two_hop_first_leg_synapses"], 8)
        self.assertEqual(result["two_hop_last_leg_synapses"], 18)
        self.assertEqual(result["total_presynaptic_partners"], 1)
        self.assertEqual(result["total_input_synapses"], 18)

    def test_disconnected_and_direct_only(self):
        graph = edges([(1, 90, 2, -1), (2, 10, 5, 1), (20, 90, 7, 1)])
        result = input_metrics(graph, {1, 2}, {90})
        self.assertEqual(result["direct_synapses"], 2)
        self.assertEqual(result["direct_negative_synapses"], 2)
        self.assertEqual(result["two_hop_first_leg_synapses"], 0)
        self.assertEqual(result["two_hop_last_leg_synapses"], 0)

    def test_negative_last_leg_counts_magnitude_not_cancellation(self):
        graph = edges([(1, 10, 3, 1), (1, 11, 5, 1), (10, 90, 7, 1), (11, 90, 11, -1)])
        result = input_metrics(graph, {1}, {90})
        self.assertEqual(result["two_hop_last_leg_synapses"], 18)
        self.assertEqual(result["two_hop_last_leg_positive_synapses"], 7)
        self.assertEqual(result["two_hop_last_leg_negative_synapses"], 11)

    def test_large_ids_remain_distinct(self):
        source, other, target = 720575940660219265, 720575940660219266, 720575940621126384
        result = input_metrics(edges([(source, target, 7, 1), (other, target, 11, -1)]),
                               {str(source)}, {str(target)})
        self.assertEqual(result["direct_synapses"], 7)
        self.assertEqual(result["total_input_synapses"], 18)

    def test_direct_edges_and_two_hop_edges_are_not_claimed_disjoint(self):
        graph = edges([(1, 2, 3, 1), (2, 90, 5, 1), (1, 90, 7, 1)])
        result = input_metrics(graph, {1, 2}, {90})
        self.assertEqual(result["direct_synapses"], 12)
        self.assertEqual(result["two_hop_first_leg_synapses"], 3)
        self.assertEqual(result["two_hop_last_leg_synapses"], 5)


class ValidationTests(unittest.TestCase):
    def test_id_validation_rejects_float_bool_and_noncanonical_strings(self):
        for value in (True, False, 720575940660219265.0, "7e17", "01", " 1", -1, 0):
            with self.subTest(value=value), self.assertRaises(ValueError):
                exact_id(value)
        self.assertEqual(exact_id("720575940660219265"), 720575940660219265)

    def test_float_ids_in_graph_rejected(self):
        graph = edges([(1, 90, 7, 1)])
        graph[PRE] = graph[PRE].astype(float)
        with self.assertRaises(ValueError):
            validate_edges(graph)

    def test_duplicate_directed_pair_rejected(self):
        with self.assertRaises(ValueError):
            validate_edges(edges([(1, 90, 7, 1), (1, 90, 3, 1)]))

    def test_bad_synapse_counts_rejected(self):
        for count in (-1, 0, 1.5):
            with self.subTest(count=count), self.assertRaises(ValueError):
                validate_edges(edges([(1, 90, count, 1)]))

    def test_signed_weight_must_equal_sign_times_unsigned_synapses(self):
        graph = edges([(1, 90, 7, -1)])
        graph.loc[0, WEIGHT] = 7
        with self.assertRaises(ValueError):
            validate_edges(graph)
        with self.assertRaises(ValueError):
            validate_edges(edges([(1, 90, 7, 0)]))

    def test_missing_columns_rejected(self):
        with self.assertRaises(ValueError):
            validate_edges(edges([(1, 90, 7, 1)]).drop(columns=[SYN]))


class PharyngealSourceTests(unittest.TestCase):
    def row(self, root_id="720575940658442625", kind="PhG1", **changes):
        return {"Connectome": FLYWIRE, "Body_ID": root_id, "Type": kind,
                "Root_Side": "R", "Subclass": "Pharyngeal", **changes}

    def test_selects_only_flywire_phg_types_and_preserves_exact_source(self):
        chosen = self.row()
        rows = [chosen, self.row("2", Connectome="hemibrain"), self.row("3", "LB1", Subclass="Labellar"),
                self.row("4", "PhG16", Root_Side="L")]
        self.assertEqual(select_pharyngeal_rows(rows), [chosen, rows[3]])

    def test_bad_type_or_subclass_is_not_silently_omitted(self):
        for row in (self.row(kind="PhG17"), self.row(Subclass="Labellar"),
                    self.row(Body_ID="7.2e17"), self.row(Root_Side="?")):
            with self.subTest(row=row), self.assertRaises(ValueError):
                select_pharyngeal_rows([row])

    def test_duplicate_pharyngeal_body_id_rejected(self):
        with self.assertRaises(ValueError):
            select_pharyngeal_rows([self.row(), self.row(kind="PhG2")])


if __name__ == "__main__":
    unittest.main()
