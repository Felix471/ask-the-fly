#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Render docs/grid_heatmap_data.json as a dependency-free SVG (sugar x bitter per water level)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Single-hue sequential ramp (blue 100 -> 700); the lightest step means near 0 Hz.
RAMP = [
    "#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec", "#5598e7", "#3987e5",
    "#2a78d6", "#256abf", "#1c5cab", "#184f95", "#104281", "#0d366b",
]
LABEL = {"none": "none", "low": "low", "medium": "medium", "high": "high", "very_high": "very high"}


def color(value: float, vmax: float) -> tuple[str, str]:
    index = min(len(RAMP) - 1, int(round((value / vmax) * (len(RAMP) - 1))))
    return RAMP[index], ("#1f1a17" if index < 7 else "#ffffff")


def render(data: dict) -> str:
    sugar_levels, bitter_levels = data["sugar_levels"], data["bitter_levels"]
    hz = data["hz"]
    vmax = max(
        max(data["mn9"][w][s][b] for s in sugar_levels for b in bitter_levels)
        for w in data["water_levels"]
    ) or 1.0
    # Water low and medium share a grid cell (identical Hz), so show one panel for both.
    panels: list[tuple[str, str]] = []
    seen_hz: set[float] = set()
    for water in data["water_levels"]:
        rate = float(hz["water"][water])
        if rate in seen_hz:
            continue
        seen_hz.add(rate)
        shared = [w for w in data["water_levels"] if float(hz["water"][w]) == rate]
        name = " = ".join(LABEL[w] for w in shared)
        suffix = ", shared cell" if len(shared) > 1 else ""
        panels.append((water, f"water {name} ({rate:g} Hz{suffix})"))

    cell, pad_l, pad_t = 62, 96, 70
    pw, ph, cols = pad_l + 5 * cell + 16, pad_t + 5 * cell + 40, 2
    rows = (len(panels) + cols - 1) // cols
    width, height = cols * pw + 40, rows * ph + 140
    hz_text = lambda dim: ", ".join(f"{LABEL[k]} {v:g}" for k, v in hz[dim].items())
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family="system-ui, -apple-system, Segoe UI, sans-serif">',
        f'<rect width="{width}" height="{height}" fill="#ffffff"/>',
        '<text x="24" y="34" font-size="20" font-weight="600" fill="#1f1a17">'
        f'Left MN9 firing rate (Hz) by sugar × bitter — lookup grid, ir94e = {data["ir94e"]}, 30 trials per cell</text>',
        f'<text x="24" y="56" font-size="13" fill="#6b625b">Rows: sugar level (Hz: {hz_text("sugar")}). '
        f'Columns: bitter level (Hz: {hz_text("bitter")}).</text>',
        '<text x="24" y="74" font-size="13" fill="#6b625b">One hue: light = near 0 Hz, dark = maximum. '
        'Hover a cell for mean ± std.</text>',
    ]
    for k, (water, title) in enumerate(panels):
        ox, oy = 24 + (k % cols) * pw, 100 + (k // cols) * ph
        out.append(f'<text x="{ox}" y="{oy + 18}" font-size="15" font-weight="600" fill="#1f1a17">{title}</text>')
        out.append(f'<text x="{ox + pad_l + 2.5 * cell}" y="{oy + pad_t - 30}" font-size="12" fill="#6b625b" text-anchor="middle">bitter →</text>')
        for j, bitter in enumerate(bitter_levels):
            out.append(f'<text x="{ox + pad_l + j * cell + cell / 2}" y="{oy + pad_t - 10}" font-size="12" fill="#6b625b" text-anchor="middle">{LABEL[bitter]}</text>')
        for i, sugar in enumerate(sugar_levels):
            y = oy + pad_t + i * cell
            out.append(f'<text x="{ox + pad_l - 8}" y="{y + cell / 2 + 4}" font-size="12" fill="#6b625b" text-anchor="end">{LABEL[sugar]}</text>')
            for j, bitter in enumerate(bitter_levels):
                value, std = data["mn9"][water][sugar][bitter], data["std"][water][sugar][bitter]
                fill, ink = color(value, vmax)
                x = ox + pad_l + j * cell
                out.append(
                    f'<rect x="{x + 1}" y="{y + 1}" width="{cell - 2}" height="{cell - 2}" rx="4" fill="{fill}">'
                    f'<title>sugar {LABEL[sugar]}, bitter {LABEL[bitter]}, {title}: {value:.1f} ± {std:.1f} Hz</title></rect>'
                )
                out.append(f'<text x="{x + cell / 2}" y="{y + cell / 2 + 5}" font-size="14" font-weight="600" fill="{ink}" text-anchor="middle">{value:.0f}</text>')
        cx, cy = ox + pad_l - 70, oy + pad_t + 2.5 * cell
        out.append(f'<text x="{cx}" y="{cy}" font-size="12" fill="#6b625b" text-anchor="middle" transform="rotate(-90 {cx} {cy})">sugar →</text>')
    lx, ly = 24, height - 28
    for i, swatch in enumerate(RAMP):
        out.append(f'<rect x="{lx + i * 22}" y="{ly - 14}" width="22" height="14" fill="{swatch}"/>')
    out.append(f'<text x="{lx}" y="{ly + 14}" font-size="12" fill="#6b625b">0 Hz</text>')
    out.append(f'<text x="{lx + len(RAMP) * 22}" y="{ly + 14}" font-size="12" fill="#6b625b" text-anchor="end">{vmax:.0f} Hz</text>')
    out.append(
        f'<text x="{lx + len(RAMP) * 22 + 16}" y="{ly}" font-size="12" fill="#6b625b">Source: data/lookup_table.json '
        '(Shiu 2024 LIF on FlyWire v783, fixed refractory path). Water low and medium share one grid cell.</text>'
    )
    out.append("</svg>")
    return "\n".join(out) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=ROOT / "docs" / "grid_heatmap_data.json")
    parser.add_argument("--out", type=Path, default=ROOT / "docs" / "grid_heatmap_sugar_bitter.svg")
    args = parser.parse_args()
    data = json.loads(args.data.read_text(encoding="utf-8"))
    args.out.write_text(render(data), encoding="utf-8")
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
