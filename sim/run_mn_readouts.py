# SPDX-License-Identifier: MIT
"""C2: 13 selected cells x 30 published-grid seeds; extra MN readouts only.

Run with WSL2 flybrain: python -B -m sim.run_mn_readouts --n-proc 13
Frozen network/protocol/grid/site files are only read. No simulation on import.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import platform
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from sim.grid import EXPECTED_DIMENSIONS, expand_grid_conditions, load_grid_levels
from scripts.mn_readouts_from_replays import aggregate_metrics, neuron_metrics

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "data/stim_protocol_mn.json"
SELECTED = (
    (0, 0, 0, 0), (0, 0, 0, 200), (120, 0, 0, 0),
    (120, 60, 0, 0), (120, 100, 0, 0), (120, 160, 0, 0),
    (120, 0, 0, 200), (0, 0, 240, 0), (0, 30, 240, 0),
    (200, 100, 60, 200), (200, 100, 0, 200), (60, 0, 0, 0), (80, 0, 0, 0),
)


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def published_grid_seed(global_index, trial, base_seed=20260910):
    for value, upper, name in ((global_index, 400, "global_index"), (trial, 30, "trial")):
        if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)) or not 0 <= value < upper:
            raise ValueError(f"invalid {name}")
    if isinstance(base_seed, (bool, np.bool_)) or not isinstance(base_seed, (int, np.integer)) or base_seed < 0:
        raise ValueError("invalid base_seed")
    return int(base_seed) + 1000 * (int(global_index) % 40) + int(trial)


def select_conditions():
    by_hz = {tuple(c["rates"][d] for d in EXPECTED_DIMENSIONS): c
             for c in expand_grid_conditions(load_grid_levels())}
    return [by_hz[hz] for hz in SELECTED]


def summarize_trials(values, latencies):
    if not len(values) or len(values) != len(latencies):
        raise ValueError("rates and latencies must be matching nonempty vectors")
    rates = np.asarray(values, dtype=float)
    if rates.ndim != 1 or not np.all(np.isfinite(rates)) or np.any(rates < 0):
        raise ValueError("invalid rates")
    observed = []
    for rate, latency in zip(rates, latencies):
        if latency is not None:
            if not math.isfinite(latency) or not 0 <= latency < 1000:
                raise ValueError("invalid first-spike latency")
            if rate == 0:
                raise ValueError("silent rate has a spike latency")
            observed.append(latency)
        elif rate > 0:
            raise ValueError("positive rate is missing its first-spike latency")
    return {"n_trials": len(rates), "rate_mean_hz": float(rates.mean()),
            "rate_std_hz": float(rates.std(ddof=0)),
            "latency_median_ms": float(np.median(observed)) if observed else None,
            "active_trials": len(observed), "silent_trials": len(rates) - len(observed)}


def ratio_of_means(numerator_values, baseline_values):
    vectors = [np.asarray(v, dtype=float) for v in (numerator_values, baseline_values)]
    if any(v.shape != (30,) or not np.all(np.isfinite(v)) or np.any(v < 0) for v in vectors):
        raise ValueError("ratio needs two complete finite nonnegative 30-trial vectors")
    denominator = float(vectors[1].mean())
    return float(vectors[0].mean()) / denominator if denominator else None


def groups_for(spec, protocol):
    result = {"MN9_L": [str(protocol["readout"]["left"])],
              "MN9_R": [str(protocol["readout"]["right"])]}
    for kind in ("MN11D", "MN11V", "CEM"):
        result[kind] = [n["Body_ID"] for n in spec["readout_neurons"] if n["Type"] == kind]
    if [len(v) for v in result.values()] != [1, 1, 2, 2, 6]:
        raise ValueError("expected exactly 12 authorised readout neurons")
    return result


def load_design():
    spec = load_json(SPEC)
    base_path = ROOT / spec["base_protocol"]
    if base_path.resolve() != (ROOT / "data/stim_protocol.json").resolve() or sha256(base_path) != spec["base_protocol_sha256"]:
        raise ValueError("frozen base protocol mismatch")
    protocol = load_json(base_path)
    inventory = load_json(ROOT / spec["readout_source"])
    selected = [n for n in inventory["neurons"] if n["Type"] in {"MN9", "MN11D", "MN11V", "CEM"}]
    if selected != spec["readout_neurons"] or not all(n["in_v783"] for n in selected):
        raise ValueError("readouts differ from the verified source inventory")
    if spec["selection_dimensions"] != list(EXPECTED_DIMENSIONS) or tuple(map(tuple, spec["selected_cells_hz"])) != SELECTED:
        raise ValueError("selection differs from the 13 authorised cells")
    if spec["trial"]["n_trials"] != 30 or spec["trial"]["seed_scheme"] != "published_grid_v1_batch40":
        raise ValueError("C2 requires 30 trials and the published grid seed scheme")
    if list(protocol["stimulus"]["channels"]) != list(EXPECTED_DIMENSIONS) or protocol["trial"]["duration_ms"] != 1000:
        raise ValueError("original four-channel order/duration changed")
    groups_for(spec, protocol)
    return spec, protocol


def _run_cell(condition, spec, protocol, output_dir, identity):
    # Brian2 is loaded only inside authorised WSL simulation workers.
    import pandas as pd
    from sim.network import build_network, load_cells

    cell_id = condition["cond_id"]
    out = Path(output_dir)
    ledger_path = out / f"{cell_id}.json"
    spikes_path = out / f"{cell_id}.npz"
    original_path = ROOT / "results/grid/full" / f"{cell_id}.parquet"
    expected = {**identity, "cell_id": cell_id, "global_index": condition["global_index"],
                "input_hz": condition["rates"],
                "seeds": [published_grid_seed(condition["global_index"], t) for t in range(30)],
                "original_grid_parquet_sha256": sha256(original_path)}
    if ledger_path.exists() or spikes_path.exists():
        if not ledger_path.exists() or not spikes_path.exists():
            raise ValueError(f"{cell_id}: incomplete output; refusing to overwrite it")
        saved = load_json(ledger_path)
        if saved.get("identity") != expected or saved.get("completed_trials") != list(range(30)) or saved.get("spikes_sha256") != sha256(spikes_path):
            raise ValueError(f"{cell_id}: stored result identity/completion/hash mismatch")
        print(f"reuse verified {cell_id}", flush=True)
        return saved
    original = pd.read_parquet(original_path, columns=["flywire_id", "trial", "t"])
    if not original.empty and (set(original["trial"].unique()) - set(range(30))):
        raise ValueError("original grid has unexpected trial indices")
    references = {(int(root_id), int(trial)): np.sort(frame["t"].to_numpy())
                  for (root_id, trial), frame in original[original["flywire_id"].isin(
                      [int(protocol["readout"][side]) for side in ("left", "right")])].groupby(["flywire_id", "trial"])}
    del original
    network = build_network(protocol, load_cells(), list(EXPECTED_DIMENSIONS))
    readouts = spec["readout_neurons"]
    root_ids = [n["Body_ID"] for n in readouts]
    groups = groups_for(spec, protocol)
    individual, grouped, raw_ids, raw_times, raw_trials = [], [], [], [], []
    started = time.perf_counter()
    for trial, seed in enumerate(expected["seeds"]):
        spikes = network.run_trial(condition["rates"], seed, 1000.0)
        for side in ("left", "right"):
            root_id = int(protocol["readout"][side])
            observed = np.sort(spikes.get(root_id, np.array([], dtype=float)))
            previous = references.get((root_id, trial), np.array([], dtype=float))
            if not np.array_equal(observed, previous):
                raise ValueError(f"STOP: {cell_id} trial {trial} seed {seed}: {side} MN9 spikes differ from original grid")
        pieces = [(int(root_id), np.asarray(spikes.get(int(root_id), []), dtype=float) * 1000) for root_id in root_ids]
        ids = np.concatenate([np.full(len(ts), rid, dtype=np.int64) for rid, ts in pieces])
        times = np.concatenate([ts for _, ts in pieces])
        metrics = neuron_metrics(ids, times, root_ids, 1000.0)
        prefix = {"cell_id": cell_id, "global_index": condition["global_index"], "trial": trial, "seed": seed}
        individual.extend({**prefix, **n, **metrics[n["Body_ID"]]} for n in readouts)
        grouped.extend({**prefix, "readout": name, **aggregate_metrics([metrics[r] for r in members])}
                       for name, members in groups.items())
        raw_ids.append(ids)
        raw_times.append(times)
        raw_trials.append(np.full(len(times), trial, dtype=np.int64))
    np.savez_compressed(spikes_path, flywire_id=np.concatenate(raw_ids), t_ms=np.concatenate(raw_times),
                        trial=np.concatenate(raw_trials), seeds=np.array(expected["seeds"], dtype=np.int64))
    saved = {"identity": expected, "completed_trials": list(range(30)),
             "mn9_bilateral_exact_spike_match_trials": 30, "spikes_sha256": sha256(spikes_path),
             "individual": individual, "grouped": grouped, "elapsed_s": time.perf_counter() - started}
    ledger_path.write_text(json.dumps(saved, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(f"complete {cell_id}: 30/30 trials; bilateral MN9 exact spike match", flush=True)
    return saved


def write_csv(path, rows):
    with Path(path).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_summary(results, spec, protocol, out):
    groups = groups_for(spec, protocol)
    individuals = [r for result in results for r in result["individual"]]
    grouped = [r for result in results for r in result["grouped"]]
    summaries, arrays = [], {}
    for result in results:
        identity = result["identity"]
        cell_id = identity["cell_id"]
        per_cell = {}
        arrays[cell_id] = {}
        for group in groups:
            rows = sorted([r for r in result["grouped"] if r["readout"] == group], key=lambda r: r["trial"])
            if [r["trial"] for r in rows] != list(range(30)):
                raise ValueError("missing/duplicate group trial; silence cannot fill missing trials")
            values, latencies = [r["rate_hz"] for r in rows], [r["first_spike_ms"] for r in rows]
            per_cell[group] = summarize_trials(values, latencies)
            arrays[cell_id][group] = values
        summaries.append({"cell_id": cell_id, "global_index": identity["global_index"],
                          "input_hz": identity["input_hz"], "readouts": per_cell})
    baseline = next(c for c in summaries if tuple(c["input_hz"].values()) == (120, 0, 0, 0))
    ratios = []
    for bitter in (0, 60, 100, 160):
        cell = next(c for c in summaries if tuple(c["input_hz"].values()) == (120, bitter, 0, 0))
        ratios.append({"bitter_hz": bitter, **{name: ratio_of_means(arrays[cell["cell_id"]][name], arrays[baseline["cell_id"]][name])
                                             for name in groups if name != "CEM"}})
    summary = {"n_cells": 13, "n_trials_per_cell": 30, "n_readout_neurons": 12,
               "std_ddof": 0, "latency_median": "observed trials only; active/silent counts reported",
               "mn9_bilateral_exact_spike_match_trials": sum(r["mn9_bilateral_exact_spike_match_trials"] for r in results),
               "cells": summaries, "bitter_ratios": ratios}
    write_csv(out / "individual_trials.csv", individuals)
    write_csv(out / "group_trials.csv", grouped)
    write_csv(out / "bitter_ratios.csv", ratios)
    (out / "summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    lines = ["### C2 rates (mean ± population SD, Hz; 30 trials)", "",
             "| Inputs (sugar,bitter,water,Ir94e), Hz | MN9 L | MN9 R | MN11D | MN11V | CEM |",
             "|---|---:|---:|---:|---:|---:|"]
    for cell in summaries:
        rates = [f"{cell['readouts'][g]['rate_mean_hz']:.3f} ± {cell['readouts'][g]['rate_std_hz']:.3f}" for g in groups]
        lines.append(f"| {tuple(cell['input_hz'].values())} | " + " | ".join(rates) + " |")
    lines += ["", "### C2 first-spike latency medians (ms; active trials / 30)", "",
              "| Inputs (sugar,bitter,water,Ir94e), Hz | MN9 L | MN9 R | MN11D | MN11V | CEM |",
              "|---|---:|---:|---:|---:|---:|"]
    for cell in summaries:
        entries = []
        for group in groups:
            value = cell["readouts"][group]
            median = "none" if value["latency_median_ms"] is None else f"{value['latency_median_ms']:.2f}"
            entries.append(f"{median} ({value['active_trials']}/30)")
        lines.append(f"| {tuple(cell['input_hz'].values())} | " + " | ".join(entries) + " |")
    lines += ["", "### Bitter / no-bitter mean-rate ratios (sugar 120 Hz; water/Ir94e 0)", "",
              "| Bitter input Hz | MN9 L | MN9 R | MN11D | MN11V |", "|---:|---:|---:|---:|---:|"]
    for row in ratios:
        lines.append(f"| {row['bitter_hz']} | " + " | ".join(f"{row[g]:.6f}" for g in groups if g != "CEM") + " |")
    (out / "tables.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n-proc", type=int, default=13)
    parser.add_argument("--out", type=Path, default=ROOT / "results/mn-readouts/c2")
    parser.add_argument("--check-design", action="store_true", help="validate inputs without simulation")
    args = parser.parse_args()
    if not 1 <= args.n_proc <= 32:
        parser.error("n-proc must be 1..32")
    out = args.out.resolve()
    if not out.is_relative_to((ROOT / "results/mn-readouts").resolve()):
        parser.error("output must be inside results/mn-readouts/")
    spec, protocol = load_design()
    conditions = select_conditions()
    if args.check_design:
        print("design valid: 13 cells x 30 published-grid trials; 12 readouts; no simulation")
        return
    if platform.system() != "Linux" or "microsoft" not in platform.release().lower():
        raise RuntimeError("Brian2 runs only in the configured WSL2 flybrain environment")
    from joblib import Parallel, delayed
    import brian2
    files = [SPEC, Path(__file__), ROOT / "sim/network.py", ROOT / "scripts/mn_readouts_from_replays.py",
             ROOT / spec["base_protocol"], ROOT / "data/cells.json", ROOT / "data/grid_levels.json",
             ROOT / spec["readout_source"], ROOT / protocol["connectivity_file"], ROOT / protocol["completeness_file"]]
    identity = {"source_sha256": {p.relative_to(ROOT).as_posix(): sha256(p) for p in files},
                "seed_scheme": "published_grid_v1_batch40", "brian2_version": brian2.__version__,
                "duration_ms": 1000, "channels": list(EXPECTED_DIMENSIONS)}
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=True).stdout.strip()
    out.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    print("C2: 13 cells x 30 trials; full network unchanged, saving only 12 MN readouts", flush=True)
    results = Parallel(n_jobs=min(13, args.n_proc), backend="loky")(
        delayed(_run_cell)(condition, spec, protocol, out, identity) for condition in conditions)
    summary = write_summary(results, spec, protocol, out)
    if any(sha256(p) != identity["source_sha256"][p.relative_to(ROOT).as_posix()] for p in files):
        raise ValueError("source changed during the run")
    meta = {**identity, "git_commit": commit, "completed_at": datetime.now(timezone.utc).isoformat(),
            "elapsed_s": time.perf_counter() - started, "n_cells": 13, "n_trials_completed": 390,
            "n_readout_neurons": 12, "n_proc": min(13, args.n_proc), "status": "complete"}
    (out / "run_meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print(f"C2 complete: {summary['mn9_bilateral_exact_spike_match_trials']}/390 bilateral MN9 exact spike matches; {meta['elapsed_s']:.1f} s", flush=True)


if __name__ == "__main__":
    main()
