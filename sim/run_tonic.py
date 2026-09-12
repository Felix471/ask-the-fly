#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Phase T: tonic-inhibition condition (Tastekin et al. 2026 Fig S17 style), designed, uncalibrated.

A brake (an inhibitory input to MN9, data/stim_protocol_tonic.json) is driven continuously with
the same Poisson mechanism the GRN channels use, at 0 / 50 / 100 / 150 Hz, while sugar takes the
five frozen grid levels and bitter, water and ir94e stay at 0 Hz. The frozen protocol, cell sets,
grid levels and lookup table are read, never written.

  .venv\\Scripts\\python -m sim.run_tonic --stage dry      # one trial per check condition
  .venv\\Scripts\\python -m sim.run_tonic --stage full     # 3 brakes x 4 drives x 5 sugar x 30 trials
  .venv\\Scripts\\python -m sim.run_tonic --stage replays  # one whole-network trial per replay condition

Results: results/tonic/<stage>/<cond_id>.parquet + .meta.json ledger, summary.csv with the extra
readouts, run_meta.json. Replays: results/tonic/replays/<cond_id>.npz.
"""

from __future__ import annotations

import argparse
import hashlib
import json
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

from sim.grid import EXPECTED_DIMENSIONS, load_grid_levels  # noqa: E402
from sim.network import load_cells, load_protocol  # noqa: E402
from sim.readout import mn9_rate  # noqa: E402
from sim.runner import _base_seed, run_conditions, seed_for  # noqa: E402

TONIC_PATH = ROOT / "data" / "stim_protocol_tonic.json"
RESULTS = ROOT / "results" / "tonic"
CHANNELS = [*EXPECTED_DIMENSIONS, "brake"]
REPLAY_SEED_OFFSET = 700_000 + 100_000


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git_commit() -> str:
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=False)
    return result.stdout.strip() if result.returncode == 0 else "unknown"


def load_tonic() -> tuple[dict, dict, dict]:
    """Return (merged protocol, cells with brake sets, tonic spec). Nothing on disk is modified."""
    tonic = json.loads(TONIC_PATH.read_text(encoding="utf-8"))
    base = load_protocol(tonic["base_protocol"])
    cells = load_cells()
    protocol = json.loads(json.dumps(base))  # deep copy of the frozen protocol
    protocol["stimulus"]["channels"]["brake"] = {"cell_set": "brake_" + next(iter(tonic["brakes"])), "phase": "T"}
    protocol["tonic"] = {k: tonic[k] for k in ("tonic_protocol_version", "brake_channel", "brakes", "taste")}
    for name, brake in tonic["brakes"].items():
        cells["sets"]["brake_" + name] = {"ids": [int(x) for x in brake["ids"]], "count": len(brake["ids"]),
                                          "source": f"data/stim_protocol_tonic.json brakes.{name}"}
    return protocol, cells, tonic


def sugar_levels() -> list[tuple[str, float]]:
    levels = load_grid_levels()["levels"]["sugar"]
    return [(name, float(hz)) for name, hz in levels.items()]


def conditions(tonic: dict) -> list[dict]:
    """Every (brake, drive, sugar level) in product order; global_index is the seed identity."""
    out = []
    for brake in tonic["brakes"]:
        for drive in tonic["brake_channel"]["drive_hz"]:
            for level, hz in sugar_levels():
                out.append({
                    "cond_id": f"T_{brake}_d{int(drive)}_s{level}",
                    "cell_set_override": {"brake": "brake_" + brake},
                    "rates": {"sugar": hz, "bitter": 0.0, "water": 0.0, "ir94e": 0.0, "brake": float(drive)},
                    "brake": brake, "drive": float(drive), "sugar_level": level,
                    "global_index": len(out),
                })
    return out


def dry_conditions(tonic: dict) -> list[dict]:
    """Per brake: drive 100 / sugar none (brake fires, MN9 silent) and drive 0 / sugar high (grid check)."""
    wanted = {("100", "none"), ("0", "high")}
    return [c for c in conditions(tonic) if (str(int(c["drive"])), c["sugar_level"]) in wanted]


def replay_conditions(tonic: dict) -> list[dict]:
    wanted = {("100", "high"), ("100", "none")}
    return [c for c in conditions(tonic) if (str(int(c["drive"])), c["sugar_level"]) in wanted]


def extra_readouts(frame: pd.DataFrame, condition: dict, cells: dict, protocol: dict, n_trials: int) -> dict:
    """Brake-cell rate, first-left-MN9-spike latency, sugar-GRN rate, all per trial then summarised."""
    duration_s = float(protocol["trial"]["duration_ms"]) / 1000.0
    brake_ids = set(cells["sets"]["brake_" + condition["brake"]]["ids"])
    sugar_ids = set(int(x) for x in cells["sets"]["sugar"]["ids"])
    left = int(protocol["readout"]["left"])

    def set_rate(ids: set[int]) -> np.ndarray:
        rates = np.zeros(n_trials)
        if not frame.empty:
            sub = frame[frame["flywire_id"].isin(ids)]
            for trial, count in sub.groupby("trial").size().items():
                rates[int(trial)] = count / len(ids) / duration_s
        return rates

    brake = set_rate(brake_ids)
    sugar = set_rate(sugar_ids)
    latency = np.full(n_trials, np.nan)
    if not frame.empty:
        sub = frame[frame["flywire_id"] == left]
        for trial, t_first in sub.groupby("trial")["t"].min().items():
            latency[int(trial)] = float(t_first) * 1000.0
    with_spike = latency[~np.isnan(latency)]
    return {
        "brake_rate_mean_hz": float(brake.mean()), "brake_rate_std_hz": float(brake.std()),
        "sugar_grn_rate_mean_hz": float(sugar.mean()), "sugar_grn_rate_std_hz": float(sugar.std()),
        "latency_left_median_ms": float(np.median(with_spike)) if len(with_spike) else float("nan"),
        "latency_left_mean_ms": float(with_spike.mean()) if len(with_spike) else float("nan"),
        "trials_without_left_spike": int(n_trials - len(with_spike)),
    }


def summarise(stage: str, conds: list[dict], cells: dict, protocol: dict, n_trials: int) -> pd.DataFrame:
    out_dir = RESULTS / stage
    summary = pd.read_csv(out_dir / "summary.csv")
    by_id = {c["cond_id"]: c for c in conds}
    rows = []
    for _, row in summary.iterrows():
        condition = by_id[row["cond_id"]]
        frame = pd.read_parquet(out_dir / f"{condition['cond_id']}.parquet")
        ledger = json.loads((out_dir / f"{condition['cond_id']}.meta.json").read_text(encoding="utf-8"))
        rates = mn9_rate(frame, protocol, n_trials, completed_trials=ledger["completed_trials"])
        rows.append({
            "cond_id": condition["cond_id"], "brake": condition["brake"], "drive_hz": condition["drive"],
            "sugar_level": condition["sugar_level"], "sugar_hz": condition["rates"]["sugar"],
            "mn9_left_mean_hz": rates["left"]["mean"], "mn9_left_std_hz": rates["left"]["std"],
            "mn9_right_mean_hz": rates["right"]["mean"], "mn9_right_std_hz": rates["right"]["std"],
            **extra_readouts(frame, condition, cells, protocol, n_trials),
            "n_trials": n_trials, "walltime_s": row["walltime_s"],
        })
    table = pd.DataFrame(rows).sort_values(["brake", "drive_hz", "sugar_hz"]).reset_index(drop=True)
    table.to_csv(out_dir / "summary_tonic.csv", index=False)
    return table


def run_stage(stage: str, conds: list[dict], n_trials: int, n_proc: int, force: bool) -> pd.DataFrame:
    protocol, cells, tonic = load_tonic()
    out_dir = RESULTS / stage
    out_dir.mkdir(parents=True, exist_ok=True)
    meta = {
        "stage": stage, "git_commit": git_commit(),
        "base_protocol_sha256": sha256(ROOT / "data" / "stim_protocol.json"),
        "tonic_protocol_sha256": sha256(TONIC_PATH), "cells_sha256": sha256(ROOT / "data" / "cells.json"),
        "grid_levels_sha256": sha256(ROOT / "data" / "grid_levels.json"),
        "n_conditions": len(conds), "n_trials": n_trials, "n_proc": n_proc, "channels": CHANNELS,
        "seed_scheme": "v2 (base_seed + trial + 1000 * global_index over the (brake, drive, sugar) product)",
        "hostname": socket.gethostname(), "start_time": datetime.now(timezone.utc).isoformat(), "end_time": None,
    }
    started = time.perf_counter()
    try:
        # One batch per brake: every condition of a batch shares one network build per worker.
        for brake in tonic["brakes"]:
            batch = [c for c in conds if c["brake"] == brake]
            if not batch:
                continue
            print(f"brake {brake}: {len(batch)} conditions x {n_trials} trials", flush=True)
            run_conditions(batch, n_trials, n_proc, protocol=protocol, cells=cells, stage=stage,
                           duration_ms=float(protocol["trial"]["duration_ms"]), force=force,
                           channels=CHANNELS, results_subdir="tonic")
        # run_conditions rewrites summary.csv per batch; rebuild it from the ledgers of every condition.
        frames = []
        for c in conds:
            ledger = json.loads((out_dir / f"{c['cond_id']}.meta.json").read_text(encoding="utf-8"))
            frames.append({"cond_id": c["cond_id"], "walltime_s": float("nan"), "n_trials": len(ledger["completed_trials"])})
        pd.DataFrame(frames).to_csv(out_dir / "summary.csv", index=False)
        table = summarise(stage, conds, cells, protocol, n_trials)
    finally:
        meta["end_time"] = datetime.now(timezone.utc).isoformat()
        meta["walltime_s"] = round(time.perf_counter() - started, 1)
        (out_dir / "run_meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print(f"{stage}: {len(conds)} conditions, walltime {meta['walltime_s']} s", flush=True)
    return table


def run_replays(n_proc: int) -> None:
    from joblib import Parallel, delayed

    from sim.network import build_network, channel_cell_sets

    protocol, cells, tonic = load_tonic()
    out_dir = RESULTS / "replays"
    out_dir.mkdir(parents=True, exist_ok=True)
    conds = replay_conditions(tonic)
    base = _base_seed(protocol)
    duration_ms = float(protocol["trial"]["duration_ms"])

    def one(condition: dict) -> dict:
        seed = base + REPLAY_SEED_OFFSET + condition["global_index"]
        mappings = channel_cell_sets(protocol, condition["cell_set_override"])
        network = build_network(protocol, cells, {name: mappings[name] for name in CHANNELS})
        started = time.perf_counter()
        spikes = network.run_trial(condition["rates"], seed, duration_ms)
        elapsed = time.perf_counter() - started
        ids = np.concatenate([np.full(len(t), fid, dtype=np.int64) for fid, t in spikes.items()]) if spikes else np.zeros(0, np.int64)
        times = np.concatenate([np.asarray(t, dtype=np.float64) for t in spikes.values()]) if spikes else np.zeros(0)
        order = np.argsort(times, kind="stable")
        np.savez_compressed(
            out_dir / f"{condition['cond_id']}.npz",
            flywire_id=ids[order], t_ms=times[order] * 1000.0, seed=np.int64(seed),
            condition_index=np.int64(condition["global_index"]),
            rates=np.array([condition["rates"][d] for d in CHANNELS], dtype=np.float64),
            channels=np.array(CHANNELS), elapsed_s=np.float64(elapsed),
        )
        left = int(protocol["readout"]["left"])
        return {"cond_id": condition["cond_id"], "seed": seed, "n_spikes": int(len(order)),
                "left_mn9_spikes": int(len(spikes.get(left, []))), "elapsed_s": round(elapsed, 2)}

    results = Parallel(n_jobs=min(n_proc, len(conds)), backend="loky")(delayed(one)(c) for c in conds)
    meta = {"git_commit": git_commit(), "tonic_protocol_sha256": sha256(TONIC_PATH), "channels": CHANNELS,
            "seed_rule": f"base_seed + {REPLAY_SEED_OFFSET} + global_index", "replays": results,
            "written_at": datetime.now(timezone.utc).isoformat()}
    (out_dir / "run_meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    for r in results:
        print(f"replay {r['cond_id']}: {r['n_spikes']} spikes, left MN9 {r['left_mn9_spikes']}, {r['elapsed_s']} s")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--stage", required=True, choices=("dry", "full", "replays"))
    parser.add_argument("--n-proc", type=int, default=14)
    parser.add_argument("--n-trials", type=int, help="override (full stage default: protocol n_trials; dry: 1)")
    parser.add_argument("--force", action="store_true", help="rerun conditions that already have a verified ledger")
    args = parser.parse_args()
    _, _, tonic = load_tonic()
    if args.stage == "replays":
        run_replays(args.n_proc)
        return 0
    if args.stage == "dry":
        conds, n_trials = dry_conditions(tonic), args.n_trials or 1
    else:
        conds, n_trials = conditions(tonic), args.n_trials or int(tonic["trial"]["n_trials"])
    table = run_stage(args.stage, conds, n_trials, args.n_proc, args.force)
    with pd.option_context("display.width", 200, "display.max_columns", 30):
        print(table[["cond_id", "mn9_left_mean_hz", "mn9_left_std_hz", "mn9_right_mean_hz", "brake_rate_mean_hz",
                     "sugar_grn_rate_mean_hz", "latency_left_median_ms", "trials_without_left_spike"]].to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
