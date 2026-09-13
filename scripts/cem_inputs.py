#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C2b: unsigned structural inputs to six CEM neurons; no simulation.

Uses the connectivity parquet named by the frozen protocol, the four frozen
labellar ID sets, and PhG1-16 FlyWire rows from Tastekin Table S1. The two-hop
readout counts real synapses on each leg separately, not products of weights or
copies of one edge for every convergent path. Output is restricted to results/.

    .venv\\Scripts\\python scripts/cem_inputs.py
"""

from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import json
from numbers import Integral
from pathlib import Path
import re
import sys

import pandas as pd
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_mn_readout_ids import read_v783_ids, select_mn_rows
from scripts.cross_check_cells import FLYWIRE, read_xlsx

PRE = "Presynaptic_ID"
POST = "Postsynaptic_ID"
SYN = "Connectivity"
SIGN = "Excitatory"
WEIGHT = "Excitatory x Connectivity"
COLUMNS = [PRE, POST, SYN, SIGN, WEIGHT]
LABELLAR = ("sugar", "bitter", "water", "ir94e")


def exact_id(value) -> int:
    """Accept only exact positive integer IDs; floats have already lost bits."""
    if isinstance(value, bool):
        raise ValueError("boolean is not a root ID")
    if isinstance(value, str):
        if not re.fullmatch(r"[1-9][0-9]*", value):
            raise ValueError(f"root ID must be a canonical integer string: {value!r}")
        value = int(value)
    if not isinstance(value, Integral) or not 0 < value <= 2**63 - 1:
        raise ValueError("root ID must be an exact positive int64")
    return int(value)


def validate_edges(edges: pd.DataFrame) -> None:
    if not set(COLUMNS).issubset(edges.columns):
        raise ValueError("missing connectivity columns")
    for field in COLUMNS:
        if not pd.api.types.is_integer_dtype(edges[field].dtype) or edges[field].isna().any():
            raise ValueError(f"{field} must contain exact non-null integers")
    for field in (PRE, POST):
        if (edges[field] <= 0).any() or (edges[field] > 2**63 - 1).any():
            raise ValueError(f"{field} contains invalid root IDs")
    if (edges[SYN] <= 0).any():
        raise ValueError("Connectivity must count positive synapses")
    if not edges[SIGN].isin((-1, 1)).all():
        raise ValueError("unexpected connectivity sign")
    if not (edges[WEIGHT] == edges[SIGN] * edges[SYN]).all():
        raise ValueError("signed weight is inconsistent with Connectivity and Excitatory")
    if edges.duplicated([PRE, POST]).any():
        raise ValueError("duplicate directed pair; synapse aggregation would be ambiguous")
    if (edges.groupby(PRE)[SIGN].nunique() > 1).any():
        raise ValueError("one presynaptic neuron has inconsistent edge signs")


def select_pharyngeal_rows(rows: list[dict]) -> list[dict]:
    selected = []
    seen = set()
    for row in rows:
        if row.get("Connectome") != FLYWIRE:
            continue
        kind = row.get("Type", "")
        pharyngeal = str(row.get("Subclass", "")).startswith("Pharyngeal")
        if not kind.startswith("PhG") and not pharyngeal:
            continue
        if not re.fullmatch(r"PhG(?:[1-9]|1[0-6])", kind) or not pharyngeal:
            raise ValueError("unexpected PhG type or non-pharyngeal PhG row")
        root_id = exact_id(row.get("Body_ID"))
        if row.get("Root_Side") not in {"L", "R"}:
            raise ValueError("unexpected PhG Root_Side")
        if root_id in seen:
            raise ValueError("duplicate PhG Body_ID")
        seen.add(root_id)
        selected.append(dict(row))
    return selected


def input_metrics(edges: pd.DataFrame, source_ids, target_ids) -> dict:
    """Counts for exact S->M->T paths; an intermediate may be any model neuron.

    Direct, first-leg and last-leg sets are separate, not necessarily disjoint.
    Within each set an edge is counted once, including for a union of targets.
    Last-leg counts therefore are actual input synapses onto T, not S->M weight
    times M->T weight. This is reachability, not propagation or net excitation.
    """
    sources = {exact_id(i) for i in source_ids}
    targets = {exact_id(i) for i in target_ids}
    onto = edges[edges[POST].isin(targets)]
    direct = onto[onto[PRE].isin(sources)]
    source_out = edges[edges[PRE].isin(sources)]
    intermediates = set(onto[PRE]).intersection(source_out[POST])
    first = source_out[source_out[POST].isin(intermediates)]
    last = onto[onto[PRE].isin(intermediates)]
    result = {
        "total_presynaptic_partners": int(onto[PRE].nunique()),
        "total_input_synapses": int(onto[SYN].sum()),
        "direct_source_partners": int(direct[PRE].nunique()),
        "two_hop_intermediates": len(intermediates),
        "two_hop_source_partners": int(first[PRE].nunique()),
    }
    for label, frame in (("total", onto), ("direct", direct),
                         ("two_hop_first_leg", first), ("two_hop_last_leg", last)):
        if label != "total":
            result[f"{label}_synapses"] = int(frame[SYN].sum())
        for sign, name in ((1, "positive"), (-1, "negative")):
            result[f"{label}_{name}_synapses"] = int(frame.loc[frame[SIGN] == sign, SYN].sum())
    return result


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def json_file(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def source_info(path: Path) -> dict:
    return {"file": path.resolve().relative_to(ROOT).as_posix(), "sha256": sha256(path)}


def markdown_table(report: dict) -> str:
    targets = report["targets"]
    groups = report["source_groups"]
    by_pair = {(r["source_group"], r["target"]): r for r in report["readouts"]}
    target_names = [r["Body_ID"] for r in targets] + ["all_six"]
    headers = [f"{r['Body_ID']} ({r['Root_Side']})" for r in targets] + ["All six (union)"]
    lines = [
        "D / A / B = direct source->CEM synapses / unique source->intermediate synapses "
        "on two-edge paths / unique intermediate->CEM synapses on those paths. "
        "The totals row instead gives unique presynaptic partners / total input synapses.",
        "",
        "| Source (n) | " + " | ".join(headers) + " |",
        "|---|" + "---:|" * len(headers),
    ]
    totals = [by_pair[(groups[0]["name"], name)] for name in target_names]
    lines.append("| All presynaptic input: partners / synapses | " + " | ".join(
        f"{r['total_presynaptic_partners']} / {r['total_input_synapses']}" for r in totals) + " |")
    for group in groups:
        counts = [by_pair[(group["name"], name)] for name in target_names]
        lines.append(f"| {group['name']} ({len(group['ids'])}) | " + " | ".join(
            f"{r['direct_synapses']} / {r['two_hop_first_leg_synapses']} / {r['two_hop_last_leg_synapses']}"
            for r in counts) + " |")
    return "\n".join(lines) + "\n"


def run(out: Path) -> dict:
    out = out.resolve()
    if not out.is_relative_to((ROOT / "results").resolve()):
        raise ValueError("connectome audit output must stay under results/")
    protocol_path = ROOT / "data/stim_protocol.json"
    cells_path = ROOT / "data/cells.json"
    ids_path = ROOT / "data/mn_readout_ids.json"
    protocol, cells, inventory = map(json_file, (protocol_path, cells_path, ids_path))
    connectivity_path = ROOT / protocol["connectivity_file"]
    completeness_path = ROOT / protocol["completeness_file"]
    xlsx_path = ROOT / inventory["source"]["file"]
    if sha256(xlsx_path) != inventory["source"]["sha256"]:
        raise ValueError("workbook no longer matches the MN inventory source")
    if sha256(completeness_path) != inventory["source"]["completeness_sha256"]:
        raise ValueError("v783 index no longer matches the MN inventory source")
    v783_text = read_v783_ids(completeness_path)
    v783 = {exact_id(i) for i in v783_text}
    sheets = read_xlsx(xlsx_path)
    source_mns = select_mn_rows(sheets["MNs"], v783_text)
    targets = [r for r in inventory["neurons"] if r["Type"] == "CEM"]
    source_targets = [r for r in source_mns if r["Type"] == "CEM"]
    if targets != source_targets or len(targets) != 6:
        raise ValueError("CEM inventory does not match all six source rows exactly")
    targets.sort(key=lambda r: (r["Root_Side"], exact_id(r["Body_ID"])))
    phg_rows = select_pharyngeal_rows(sheets["GRNs"])
    if len(phg_rows) != 50 or {r["Type"] for r in phg_rows} != {f"PhG{i}" for i in range(1, 17)}:
        raise ValueError("expected exactly 50 PhG1-16 FlyWire rows")
    labellar = {}
    for name in LABELLAR:
        ids = [exact_id(i) for i in cells["sets"][name]["ids"]]
        if len(ids) != len(set(ids)) or len(ids) != protocol["stimulus"]["channels"][name]["count"]:
            raise ValueError(f"invalid frozen {name} ID count")
        labellar[name] = set(ids)
    phg = {r["Type"]: set() for r in phg_rows}
    for row in phg_rows:
        phg[row["Type"]].add(exact_id(row["Body_ID"]))
    groups = [(name, labellar[name]) for name in LABELLAR]
    groups.append(("Labellar union", set().union(*labellar.values())))
    groups += [(f"PhG{i}", phg[f"PhG{i}"]) for i in range(1, 17)]
    groups.append(("Pharyngeal union", set().union(*phg.values())))
    source_union = set().union(*(group_ids for _, group_ids in groups))
    target_ids = {exact_id(r["Body_ID"]) for r in targets}
    if not (source_union | target_ids).issubset(v783):
        raise ValueError("source or CEM IDs missing from the modeled v783 population")
    if not groups[4][1].isdisjoint(groups[-1][1]):
        raise ValueError("pharyngeal and frozen labellar inventories unexpectedly overlap")

    # Read only necessary edges, avoiding a full 15-million-row graph in memory.
    inbound = pd.read_parquet(connectivity_path, columns=COLUMNS,
                             filters=[(POST, "in", sorted(target_ids))])
    outbound = pd.read_parquet(connectivity_path, columns=COLUMNS,
                              filters=[(PRE, "in", sorted(source_union))])
    validate_edges(inbound)
    validate_edges(outbound)
    edges = pd.concat([inbound, outbound], ignore_index=True).drop_duplicates(COLUMNS)
    validate_edges(edges)
    endpoints = set(edges[PRE]) | set(edges[POST])
    if not endpoints.issubset(v783):
        raise ValueError("relevant connectivity edges contain non-v783 endpoints")
    target_groups = [(r["Body_ID"], {exact_id(r["Body_ID"])}) for r in targets]
    target_groups.append(("all_six", target_ids))
    readouts = []
    for source_name, source_ids in groups:
        for target_name, selected_targets in target_groups:
            readouts.append({"source_group": source_name, "source_n": len(source_ids),
                             "target": target_name, "target_n": len(selected_targets),
                             **input_metrics(edges, source_ids, selected_targets)})
    report = {
        "schema_version": "cem_inputs_v1",
        "analysis": "C2b: structural connectivity only; no simulation",
        "sources": {name: source_info(path) for name, path in (
            ("connectivity", connectivity_path), ("completeness", completeness_path),
            ("protocol", protocol_path), ("frozen_cells", cells_path),
            ("mn_inventory", ids_path), ("xlsx", xlsx_path))},
        "xlsx_selection": {"sheet": "GRNs", "Connectome": FLYWIRE,
                           "types": "PhG1 through PhG16", "n_rows": len(phg_rows)},
        "target_muscle_source": "MNs sheet, exact Target_Muscle column; all CEM rows: Crop Entry",
        "n_connectivity_rows": pq.ParquetFile(connectivity_path).metadata.num_rows,
        "n_relevant_edges": len(edges),
        "n_model_neurons": len(v783),
        "definitions": {
            "partners": "Distinct Presynaptic_ID values with a positive Connectivity count onto the selected CEM target(s).",
            "synapses": "Unsigned Connectivity; both Excitatory signs included without cancellation.",
            "direct": "Sum Connectivity on source-to-CEM directed edges.",
            "two_hop_first_leg": "Sum Connectivity once per source-to-intermediate edge when that intermediate has an edge to at least one selected CEM.",
            "two_hop_last_leg": "Sum Connectivity once per intermediate-to-CEM edge when that intermediate receives at least one source edge.",
            "two_hop_intermediates": "Any v783 neuron with both legs; no cell-class or sign filter. Exact two-edge walks, not paths of length up to two.",
            "union": "Recompute on union of source IDs and/or targets: convergent first legs and shared presynaptic partners are not summed multiple times.",
            "overlap": "Direct/first-leg/last-leg and different source groups can overlap; their counts are not additive.",
            "sign_caveat": "Structural input counts do not predict firing, net excitation, efficacy, or the activity of any intermediate; negative and positive edges both count.",
        },
        "targets": targets,
        "pharyngeal_rows": phg_rows,
        "pharyngeal_type_counts": dict(sorted(Counter(r["Type"] for r in phg_rows).items())),
        "source_groups": [{"name": name, "ids": [str(i) for i in sorted(ids)]} for name, ids in groups],
        "readouts": readouts,
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / "cem_inputs.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (out / "cem_inputs.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(readouts[0]))
        writer.writeheader()
        writer.writerows(readouts)
    edges.sort_values([PRE, POST]).to_csv(out / "relevant_edges.csv", index=False)
    table = markdown_table(report)
    (out / "cem_inputs_table.md").write_text(table, encoding="utf-8")
    print(table)
    print(f"connectome audit valid: 6 CEM targets, 50 PhG source neurons, {len(edges)} relevant edges; no simulation")
    print(f"outputs: {out}")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", type=Path, default=ROOT / "results/mn-readouts/c2b")
    args = parser.parse_args()
    run(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
