# SPDX-License-Identifier: MIT
"""Q06: every bad production bundle fails with its own reason; a good one passes."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import validate_release as vr  # noqa: E402

LEVELS = {"sugar": {"none": 0, "low": 60}, "bitter": {"none": 0}, "water": {"none": 0, "low": 60, "medium": 60}, "ir94e": {"none": 0}}


def cell(sugar, water, mean=10.0, n=30):
    return {"sugar": sugar, "bitter": "none", "water": water, "ir94e": "none",
            "hz": {"sugar": LEVELS["sugar"][sugar], "bitter": 0, "water": LEVELS["water"][water], "ir94e": 0},
            "mn9_mean": mean, "mn9_std": 1.0, "mn9_left_mean": mean, "mn9_left_std": 1.0, "n_trials": n}


def dish(key, sugar="low", water="low", review="llm_v1"):
    return {"key": key, "display": {"zh": key, "en": key}, "sugar": sugar, "bitter": "none", "water": water, "ir94e": "none", "review": review}


class Bundle:
    """A minimal but complete release tree in a temp dir; mutate then validate."""

    def __init__(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.cells = [cell("none", "none"), cell("low", "low"), cell("low", "none")]
        self.table = {"schema_version": "lookup_v1", "levels": LEVELS, "cells": self.cells, "cells_sha256": vr.cells_sha256(self.cells)}
        self.dishes = [dish("a"), dish("b", "none", "none")]
        self.sections = {"sections": []}
        self.named = {"neurons": []}
        self.variants = ["baseline", "silence_x"]
        self.write()

    def write(self, table=None, dishes=None, site_dishes=None):
        table = self.table if table is None else table
        dishes = self.dishes if dishes is None else dishes
        site_dishes = dishes if site_dishes is None else site_dishes
        for rel, obj in (("data/dishes.json", dishes), ("site/data/dishes.json", site_dishes),
                         ("data/lookup_table.json", table), ("site/data/lookup_table.json", table),
                         ("data/dish_sections.json", self.sections), ("site/data/sections.json", self.sections),
                         ("data/named_neurons.json", self.named), ("site/data/named_neurons.json", self.named),
                         ("site/data/neurons.json", {"layout": "flywire_v783_soma"}),
                         ("site/config.json", {"site_url": "https://example.test/"})):
            path = self.root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(obj), encoding="utf-8")
        (self.root / "site" / "strings.js").write_text("export const STRINGS = {};", encoding="utf-8")
        (self.root / "site" / "index.html").write_text('<script type="module" src="app.js"></script>', encoding="utf-8")
        replay = self.root / "site" / "data" / "replay"
        replay.mkdir(parents=True, exist_ok=True)
        ids = [vr.cell_id(c) for c in table["cells"]]
        manifest = {"n_cells": len(ids), "variants": self.variants, "cells": {i: {} for i in ids}}
        (replay / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        for p in replay.glob("*.bin"):
            p.unlink()
        for i in ids:
            for v in self.variants:
                (replay / (f"{i}.bin" if v == "baseline" else f"{i}_{v}.bin")).write_bytes(b"AFR1")

    def problems(self):
        return vr.validate(self.root)


class ValidateRelease(unittest.TestCase):
    def setUp(self):
        self.b = Bundle()

    def tearDown(self):
        self.b.tmp.cleanup()

    def test_good_bundle_passes(self):
        self.assertEqual(self.b.problems(), [])

    def test_stub_table_fails(self):
        self.b.write(table={**self.b.table, "stub": True})
        self.assertTrue(any("stub" in p for p in self.b.problems()))

    def test_needs_review_fails(self):
        self.b.write(dishes=[dish("a", review="needs_review"), dish("b", "none", "none")])
        self.assertTrue(any("needs_review" in p for p in self.b.problems()))

    def test_draft_fails(self):
        self.b.write(dishes=[dish("a", review="draft"), dish("b", "none", "none")])
        self.assertTrue(any("draft" in p for p in self.b.problems()))

    def test_source_site_mismatch_fails(self):
        self.b.write(site_dishes=[dish("a"), dish("b", "none", "none"), dish("c", "none", "none")])
        self.assertTrue(any("sync: site/data/dishes.json differs" in p for p in self.b.problems()))

    def test_missing_variant_fails(self):
        (self.b.root / "site" / "data" / "replay" / "G_slow_bnone_wlow_inone_silence_x.bin").unlink()
        self.assertTrue(any("missing G_slow_bnone_wlow_inone_silence_x.bin" in p for p in self.b.problems()))

    def test_orphan_replay_fails(self):
        (self.b.root / "site" / "data" / "replay" / "G_old.bin").write_bytes(b"AFR1")
        self.assertTrue(any("orphan file G_old.bin" in p for p in self.b.problems()))

    def test_non_finite_mn9_fails(self):
        cells = [cell("none", "none"), cell("low", "low", mean=float("nan")), cell("low", "none")]
        table = {**self.b.table, "cells": cells, "cells_sha256": vr.cells_sha256(cells)}
        self.b.write(table=table)
        self.assertTrue(any("not a finite number" in p for p in self.b.problems()))

    def test_tampered_cells_hash_fails(self):
        cells = [cell("none", "none"), cell("low", "low", mean=99.0), cell("low", "none")]
        self.b.write(table={**self.b.table, "cells": cells})  # hash left as before
        self.assertTrue(any("cells_sha256 does not match" in p for p in self.b.problems()))

    def test_non_integer_trials_fails(self):
        cells = [cell("none", "none"), cell("low", "low", n=29.5), cell("low", "none")]
        self.b.write(table={**self.b.table, "cells": cells, "cells_sha256": vr.cells_sha256(cells)})
        self.assertTrue(any("n_trials is not a positive integer" in p for p in self.b.problems()))

    def test_dish_without_replay_fails(self):
        cells = [cell("none", "none"), cell("low", "low")]  # dish "b" needs (none, none): fine; drop (low, none): fine
        table = {**self.b.table, "cells": cells, "cells_sha256": vr.cells_sha256(cells)}
        self.b.write(table=table, dishes=[dish("a"), dish("z", "low", "none")])
        self.assertTrue(any("dish 'z'" in p for p in self.b.problems()))

    def test_invalid_and_missing_ir94e_fail_and_shipped_dictionary_passes(self):
        invalid = dish("invalid")
        invalid["ir94e"] = "very_high"
        missing = dish("missing")
        del missing["ir94e"]
        self.b.write(dishes=[invalid, missing])
        problems = self.b.problems()
        self.assertIn("dictionary: 'invalid' ir94e level 'very_high' invalid", problems)
        self.assertIn("dictionary: 'missing' ir94e level None invalid", problems)
        self.assertIn("replay: dish 'missing' lacks ir94e", problems)

        shipped_root = Path(__file__).resolve().parents[1]
        shipped_problems, _ = vr.check_dictionary(shipped_root)
        self.assertFalse(any("ir94e level" in p for p in shipped_problems), shipped_problems)

    def test_placeholder_layout_fails(self):
        (self.b.root / "site" / "data" / "neurons.json").write_text(json.dumps({"layout": "placeholder"}), encoding="utf-8")
        self.assertTrue(any("placeholder layout" in p for p in self.b.problems()))


if __name__ == "__main__":
    unittest.main()
