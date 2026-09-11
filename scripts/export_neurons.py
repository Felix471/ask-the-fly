#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Write site/data/neurons.json: a 2D layout for every neuron in data/replay_neurons.json.

Real layout (``--annotations``): FlyWire soma/nucleus positions from the flywire
annotations table (Schlegel et al. 2024; columns root_783 or root_id, pos_x, pos_y,
pos_z in nm), projected to the anterior view (x = mediolateral, y = dorsoventral).
Every indexed neuron must be present; a background subsample of non-replay neurons
is added for the brain silhouette up to the size budget.

Placeholder layout (``--placeholder``): a deterministic pseudo-anatomical scatter
(hash-seeded, GRNs low-centre, MN9 low) so the front end can be built before the
annotations are available. The output is flagged ``"layout": "placeholder"`` and the
site labels it as such.

Output format (kept under ~300 KB):
  {"schema_version": "neurons_v1", "layout": "flywire_v783_soma" | "placeholder",
   "n": N, "n_indexed": K, "bounds": {...}, "flag_bits": {...},
   "xy_b64": base64(Uint16 x0,y0,x1,y1,... scaled to 0..65535),
   "flags_b64": base64(Uint8 per neuron)}
Neurons 0..K-1 are the replay index order (spikes refer to them); K..N-1 are background.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = ROOT / "data" / "replay_neurons.json"
OUT_PATH = ROOT / "site" / "data" / "neurons.json"


def load_index() -> dict:
    return json.loads(INDEX_PATH.read_text(encoding="utf-8"))


def placeholder_xy(root_ids: list[str], flags: np.ndarray) -> np.ndarray:
    rng = np.random.default_rng(783)
    n = len(root_ids)
    # Ellipse-shaped scatter; deterministic per root id so re-exports are stable.
    h = np.array([int(hashlib.blake2b(r.encode(), digest_size=8).hexdigest(), 16) for r in root_ids], dtype=np.float64)
    u = (h % 1_000_003) / 1_000_003.0
    v = ((h // 1_000_003) % 1_000_003) / 1_000_003.0
    theta = 2 * np.pi * u
    radius = np.sqrt(v)
    x = 0.5 + 0.48 * radius * np.cos(theta)
    y = 0.45 + 0.40 * radius * np.sin(theta)
    grn = (flags & 15) > 0
    mn9 = (flags & 48) > 0
    x[grn] = 0.5 + rng.normal(0, 0.06, grn.sum())
    y[grn] = 0.82 + rng.normal(0, 0.03, grn.sum())
    x[mn9] = 0.5 + np.where((flags[mn9] & 16) > 0, -0.12, 0.12)
    y[mn9] = 0.93
    return np.column_stack([np.clip(x, 0, 1), np.clip(y, 0, 1)])


def annotation_xy(root_ids: list[str], annotations: Path, background: int) -> tuple[np.ndarray, list[str]]:
    import pandas as pd

    table = pd.read_csv(annotations, sep="\t" if annotations.suffix.lower() in (".tsv", ".txt") else ",", low_memory=False)
    id_col = next((c for c in ("root_783", "root_id", "root_id_783") if c in table.columns), None)
    if id_col is None or not {"pos_x", "pos_y"} <= set(table.columns):
        raise ValueError(f"{annotations}: need a root id column (root_783/root_id) and pos_x/pos_y")
    table = table.dropna(subset=[id_col, "pos_x", "pos_y"])
    table[id_col] = table[id_col].astype(np.int64).astype(str)
    positions = table.set_index(id_col)[["pos_x", "pos_y"]]
    missing = [r for r in root_ids if r not in positions.index]
    if missing:
        raise ValueError(f"{len(missing)} indexed neurons lack positions, e.g. {missing[:5]}")
    xy = positions.loc[root_ids].to_numpy(dtype=np.float64)
    others = positions.drop(index=[r for r in root_ids if r in positions.index])
    if background and len(others):
        sample = others.sample(n=min(background, len(others)), random_state=783)
        xy = np.vstack([xy, sample.to_numpy(dtype=np.float64)])
        extra = list(sample.index)
    else:
        extra = []
    # Anterior view: x = mediolateral, y = dorsoventral (FlyWire y grows ventrally, so
    # dorsal ends up on top of the canvas). Keep the aspect ratio: one scale for both
    # axes, the shorter axis centred.
    lo, hi = xy.min(axis=0), xy.max(axis=0)
    span = float(max(hi - lo))
    offset = (1.0 - (hi - lo) / max(span, 1e-9)) / 2.0
    xy = (xy - lo) / max(span, 1e-9) + offset
    global FRAME
    FRAME = {"lo": [float(lo[0]), float(lo[1])], "span": span, "offset": [float(offset[0]), float(offset[1])],
             "voxel_nm": [4.0, 4.0], "units": "FlyWire voxel coordinates (pos_x, pos_y)"}
    return xy, extra


FRAME: dict | None = None


def named_entries(root_ids: list[str]) -> list[dict]:
    """Named SEZ neurons (data/named_neurons.json) with their index in this file."""
    path = ROOT / "data" / "named_neurons.json"
    if not path.exists():
        return []
    position = {rid: i for i, rid in enumerate(root_ids)}
    out = []
    for entry in json.loads(path.read_text(encoding="utf-8"))["neurons"]:
        cells = [{"index": position[c["root_id"]], "root_id": c["root_id"], "side": c["side"]}
                 for c in entry["cells"] if c["root_id"] in position]
        if cells:
            out.append({"key": entry["key"], "label": entry["label"], "code": entry["code"], "cells": cells})
    return out


def write(xy: np.ndarray, flags: np.ndarray, layout: str, n_indexed: int, meta: dict) -> None:
    q = np.clip(np.round(xy * 65535), 0, 65535).astype("<u2")
    payload = {
        "frame": FRAME,
        "named": named_entries(meta["root_ids"]),
        "schema_version": "neurons_v1",
        "layout": layout,
        "n": int(len(xy)),
        "n_indexed": int(n_indexed),
        "flag_bits": meta["flag_bits"],
        "git_commit": meta["git_commit"],
        "source": ("FlyWire annotations, Schlegel et al. 2024 (Nature), CC BY 4.0: nucleus positions pos_x/pos_y "
                   "in the FlyWire v783 space, anterior view, aspect preserved" if layout != "placeholder"
                   else "deterministic placeholder scatter; not anatomical"),
        "xy_b64": base64.b64encode(q.tobytes()).decode("ascii"),
        "flags_b64": base64.b64encode(flags.astype(np.uint8).tobytes()).decode("ascii"),
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"wrote {OUT_PATH}: {len(xy)} neurons ({n_indexed} indexed, layout={layout}), {OUT_PATH.stat().st_size / 1024:.0f} KB")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--annotations", type=Path, help="flywire annotations table (tsv/csv) with root ids and pos_x/pos_y")
    mode.add_argument("--placeholder", action="store_true")
    parser.add_argument("--background", type=int, default=20000, help="non-replay neurons to add for the silhouette")
    parser.add_argument("--budget-kb", type=int, default=300)
    args = parser.parse_args()
    index = load_index()
    root_ids = index["root_ids"]
    flags = np.asarray(index["flags"], dtype=np.uint8)
    if args.placeholder:
        write(placeholder_xy(root_ids, flags), flags, "placeholder", len(root_ids), index)
        return 0
    background = args.background
    while True:
        xy, extra = annotation_xy(root_ids, args.annotations, background)
        all_flags = np.concatenate([flags, np.zeros(len(extra), dtype=np.uint8)])
        write(xy, all_flags, "flywire_v783_soma", len(root_ids), index)
        if OUT_PATH.stat().st_size <= args.budget_kb * 1024 or background == 0:
            return 0
        background = max(0, background // 2)
        print(f"over budget; retrying with background={background}")


if __name__ == "__main__":
    raise SystemExit(main())
