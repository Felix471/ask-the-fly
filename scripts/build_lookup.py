#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Build the versioned product lookup table from a completed grid run."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sim.grid import EXPECTED_DIMENSIONS, expand_grid_conditions, load_grid_levels


REQUIRED_COLUMNS = {
    "cond_id", "mn9_left_mean_hz", "mn9_left_std_hz",
    "mn9_right_mean_hz", "mn9_right_std_hz",
    "mn9_aggregated_mean_hz", "mn9_aggregated_std_hz", "n_trials",
    *(f"{dimension}_hz" for dimension in EXPECTED_DIMENSIONS),
    *EXPECTED_DIMENSIONS,
}


def _round(value: object) -> float:
    return round(float(value), 3)


def _cells_sha256(cells: list[dict]) -> str:
    encoded = json.dumps(
        cells, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build(results: Path, allow_partial: bool = False) -> dict:
    grid_levels = load_grid_levels()
    expected = expand_grid_conditions(grid_levels)
    frame = pd.read_csv(results / "summary.csv")
    missing_columns = REQUIRED_COLUMNS - set(frame.columns)
    if missing_columns:
        raise ValueError(f"Missing summary columns: {sorted(missing_columns)}")
    duplicates = frame.loc[frame["cond_id"].duplicated(), "cond_id"].tolist()
    if duplicates:
        raise ValueError(f"Duplicate summary cells: {duplicates[:10]}")
    rows = frame.set_index("cond_id", drop=False)
    expected_ids = {condition["cond_id"] for condition in expected}
    unexpected = sorted(set(rows.index) - expected_ids)
    if unexpected:
        raise ValueError(f"Unexpected summary cells: {unexpected[:10]}")

    required_trials = int(grid_levels["notes"]["n_trials_per_cell"])
    cells = []
    missing = []
    short = []
    for condition in expected:
        cond_id = condition["cond_id"]
        if cond_id not in rows.index:
            missing.append(cond_id)
            continue
        row = rows.loc[cond_id]
        n_trials = int(row["n_trials"])
        if n_trials < required_trials:
            short.append((cond_id, n_trials))

        for dimension in EXPECTED_DIMENSIONS:
            if str(row[dimension]) != condition["levels"][dimension]:
                raise ValueError(f"{cond_id}: mismatched {dimension} level")
            if float(row[f"{dimension}_hz"]) != float(condition["rates"][dimension]):
                raise ValueError(f"{cond_id}: mismatched {dimension} rate")

        cell = {
            **condition["levels"],
            "hz": condition["rates"].copy(),
            "mn9_mean": _round(row["mn9_aggregated_mean_hz"]),
            "mn9_std": _round(row["mn9_aggregated_std_hz"]),
            "mn9_left_mean": _round(row["mn9_left_mean_hz"]),
            "mn9_left_std": _round(row["mn9_left_std_hz"]),
            "mn9_right_mean": _round(row["mn9_right_mean_hz"]),
            "mn9_right_std": _round(row["mn9_right_std_hz"]),
            "n_trials": n_trials,
        }
        cells.append(cell)

    if missing and not allow_partial:
        raise ValueError(f"Missing {len(missing)} grid cells; first: {missing[:10]}")
    if short and not allow_partial:
        raise ValueError(
            f"{len(short)} grid cells have fewer than {required_trials} trials; "
            f"first: {short[:10]}"
        )

    meta = json.loads((results / "run_meta.json").read_text(encoding="utf-8"))
    metadata_keys = ("git_commit", "protocol_sha256", "cells_sha256", "grid_levels_sha256")
    absent_meta = [key for key in metadata_keys if not meta.get(key)]
    if absent_meta:
        raise ValueError(f"Missing run metadata: {absent_meta}")
    protocol = json.loads(
        (ROOT / "data" / "stim_protocol.json").read_text(encoding="utf-8")
    )
    readout = protocol["readout"]
    payload = {
        "schema_version": "lookup_v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "git_commit": meta["git_commit"],
        "protocol_sha256": meta["protocol_sha256"],
        "source_cells_sha256": meta["cells_sha256"],
        "grid_levels_sha256": meta["grid_levels_sha256"],
        "data_version": "flywire_v783",
        "model": "Shiu 2024 LIF, Brian2 2.9.0 cython, store/restore path",
        "readout": {
            "neuron": "MN9",
            "aggregation": "left_only",
            "left": readout["left"],
            "right": readout["right"],
            "unit": "Hz (spikes per 1000 ms trial)",
        },
        "n_trials_per_cell": required_trials,
        "dimensions": list(EXPECTED_DIMENSIONS),
        "levels": grid_levels["levels"],
        "level_notes": grid_levels["notes"],
        "cells": cells,
        "cells_sha256": _cells_sha256(cells),
    }
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=ROOT / "results" / "grid" / "full")
    parser.add_argument("--out", type=Path, default=ROOT / "data" / "lookup_table.json")
    parser.add_argument("--allow-partial", action="store_true")
    args = parser.parse_args()
    payload = build(args.results, args.allow_partial)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(
        f"wrote {args.out} ({len(payload['cells'])} cells, "
        f"cells_sha256={payload['cells_sha256']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
