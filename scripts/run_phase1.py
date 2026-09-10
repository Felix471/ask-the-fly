#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Run Brian2 Phase 1 smoke or characterization simulations."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import socket
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import brian2

from sim.network import load_cells, load_protocol
from sim.phase1 import CHANNELS, expand_phase1_conditions, phase1_condition_counts
from sim.runner import run_conditions


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git_commit() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=False
    )
    return result.stdout.strip() if result.returncode == 0 else "unknown"


def write_meta(stage: str, meta: dict) -> None:
    directory = ROOT / "results" / "phase1" / stage
    directory.mkdir(parents=True, exist_ok=True)
    meta["end_time"] = datetime.now(timezone.utc).isoformat()
    (directory / "run_meta.json").write_text(
        json.dumps(meta, indent=2) + "\n", encoding="utf-8"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", required=True, choices=("smoke", "characterize"))
    parser.add_argument("--n-proc", type=int, default=14)
    parser.add_argument("--n-trials", type=int)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--batch-size", type=int, default=40,
                        help="conditions per joblib batch; bounds parent-process memory (all spikes of a batch are returned at once)")
    args = parser.parse_args()
    if args.n_proc <= 0:
        parser.error("--n-proc must be positive")
    if args.n_trials is not None and args.n_trials <= 0:
        parser.error("--n-trials must be positive")

    protocol, cells = load_protocol(), load_cells()
    all_conditions = expand_phase1_conditions(protocol)
    raw_count, unique_count = phase1_condition_counts(protocol)
    print(f"Phase 1 conditions: {raw_count} raw, {unique_count} deduplicated")
    if args.stage == "smoke":
        wanted = {
            "S_sugar_100Hz", "S_water_100Hz", "P_sugar100Hz_bitter100Hz"
        }
        conditions = [condition for condition in all_conditions if condition["cond_id"] in wanted]
        if len(conditions) != len(wanted):
            missing = wanted - {condition["cond_id"] for condition in conditions}
            raise ValueError(f"Missing smoke conditions: {sorted(missing)}")
        n_trials = 1
    else:
        conditions = all_conditions
        n_trials = args.n_trials or int(protocol["trial"]["n_trials"])

    meta = {
        "git_commit": git_commit(),
        "protocol_sha256": sha256(ROOT / "data" / "stim_protocol.json"),
        "cells_sha256": sha256(ROOT / "data" / "cells.json"),
        "brian2_version": brian2.__version__,
        "codegen_target": str(brian2.prefs.codegen.target),
        "n_proc": args.n_proc,
        "hostname": socket.gethostname(),
        "start_time": datetime.now(timezone.utc).isoformat(),
        "end_time": None,
        "n_conditions": len(conditions),
        "n_conditions_raw": raw_count,
    }
    try:
        import pandas as pd
        batch_size = max(1, args.batch_size)
        batches = [conditions[i:i + batch_size] for i in range(0, len(conditions), batch_size)]
        summaries = []
        for batch_index, batch in enumerate(batches, start=1):
            print(f"batch {batch_index}/{len(batches)}: {len(batch)} conditions x {n_trials} trials", flush=True)
            summaries.append(run_conditions(
                batch,
                n_trials,
                args.n_proc,
                protocol=protocol,
                cells=cells,
                stage=args.stage,
                duration_ms=1000.0,
                force=args.force,
                channels=list(CHANNELS),
                results_subdir="phase1",
            ))
        summary = pd.concat(summaries, ignore_index=True)
        rates_by_id = {condition["cond_id"]: condition["rates"] for condition in conditions}
        for channel in CHANNELS:
            summary[f"{channel}_hz"] = summary["cond_id"].map(
                lambda cond_id, name=channel: rates_by_id[cond_id][name]
            )
        output = ROOT / "results" / "phase1" / args.stage / "summary.csv"
        summary.to_csv(output, index=False)
        print(summary.to_string(index=False))
    finally:
        write_meta(args.stage, meta)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
