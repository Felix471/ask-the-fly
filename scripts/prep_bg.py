#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Background textures: assets/raw/bg/*.png -> site/assets/bg/*.png (256 x 256, nearest-neighbour,
one shared palette), with a seamless-tiling check and contrast measurements for the stage overlay.

  .venv\\Scripts\\python scripts/prep_bg.py                 # build + report
  .venv\\Scripts\\python scripts/prep_bg.py --colours 24

The report prints, per texture: seam score (mean |diff| across the wrap edge vs. the mean
|diff| between interior neighbours; <= 1.5x is seamless), file size, and the WCAG contrast
of the stage/page text colours against the darkest and lightest tile pixels, with and
without the cream overlay the CSS applies.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "assets" / "raw" / "bg"
OUT = ROOT / "site" / "assets" / "bg"
SIZE = 256
INK = (0x1F, 0x1A, 0x17)      # --ink: plate labels, body text
MUTED = (0x6B, 0x62, 0x5B)    # --muted: Hz sub-labels, hints
CREAM = (0xFB, 0xF8, 0xF2)    # --bg


def luminance(rgb):
    def channel(c):
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (channel(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(fg, bg):
    a, b = luminance(fg), luminance(bg)
    hi, lo = max(a, b), min(a, b)
    return (hi + 0.05) / (lo + 0.05)


def blend(rgb, over, alpha):
    return tuple(round(c * (1 - alpha) + o * alpha) for c, o in zip(rgb, over))


def seam_score(img: Image.Image) -> float:
    px = img.convert("RGB").load()
    w, h = img.size

    def diff(a, b):
        return sum(abs(x - y) for x, y in zip(a, b)) / 3

    edge = []
    for y in range(h):
        edge.append(diff(px[w - 1, y], px[0, y]))
    for x in range(w):
        edge.append(diff(px[x, h - 1], px[x, 0]))
    interior = []
    for y in range(h):
        for x in range(0, w - 1, 7):
            interior.append(diff(px[x, y], px[x + 1, y]))
    for x in range(w):
        for y in range(0, h - 1, 7):
            interior.append(diff(px[x, y], px[x, y + 1]))
    mean_edge = sum(edge) / len(edge)
    mean_interior = max(1e-6, sum(interior) / len(interior))
    return mean_edge / mean_interior


def extremes(img: Image.Image):
    colours = img.convert("RGB").getcolors(1 << 20)
    by_lum = sorted(colours, key=lambda item: luminance(item[1]))
    return by_lum[0][1], by_lum[-1][1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--colours", type=int, default=32, help="shared palette size")
    parser.add_argument("--stage-overlay", type=float, default=0.35, help="alpha of the cream overlay the stage CSS applies")
    args = parser.parse_args()
    names = ("tablecloth", "paper")
    raws = {}
    for name in names:
        path = RAW / f"{name}.png"
        if not path.exists():
            print(f"missing {path}")
            return 1
        raws[name] = Image.open(path).convert("RGBA").resize((SIZE, SIZE), Image.NEAREST)
    # One shared palette learned from both textures, then applied without dithering.
    sheet = Image.new("RGBA", (SIZE * 2, SIZE))
    for i, name in enumerate(names):
        sheet.paste(raws[name], (i * SIZE, 0))
    palette = sheet.convert("RGB").quantize(colors=args.colours, method=Image.MEDIANCUT, dither=Image.NONE)
    OUT.mkdir(parents=True, exist_ok=True)
    total = 0
    for name in names:
        rgb = raws[name].convert("RGB").quantize(palette=palette, dither=Image.NONE).convert("RGB")
        out = OUT / f"{name}.png"
        rgb.quantize(colors=args.colours, method=Image.MEDIANCUT, dither=Image.NONE).save(out, optimize=True)
        size = out.stat().st_size
        total += size
        dark, light = extremes(rgb)
        seam = seam_score(rgb)
        print(f"{name}: {SIZE}x{SIZE}, {size / 1024:.1f} KB, colours {len(rgb.getcolors(1 << 20))}, seam score {seam:.2f} ({'seamless' if seam <= 1.5 else 'VISIBLE SEAM'})")
        print(f"  darkest {dark} lightest {light}")
        for label, fg in (("ink", INK), ("muted", MUTED)):
            raw_c = min(contrast(fg, dark), contrast(fg, light))
            over = blend(dark, CREAM, args.stage_overlay), blend(light, CREAM, args.stage_overlay)
            over_c = min(contrast(fg, over[0]), contrast(fg, over[1]))
            print(f"  {label} on tile: min contrast {raw_c:.2f}:1 raw, {over_c:.2f}:1 with {args.stage_overlay:.0%} cream overlay")
    print(f"total {total / 1024:.1f} KB added")
    return 0


if __name__ == "__main__":
    sys.exit(main())
