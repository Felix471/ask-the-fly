import unittest

import pandas as pd

from scripts.salt_output_signs import audit_signs


class SaltOutputSignsTests(unittest.TestCase):
    def inputs(self):
        rows = [{"Body_ID": "101", "Subtype": "LB3d"}, {"Body_ID": "102", "Subtype": "LB3b"}]
        edges = pd.DataFrame({"Presynaptic_ID": [101, 101, 102], "Postsynaptic_ID": [201, 202, 201],
                              "Connectivity": [3, 2, 4], "Excitatory": [1, 1, 1],
                              "Excitatory x Connectivity": [3, 2, 4]})
        annotations = pd.DataFrame({"root_id": ["101", "102"], "top_nt": ["glutamate", "serotonin"]})
        return rows, edges, annotations

    def test_counts_neurons_not_edges_and_compares_explicit_annotation(self):
        result = audit_signs(*self.inputs())
        self.assertEqual(result["summary"]["LB3d"]["positive_cells"], 1)
        self.assertEqual(result["summary"]["LB3d"]["top_nt_sign_disagreements"], 1)
        self.assertEqual(result["summary"]["LB3b"]["top_nt_sign_disagreements"], 0)
        self.assertEqual(result["neurons"][0]["output_synapses"], 5)

    def test_missing_output_is_not_silently_positive(self):
        rows, edges, annotations = self.inputs()
        with self.assertRaises(ValueError):
            audit_signs(rows, edges.iloc[:2], annotations)

    def test_inconsistent_outputs_rejected(self):
        rows, edges, annotations = self.inputs()
        edges.loc[1, "Excitatory"] = -1
        edges.loc[1, "Excitatory x Connectivity"] = -2
        with self.assertRaises(ValueError):
            audit_signs(rows, edges, annotations)

    def test_missing_or_unknown_annotation_rejected(self):
        rows, edges, annotations = self.inputs()
        with self.assertRaises(ValueError):
            audit_signs(rows, edges, annotations.iloc[:1])
        annotations.loc[0, "top_nt"] = "unknown"
        with self.assertRaises(ValueError):
            audit_signs(rows, edges, annotations)

    def test_duplicate_id_rejected(self):
        rows, edges, annotations = self.inputs()
        with self.assertRaises(ValueError):
            audit_signs(rows + rows[:1], edges, annotations)
        with self.assertRaises(ValueError):
            audit_signs(rows, edges, pd.concat([annotations, annotations.iloc[:1]]))

    def test_negative_matches_glutamate(self):
        rows, edges, annotations = self.inputs()
        edges.loc[:1, "Excitatory"] = -1
        edges.loc[:1, "Excitatory x Connectivity"] *= -1
        result = audit_signs(rows, edges, annotations)
        self.assertEqual(result["summary"]["LB3d"]["negative_cells"], 1)
        self.assertEqual(result["summary"]["LB3d"]["top_nt_sign_disagreements"], 0)


if __name__ == "__main__":
    unittest.main()
