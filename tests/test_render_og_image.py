# SPDX-License-Identifier: MIT
"""The link-preview image takes its example scores from the shipped data."""

import json
import unittest
from pathlib import Path

from scripts import render_og_image as og

ROOT = Path(__file__).resolve().parents[1]


class ExampleRows(unittest.TestCase):
    def test_rows_match_the_shipped_female_table(self):
        menu = {"watermelon": 70.567, "mapo tofu": 0.667, "black coffee": 0.0}
        rows = og.example_rows()
        self.assertEqual([round(hz, 3) for _label, hz, _win in rows], list(menu.values()))
        self.assertEqual([win for _label, _hz, win in rows], [True, False, False])
        self.assertEqual(rows[1][0], "mapo tofu 麻婆豆腐")

    def test_rows_follow_the_table_not_a_constant(self):
        table = json.loads(og.LOOKUP.read_text(encoding="utf-8"))
        dishes = json.loads(og.DISHES.read_text(encoding="utf-8"))
        entries = {e["key"]: e for e in (dishes["dishes"] if isinstance(dishes, dict) else dishes)}
        for label, hz, _win in og.example_rows(("honey", "steak")):
            key = "honey" if label.startswith("honey") else "steak"
            cell = next(c for c in table["cells"] if all(c["hz"][a] == table["levels"][a][entries[key].get(a, "none")] for a in og.AXES))
            self.assertEqual(hz, cell["mn9_mean"])

    def test_a_tied_top_is_refused(self):
        with self.assertRaises(ValueError):
            og.example_rows(("steak", "black coffee"))


if __name__ == "__main__":
    unittest.main()
