# SPDX-License-Identifier: MIT
# Derived from Shiu et al. (2024) model.py, used under the MIT License.
"""Condition expansion, worker sharding, and result writing."""

from __future__ import annotations

import itertools
import gc
import os
import hashlib
import json
import re
from datetime import datetime, timezone
import time
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

from sim.readout import mn9_rate

ROOT = Path(__file__).resolve().parents[1]


def _load_json(relative_path: str) -> dict:
    import json

    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


def expand_conditions(protocol: dict, condition_keys: Iterable[str]) -> list[dict]:
    """Expand scalar/list protocol rates into concrete Phase-0 conditions."""
    expanded: list[dict] = []
    for key in condition_keys:
        spec = protocol["phase0_conditions"][key]
        rate_fields = [(name[:-3], value) for name, value in spec.items() if name.endswith("_hz")]
        channels = [name for name, _ in rate_fields]
        choices = [value if isinstance(value, list) else [value] for _, value in rate_fields]
        override = {"sugar": spec["cell_set"]} if "cell_set" in spec else {}
        for values in itertools.product(*choices):
            rates = dict(zip(channels, (float(value) for value in values)))
            if key == "D_baseline":
                cond_id = key
            else:
                suffix = "_".join(f"{channel}{value:g}Hz" for channel, value in rates.items())
                cond_id = f"{key}_{suffix}"
            expanded.append(
                {"cond_id": cond_id, "cell_set_override": override.copy(), "rates": rates}
            )
    return expanded


class ResumeError(RuntimeError):
    """An existing result cannot be reused as-is (never silently zero-filled or relabelled)."""


# Seed schemes. v1 (legacy): seed = base + trial + 1000 * index within the list
# handed to run_conditions, so batching changed the seeds. v2: the same formula
# on the condition's stable `global_index` (D02). Every published table so far
# was produced under v1; see docs/grid_provenance.md.
def seed_scheme_for(conditions: list[dict]) -> str:
    return "v2" if conditions and all("global_index" in c for c in conditions) else "v1"


def seed_for(base_seed: int, condition: dict, trial: int, local_index: int) -> int:
    index = condition["global_index"] if "global_index" in condition else local_index
    return int(base_seed) + int(trial) + 1000 * int(index)


def _json_sha256(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def ledger_expectation(condition: dict, n_trials: int, duration_ms: float, protocol: dict, cells: dict, channels) -> dict:
    """The immutable identity a stored result must match before it is reused (D01)."""
    return {
        "cond_id": condition["cond_id"],
        "n_trials": int(n_trials),
        "duration_ms": float(duration_ms),
        "rates": {k: float(v) for k, v in condition.get("rates", {}).items()},
        "channels": list(channels) if channels else None,
        "protocol_sha256": _json_sha256(protocol),
        "cells_sha256": _json_sha256(cells),
        "readout": protocol.get("readout"),
        "seed_scheme": seed_scheme_for([condition]),
    }


def ledger_path(output_dir: Path, cond_id: str) -> Path:
    return output_dir / f"{cond_id}.meta.json"


def write_ledger(output_dir: Path, expectation: dict, completed_trials: list[int], seeds: list[int]) -> dict:
    ledger = {**expectation, "completed_trials": sorted(int(t) for t in completed_trials), "seeds": [int(x) for x in seeds],
              "written_at": datetime.now(timezone.utc).isoformat()}
    path = ledger_path(output_dir, expectation["cond_id"])
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(ledger, indent=2), encoding="utf-8")
    os.replace(tmp, path)
    return ledger


def reuse_condition(condition: dict, parquet_path: Path, expectation: dict) -> tuple[dict, int]:
    """Validate a stored result against the ledger and the requested run, then read it out.
    Raises ResumeError on any mismatch; never interprets missing trials as zero spikes."""
    ledger_file = ledger_path(parquet_path.parent, condition["cond_id"])
    if not ledger_file.exists():
        raise ResumeError(f"{parquet_path}: no completion ledger ({ledger_file.name}); rerun this condition with --force")
    try:
        ledger = json.loads(ledger_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ResumeError(f"{ledger_file}: unreadable ledger: {exc}") from exc
    mismatches = [key for key in expectation if ledger.get(key) != expectation[key]]
    if mismatches:
        details = "; ".join(f"{k}: stored {ledger.get(k)!r} vs requested {expectation[k]!r}" for k in mismatches)
        raise ResumeError(f"{parquet_path}: stored run does not match the requested run ({details})")
    completed = sorted(int(t) for t in ledger.get("completed_trials", []))
    if completed != list(range(expectation["n_trials"])):
        raise ResumeError(f"{parquet_path}: completed trials {completed} do not cover n_trials={expectation['n_trials']}")
    try:
        frame = pd.read_parquet(parquet_path)
    except Exception as exc:  # noqa: BLE001 - any reader failure means the result is unusable
        raise ResumeError(f"{parquet_path}: unreadable result: {exc}") from exc
    protocol_like = {"trial": {"duration_ms": expectation["duration_ms"]}, "readout": expectation["readout"]}
    try:
        rates = mn9_rate(frame, protocol_like, expectation["n_trials"], completed_trials=completed)
    except ValueError as exc:
        raise ResumeError(f"{parquet_path}: {exc}") from exc
    return rates, expectation["n_trials"]


def _base_seed(protocol: dict) -> int:
    match = re.search(r"base_seed\s*=\s*(\d+)", protocol["trial"]["seed_rule"])
    if not match:
        raise ValueError(f"Cannot parse seed rule: {protocol['trial']['seed_rule']}")
    return int(match.group(1))


def spikes_dataframe(spikes_by_trial: list[tuple[int, dict[int, np.ndarray]]]) -> pd.DataFrame:
    frames = []
    for trial, spikes in spikes_by_trial:
        for flywire_id, times in spikes.items():
            if len(times):
                frames.append(
                    pd.DataFrame(
                        {
                            "t": np.asarray(times, dtype=float),
                            "trial": np.full(len(times), trial, dtype=np.int64),
                            "flywire_id": np.full(len(times), flywire_id, dtype=np.int64),
                        }
                    )
                )
    if frames:
        return pd.concat(frames, ignore_index=True)
    return pd.DataFrame(
        {"t": pd.Series(dtype="float64"), "trial": pd.Series(dtype="int64"), "flywire_id": pd.Series(dtype="int64")}
    )


def _rss_mb() -> float:
    try:
        import resource

        return float(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) / 1024.0
    except ImportError:
        return float("nan")


def _run_shard(
    worker_id: int,
    jobs: list[tuple],
    protocol: dict,
    cells: dict,
    duration_ms: float,
    channels: list[str] | None,
) -> dict:
    from sim.network import build_network, channel_cell_sets

    network = None
    current_signature = None
    output = []
    first = True
    for condition_index, condition, trial, seed in jobs:
        override = condition["cell_set_override"]
        signature = tuple(sorted(override.items()))
        if signature != current_signature:
            # A' is ordered after the primary conditions. Release the primary
            # network before building its sugar_bench21 replacement so a worker
            # never holds two full connectomes at once.
            network = None
            gc.collect()
            mappings = channel_cell_sets(protocol, override)
            selected_channels = channels
            if selected_channels is None:
                # Preserve Phase 0's channel inference when none are supplied.
                selected_channels = sorted({
                    name for spec in protocol["phase0_conditions"].values()
                    for name in (field[:-3] for field in spec if field.endswith("_hz"))
                })
            network = build_network(
                protocol, cells, {name: mappings[name] for name in selected_channels}
            )
            current_signature = signature
        start = time.perf_counter()
        spikes = network.run_trial(condition["rates"], seed, duration_ms)
        elapsed = time.perf_counter() - start
        rss = _rss_mb() if first and worker_id == 0 else None
        first = False
        output.append((condition_index, trial, spikes, elapsed, rss))
    return {"worker_id": worker_id, "output": output}


def run_conditions(
    conditions: list[dict],
    n_trials: int,
    n_proc: int | None = None,
    *,
    protocol: dict | None = None,
    cells: dict | None = None,
    stage: str = "full",
    duration_ms: float | None = None,
    force: bool = True,
    channels: list[str] | None = None,
    results_subdir: str = "phase0",
) -> pd.DataFrame:
    """Run round-robin worker shards and write one parquet per condition."""
    from joblib import Parallel, delayed

    protocol = _load_json("data/stim_protocol.json") if protocol is None else protocol
    cells = _load_json("data/cells.json") if cells is None else cells
    duration_ms = float(protocol["trial"]["duration_ms"] if duration_ms is None else duration_ms)
    output_dir = ROOT / "results" / results_subdir / stage
    output_dir.mkdir(parents=True, exist_ok=True)
    pending = []
    skipped = []
    for index, condition in enumerate(conditions):
        path = output_dir / f"{condition['cond_id']}.parquet"
        if path.exists() and not force:
            skipped.append((index, condition, path))
        else:
            pending.append((index, condition))

    cpu_count = os.cpu_count() or 1
    requested = min(24, cpu_count) if n_proc is None else int(n_proc)
    workers = max(1, min(requested, max(1, len(pending) * n_trials)))
    jobs = []
    base_seed = _base_seed(protocol)
    scheme = seed_scheme_for(conditions)
    for index, condition in pending:
        for trial in range(n_trials):
            jobs.append((index, condition, trial, seed_for(base_seed, condition, trial, index)))
    shards = [jobs[offset::workers] for offset in range(workers)] if jobs else []

    started = time.perf_counter()
    worker_results = Parallel(n_jobs=workers, backend="loky")(
        delayed(_run_shard)(worker, shard, protocol, cells, duration_ms, channels)
        for worker, shard in enumerate(shards)
    ) if shards else []
    elapsed_total = time.perf_counter() - started
    rss_values = [
        item[4]
        for result in worker_results
        for item in result["output"]
        if item[4] is not None
    ]
    if rss_values:
        print(f"worker 0 RSS after first job: {rss_values[0]:.1f} MiB")

    summaries = []
    for index, condition in pending:
        items = []
        condition_walltime = 0.0
        # Consume matching tuples in place so completed conditions release their
        # spike arrays without constructing a second flattened result list.
        for result in worker_results:
            output = result["output"]
            for position in range(len(output) - 1, -1, -1):
                ci, trial, spikes, trial_walltime, _ = output[position]
                if ci == index:
                    items.append((trial, spikes))
                    condition_walltime += trial_walltime
                    del output[position]
        items.sort(key=lambda item: item[0])
        completed = [trial for trial, _ in items]
        if completed != list(range(n_trials)):
            raise RuntimeError(f"{condition['cond_id']}: workers returned trials {completed}, expected 0..{n_trials - 1}")
        frame = spikes_dataframe(items)
        frame.to_parquet(output_dir / f"{condition['cond_id']}.parquet", index=False)
        # Use the actual duration for stage-specific readout calculations.
        stage_protocol = {**protocol, "trial": {**protocol["trial"], "duration_ms": duration_ms}}
        expectation = ledger_expectation(condition, n_trials, duration_ms, protocol, cells, channels)
        write_ledger(output_dir, expectation, completed, [seed_for(base_seed, condition, t, index) for t in completed])
        rates = mn9_rate(frame, stage_protocol, n_trials, completed_trials=completed)
        summaries.append(
            {
                "cond_id": condition["cond_id"],
                "mn9_left_mean_hz": rates["left"]["mean"],
                "mn9_left_std_hz": rates["left"]["std"],
                "mn9_right_mean_hz": rates["right"]["mean"],
                "mn9_right_std_hz": rates["right"]["std"],
                "mn9_aggregated_mean_hz": rates["aggregated"]["mean"],
                "mn9_aggregated_std_hz": rates["aggregated"]["std"],
                "n_trials": n_trials,
                "seed_scheme": scheme,
                "walltime_s": condition_walltime,
            }
        )
        del items, frame
    for _, condition, path in skipped:
        # Reuse only what the ledger proves complete and identical (D01).
        expectation = ledger_expectation(condition, n_trials, duration_ms, protocol, cells, channels)
        rates, ledger_trials = reuse_condition(condition, path, expectation)
        summaries.append(
            {
                "cond_id": condition["cond_id"],
                "mn9_left_mean_hz": rates["left"]["mean"],
                "mn9_left_std_hz": rates["left"]["std"],
                "mn9_right_mean_hz": rates["right"]["mean"],
                "mn9_right_std_hz": rates["right"]["std"],
                "mn9_aggregated_mean_hz": rates["aggregated"]["mean"],
                "mn9_aggregated_std_hz": rates["aggregated"]["std"],
                "n_trials": ledger_trials,
                "seed_scheme": expectation["seed_scheme"],
                "walltime_s": 0.0,
            }
        )
        print(f"reusing verified {path}")
    summary = pd.DataFrame(summaries)
    summary.to_csv(output_dir / "summary.csv", index=False)
    print(f"parallel stage walltime: {elapsed_total:.3f} s")
    return summary
