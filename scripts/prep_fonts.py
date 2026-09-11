#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Display-tier fonts: subset and convert to woff2, copy licenses, report sizes and coverage.

Inputs (gitignored, assets/raw/fonts/):
  PixelifySans[wght].ttf + PixelifySans-OFL.txt          (Latin; google/fonts ofl/pixelifysans)
  fusion/fusion-pixel-12px-proportional-zh_hans.ttf       (CJK; TakWolf/fusion-pixel-font release)
  fusion/OFL.txt, fusion/LICENSES/**                      (Fusion Pixel and its component fonts)
Glyph list: site/assets/fonts/glyphs-zh.txt (built by this script from data/dishes.json zh
display names + aliases, data/dish_sections.json, every zh string in copy/site_strings.json,
digits, ASCII and CJK punctuation).

Outputs: site/assets/fonts/pixelify-sans.woff2, fusion-pixel-12px-zh.woff2, LICENSE-*.txt,
glyphs-zh.txt, coverage.json (what the CJK subset covers and what falls back to the system font).

  .venv\\Scripts\\python scripts/prep_fonts.py
"""

from __future__ import annotations

import json
import string
import sys
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "assets" / "raw" / "fonts"
OUT = ROOT / "site" / "assets" / "fonts"
PIXELIFY = RAW / "PixelifySans[wght].ttf"
FUSION = RAW / "fusion" / "fusion-pixel-12px-proportional-zh_hans.ttf"
CJK_PUNCT = "，。、：；！？（）「」『』《》〈〉…·—～×±≈℃％"


def is_cjk_or_fullwidth(ch: str) -> bool:
    o = ord(ch)
    return 0x2E80 <= o <= 0x9FFF or 0xF900 <= o <= 0xFAFF or 0xFF00 <= o <= 0xFFEF or 0x3000 <= o <= 0x303F


def glyph_list() -> str:
    chars: set[str] = set()
    for entry in json.loads((ROOT / "data" / "dishes.json").read_text(encoding="utf-8")):
        for text in [entry["display"].get("zh", ""), *entry.get("aliases", [])]:
            chars.update(ch for ch in text if is_cjk_or_fullwidth(ch))
    strings = json.loads((ROOT / "copy" / "site_strings.json").read_text(encoding="utf-8"))
    entries = strings if isinstance(strings, list) else strings["strings"]
    for entry in entries:
        chars.update(ch for ch in entry["zh"] if not ch.isspace())
    for section in json.loads((ROOT / "data" / "dish_sections.json").read_text(encoding="utf-8"))["sections"]:
        chars.update(section["zh"])
    chars.update(string.digits, string.ascii_letters, string.punctuation, CJK_PUNCT)
    chars.discard(" ")
    return "".join(sorted(chars))


def subset_font(src: Path, dst: Path, *, unicodes: str | None = None, text: str | None = None, features=("*",)) -> tuple[int, set[str]]:
    options = subset.Options()
    options.flavor = "woff2"
    options.layout_features = list(features)
    options.name_IDs = ["*"]
    options.notdef_outline = True
    options.recalc_bounds = True
    options.drop_tables += ["DSIG"]
    font = TTFont(str(src))
    cmap = font.getBestCmap()
    subsetter = subset.Subsetter(options=options)
    if text is not None:
        wanted = {ch for ch in text}
        missing = {ch for ch in wanted if ord(ch) not in cmap}
        subsetter.populate(text="".join(sorted(wanted - missing)))
    else:
        missing = set()
        subsetter.populate(unicodes=subset.parse_unicodes(unicodes))
    subsetter.subset(font)
    dst.parent.mkdir(parents=True, exist_ok=True)
    font.flavor = "woff2"
    font.save(str(dst))
    return dst.stat().st_size, missing


def main() -> int:
    for path in (PIXELIFY, FUSION):
        if not path.exists():
            print(f"missing {path}")
            return 1
    OUT.mkdir(parents=True, exist_ok=True)
    glyphs = glyph_list()
    (OUT / "glyphs-zh.txt").write_text(glyphs + "\n", encoding="utf-8")

    # Latin display font: Basic Latin + Latin-1 Supplement + the punctuation the copy uses.
    # Pixelify Sans's fi/fl ligatures read as "A" at pixel sizes ("fly" -> "Ay"), so
    # no discretionary or standard ligature features are kept: kerning only.
    latin_size, _ = subset_font(PIXELIFY, OUT / "pixelify-sans.woff2", unicodes="U+0020-00FF,U+2013-2014,U+2018-201A,U+201C-201E,U+2026,U+00D7,U+2103,U+FF05", features=("kern",))
    # CJK display font: exactly the glyphs the site can show, nothing else.
    cjk_size, missing = subset_font(FUSION, OUT / "fusion-pixel-12px-zh.woff2", text=glyphs)

    (OUT / "LICENSE-PixelifySans.txt").write_text((RAW / "PixelifySans-OFL.txt").read_text(encoding="utf-8"), encoding="utf-8")
    parts = ["Fusion Pixel Font (https://github.com/TakWolf/fusion-pixel-font), 12px proportional, zh_hans build, subset for this site.\n",
             (RAW / "fusion" / "OFL.txt").read_text(encoding="utf-8")]
    for lic in sorted((RAW / "fusion" / "LICENSES").rglob("*")):
        if lic.is_file():
            parts.append(f"\n\n===== component: {lic.parent.name} ({lic.name}) =====\n\n" + lic.read_text(encoding="utf-8", errors="replace"))
    (OUT / "LICENSE-FusionPixel.txt").write_text("".join(parts), encoding="utf-8")

    covered = [ch for ch in glyphs if ch not in missing]
    coverage = {
        "glyphs_requested": len(glyphs),
        "cjk_covered": len(covered),
        "fallback_to_system": sorted(missing),
        "pixelify_sans_woff2_bytes": latin_size,
        "fusion_pixel_zh_woff2_bytes": cjk_size,
    }
    (OUT / "coverage.json").write_text(json.dumps(coverage, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"glyphs requested: {len(glyphs)} (CJK ideographs {sum(1 for c in glyphs if 0x2E80 <= ord(c) <= 0x9FFF)})")
    print(f"pixelify-sans.woff2: {latin_size / 1024:.1f} KB")
    print(f"fusion-pixel-12px-zh.woff2: {cjk_size / 1024:.1f} KB, covers {len(covered)} of {len(glyphs)}; system fallback for {len(missing)}: {''.join(sorted(missing))[:80]}")
    print(f"total: {(latin_size + cjk_size) / 1024:.1f} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
