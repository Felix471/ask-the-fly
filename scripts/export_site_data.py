#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Copy the dish dictionary and the lookup table into the static site's data folder.

Until the real lookup table lands, ``--stub`` writes a table with the same
schema (lookup_v1) whose MN9 values come from a crude closed-form guess. The
stub is marked ``"stub": true`` and the site shows a banner while it is in use.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sim.grid import EXPECTED_DIMENSIONS, expand_grid_conditions, load_grid_levels

SITE_DATA = ROOT / "site" / "data"


def _cells_sha256(cells: list[dict]) -> str:
    encoded = json.dumps(
        cells, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _stub_mn9(rates: dict) -> float:
    """Crude guess shaped like the Phase 1 characterization; NOT a simulation result."""
    sugar, bitter, water, ir94e = (
        float(rates["sugar"]), float(rates["bitter"]), float(rates["water"]), float(rates["ir94e"])
    )
    # Sugar alone: threshold near 40 Hz, saturating near 90 Hz MN9.
    drive = max(0.0, sugar - 35.0)
    base = 95.0 * (1.0 - 2.718281828 ** (-drive / 45.0))
    # Weak water helps weak sugar most; strong water drives MN9 alone.
    helper = min(30.0, water / 2.0) * (1.0 - base / 95.0) if sugar > 0 else 0.0
    alone = max(0.0, (water - 120.0) * 0.4)
    value = max(base + helper, alone)
    # Bitter and ir94e suppress multiplicatively.
    value *= max(0.0, 1.0 - bitter / 170.0)
    value *= max(0.0, 1.0 - ir94e / 500.0)
    return round(value, 3)


def build_stub() -> dict:
    grid_levels = load_grid_levels()
    protocol = json.loads((ROOT / "data" / "stim_protocol.json").read_text(encoding="utf-8"))
    cells = []
    for condition in expand_grid_conditions(grid_levels):
        mean = _stub_mn9(condition["rates"])
        std = round(min(7.0, 1.0 + mean * 0.06), 3)
        cells.append({
            **condition["levels"],
            "hz": condition["rates"].copy(),
            "mn9_mean": mean,
            "mn9_std": std,
            "mn9_left_mean": mean,
            "mn9_left_std": std,
            "mn9_right_mean": 0.0,
            "mn9_right_std": 0.0,
            "n_trials": 0,
        })
    readout = protocol["readout"]
    return {
        "schema_version": "lookup_v1",
        "stub": True,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "git_commit": "stub",
        "protocol_sha256": "stub",
        "source_cells_sha256": "stub",
        "grid_levels_sha256": "stub",
        "data_version": "flywire_v783",
        "model": "STUB: closed-form guess shaped like docs/phase1_characterization.md; replace with build_lookup.py output",
        "readout": {
            "neuron": "MN9", "aggregation": "left_only",
            "left": readout["left"], "right": readout["right"],
            "unit": "Hz (spikes per 1000 ms trial)",
        },
        "n_trials_per_cell": 0,
        "dimensions": list(EXPECTED_DIMENSIONS),
        "levels": grid_levels["levels"],
        "level_notes": grid_levels["notes"],
        "cells": cells,
        "cells_sha256": _cells_sha256(cells),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lookup", type=Path, default=ROOT / "data" / "lookup_table.json")
    parser.add_argument("--dishes", type=Path, default=ROOT / "data" / "dishes.json")
    parser.add_argument("--out-dir", type=Path, default=SITE_DATA)
    parser.add_argument(
        "--stub", action="store_true",
        help="write a stub lookup table instead of copying --lookup",
    )
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(args.dishes, args.out_dir / "dishes.json")
    print(f"copied {args.dishes} -> {args.out_dir / 'dishes.json'}")
    named = ROOT / "data" / "named_neurons.json"
    if named.exists():
        shutil.copyfile(named, args.out_dir / "named_neurons.json")
        print(f"copied {named} -> {args.out_dir / 'named_neurons.json'}")
    target = args.out_dir / "lookup_table.json"
    if args.stub:
        payload = build_stub()
        target.write_text(json.dumps(payload, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"wrote STUB lookup table -> {target} ({len(payload['cells'])} cells)")
    else:
        if not args.lookup.exists():
            parser.error(f"{args.lookup} does not exist; run scripts/build_lookup.py or pass --stub")
        shutil.copyfile(args.lookup, target)
        print(f"copied {args.lookup} -> {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
