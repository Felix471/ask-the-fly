#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C1 only: read the 400 existing whole-network replay trials; never simulate.

Writes per-neuron, per-type/side and per-type rates/latencies plus screen tables
under results/. Sparse absence means silence only after full-monitor coverage is
verified. The extra replay seeds are NOT the lookup grid's 30 trial seeds.

  .venv\\Scripts\\python scripts/mn_readouts_from_replays.py
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import struct
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sim.grid import EXPECTED_DIMENSIONS, expand_grid_conditions, load_grid_levels
from scripts.validate_release import cells_sha256


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def validate_spikes(ids, times, duration_ms):
    if not math.isfinite(duration_ms) or duration_ms <= 0:
        raise ValueError("duration_ms must be finite and positive")
    ids, times = np.asarray(ids), np.asarray(times)
    if ids.ndim != 1 or times.ndim != 1 or ids.shape != times.shape:
        raise ValueError("spike arrays must be matching one-dimensional arrays")
    if not np.issubdtype(ids.dtype, np.integer):
        raise ValueError("FlyWire IDs must be integers, never floating point")
    if np.any(ids < 0) or not np.all(np.isfinite(times)):
        raise ValueError("invalid spike IDs or nonfinite times")
    if np.any(times < 0) or np.any(times >= duration_ms):
        raise ValueError("spike time outside [0, duration_ms)")


def neuron_metrics(ids, times, readout_ids, duration_ms):
    """Individual Hz and first spike in ms, including zeros for monitored silence."""
    validate_spikes(ids, times, duration_ms)
    ids, times = np.asarray(ids), np.asarray(times)
    unique, inverse, counts = np.unique(ids, return_inverse=True, return_counts=True)
    first = np.full(len(unique), np.inf)
    np.minimum.at(first, inverse, times)
    positions = {int(root_id): i for i, root_id in enumerate(unique)}
    result = {}
    for root_id in readout_ids:
        is_integer = isinstance(root_id, (int, np.integer)) and not isinstance(root_id, (bool, np.bool_))
        is_digit_string = isinstance(root_id, str) and re.fullmatch(r"[0-9]+", root_id) is not None
        if not (is_integer or is_digit_string):
            raise ValueError("readout IDs must be exact integers or digit strings, never floats or booleans")
        pos = positions.get(int(root_id))
        count = int(counts[pos]) if pos is not None else 0
        result[str(root_id)] = {
            "spike_count": count,
            "rate_hz": count / (duration_ms / 1000.0),
            "first_spike_ms": float(first[pos]) if pos is not None else None,
        }
    return result


def aggregate_metrics(items):
    """Mean Hz per member (silent members included); earliest spike of any member."""
    if not items:
        raise ValueError("cannot aggregate an empty neuron group")
    count = sum(item["spike_count"] for item in items)
    total_rate = sum(item["rate_hz"] for item in items)
    first = [item["first_spike_ms"] for item in items if item["first_spike_ms"] is not None]
    return {"n_neurons": len(items), "spike_count": count,
            "total_rate_hz": total_rate, "rate_hz": total_rate / len(items),
            "first_spike_ms": min(first) if first else None}


def spearman(x, y):
    """Pearson correlation of average-tie ranks; undefined constant series -> None."""
    if len(x) != len(y) or not len(x):
        raise ValueError("Spearman needs matching nonempty vectors")
    x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    if x.ndim != 1 or y.ndim != 1 or not np.all(np.isfinite(x)) or not np.all(np.isfinite(y)):
        raise ValueError("Spearman needs finite one-dimensional vectors")

    def ranks(values):
        order = np.argsort(values, kind="stable")
        result = np.empty(len(values), dtype=float)
        start = 0
        while start < len(values):
            stop = start + 1
            while stop < len(values) and values[order[stop]] == values[order[start]]:
                stop += 1
            result[order[start:stop]] = (start + stop - 1) / 2.0
            start = stop
        return result - result.mean()

    a, b = ranks(x), ranks(y)
    denominator = float(np.sqrt(np.dot(a, a) * np.dot(b, b)))
    return float(np.dot(a, b) / denominator) if denominator else None


def validate_replay(data, condition, expected_seed, duration_ms):
    required = {"flywire_id", "t_ms", "seed", "condition_index", "rates"}
    if not required.issubset(data):
        raise ValueError(f"missing replay fields: {sorted(required - set(data))}")
    for field, expected in (("seed", expected_seed), ("condition_index", condition["global_index"])):
        value = np.asarray(data[field])
        if value.shape != () or not np.issubdtype(value.dtype, np.integer) or int(value) != expected:
            raise ValueError(f"replay {field} does not match expected {expected}")
    expected_rates = [condition["rates"][d] for d in EXPECTED_DIMENSIONS]
    if not np.array_equal(np.asarray(data["rates"]), expected_rates):
        raise ValueError("replay rates do not match grid condition")
    validate_spikes(data["flywire_id"], data["t_ms"], duration_ms)


def read_replay_header(path):
    with Path(path).open("rb") as handle:
        prefix = handle.read(8)
        if len(prefix) != 8 or prefix[:4] != b"AFR1":
            raise ValueError("invalid AFR1 replay prefix")
        length = struct.unpack("<I", prefix[4:])[0]
        if not 0 < length <= Path(path).stat().st_size - 8:
            raise ValueError("truncated or invalid AFR1 header length")
        try:
            header = json.loads(handle.read(length))
        except (ValueError, UnicodeDecodeError) as error:
            raise ValueError("invalid AFR1 JSON header") from error
        if not isinstance(header, dict):
            raise ValueError("AFR1 header must be a JSON object")
        return header


def verify_mn9(data, header, manifest_cell, condition, protocol, duration_ms):
    """Exact same-trial sanity, not equality to an unrelated 30-trial lookup mean."""
    expected = {"cell_id": condition["cond_id"], "variant": "baseline",
                "seed": int(data["seed"]), "duration_ms": duration_ms,
                "hz": condition["rates"]}
    for key, value in expected.items():
        if header.get(key) != value:
            raise ValueError(f"MN9 sanity: header {key} mismatch")
    result = {}
    for side in ("left", "right"):
        times = np.sort(data["t_ms"][data["flywire_id"] == int(protocol["readout"][side])])
        rounded = np.round(times, 1).tolist()
        first = round(float(times[0]), 1) if len(times) else None
        if header.get(f"mn9_{side}_count") != len(times):
            raise ValueError(f"MN9 sanity: {side} count mismatch")
        if header.get(f"mn9_{side}_ms") != rounded:
            raise ValueError(f"MN9 sanity: {side} spike times mismatch")
        if header.get(f"mn9_{side}_first_ms") != first:
            raise ValueError(f"MN9 sanity: {side} first-spike latency mismatch")
        result[f"{side}_count"] = len(times)
        result[f"{side}_first_ms"] = float(times[0]) if len(times) else None
    if manifest_cell.get("mn9_left_count") != result["left_count"]:
        raise ValueError("MN9 sanity: manifest left count mismatch")
    return result


def write_csv(path, rows):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def axis_rows(cells, levels, dimension, sugar="none"):
    by_rates = {tuple(cell["input_hz"][d] for d in EXPECTED_DIMENSIONS): cell for cell in cells}
    result = []
    for level, rate in levels["levels"][dimension].items():
        inputs = {d: 0 for d in EXPECTED_DIMENSIONS}
        inputs["sugar"] = levels["levels"]["sugar"][sugar]
        inputs[dimension] = rate
        result.append({"level": level, "input_hz": rate,
                       "cell": by_rates[tuple(inputs[d] for d in EXPECTED_DIMENSIONS)]})
    return result


def number(value):
    return "—" if value is None else f"{value:.3f}".rstrip("0").rstrip(".")


def screen_tables(summary):
    """Only computed tables; the interpretation stays in the authored research doc."""
    types = [row["Type"] for row in summary["correlations"]]
    lines = []
    titles = {"sugar": "Sugar only", "bitter": "Bitter at sugar high (120 Hz)",
              "water": "Water at sugar none", "ir94e": "Ir94e at sugar high (120 Hz)",
              "ir94e_sugar_none": "Ir94e alone (sugar, bitter and water none)"}
    for axis, points in summary["axes"].items():
        lines += [f"### {titles[axis]}", "",
                  "| MN type (mean Hz per neuron) | " + " | ".join(f"{p['level']} ({p['input_hz']} Hz)" for p in points) + " |",
                  "|---|" + "---:|" * len(points),
                  "| Frozen left MN9 (reference) | " + " | ".join(number(p["cell"]["mn9_left_rate_hz"]) for p in points) + " |"]
        for kind in types:
            lines.append(f"| {kind} | " + " | ".join(number(p["cell"]["types"][kind]["rate_hz"]) for p in points) + " |")
        lines += [""]
    lines += ["### Across all 400 unique cells", "",
              "| MN type | Neurons | Active cells | Spearman vs frozen left MN9 |",
              "|---|---:|---:|---:|"]
    for row in summary["correlations"]:
        lines.append(f"| {row['Type']} | {row['n_neurons']} | {row['active_cells']} | {number(row['spearman'])} |")
    lines += ["", "### Strongest on/silent disagreements", "",
              "Silence means exactly zero spikes in this trial; 'strongest' ranks the active readout's Hz, without a behavioral threshold. Up to three cells per direction/type are in `disagreements.json`; all discordant cells are in the CSV. Cell IDs below omit the common `G_` prefix.", "",
              "| MN type | Highest left MN9 while type silent (Hz; cell) | Highest type mean while left MN9 silent (Hz; cell) |",
              "|---|---|---|"]
    for kind in types:
        entries = []
        for direction, metric in (("mn9_on_type_silent", "mn9_left_rate_hz"), ("type_on_mn9_silent", "type_rate_hz")):
            found = summary["disagreements"][kind][direction]
            entries.append(f"{number(found[0][metric])}; `{found[0]['cell_id'][2:]}`" if found else "none")
        lines.append(f"| {kind} | {' | '.join(entries)} |")
    return "\n".join(lines) + "\n"


def run(ids_path, replay_dir, output_dir):
    # Analysis artifacts cannot overwrite frozen inputs or public/site files.
    if not output_dir.resolve().is_relative_to((ROOT / "results").resolve()):
        raise ValueError("analysis output directory must be inside results/")
    ids_document = load_json(ids_path)
    neurons = ids_document["neurons"]
    if ids_document.get("schema_version") != "mn_readout_ids_v1" or len(neurons) != 66:
        raise ValueError("expected the complete 66-neuron FlyWire MN source")
    root_ids = [row["Body_ID"] for row in neurons]
    if len(set(root_ids)) != 66 or any(not isinstance(i, str) or not i.isdigit() for i in root_ids):
        raise ValueError("MN IDs must be unique exact digit strings")
    protocol_path, cells_path, grid_path = [ROOT / "data" / name for name in ("stim_protocol.json", "cells.json", "grid_levels.json")]
    protocol, frozen_cells = load_json(protocol_path), load_json(cells_path)
    grid = load_grid_levels(grid_path)
    conditions = expand_grid_conditions(grid)
    meta = load_json(replay_dir / "run_meta.json")
    duration = float(meta["duration_ms"])
    if len(conditions) != 400 or meta["n_cells_run"] != 400 or duration != 1000:
        raise ValueError("C1 requires all 400 complete 1-second baseline replays")
    if meta.get("silence") or meta.get("silence_ids"):
        raise ValueError("not an unsilenced baseline replay run")
    source_paths = {"protocol_sha256": protocol_path, "cells_sha256": cells_path, "grid_levels_sha256": grid_path}
    for key, path in source_paths.items():
        if meta[key] != sha256(path):
            raise ValueError(f"replay provenance does not match frozen {path.name}")
    completeness = ROOT / protocol["completeness_file"]
    if sha256(completeness) != ids_document["source"]["completeness_sha256"]:
        raise ValueError("MN source and model completeness index differ")
    with completeness.open(encoding="utf-8") as handle:
        v783 = {int(row[0]) for row in csv.reader(handle) if row and row[0].isdigit()}
    missing = [row for row in neurons if int(row["Body_ID"]) not in v783 or not row["in_v783"]]
    if missing:
        raise ValueError(f"STOP: MNs absent from monitored v783 population: {missing}")
    for side in ("left", "right"):
        root_id = str(protocol["readout"][side])
        if int(root_id) != int(frozen_cells["sets"]["mn9"][side]):
            raise ValueError("frozen protocol/cell-set MN9 IDs differ")
        if not any(row["Body_ID"] == root_id and row["Type"] == "MN9" for row in neurons):
            raise ValueError(f"frozen {side} MN9 is not in source MN9 rows")
    base_match = re.search(r"base_seed\s*=\s*(\d+)", protocol["trial"]["seed_rule"])
    if not base_match or meta["seed_rule"] != "base_seed + 700000 + grid_condition_index":
        raise ValueError("unknown replay seed rule")
    base_seed = int(base_match.group(1))
    manifest_path = ROOT / "site/data/replay/manifest.json"
    manifest = load_json(manifest_path)
    lookup_path = ROOT / "data/lookup_table.json"
    lookup = load_json(lookup_path)
    if lookup["cells_sha256"] != cells_sha256(lookup["cells"]):
        raise ValueError("lookup cells hash mismatch")
    lookup_by_hz = {tuple(c["hz"][d] for d in EXPECTED_DIMENSIONS): c for c in lookup["cells"]}
    if len(lookup_by_hz) != 400 or int(lookup["readout"]["left"]) != int(protocol["readout"]["left"]):
        raise ValueError("lookup grid/readout mismatch")
    groups, sides = defaultdict(list), defaultdict(list)
    for row in neurons:
        groups[row["Type"]].append(row["Body_ID"])
        sides[(row["Type"], row["Root_Side"])].append(row["Body_ID"])
    cells, neuron_rows, side_rows, type_rows, provenance = [], [], [], [], []
    active_ids, spike_total = set(), 0
    for condition in conditions:
        path = replay_dir / f"{condition['cond_id']}.npz"
        with np.load(path, allow_pickle=False) as data:
            validate_replay(data, condition, base_seed + 700000 + condition["global_index"], duration)
            unique_ids = set(int(x) for x in np.unique(data["flywire_id"]))
            if unique_ids - v783:
                raise ValueError(f"{path.name}: spikes outside the model index")
            active_ids.update(unique_ids)
            spike_total += len(data["t_ms"])
            header_path = ROOT / "site/data/replay" / f"{condition['cond_id']}.bin"
            header = read_replay_header(header_path)
            if header["protocol_sha256"] != meta["protocol_sha256"] or header["git_commit"] != meta["git_commit"]:
                raise ValueError(f"{path.name}: raw and packed provenance differ")
            sanity = verify_mn9(data, header, manifest["cells"][condition["cond_id"]], condition, protocol, duration)
            metrics = neuron_metrics(data["flywire_id"], data["t_ms"], root_ids, duration)
            prefix = {"cell_id": condition["cond_id"], "global_index": condition["global_index"],
                      "seed": int(data["seed"]), **condition["levels"],
                      **{f"{d}_input_hz": condition["rates"][d] for d in EXPECTED_DIMENSIONS}}
            for row in neurons:
                neuron_rows.append({**prefix, **row, **metrics[row["Body_ID"]]})
            type_metrics = {}
            for kind, members in sorted(groups.items()):
                type_metrics[kind] = aggregate_metrics([metrics[r] for r in members])
                type_rows.append({**prefix, "Type": kind, **type_metrics[kind]})
            for (kind, side), members in sorted(sides.items()):
                side_rows.append({**prefix, "Type": kind, "Root_Side": side,
                                  **aggregate_metrics([metrics[r] for r in members])})
            lookup_cell = lookup_by_hz[tuple(condition["rates"][d] for d in EXPECTED_DIMENSIONS)]
            cell = {"cell_id": condition["cond_id"], "global_index": condition["global_index"],
                    "seed": int(data["seed"]), "levels": condition["levels"], "input_hz": condition["rates"],
                    "mn9_left_rate_hz": sanity["left_count"] / (duration / 1000),
                    "mn9_left_first_ms": sanity["left_first_ms"], "lookup_mn9_mean_hz": lookup_cell["mn9_mean"],
                    "lookup_mn9_std_hz": lookup_cell["mn9_std"], "types": type_metrics}
            cells.append(cell)
            provenance.append({"cell_id": condition["cond_id"], "sha256": sha256(path), "seed": int(data["seed"])})
    if spike_total != meta["n_spikes_total"]:
        raise ValueError("saved spike total does not match complete replay run metadata")
    reference = [cell["mn9_left_rate_hz"] for cell in cells]
    correlations, disagreements, discordant_rows = [], {}, []
    for kind, members in sorted(groups.items()):
        values = [cell["types"][kind]["rate_hz"] for cell in cells]
        correlations.append({"Type": kind, "n_neurons": len(members),
                             "active_cells": sum(value > 0 for value in values), "spearman": spearman(values, reference)})
        both_directions = {"mn9_on_type_silent": [], "type_on_mn9_silent": []}
        for cell, value in zip(cells, values):
            direction = ("mn9_on_type_silent" if cell["mn9_left_rate_hz"] > 0 and value == 0 else
                         "type_on_mn9_silent" if value > 0 and cell["mn9_left_rate_hz"] == 0 else None)
            if direction:
                row = {"Type": kind, "direction": direction, "cell_id": cell["cell_id"],
                       "mn9_left_rate_hz": cell["mn9_left_rate_hz"], "type_rate_hz": value}
                both_directions[direction].append(row)
                discordant_rows.append(row)
        disagreements[kind] = {
            direction: sorted(rows, key=lambda r: (-max(r["mn9_left_rate_hz"], r["type_rate_hz"]), r["cell_id"]))[:3]
            for direction, rows in both_directions.items()}
    axes = {dimension: axis_rows(cells, grid, dimension, "high" if dimension in ("bitter", "ir94e") else "none")
            for dimension in EXPECTED_DIMENSIONS}
    axes["ir94e_sugar_none"] = axis_rows(cells, grid, "ir94e", "none")
    summary = {
        "schema_version": "feeding_mn_screen_v1", "n_cells": len(cells), "n_trials_per_cell": 1,
        "duration_ms": duration,
        "definitions": {"rate_hz": "mean per neuron, including silent members; total also saved",
                        "first_spike_ms": "earliest spike in group, null if all members silent; not average latency",
                        "sides": "XLSX Root_Side; frozen left MN9 is source R, not source L",
                        "spearman": "average-tie ranks, 400 unique cells, undefined for constant series",
                        "disagreement": "exact silence vs positive firing; strongest ranked by active rate, no behavioral cutoff"},
        "sources": {"ids": str(ids_path.relative_to(ROOT)), "ids_sha256": sha256(ids_path),
                    "replay_directory": str(replay_dir.relative_to(ROOT)), "replay_metadata": meta,
                    "replay_metadata_sha256": sha256(replay_dir / "run_meta.json"),
                    "lookup_cells_sha256": lookup["cells_sha256"], "manifest_sha256": sha256(manifest_path),
                    "replay_files": provenance},
        "coverage": {"monitor": "SpikeMonitor(neurons), all neurons in the v783 completeness index",
                     "model_neurons": len(v783), "mn_neurons": len(neurons), "mn_types": len(groups),
                     "type_side_groups": len(sides), "missing_from_model": [], "total_spikes": spike_total,
                     "mn_ids_active_in_any_cell": sorted(set(root_ids) & {str(i) for i in active_ids}),
                     "mn_ids_silent_in_all_cells": sorted(set(root_ids) - {str(i) for i in active_ids})},
        "sanity": {"raw_vs_packed_mn9_both_sides_passed_cells": len(cells),
                   "raw_vs_manifest_left_mn9_passed_cells": len(cells),
                   "lookup_trial_comparison": "not applicable: replay seed is separate from all 30 grid trial seeds; lookup stores means/std, not individual trials"},
        "correlations": correlations, "disagreements": disagreements, "axes": axes, "cells": cells,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "neuron_readouts.csv", neuron_rows)
    write_csv(output_dir / "type_side_readouts.csv", side_rows)
    write_csv(output_dir / "type_readouts.csv", type_rows)
    write_csv(output_dir / "correlations.csv", correlations)
    write_csv(output_dir / "discordant_cells.csv", discordant_rows)
    (output_dir / "disagreements.json").write_text(json.dumps(disagreements, indent=2) + "\n", encoding="utf-8")
    (output_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    (output_dir / "screen_tables.md").write_text(screen_tables(summary), encoding="utf-8")
    print(f"screen valid: {len(cells)} cells; {len(neurons)} MNs; {len(groups)} types; {len(sides)} type/side groups")
    print(f"same-replay MN9 sanity passed for all {len(cells)} cells; no simulations")
    print(f"wrote {output_dir}")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ids", type=Path, default=ROOT / "data/mn_readout_ids.json")
    parser.add_argument("--replays", type=Path, default=ROOT / "results/replay")
    parser.add_argument("--out", type=Path, default=ROOT / "results/mn-readouts/c1")
    args = parser.parse_args()
    run(args.ids.resolve(), args.replays.resolve(), args.out.resolve())


if __name__ == "__main__":
    main()
