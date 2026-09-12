# SPDX-License-Identifier: MIT
"""D07: a stability batch must be complete and single-version before it can be merged; otherwise only a draft."""

import json
import tempfile
import unittest
from pathlib import Path

from encoder import merge as m


def entry(
    key, sugar="low", bitter="none", water="low", version="model@encode_v2.2",
    ir94e=None,
):
    result = {
        "key": key, "aliases": [], "display": {"zh": key, "en": key},
        "sugar": sugar, "bitter": bitter, "water": water,
        "reason": {"sugar": "r", "bitter": "r", "water": "r"},
        "confidence": {"sugar": 0.9, "bitter": 0.9, "water": 0.9},
        "review": "llm_v1", "encoder_version": version,
    }
    if ir94e is not None:
        result["ir94e"] = ir94e
        result["reason"]["ir94e"] = "r"
        result["confidence"]["ir94e"] = 0.9
    return result


FOODS = [{"zh": "菜一", "en": "dish one", "key": "dish-one"}, {"zh": "菜二", "en": "dish two", "key": "dish-two"}]


def records(
    repeats=3, langs=("zh", "en"), version="model@encode_v2.2", foods=FOODS,
    ir94e=None, ir94e_by_lang=None,
):
    rows = []
    for index, food in enumerate(foods):
        for lang in langs:
            for repeat in range(1, repeats + 1):
                rows.append({
                    "food_index": index, "food": food, "lang": lang, "repeat": repeat,
                    "encoder_version": version, "prompt_version": version.split("@")[1],
                    "schema_version": "schema_v2" if ir94e is not None or ir94e_by_lang else "schema_v1",
                    "entry": entry(
                        food["key"], version=version,
                        ir94e=(ir94e_by_lang or {}).get(lang, ir94e),
                    ),
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

    def test_batch_missing_a_whole_trailing_food_cannot_merge(self):
        self.write([r for r in records() if r["food_index"] == 0])
        with self.assertRaises(m.MergeError) as ctx:
            m.merge(self.raw, self.dest, replace_llm=True)
        self.assertIn("food 1", str(ctx.exception))
        self.assertEqual(self.dest.read_text(encoding="utf-8"), "[]")

    def test_full_merge_reports_a_dropped_ir94e(self):
        self.dest.write_text(json.dumps([entry("dish-one", ir94e="low"), entry("dish-two", ir94e="low")]), encoding="utf-8")
        self.write(records(version="model@encode_v2.2"))
        import io, contextlib
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            m.merge(self.raw, self.dest, replace_llm=True)
        self.assertIn("dropped ir94e from 'dish-one'", out.getvalue())
        self.assertIn("dish-one | ir94e | low -> (absent)", out.getvalue())
        self.assertNotIn("ir94e", json.loads(self.dest.read_text(encoding="utf-8"))[0])

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


class OnlyDimensionMerge(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.foods = self.root / "foods.json"
        self.foods.write_text(json.dumps(FOODS, ensure_ascii=False), encoding="utf-8")
        self.dest = self.root / "dishes.json"
        self.raw = self.root / "raw.jsonl"
        m.FOODS_OVERRIDE = self.foods
        m.STABILITY_REPEATS = 3
        first = entry("dish-one", version="model@encode_v2.2")
        first["arbitration"] = {
            "water": {
                "zh": "low", "en": "medium", "chosen": "low", "rule": "lower_level",
            }
        }
        second = entry("dish-two", version="model@encode_v2.2")
        second["review"] = "human_checked"
        self.initial = [first, second]
        self._reset_destination()

    def tearDown(self):
        m.FOODS_OVERRIDE = None
        m.STABILITY_REPEATS = 6
        self.tmp.cleanup()

    def write(self, rows):
        self.raw.write_text(
            "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
            encoding="utf-8",
        )

    def _reset_destination(self):
        self.dest.write_text(
            json.dumps(self.initial, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    @staticmethod
    def _old_projection(value):
        return {
            "sugar": value["sugar"], "bitter": value["bitter"], "water": value["water"],
            "reason": {k: v for k, v in value["reason"].items() if k != "ir94e"},
            "confidence": {k: v for k, v in value["confidence"].items() if k != "ir94e"},
            "review": value["review"], "encoder_version": value["encoder_version"],
            "aliases": value["aliases"], "display": value["display"],
            "water_arbitration": value.get("arbitration", {}).get("water"),
        }

    def test_only_ir94e_leaves_other_fields_byte_identical(self):
        before = json.loads(self.dest.read_text(encoding="utf-8"))
        self.write(records(version="model@encode_v2.3", ir94e="low"))
        m.merge(self.raw, self.dest, replace_llm=True, only_dimension="ir94e")
        after = json.loads(self.dest.read_text(encoding="utf-8"))
        for old, new in zip(before, after):
            self.assertEqual(
                json.dumps(self._old_projection(old), sort_keys=True),
                json.dumps(self._old_projection(new), sort_keys=True),
            )
            self.assertEqual(new["ir94e"], "low")
            self.assertEqual(new["reason"]["ir94e"], "r")
            self.assertEqual(new["confidence"]["ir94e"], 0.9)
            self.assertEqual(
                new["encoder_version_by_dimension"], {"ir94e": "model@encode_v2.3"}
            )
        self.assertEqual(after[1]["review"], "human_checked")

    def test_only_ir94e_key_order_is_stable(self):
        self.write(records(version="model@encode_v2.3", ir94e="low"))
        m.merge(self.raw, self.dest, only_dimension="ir94e")
        written = json.loads(self.dest.read_text(encoding="utf-8"))[0]
        self.assertEqual(list(written), [
            "key", "aliases", "display", "sugar", "bitter", "water", "ir94e", "reason",
            "confidence", "review", "encoder_version", "encoder_version_by_dimension",
            "arbitration",
        ])

    def test_very_high_ir94e_is_rejected(self):
        original = self.dest.read_text(encoding="utf-8")
        self.write(records(version="model@encode_v2.3", ir94e="very_high"))
        with self.assertRaisesRegex(m.MergeError, "ir94e"):
            m.merge(self.raw, self.dest, only_dimension="ir94e")
        self.assertEqual(self.dest.read_text(encoding="utf-8"), original)

    def test_missing_ir94e_is_rejected_when_flag_set(self):
        original = self.dest.read_text(encoding="utf-8")
        self.write(records(version="model@encode_v2.2"))
        with self.assertRaisesRegex(m.MergeError, "ir94e"):
            m.merge(self.raw, self.dest, only_dimension="ir94e")
        self.assertEqual(self.dest.read_text(encoding="utf-8"), original)

    def test_missing_ir94e_is_fine_without_flag(self):
        self.write(records(version="model@encode_v2.2"))
        m.merge(self.raw, self.dest, replace_llm=True)
        written = json.loads(self.dest.read_text(encoding="utf-8"))
        self.assertNotIn("ir94e", written[0])

    def test_unknown_dish_is_rejected_in_only_dimension_mode(self):
        original = self.dest.read_text(encoding="utf-8")
        foods = [*FOODS, {"zh": "菜三", "en": "dish three", "key": "dish-three"}]
        self.foods.write_text(json.dumps(foods, ensure_ascii=False), encoding="utf-8")
        self.write(records(version="model@encode_v2.3", foods=foods, ir94e="low"))
        with self.assertRaisesRegex(m.MergeError, "not in the dictionary"):
            m.merge(self.raw, self.dest, only_dimension="ir94e")
        self.assertEqual(self.dest.read_text(encoding="utf-8"), original)

    def test_ir94e_needs_review_rule(self):
        self.write(records(
            version="model@encode_v2.3",
            ir94e_by_lang={"zh": "none", "en": "medium"},
        ))
        m.merge(self.raw, self.dest, only_dimension="ir94e")
        written = json.loads(self.dest.read_text(encoding="utf-8"))
        self.assertEqual(written[0]["review"], "needs_review")
        self.assertEqual(written[0]["arbitration"]["ir94e"], {
            "zh": "none", "en": "medium", "chosen": "medium", "rule": "needs_review",
        })
        self.assertEqual(written[0]["arbitration"]["water"], self.initial[0]["arbitration"]["water"])

        self._reset_destination()
        self.write(records(
            version="model@encode_v2.3", ir94e_by_lang={"zh": "none", "en": "low"},
        ))
        m.merge(self.raw, self.dest, only_dimension="ir94e")
        written = json.loads(self.dest.read_text(encoding="utf-8"))
        self.assertEqual(written[0]["ir94e"], "none")
        self.assertEqual(written[0]["arbitration"]["ir94e"]["rule"], "lower_level")
        self.assertEqual(written[0]["review"], "llm_v1")

    def test_only_dimension_rejects_core_dimensions(self):
        self.write(records())
        with self.assertRaises(m.MergeError):
            m.merge(self.raw, self.dest, only_dimension="sugar")


class EncodeValidation(unittest.TestCase):
    @staticmethod
    def payload():
        return {
            "key": "dish", "aliases": ["Dish"], "display": {"zh": "菜", "en": "Dish"},
            "sugar": "low", "bitter": "none", "water": "medium", "ir94e": "high",
            "reason": {"sugar": "r", "bitter": "r", "water": "r", "ir94e": "r"},
            "confidence": {"sugar": 0.9, "bitter": 0.9, "water": 0.9, "ir94e": 0.9},
        }

    def test_v23_four_dimensions_validate(self):
        from encoder import encode as e

        result = e._validate_model_entry(self.payload(), "m", "encode_v2.3")
        self.assertEqual(result["ir94e"], "high")
        self.assertEqual(result["reason"]["ir94e"], "r")
        self.assertEqual(result["confidence"]["ir94e"], 0.9)
        self.assertEqual(result["encoder_version"], "m@encode_v2.3")

    def test_v23_rejects_very_high_ir94e(self):
        from encoder import encode as e

        payload = self.payload(); payload["ir94e"] = "very_high"
        with self.assertRaisesRegex(ValueError, "ir94e"):
            e._validate_model_entry(payload, "m", "encode_v2.3")

    def test_v23_requires_ir94e(self):
        from encoder import encode as e

        payload = self.payload(); del payload["ir94e"]
        with self.assertRaises(ValueError):
            e._validate_model_entry(payload, "m", "encode_v2.3")

    def test_v22_accepts_three_dimensions(self):
        from encoder import encode as e

        payload = self.payload()
        del payload["ir94e"]; del payload["reason"]["ir94e"]; del payload["confidence"]["ir94e"]
        result = e._validate_model_entry(payload, "m", "encode_v2.2")
        self.assertNotIn("ir94e", result)

    def test_dimensions_for_prompt(self):
        from encoder import encode as e

        self.assertEqual(e.dimensions_for("encode_v2.2"), ("sugar", "bitter", "water"))
        self.assertIn("ir94e", e.dimensions_for("encode_v2.3"))
        self.assertIn("ir94e", e.dimensions_for("encode_v3"))


class LevelsForIr94e(unittest.TestCase):
    def test_levels_and_grid_mapping(self):
        from encoder.levels import IR94E_HZ, LEVELS, levels_for

        self.assertEqual(levels_for("ir94e"), ("none", "low", "medium", "high"))
        self.assertIs(levels_for("sugar"), LEVELS)
        grid_path = Path(__file__).resolve().parents[1] / "data" / "grid_levels.json"
        grid = json.loads(grid_path.read_text(encoding="utf-8"))
        self.assertEqual(IR94E_HZ, grid["levels"]["ir94e"])


if __name__ == "__main__":
    unittest.main()
