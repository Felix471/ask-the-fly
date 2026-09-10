# SPDX-License-Identifier: MIT
# Derived from Shiu et al. (2024) model.py, used under the MIT License.
"""Condition expansion, worker sharding, and Phase-0 result writing."""

from __future__ import annotations

import itertools
import gc
import os
import re
import time
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

from sim.network import ROOT, build_network, channel_cell_sets, load_cells, load_protocol
from sim.readout import mn9_rate


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


def _run_shard(worker_id: int, jobs: list[tuple], protocol: dict, cells: dict, duration_ms: float) -> dict:
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
            # Phase 0 uses only the channels named by its frozen conditions.
            phase0_channels = {
                name for spec in protocol["phase0_conditions"].values()
                for name in (field[:-3] for field in spec if field.endswith("_hz"))
            }
            network = build_network(
                protocol, cells, {name: mappings[name] for name in mappings if name in phase0_channels}
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
) -> pd.DataFrame:
    """Run round-robin worker shards and write one parquet per condition."""
    protocol = load_protocol() if protocol is None else protocol
    cells = load_cells() if cells is None else cells
    duration_ms = float(protocol["trial"]["duration_ms"] if duration_ms is None else duration_ms)
    output_dir = ROOT / "results" / "phase0" / stage
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
    for index, condition in pending:
        for trial in range(n_trials):
            jobs.append((index, condition, trial, base_seed + trial + 1000 * index))
    shards = [jobs[offset::workers] for offset in range(workers)] if jobs else []

    started = time.perf_counter()
    worker_results = Parallel(n_jobs=workers, backend="loky")(
        delayed(_run_shard)(worker, shard, protocol, cells, duration_ms)
        for worker, shard in enumerate(shards)
    ) if shards else []
    elapsed_total = time.perf_counter() - started
    flat = [item for result in worker_results for item in result["output"]]
    rss_values = [item[4] for item in flat if item[4] is not None]
    if rss_values:
        print(f"worker 0 RSS after first job: {rss_values[0]:.1f} MiB")

    summaries = []
    for index, condition in pending:
        items = [(trial, spikes) for ci, trial, spikes, _, _ in flat if ci == index]
        frame = spikes_dataframe(items)
        frame.to_parquet(output_dir / f"{condition['cond_id']}.parquet", index=False)
        # Use the actual duration for stage-specific readout calculations.
        stage_protocol = {**protocol, "trial": {**protocol["trial"], "duration_ms": duration_ms}}
        rates = mn9_rate(frame, stage_protocol, n_trials)
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
                "walltime_s": sum(item[3] for item in flat if item[0] == index),
            }
        )
    for _, condition, path in skipped:
        frame = pd.read_parquet(path)
        stage_protocol = {**protocol, "trial": {**protocol["trial"], "duration_ms": duration_ms}}
        rates = mn9_rate(frame, stage_protocol, n_trials)
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
                "walltime_s": 0.0,
            }
        )
        print(f"skipping existing {path}")
    summary = pd.DataFrame(summaries)
    summary.to_csv(output_dir / "summary.csv", index=False)
    print(f"parallel stage walltime: {elapsed_total:.3f} s")
    return summary
