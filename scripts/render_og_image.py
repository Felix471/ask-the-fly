#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Render site/og-image.png (1200 x 630) from the share-card design for link previews."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "site" / "og-image.png"
FONT_CANDIDATES = [
    "C:/Windows/Fonts/msyhbd.ttc", "C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/NotoSansSC-VF.ttf",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc", "/System/Library/Fonts/PingFang.ttc",
]

INK, MUTED, ACCENT, PAPER, LINE = "#1f1a17", "#6b625b", "#b5471f", "#fbf8f2", "#e2dbd0"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    for candidate in FONT_CANDIDATES:
        if "bd" in candidate and not bold:
            continue
        if Path(candidate).exists():
            try:
                return ImageFont.truetype(candidate, size)
            except OSError:
                continue
    return ImageFont.load_default()


def render(path: Path) -> None:
    W, H = 1200, 630
    im = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 14), fill=ACCENT)
    d.text((64, 70), "Ask the Fly · 问问果蝇", font=font(64, True), fill=INK)
    d.text((64, 160), "A fly-brain model tastes your menu and picks for you.", font=font(32), fill=MUTED)
    d.text((64, 204), "让一只果蝇脑模型替你尝一口，然后选菜。", font=font(32), fill=MUTED)
    # Mini bar comparison, echoing the card's middle third.
    rows = [("watermelon 西瓜", 70.6, True), ("mapo tofu 麻婆豆腐", 62.5, False), ("black coffee 黑咖啡", 0.0, False)]
    y = 290
    for label, hz, win in rows:
        colour = ACCENT if win else INK
        d.text((64, y), label, font=font(26, win), fill=colour)
        d.text((1136, y), f"{hz:.1f} Hz", font=font(26, win), fill=colour, anchor="ra")
        d.rectangle((64, y + 40, 1136, y + 52), fill=LINE)
        width = int((1136 - 64) * min(1.0, hz / 100.0))
        if width:
            d.rectangle((64, y + 40, 64 + width, y + 52), fill=colour)
        y += 78
    d.line((64, 548, 1136, 548), fill=LINE, width=2)
    d.text((64, 566), "Shiu 2024 LIF model · FlyWire v783 · MN9 readout · precomputed, not run live · It only does the first bite.",
           font=font(22), fill=MUTED)
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path, optimize=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    render(args.out)
    print(f"wrote {args.out} ({args.out.stat().st_size / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
