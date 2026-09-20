# SPDX-License-Identifier: MIT
"""Q06: every bad production bundle fails with its own reason; a good one passes."""

import json
import hashlib
import sys
import tempfile
import unittest
from unittest.mock import patch
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
        sprites = self.root / "site/assets/dishes"
        sprites.mkdir(parents=True)
        (sprites / "fallbacks.json").write_text('{"fallbacks": {}}', encoding="utf-8")
        for name in ("a", "b"):
            (sprites / f"{name}.png").write_bytes(b"sprite")

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
        (self.root / "site" / "strings.js").write_text(
            'export const STRINGS = { en: { "releaseSummary": "x" }, zh: { "releaseSummary": "y" } };', encoding="utf-8")
        (self.root / "CHANGELOG.md").write_text("# Changelog\n\n## v1.2.0 — 2026-09-13\n\n- x\n\n## v1.1.1 — 2026-09-12\n\n- y\n", encoding="utf-8")
        (self.root / "site" / "data" / "release.json").write_text(
            json.dumps({"version": "v1.2.0", "date": "2026-09-13", "summary_key": "releaseSummary"}), encoding="utf-8")
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

    def test_sprites_pass_and_validate_calls_check(self):
        self.assertEqual(vr.check_sprites(self.b.root), [])
        (self.b.root / "site/assets/dishes/a.png").unlink()
        self.assertTrue(any("sprites:" in p and "missing" in p for p in self.b.problems()))

    def test_sprites_shared_and_missing(self):
        sprites = self.b.root / "site/assets/dishes"
        (sprites / "b.png").unlink()
        (sprites / "fallbacks.json").write_text('{"fallbacks": {"b": "a"}}', encoding="utf-8")
        errors = vr.check_sprites(self.b.root)
        self.assertTrue(any("shared" in p and "a, b" in p for p in errors), errors)
        self.assertTrue(any("borrow" in p for p in errors), errors)
        (sprites / "a.png").unlink()
        errors = vr.check_sprites(self.b.root)
        self.assertTrue(any("fallback target" in p and "missing" in p for p in errors), errors)
        self.assertTrue(any("'a'" in p and "missing" in p for p in errors), errors)

    def test_sprites_invalid_fallbacks_and_unused_target(self):
        path = self.b.root / "site/assets/dishes/fallbacks.json"
        for content in ('{', '[]', '{"fallbacks": []}', '{"fallbacks": {"b": 2}}',
                        '{"fallbacks": {"b": "../a"}}', '{"fallbacks": {"b": "gone"}}'):
            with self.subTest(content=content):
                path.write_text(content, encoding="utf-8")
                self.assertTrue(vr.check_sprites(self.b.root))
        path.unlink()
        self.assertTrue(vr.check_sprites(self.b.root))

    def test_sprites_slug_collision_and_own_sprite_precedence(self):
        path = self.b.root / "site/assets/dishes/fallbacks.json"
        path.write_text('{"fallbacks": {"b": "a"}}', encoding="utf-8")
        self.assertEqual(vr.check_sprites(self.b.root), [])
        self.b.write(dishes=[dish("a"), dish("A!")])
        self.assertTrue(any("shared" in p for p in vr.check_sprites(self.b.root)))

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

    def test_release_json_must_match_changelog_top_entry(self):
        self.assertFalse([p for p in self.b.problems() if p.startswith("release:")])
        release = self.b.root / "site" / "data" / "release.json"
        release.write_text(json.dumps({"version": "v1.1.1", "date": "2026-09-12", "summary_key": "releaseSummary"}), encoding="utf-8")
        problems = self.b.problems()
        self.assertTrue(any("version 'v1.1.1' != CHANGELOG.md top entry 'v1.2.0'" in p for p in problems), problems)
        release.write_text(json.dumps({"version": "v1.2.0", "date": "2026-09-12", "summary_key": "releaseSummary"}), encoding="utf-8")
        self.assertTrue(any("date '2026-09-12' != CHANGELOG.md top entry date '2026-09-13'" in p for p in self.b.problems()))
        release.write_text(json.dumps({"version": "v1.2.0", "date": "2026-09-13", "summary_key": "nope"}), encoding="utf-8")
        self.assertTrue(any("summary_key 'nope' is not defined" in p for p in self.b.problems()))
        release.unlink()
        self.assertTrue(any("release.json missing" in p for p in self.b.problems()))

    def test_placeholder_layout_fails(self):
        (self.b.root / "site" / "data" / "neurons.json").write_text(json.dumps({"layout": "placeholder"}), encoding="utf-8")
        self.assertTrue(any("placeholder layout" in p for p in self.b.problems()))


class PrepareNewSprites(unittest.TestCase):
    def test_crop_ignores_alpha_that_final_palette_discards(self):
        import prep_assets as prep
        from PIL import Image
        image = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
        image.putpixel((0, 0), (100, 80, 60, 1))
        image.paste((100, 80, 60, 255), (30, 30, 70, 70))
        self.assertEqual(prep.crop_and_square(image, 0).size, (40, 40))

    def test_only_new_skips_fly_and_non_dictionary_raw_images(self):
        import prep_assets as prep
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw, out = root / "assets/raw", root / "site/assets/dishes"
            (raw / "fly").mkdir(parents=True)
            out.mkdir(parents=True)
            (root / "data").mkdir()
            (root / "data/dishes.json").write_text('[{"key":"a"},{"key":"new dish"}]')
            for name in ("a", "new-dish", "batch3_replacements_sheet"):
                (raw / f"{name}.png").write_bytes(b"raw")
            (raw / "fly/idle_1.png").write_bytes(b"raw")
            (out / "a.png").write_bytes(b"existing")
            with patch.object(prep, "ROOT", root), patch.object(prep, "OUT_DISHES", out), \
                 patch.object(prep, "prepare", return_value=[]) as prepare, \
                 patch.object(sys, "argv", ["prep_assets.py", "--raw", str(raw), "--only-new"]):
                self.assertEqual(prep.main(), 0)
            self.assertEqual(prepare.call_count, 1)
            self.assertEqual(prepare.call_args.args[0], [raw / "new-dish.png"])


class ValidateMale(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        repo = Path(__file__).resolve().parents[1]
        self.table = json.loads((repo / 'data/lookup_table_male.json').read_text())
        self.write('data/lookup_table_male.json', self.table)
        self.write('site/data/lookup_table_male.json', self.table)
        self.write('data/lookup_table_v1_2.json', json.loads((repo / 'data/lookup_table_v1_2.json').read_text()))
        dishes = json.loads((repo / 'data/dishes.json').read_text(encoding='utf-8'))
        self.write('data/dishes.json', dishes)
        self.write('data/malecns/male_female_comparison.json', {'n_distinct_male_cells': 55})
        self.write('data/replay_neurons_male.json', {'n_neurons': 11271})
        self.write('site/data/neurons_male.json', {'schema_version': 'neurons_v1',
                   'layout': 'malecns_v1_soma', 'n_indexed': 11271})
        self.outlines = dict(schema_version='neuropils_v1', source='Synthetic test meshes', groups=[
            dict(key=str(i), polygon=[[.1,.1],[.2,.1],[.2,.2]], label_at=[.15,.15],
                 label_en='ROI', label_zh='ROI') for i in range(5)])
        self.write('site/data/neuropils_male.json', self.outlines)
        from sim.grid import resolve_levels
        self.ids = sorted({vr.cell_id(resolve_levels(self.table, d)) for d in dishes})
        cells = {}
        for cid in self.ids:
            payload = b'AFR1' + cid.encode()
            (self.root / 'site/data/replay_male').mkdir(parents=True, exist_ok=True)
            (self.root / f'site/data/replay_male/{cid}.bin').write_bytes(payload)
            cells[cid] = {'bytes': len(payload), 'sha256': hashlib.sha256(payload).hexdigest()}
        self.write('site/data/replay_male/manifest.json', {
            'schema_version': 'replay_manifest_v1', 'fly': 'male', 'git_commit': 'a' * 40,
            'n_cells': len(cells), 'n_cells_recorded': 400, 'variants': ['baseline'],
            'shipping_rule': 'cells occupied by the 174 dishes; the other recorded cells stay in the research pack',
            'source_manifest_sha256': 'b' * 64, 'cells': cells})

    def write(self, rel, value):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding='utf-8')

    def test_male_data_checked_before_ui_activation(self):
        self.assertEqual(vr.check_male(self.root), [])

    def test_male_neuropils_required_complete_and_in_bounds(self):
        path = self.root / 'site/data/neuropils_male.json'
        path.unlink()
        self.assertTrue(any('neuropils missing' in p for p in vr.check_male(self.root)))
        for coordinate in (-.01, 1.01, float('nan'), True):
            self.outlines['groups'][0]['polygon'][0][0] = coordinate
            self.write('site/data/neuropils_male.json', self.outlines)
            self.assertTrue(any('invalid neuropil polygon' in p for p in vr.check_male(self.root)))
        self.outlines['groups'][0]['polygon'][0][0] = .1
        self.outlines['groups'].pop()
        self.write('site/data/neuropils_male.json', self.outlines)
        self.assertTrue(any('at least 5 groups' in p for p in vr.check_male(self.root)))

    def test_tampered_male_cell(self):
        self.table['cells'][0]['mn9_mean'] = 42
        self.write('site/data/lookup_table_male.json', self.table)
        errors = vr.check_male(self.root)
        self.assertTrue(any('hash' in p for p in errors), errors)
        self.assertTrue(any('bytes differ' in p for p in errors), errors)
        self.assertTrue(any('state rule' in p for p in errors), errors)

    def test_missing_dish_replay(self):
        (self.root / f'site/data/replay_male/{self.ids[0]}.bin').unlink()
        self.assertTrue(any('missing' in p for p in vr.check_male(self.root)))

    def test_orphan_male_replay(self):
        (self.root / 'site/data/replay_male/orphan.bin').write_bytes(b'AFR1')
        self.assertTrue(any('orphan' in p for p in vr.check_male(self.root)))

    def test_wrong_male_neurons_layout(self):
        self.write('site/data/neurons_male.json', {'layout': 'flywire_v783_soma', 'n_indexed': 11271})
        self.assertTrue(any('layout' in p for p in vr.check_male(self.root)))

    def test_tampered_replay_bytes(self):
        (self.root / f'site/data/replay_male/{self.ids[0]}.bin').write_bytes(b'corrupt')
        self.assertTrue(any('sha256' in p for p in vr.check_male(self.root)))

    def test_invalid_statistics_and_coordinates_even_with_matching_hash(self):
        self.table['cells'][0].update(cem_sd=-1, mn11v_mean=float('nan'), water='low')
        self.table['cells_sha256'] = vr.cells_sha256(self.table['cells'])
        for rel in ('data/lookup_table_male.json', 'site/data/lookup_table_male.json'):
            self.write(rel, self.table)
        errors = vr.check_male(self.root)
        for text in ('cem_sd', 'mn11v_mean', 'coordinates'):
            self.assertTrue(any(text in p for p in errors), errors)


if __name__ == "__main__":
    unittest.main()
