# SPDX-License-Identifier: MIT
"""D07: a stability batch must be complete and single-version before it can be merged; otherwise only a draft."""

import json
import tempfile
import unittest
from pathlib import Path

from encoder import merge as m


def entry(key, sugar="low", bitter="none", water="low", version="model@encode_v2.2"):
    return {
        "key": key, "aliases": [], "display": {"zh": key, "en": key},
        "sugar": sugar, "bitter": bitter, "water": water,
        "reason": {"sugar": "r", "bitter": "r", "water": "r"},
        "confidence": {"sugar": 0.9, "bitter": 0.9, "water": 0.9},
        "review": "llm_v1", "encoder_version": version,
    }


FOODS = [{"zh": "菜一", "en": "dish one", "key": "dish-one"}, {"zh": "菜二", "en": "dish two", "key": "dish-two"}]


def records(repeats=3, langs=("zh", "en"), version="model@encode_v2.2", foods=FOODS):
    rows = []
    for index, food in enumerate(foods):
        for lang in langs:
            for repeat in range(1, repeats + 1):
                rows.append({
                    "food_index": index, "food": food, "lang": lang, "repeat": repeat,
                    "encoder_version": version, "prompt_version": version.split("@")[1], "schema_version": "schema_v1",
                    "entry": entry(food["key"], version=version),
                })
    return rows


class ValidateStability(unittest.TestCase):
    def test_complete_batch_passes(self):
        self.assertEqual(m.validate_stability(records(), FOODS, repeats=3), [])

    def test_missing_repeat_is_reported(self):
        rows = [r for r in records() if not (r["food_index"] == 1 and r["lang"] == "en" and r["repeat"] == 3)]
        problems = m.validate_stability(rows, FOODS, repeats=3)
        self.assertTrue(any("food 1 en" in p and "missing repeats [3]" in p for p in problems), problems)

    def test_missing_language_is_reported(self):
        rows = [r for r in records() if r["lang"] == "zh"]
        problems = m.validate_stability(rows, FOODS, repeats=3)
        self.assertTrue(any("food 0 en" in p for p in problems), problems)

    def test_duplicate_repeat_id_is_reported_and_not_counted_as_extra_sample(self):
        rows = records()
        dup = dict(rows[0]); rows.append(dup)  # repeat 1 twice for food 0 zh
        problems = m.validate_stability(rows, FOODS, repeats=3)
        self.assertTrue(any("duplicate repeat ids [1]" in p for p in problems), problems)

    def test_mixed_encoder_versions_are_rejected(self):
        rows = records()
        rows[0]["encoder_version"] = "other@encode_v1"
        problems = m.validate_stability(rows, FOODS, repeats=3)
        self.assertTrue(any("mixed encoder_version" in p for p in problems), problems)

    def test_error_records_do_not_count_as_samples(self):
        rows = records()
        rows[5] = {"food_index": 0, "lang": "zh", "repeat": 3, "error": "timeout"}
        problems = m.validate_stability(rows, FOODS, repeats=3)
        self.assertTrue(any("error" in p for p in problems), problems)
        self.assertTrue(any("missing repeats" in p for p in problems), problems)


class MergeGate(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.foods = root / "foods.json"
        self.foods.write_text(json.dumps(FOODS, ensure_ascii=False), encoding="utf-8")
        self.dest = root / "dishes.json"
        self.dest.write_text("[]", encoding="utf-8")
        self.raw = root / "raw.jsonl"
        self.root = root
        m.FOODS_OVERRIDE = self.foods
        m.STABILITY_REPEATS = 3

    def tearDown(self):
        m.FOODS_OVERRIDE = None
        m.STABILITY_REPEATS = 6
        self.tmp.cleanup()

    def write(self, rows):
        self.raw.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")

    def test_complete_batch_merges(self):
        self.write(records())
        added, skipped, _ = m.merge(self.raw, self.dest, replace_llm=True)
        self.assertEqual(added, 2)
        self.assertEqual(len(json.loads(self.dest.read_text(encoding="utf-8"))), 2)

    def test_incomplete_batch_cannot_merge(self):
        self.write(records()[:-1])
        with self.assertRaises(m.MergeError) as ctx:
            m.merge(self.raw, self.dest, replace_llm=True)
        self.assertIn("incomplete", str(ctx.exception))
        self.assertEqual(self.dest.read_text(encoding="utf-8"), "[]", "destination untouched")

    def test_incomplete_batch_produces_a_draft_only(self):
        self.write(records()[:-1])
        draft = self.root / "draft.json"
        n = m.write_draft(self.raw, draft)
        self.assertEqual(n, 2)
        entries = json.loads(draft.read_text(encoding="utf-8"))
        self.assertTrue(all(e["review"] == "draft" for e in entries))
        self.assertEqual(self.dest.read_text(encoding="utf-8"), "[]")
        with self.assertRaises(m.MergeError):
            m.merge(draft, self.dest, replace_llm=True)  # a draft is not mergeable either


if __name__ == "__main__":
    unittest.main()
