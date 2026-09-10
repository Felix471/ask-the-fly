#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Derived from Shiu et al. (2024) model.py, used under the MIT License.
"""Run Phase-0 smoke, equivalence, sanity, or full simulations."""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import os
import platform
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import brian2
from brian2 import prefs

from sim import legacy
from sim.network import build_network, channel_cell_sets, load_cells, load_protocol
from sim.readout import mn9_rate
from sim.runner import _base_seed, expand_conditions, run_conditions, spikes_dataframe


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


def metadata_start(args: argparse.Namespace, n_proc: int) -> dict:
    return {
        "git_commit": git_commit(),
        "protocol_sha256": sha256(ROOT / "data/stim_protocol.json"),
        "cells_sha256": sha256(ROOT / "data/cells.json"),
        "brian2_version": brian2.__version__,
        "codegen_target": args.target,
        "n_proc": n_proc,
        "hostname": socket.gethostname(),
        "start_time": datetime.now(timezone.utc).isoformat(),
        "end_time": None,
    }


def write_meta(stage: str, meta: dict) -> None:
    directory = ROOT / "results" / "phase0" / stage
    directory.mkdir(parents=True, exist_ok=True)
    meta["end_time"] = datetime.now(timezone.utc).isoformat()
    (directory / "run_meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")


def smoke(protocol: dict, cells: dict, target: str) -> None:
    mappings = channel_cell_sets(protocol)
    start = time.perf_counter()
    network = build_network(protocol, cells, {"sugar": mappings["sugar"], "bitter": mappings["bitter"]})
    build_seconds = time.perf_counter() - start
    start = time.perf_counter()
    spikes = network.run_trial({"sugar": 100.0, "bitter": 0.0}, _base_seed(protocol), 200.0)
    run_seconds = time.perf_counter() - start
    count = len(spikes.get(int(protocol["readout"]["left"]), [])) + len(
        spikes.get(int(protocol["readout"]["right"]), [])
    )
    frame = spikes_dataframe([(0, spikes)])
    directory = ROOT / "results" / "phase0" / "smoke"
    directory.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(directory / "A_sugar_dose_sugar100Hz_bitter0Hz.parquet", index=False)
    stage_protocol = {**protocol, "trial": {**protocol["trial"], "duration_ms": 200}}
    rates = mn9_rate(frame, stage_protocol, 1)
    pd.DataFrame([{
        "cond_id": "A_sugar_dose_sugar100Hz_bitter0Hz",
        "mn9_left_mean_hz": rates["left"]["mean"],
        "mn9_left_std_hz": rates["left"]["std"],
        "mn9_right_mean_hz": rates["right"]["mean"],
        "mn9_right_std_hz": rates["right"]["std"],
        "mn9_aggregated_mean_hz": rates["aggregated"]["mean"],
        "mn9_aggregated_std_hz": rates["aggregated"]["std"],
        "n_trials": 1,
        "walltime_s": run_seconds,
    }]).to_csv(directory / "summary.csv", index=False)
    print(f"smoke target: {target}")
    print(f"build time: {build_seconds:.3f} s")
    print(f"run time: {run_seconds:.3f} s")
    print(f"MN9 spike count: {count}")


def equivalence(protocol: dict, cells: dict) -> None:
    mappings = {"sugar": channel_cell_sets(protocol)["sugar"]}
    duration = float(protocol["trial"]["duration_ms"])
    seeds = [_base_seed(protocol) + trial for trial in range(5)]
    build_start = time.perf_counter()
    network = build_network(protocol, cells, mappings)
    reusable_build = time.perf_counter() - build_start
    reusable, reusable_times = [], []
    for seed in seeds:
        start = time.perf_counter()
        reusable.append(network.run_trial({"sugar": 100.0}, seed, duration))
        reusable_times.append(time.perf_counter() - start)

    legacy_results, legacy_times = [], []
    for seed in seeds:
        start = time.perf_counter()
        result = legacy.run_trial(protocol, cells, mappings, {"sugar": 100.0}, seed, duration)
        legacy_times.append(time.perf_counter() - start)
        legacy_results.append(result)
        gc.collect()

    reusable_df = spikes_dataframe(list(enumerate(reusable)))
    legacy_df = spikes_dataframe(list(enumerate(legacy_results)))
    reusable_rates = mn9_rate(reusable_df, protocol, 5)
    legacy_rates = mn9_rate(legacy_df, protocol, 5)
    reusable_rate = reusable_rates["left"]
    legacy_rate = legacy_rates["left"]
    directory = ROOT / "results" / "phase0" / "equiv"
    directory.mkdir(parents=True, exist_ok=True)
    reusable_df.to_parquet(directory / "reusable_sugar100Hz.parquet", index=False)
    legacy_df.to_parquet(directory / "legacy_sugar100Hz.parquet", index=False)
    pd.DataFrame([
        {
            "cond_id": "reusable_sugar100Hz",
            "mn9_left_mean_hz": reusable_rates["left"]["mean"],
            "mn9_left_std_hz": reusable_rates["left"]["std"],
            "mn9_right_mean_hz": reusable_rates["right"]["mean"],
            "mn9_right_std_hz": reusable_rates["right"]["std"],
            "mn9_aggregated_mean_hz": reusable_rates["aggregated"]["mean"],
            "mn9_aggregated_std_hz": reusable_rates["aggregated"]["std"],
            "n_trials": 5,
            "walltime_s": sum(reusable_times),
        },
        {
            "cond_id": "legacy_sugar100Hz",
            "mn9_left_mean_hz": legacy_rates["left"]["mean"],
            "mn9_left_std_hz": legacy_rates["left"]["std"],
            "mn9_right_mean_hz": legacy_rates["right"]["mean"],
            "mn9_right_std_hz": legacy_rates["right"]["std"],
            "mn9_aggregated_mean_hz": legacy_rates["aggregated"]["mean"],
            "mn9_aggregated_std_hz": legacy_rates["aggregated"]["std"],
            "n_trials": 5,
            "walltime_s": sum(legacy_times),
        },
    ]).to_csv(directory / "summary.csv", index=False)
    print(f"reusable MN9-left: {reusable_rate['mean']:.3f} +/- {reusable_rate['std']:.3f} Hz")
    print(f"legacy MN9-left: {legacy_rate['mean']:.3f} +/- {legacy_rate['std']:.3f} Hz")
    print(f"reusable build time: {reusable_build:.3f} s")
    print("reusable per-trial walltimes: " + ", ".join(f"{value:.3f} s" for value in reusable_times))
    print(f"reusable time to first run: {reusable_times[0]:.3f} s")
    print(f"reusable mean subsequent run time: {np.mean(reusable_times[1:]):.3f} s")
    print("legacy per-trial walltimes: " + ", ".join(f"{value:.3f} s" for value in legacy_times))
    print(f"legacy time to first run: {legacy_times[0]:.3f} s")
    print(f"legacy mean subsequent run time: {np.mean(legacy_times[1:]):.3f} s")
    lo1, hi1 = reusable_rate["mean"] - reusable_rate["std"], reusable_rate["mean"] + reusable_rate["std"]
    lo2, hi2 = legacy_rate["mean"] - legacy_rate["std"], legacy_rate["mean"] + legacy_rate["std"]
    if max(lo1, lo2) > min(hi1, hi2):
        raise RuntimeError("Equivalence check failed: MN9-left mean +/- 1 std intervals do not overlap")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", required=True, choices=("smoke", "equiv", "sanity", "full"))
    parser.add_argument("--target", choices=("cython", "numpy"), default="cython")
    parser.add_argument("--n-proc", type=int, default=min(24, os.cpu_count() or 1))
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if args.target == "numpy" and args.stage != "smoke":
        parser.error("--target numpy is allowed only for --stage smoke")
    prefs.codegen.target = args.target
    protocol, cells = load_protocol(), load_cells()
    meta = metadata_start(args, args.n_proc)
    try:
        if args.stage == "smoke":
            smoke(protocol, cells, args.target)
        elif args.stage == "equiv":
            equivalence(protocol, cells)
        else:
            keys = list(protocol["phase0_conditions"])
            if args.stage == "sanity":
                keys.remove("A_prime_sugar_bench21")
            conditions = expand_conditions(protocol, keys)
            if args.stage == "sanity":
                conditions = [
                    condition for condition in conditions
                    if not condition["cond_id"].startswith("A_sugar_dose_")
                    or condition["rates"]["sugar"] in (25.0, 100.0, 200.0)
                ]
            summary = run_conditions(
                conditions,
                protocol["trial"]["sanity_n_trials" if args.stage == "sanity" else "n_trials"],
                args.n_proc,
                protocol=protocol,
                cells=cells,
                stage=args.stage,
                force=args.force if args.stage == "full" else True,
            )
            print(summary.to_string(index=False))
    finally:
        write_meta(args.stage, meta)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
