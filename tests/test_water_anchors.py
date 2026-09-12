# SPDX-License-Identifier: MIT
"""scripts/check_water_anchors.py: a stability run whose modal water level for an anchor food
leaves its anchor is reported per (food, language); it never rewrites anything."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import check_water_anchors as w  # noqa: E402


def rows(food_en, lang, waters):
    return [{"food_index": 0, "food": {"zh": "x", "en": food_en}, "lang": lang, "repeat": i + 1,
             "entry": {"key": food_en, "water": water, "sugar": "none", "bitter": "none"}}
            for i, water in enumerate(waters)]


class WaterAnchors(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.raw = Path(self.tmp.name) / "raw.jsonl"

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, records):
        self.raw.write_text("\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")

    def test_anchor_at_its_level_passes(self):
        self.write(rows("miso soup", "zh", ["medium"] * 6) + rows("miso soup", "en", ["medium"] * 6))
        self.assertEqual(w.check(self.raw), ([], 1))

    def test_drift_is_reported_per_language(self):
        self.write(rows("miso soup", "zh", ["high"] * 6) + rows("miso soup", "en", ["medium"] * 5 + ["high"]))
        drift, checked = w.check(self.raw)
        self.assertEqual(checked, 1)
        self.assertEqual(len(drift), 1)
        self.assertIn("miso soup [zh]: water modal high, anchor medium (6/6 runs)", drift[0])

    def test_non_anchor_foods_are_ignored_and_nothing_is_rewritten(self):
        self.write(rows("hotpot", "en", ["low"] * 3))
        before = self.raw.read_text(encoding="utf-8")
        self.assertEqual(w.check(self.raw), ([], 0))
        self.assertEqual(self.raw.read_text(encoding="utf-8"), before)


if __name__ == "__main__":
    unittest.main()
