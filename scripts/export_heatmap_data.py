#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Export the ir94e=none lookup slice for the grid heatmap page."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sim.lookup import LookupTable


def export(lookup_path: Path) -> dict:
    table = LookupTable.load(lookup_path)
    sugar_levels = list(table.levels["sugar"])
    bitter_levels = list(table.levels["bitter"])
    water_levels = list(table.levels["water"])
    # Resolve by level names through the table so level names that share a
    # grid cell (water low/medium, both 60 Hz) both get a surface entry.
    def surface(field: str) -> dict:
        return {
            water: {
                sugar: {
                    bitter: table.get(
                        sugar=sugar, bitter=bitter, water=water, ir94e="none"
                    )[field]
                    for bitter in bitter_levels
                }
                for sugar in sugar_levels
            }
            for water in water_levels
        }

    return {
        "sugar_levels": sugar_levels,
        "bitter_levels": bitter_levels,
        "water_levels": water_levels,
        "ir94e": "none",
        "hz": {
            dimension: table.levels[dimension]
            for dimension in ("sugar", "bitter", "water", "ir94e")
        },
        "mn9": surface("mn9_mean"),
        "std": surface("mn9_std"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--lookup", "--input", dest="lookup", type=Path,
        default=ROOT / "data" / "lookup_table.json",
    )
    parser.add_argument(
        "--out", type=Path, default=ROOT / "docs" / "grid_heatmap_data.json"
    )
    args = parser.parse_args()
    payload = export(args.lookup)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(payload, separators=(",", ":"), ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {args.out} ({len(payload['water_levels'])} water slices)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
