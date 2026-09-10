#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Run the confirmed Phase 1 lookup grid with Brian2."""

from __future__ import annotations

import argparse
import hashlib
import json
import socket
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import brian2

from sim.grid import EXPECTED_DIMENSIONS, expand_grid_conditions, load_grid_levels
from sim.network import load_cells, load_protocol
from sim.runner import run_conditions


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git_commit() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True,
        capture_output=True, check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else "unknown"


def write_meta(stage: str, meta: dict) -> None:
    directory = ROOT / "results" / "grid" / stage
    directory.mkdir(parents=True, exist_ok=True)
    meta["end_time"] = datetime.now(timezone.utc).isoformat()
    (directory / "run_meta.json").write_text(
        json.dumps(meta, indent=2) + "\n", encoding="utf-8"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", required=True, choices=("smoke", "full"))
    parser.add_argument("--n-proc", type=int, default=14)
    parser.add_argument("--batch-size", type=int, default=40)
    parser.add_argument("--n-trials", type=int)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if args.n_proc <= 0:
        parser.error("--n-proc must be positive")
    if args.batch_size <= 0:
        parser.error("--batch-size must be positive")
    if args.n_trials is not None and args.n_trials <= 0:
        parser.error("--n-trials must be positive")

    protocol, source_cells = load_protocol(), load_cells()
    grid_levels = load_grid_levels()
    all_conditions = expand_grid_conditions(grid_levels)
    if args.stage == "smoke":
        wanted = (
            ("none", "none", "none", "none"),
            ("high", "none", "none", "none"),
            ("high", "medium", "medium", "none"),
        )
        by_levels = {
            tuple(condition["levels"][dimension] for dimension in EXPECTED_DIMENSIONS): condition
            for condition in all_conditions
        }
        conditions = [by_levels[key] for key in wanted]
        n_trials = 1
    else:
        conditions = all_conditions
        n_trials = args.n_trials or int(grid_levels["notes"]["n_trials_per_cell"])

    meta = {
        "git_commit": git_commit(),
        "protocol_sha256": sha256(ROOT / "data" / "stim_protocol.json"),
        "cells_sha256": sha256(ROOT / "data" / "cells.json"),
        "grid_levels_sha256": sha256(ROOT / "data" / "grid_levels.json"),
        "brian2_version": brian2.__version__,
        "codegen_target": str(brian2.prefs.codegen.target),
        "n_proc": args.n_proc,
        "hostname": socket.gethostname(),
        "start_time": datetime.now(timezone.utc).isoformat(),
        "end_time": None,
        "n_cells": len(conditions),
        "n_trials": n_trials,
    }
    try:
        import pandas as pd

        batches = [
            conditions[offset:offset + args.batch_size]
            for offset in range(0, len(conditions), args.batch_size)
        ]
        summaries = []
        for batch_index, batch in enumerate(batches, start=1):
            print(
                f"batch {batch_index}/{len(batches)}: "
                f"{len(batch)} cells x {n_trials} trials", flush=True,
            )
            summaries.append(run_conditions(
                batch,
                n_trials,
                args.n_proc,
                protocol=protocol,
                cells=source_cells,
                stage=args.stage,
                duration_ms=1000.0,
                force=args.force,
                channels=list(EXPECTED_DIMENSIONS),
                results_subdir="grid",
            ))
        summary = pd.concat(summaries, ignore_index=True)
        condition_by_id = {condition["cond_id"]: condition for condition in conditions}
        for dimension in EXPECTED_DIMENSIONS:
            summary[f"{dimension}_hz"] = summary["cond_id"].map(
                lambda cond_id, name=dimension: condition_by_id[cond_id]["rates"][name]
            )
            summary[dimension] = summary["cond_id"].map(
                lambda cond_id, name=dimension: condition_by_id[cond_id]["levels"][name]
            )
        output = ROOT / "results" / "grid" / args.stage / "summary.csv"
        summary.to_csv(output, index=False)
        print(f"wrote {output.relative_to(ROOT)} ({len(summary)} cells)")
    finally:
        write_meta(args.stage, meta)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
