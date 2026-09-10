#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Run the independent PyTorch Phase-0 cross-check."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sim.network import channel_cell_sets, load_cells, load_protocol
from sim.readout import mn9_rate
from sim.runner import _base_seed, expand_conditions
from sim.torch_backend import build_torch_network


SUMMARY_COLUMNS = [
    "cond_id",
    "mn9_left_mean_hz",
    "mn9_left_std_hz",
    "mn9_right_mean_hz",
    "mn9_right_std_hz",
    "mn9_aggregated_mean_hz",
    "mn9_aggregated_std_hz",
    "n_trials",
    "walltime_s",
]


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


def synchronize(device: torch.device) -> None:
    if device.type == "cuda":
        torch.cuda.synchronize(device)


def summary_row(
    cond_id: str,
    frame: pd.DataFrame,
    protocol: dict,
    n_trials: int,
    duration_ms: float,
    walltime_s: float,
) -> dict:
    stage_protocol = {**protocol, "trial": {**protocol["trial"], "duration_ms": duration_ms}}
    rates = mn9_rate(frame, stage_protocol, n_trials)
    return {
        "cond_id": cond_id,
        "mn9_left_mean_hz": rates["left"]["mean"],
        "mn9_left_std_hz": rates["left"]["std"],
        "mn9_right_mean_hz": rates["right"]["mean"],
        "mn9_right_std_hz": rates["right"]["std"],
        "mn9_aggregated_mean_hz": rates["aggregated"]["mean"],
        "mn9_aggregated_std_hz": rates["aggregated"]["std"],
        "n_trials": n_trials,
        "walltime_s": walltime_s,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", required=True, choices=("smoke", "full"))
    parser.add_argument("--n-trials", type=int)
    parser.add_argument("--device", choices=("cuda", "cpu"))
    args = parser.parse_args()

    if args.n_trials is not None and args.n_trials <= 0:
        parser.error("--n-trials must be positive")
    protocol = load_protocol()
    cells = load_cells()
    device = torch.device(args.device or ("cuda" if torch.cuda.is_available() else "cpu"))
    output_dir = ROOT / "results" / "phase0_torch" / args.stage
    output_dir.mkdir(parents=True, exist_ok=True)
    started_at = datetime.now(timezone.utc).isoformat()
    meta = {
        "torch_version": torch.__version__,
        "device": str(device),
        "device_name": torch.cuda.get_device_name(device) if device.type == "cuda" else "CPU",
        "dt_ms": float(protocol["model"]["dt_ms"]),
        "git_commit": git_commit(),
        "protocol_sha256": sha256(ROOT / "data" / "stim_protocol.json"),
        "start_time": started_at,
        "end_time": None,
    }

    try:
        mappings = channel_cell_sets(protocol)
        synchronize(device)
        build_start = time.perf_counter()
        network = build_torch_network(
            protocol,
            cells,
            {"sugar": mappings["sugar"], "bitter": mappings["bitter"]},
            device,
        )
        synchronize(device)
        build_seconds = time.perf_counter() - build_start
        print(f"device: {meta['device_name']} ({device})")
        print(f"neurons: {network.n_neurons}; coalesced duplicate edges: {network.duplicate_edges}")
        print(f"build time: {build_seconds:.3f} s")

        base_seed = _base_seed(protocol)
        if args.stage == "smoke":
            duration_ms = 200.0
            n_trials = 1
            cond_id = "A_sugar_dose_sugar100Hz_bitter0Hz"
            synchronize(device)
            run_start = time.perf_counter()
            frame = network.run_batched(
                {"sugar": 100.0, "bitter": 0.0}, [base_seed], duration_ms
            )
            synchronize(device)
            elapsed = time.perf_counter() - run_start
            frame.to_parquet(output_dir / f"{cond_id}.parquet", index=False)
            summary = pd.DataFrame(
                [summary_row(cond_id, frame, protocol, n_trials, duration_ms, elapsed)],
                columns=SUMMARY_COLUMNS,
            )
            summary.to_csv(output_dir / "summary.csv", index=False)
            left = int(protocol["readout"]["left"])
            right = int(protocol["readout"]["right"])
            left_count = int((frame["flywire_id"] == left).sum())
            right_count = int((frame["flywire_id"] == right).sum())
            print(f"per-trial time (200 ms): {elapsed:.3f} s")
            print(f"projected per-trial time (1000 ms): {elapsed * 5.0:.3f} s")
            print(f"MN9-left spike count: {left_count}")
            print(f"MN9-right spike count: {right_count}")
        else:
            duration_ms = float(protocol["trial"]["duration_ms"])
            n_trials = int(args.n_trials or protocol["trial"]["n_trials"])
            conditions = expand_conditions(protocol, ["A_sugar_dose", "D_baseline"])
            rows = []
            for condition_index, condition in enumerate(conditions):
                seeds = [
                    base_seed + trial + 1000 * condition_index for trial in range(n_trials)
                ]
                synchronize(device)
                run_start = time.perf_counter()
                frame = network.run_batched(condition["rates"], seeds, duration_ms)
                synchronize(device)
                elapsed = time.perf_counter() - run_start
                frame.to_parquet(
                    output_dir / f"{condition['cond_id']}.parquet", index=False
                )
                rows.append(
                    summary_row(
                        condition["cond_id"], frame, protocol, n_trials, duration_ms, elapsed
                    )
                )
                print(
                    f"{condition['cond_id']}: {elapsed:.3f} s batch, "
                    f"{elapsed / n_trials:.3f} s/trial"
                )
            summary = pd.DataFrame(rows, columns=SUMMARY_COLUMNS)
            summary.to_csv(output_dir / "summary.csv", index=False)
            print(summary.to_string(index=False))
    finally:
        meta["end_time"] = datetime.now(timezone.utc).isoformat()
        (output_dir / "run_meta.json").write_text(
            json.dumps(meta, indent=2) + "\n", encoding="utf-8"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
