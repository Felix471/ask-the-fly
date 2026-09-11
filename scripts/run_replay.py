#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Record one whole-network replay trial per lookup-grid cell (fixed path, fixed seed).

Stage 1 (``run``): for every grid cell run ONE extra 1 s trial with the SpikeMonitor
on the whole network and save every spike to results/replay/<cell_id>.npz
(gitignored) together with the seed and provenance.

Stage 2 (``pack``): build the neuron index (every neuron that spikes in any replay,
plus every GRN and MN9) and write the compact per-cell files the site fetches:
site/data/replay/<cell_id>.bin (see FORMAT below) and data/replay_neurons.json
(root ids + flags, in index order; x/y come from scripts/export_neurons.py).

FORMAT of <cell_id>.bin (little-endian):
  magic  b"AFR1"            4 bytes
  hlen   uint32             length of the UTF-8 JSON header that follows
  header JSON               provenance, counts, MN9 spike times (ms)
  idx    uint16|uint32[n_spikes]  neuron index (header idx_dtype: u16 when the index fits, else u32)
  t      uint16[n_spikes]   spike time in 0.1 ms units (0..10000), sorted ascending
"""

from __future__ import annotations

import argparse
import hashlib
import json
import socket
import struct
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

from sim.grid import EXPECTED_DIMENSIONS, expand_grid_conditions, load_grid_levels
from sim.runner import _base_seed, _run_shard

RAW_DIR = ROOT / "results" / "replay"
SITE_DIR = ROOT / "site" / "data" / "replay"
INDEX_PATH = ROOT / "data" / "replay_neurons.json"
REPLAY_SEED_OFFSET = 700_000  # keeps replay seeds disjoint from grid seeds (base + trial + 1000 * index)
MAGIC = b"AFR1"
FLAG_BITS = {"sugar": 1, "bitter": 2, "water": 4, "ir94e": 8, "mn9_left": 16, "mn9_right": 32, "named": 64}


def git_commit() -> str:
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=False)
    return result.stdout.strip() if result.returncode == 0 else "unknown"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def replay_seed(protocol: dict, condition_index: int) -> int:
    return _base_seed(protocol) + REPLAY_SEED_OFFSET + condition_index


def _run_shard_silenced(worker_id, jobs, protocol, cells, duration_ms, channels, silence_ids):
    """sim.runner._run_shard with an optional list of silenced FlyWire IDs."""
    if not silence_ids:
        return _run_shard(worker_id, jobs, protocol, cells, duration_ms, channels)
    import time as _time

    from sim.network import build_network, channel_cell_sets

    mappings = channel_cell_sets(protocol)
    network = build_network(protocol, cells, {name: mappings[name] for name in channels}, silence_ids=silence_ids)
    output = []
    for condition_index, condition, trial, seed in jobs:
        start = _time.perf_counter()
        spikes = network.run_trial(condition["rates"], seed, duration_ms)
        output.append((condition_index, trial, spikes, _time.perf_counter() - start, None))
    return {"worker_id": worker_id, "output": output}


def run(args: argparse.Namespace) -> int:
    from joblib import Parallel, delayed

    from sim.network import load_cells, load_protocol

    protocol, cells = load_protocol(), load_cells()
    conditions = expand_grid_conditions(load_grid_levels())
    if args.limit:
        conditions = conditions[: args.limit]
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    silence_ids: list[int] = []
    suffix = ""
    if args.silence:
        named = json.loads((ROOT / "data" / "named_neurons.json").read_text(encoding="utf-8"))
        entry = next((n for n in named["neurons"] if n["key"] == args.silence), None)
        if entry is None or not entry["root_ids"]:
            raise SystemExit(f"--silence {args.silence}: no v783 ids in data/named_neurons.json")
        silence_ids = [int(r) for r in entry["root_ids"]]
        suffix = f"_silence_{args.silence}"
        print(f"silencing {entry['label']}: {silence_ids}", flush=True)
    jobs = []
    for index, condition in enumerate(conditions):
        target = RAW_DIR / f"{condition['cond_id']}{suffix}.npz"
        if target.exists() and not args.force:
            continue
        jobs.append((index, condition, 0, replay_seed(protocol, index)))
    print(f"replay: {len(conditions)} cells, {len(jobs)} to run, {args.n_proc} workers", flush=True)
    if not jobs:
        return 0
    workers = min(args.n_proc, len(jobs))
    shards = [jobs[offset::workers] for offset in range(workers)]
    started = time.perf_counter()
    meta = {
        "git_commit": git_commit(),
        "protocol_sha256": sha256(ROOT / "data" / "stim_protocol.json"),
        "cells_sha256": sha256(ROOT / "data" / "cells.json"),
        "grid_levels_sha256": sha256(ROOT / "data" / "grid_levels.json"),
        "hostname": socket.gethostname(),
        "start_time": datetime.now(timezone.utc).isoformat(),
        "seed_rule": f"base_seed + {REPLAY_SEED_OFFSET} + grid_condition_index",
        "duration_ms": 1000.0,
        "path": "fixed per-channel refractory rule (store/restore)",
        "silence": args.silence,
        "silence_ids": [str(i) for i in silence_ids],
    }
    results = Parallel(n_jobs=workers, backend="loky")(
        delayed(_run_shard_silenced)(worker_id, shard, protocol, cells, 1000.0, list(EXPECTED_DIMENSIONS), silence_ids)
        for worker_id, shard in enumerate(shards)
    )
    by_index = {condition_index: (condition, seed) for condition_index, condition, _, seed in jobs}
    n_spikes_total = 0
    for result in results:
        for condition_index, _trial, spikes, elapsed, _rss in result["output"]:
            condition, seed = by_index[condition_index]
            ids = np.concatenate([np.full(len(t), fid, dtype=np.int64) for fid, t in spikes.items()]) if spikes else np.zeros(0, np.int64)
            times = np.concatenate([np.asarray(t, dtype=np.float64) for t in spikes.values()]) if spikes else np.zeros(0)
            order = np.argsort(times, kind="stable")
            n_spikes_total += len(order)
            np.savez_compressed(
                RAW_DIR / f"{condition['cond_id']}{suffix}.npz",
                flywire_id=ids[order], t_ms=times[order] * 1000.0,
                seed=np.int64(seed), condition_index=np.int64(condition_index),
                rates=np.array([condition["rates"][d] for d in EXPECTED_DIMENSIONS], dtype=np.float64),
                elapsed_s=np.float64(elapsed),
            )
    meta["end_time"] = datetime.now(timezone.utc).isoformat()
    meta["n_cells_run"] = len(jobs)
    meta["n_spikes_total"] = int(n_spikes_total)
    meta["walltime_s"] = round(time.perf_counter() - started, 1)
    (RAW_DIR / f"run_meta{suffix}.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print(f"replay: {len(jobs)} trials, {n_spikes_total} spikes, {meta['walltime_s']} s", flush=True)
    return 0


def pack(args: argparse.Namespace) -> int:
    # JSON only: keep the pack step runnable without Brian2 (Windows venv).
    protocol = json.loads((ROOT / "data" / "stim_protocol.json").read_text(encoding="utf-8"))
    cells = json.loads((ROOT / "data" / "cells.json").read_text(encoding="utf-8"))
    conditions = expand_grid_conditions(load_grid_levels())
    meta = json.loads((RAW_DIR / "run_meta.json").read_text(encoding="utf-8"))
    readout = protocol["readout"]
    left, right = int(readout["left"]), int(readout["right"])

    # Flags per root id: GRN channels from the frozen cell sets, MN9 left/right.
    flags: dict[int, int] = {}
    channel_sets = {name: spec["cell_set"] for name, spec in protocol["stimulus"]["channels"].items()}
    for channel, cell_set in channel_sets.items():
        for fid in cells["sets"][cell_set]["ids"]:
            flags[int(fid)] = flags.get(int(fid), 0) | FLAG_BITS[channel]
    flags[left] = flags.get(left, 0) | FLAG_BITS["mn9_left"]
    flags[right] = flags.get(right, 0) | FLAG_BITS["mn9_right"]
    # Named SEZ neurons (data/named_neurons.json) are always indexed so the site can
    # draw and label them even in cells where they never fire.
    named_path = ROOT / "data" / "named_neurons.json"
    named = json.loads(named_path.read_text(encoding="utf-8"))["neurons"] if named_path.exists() else []
    for entry in named:
        for rid in entry["root_ids"]:
            flags[int(rid)] = flags.get(int(rid), 0) | FLAG_BITS["named"]

    # Variants: the baseline replay plus every recorded silencing run (<cell>_silence_<key>.npz).
    variants = [""] + sorted({p.name[len(conditions[0]["cond_id"]):].removesuffix(".npz")
                              for p in RAW_DIR.glob(f"{conditions[0]['cond_id']}_silence_*.npz")})
    loaded = {}
    spiking: set[int] = set()
    for condition in conditions:
        for variant in variants:
            path = RAW_DIR / f"{condition['cond_id']}{variant}.npz"
            if not path.exists():
                raise FileNotFoundError(f"missing replay {path}; run `run` first")
            data = np.load(path)
            loaded[(condition["cond_id"], variant)] = data
            spiking.update(int(v) for v in np.unique(data["flywire_id"]))
    index_ids = sorted(spiking | set(flags))
    variant_meta = {}
    for variant in variants:
        meta_path = RAW_DIR / f"run_meta{variant}.json"
        variant_meta[variant] = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else meta
    position = {fid: i for i, fid in enumerate(index_ids)}
    INDEX_PATH.write_text(json.dumps({
        "schema_version": "replay_neurons_v1",
        "git_commit": meta["git_commit"],
        "replay_run": {k: meta[k] for k in ("start_time", "end_time", "seed_rule", "path", "n_cells_run", "n_spikes_total")},
        "flag_bits": FLAG_BITS,
        "n_neurons": len(index_ids),
        "root_ids": [str(fid) for fid in index_ids],
        "flags": [flags.get(fid, 0) for fid in index_ids],
    }, separators=(",", ":")) + "\n", encoding="utf-8")

    SITE_DIR.mkdir(parents=True, exist_ok=True)
    idx_dtype = np.dtype("<u2") if len(index_ids) <= 65535 else np.dtype("<u4")
    sizes = []
    n_model_neurons = int(pd.read_csv(ROOT / protocol["completeness_file"], index_col=0).shape[0])
    for condition, variant in ((c, v) for c in conditions for v in variants):
        data = loaded[(condition["cond_id"], variant)]
        vmeta = variant_meta[variant]
        ids, t_ms = data["flywire_id"], data["t_ms"]
        idx = np.fromiter((position[int(v)] for v in ids), dtype=idx_dtype, count=len(ids))
        t_units = np.clip(np.round(t_ms * 10.0), 0, 10000).astype(np.uint16)
        left_t = np.round(t_ms[ids == left], 1).tolist()
        right_t = np.round(t_ms[ids == right], 1).tolist()
        header = {
            "schema_version": "replay_v2",
            "cell_id": condition["cond_id"],
            "variant": variant.lstrip("_") or "baseline",
            "silenced": vmeta.get("silence"),
            "silenced_root_ids": vmeta.get("silence_ids", []),
            "n_model_neurons": n_model_neurons,
            "mn9_left_first_ms": (round(float(t_ms[ids == left].min()), 1) if np.any(ids == left) else None),
            "mn9_right_first_ms": (round(float(t_ms[ids == right].min()), 1) if np.any(ids == right) else None),
            "levels": condition["levels"],
            "hz": condition["rates"],
            "seed": int(data["seed"]),
            "seed_rule": meta["seed_rule"],
            "git_commit": vmeta["git_commit"],
            "protocol_sha256": vmeta["protocol_sha256"],
            "duration_ms": 1000.0,
            "t_unit_ms": 0.1,
            "idx_dtype": "u16" if idx_dtype.itemsize == 2 else "u32",
            "n_spikes": int(len(idx)),
            "n_neurons_active": int(len(np.unique(ids))),
            "mn9_left_ms": left_t,
            "mn9_right_ms": right_t,
            "mn9_left_count": len(left_t),
            "mn9_right_count": len(right_t),
            "note": "recorded output of one extra 1 s trial of the fixed-path Brian2 model; not a live simulation",
        }
        blob = json.dumps(header, separators=(",", ":")).encode("utf-8")
        payload = MAGIC + struct.pack("<I", len(blob)) + blob + idx.tobytes() + t_units.tobytes()
        (SITE_DIR / f"{condition['cond_id']}{variant}.bin").write_bytes(payload)
        sizes.append(len(payload))
    manifest = {
        "schema_version": "replay_manifest_v1",
        "git_commit": meta["git_commit"],
        "n_cells": len(conditions),
        "variants": [v.lstrip("_") or "baseline" for v in variants],
        "named_neurons": [{"key": e["key"], "label": e["label"], "root_ids": e["root_ids"]} for e in named if e["root_ids"]],
        "cells": {c["cond_id"]: {"levels": c["levels"], "n_spikes": int(len(loaded[(c["cond_id"], "")]["t_ms"])),
                                 "mn9_left_count": int(np.sum(loaded[(c["cond_id"], "")]["flywire_id"] == left)),
                                 **{f"mn9_left_count{v}": int(np.sum(loaded[(c["cond_id"], v)]["flywire_id"] == left)) for v in variants if v}}
                  for c in conditions},
    }
    (SITE_DIR / "manifest.json").write_text(json.dumps(manifest, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"packed {len(conditions)} cells: {len(index_ids)} indexed neurons; file sizes "
          f"min {min(sizes)/1024:.1f} KB, median {sorted(sizes)[len(sizes)//2]/1024:.1f} KB, max {max(sizes)/1024:.1f} KB")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    run_parser = sub.add_parser("run")
    run_parser.add_argument("--n-proc", type=int, default=14)
    run_parser.add_argument("--limit", type=int)
    run_parser.add_argument("--force", action="store_true")
    run_parser.add_argument("--silence", help="key from data/named_neurons.json: record every cell with that neuron's synapses zeroed")
    run_parser.set_defaults(function=run)
    pack_parser = sub.add_parser("pack")
    pack_parser.set_defaults(function=pack)
    args = parser.parse_args()
    return args.function(args)


if __name__ == "__main__":
    raise SystemExit(main())
