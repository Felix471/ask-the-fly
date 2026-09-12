#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Candidate "brake" neurons for a tonic-inhibition condition (Tastekin et al. 2026, Fig S17 style).

Analysis only: reads the vendored FlyWire v783 connectivity, the Schlegel 2024 annotation
table and the Shiu 2024 SEZ neuron dictionary, and writes docs/tonic_candidates.md. No
simulation is run and nothing under data/ is written.

Method
- Inhibitory presynaptic partners of MN9 are rows of the connectivity table whose
  `Excitatory x Connectivity` is negative (the same signed column sim/network.py turns
  into synaptic weights); `Connectivity` is the synapse count.
- Candidates are ranked by inhibitory synapses onto left MN9 (the readout neuron); the
  primary table keeps top_nt == gaba, the secondary table lists the glutamatergic ones.
- Per candidate: synapses onto right MN9, Shiu names, direct input synapses from the frozen
  GRN sets in data/cells.json, and breadth (distinct postsynaptic partners / output synapses,
  distinct presynaptic partners).

  .venv\\Scripts\\python scripts/tonic_candidates.py [--top 15] [--out docs/tonic_candidates.md]

The document's "## Notes on the top five" section is hand-written; the script keeps it verbatim
when it regenerates the tables above it.
"""

from __future__ import annotations

import argparse
import json
import pickle
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONNECTIVITY = ROOT / "vendor" / "fly-brain" / "data" / "2025_Connectivity_783.parquet"
SEZ_PICKLE = ROOT / "vendor" / "fly-brain" / "data" / "sez_neurons.pickle"
ANNOTATIONS = ROOT / "data" / "external" / "Supplemental_file1_neuron_annotations.tsv"
CELLS = ROOT / "data" / "cells.json"
MN9_LEFT = 720575940660219265
MN9_RIGHT = 720575940618238523
GRN_SETS = ("sugar", "bitter", "water", "ir94e")
ANNOTATION_COLUMNS = ("super_class", "cell_class", "cell_type", "hemibrain_type", "top_nt", "top_nt_conf", "side")
NOTES_HEADING = "## Notes on the top five"


def require(path: Path, what: str) -> None:
    if not path.exists():
        sys.exit(f"missing {what}: {path}\n(the vendor files are not in the repository; see docs/environment.md)")


def load_inputs():
    for path, what in ((CONNECTIVITY, "connectivity parquet"), (SEZ_PICKLE, "SEZ neuron pickle"),
                       (ANNOTATIONS, "annotation table"), (CELLS, "cells.json")):
        require(path, what)
    import pandas as pd  # after the file check so a missing vendor file is reported first

    conn = pd.read_parquet(CONNECTIVITY, columns=["Presynaptic_ID", "Postsynaptic_ID", "Connectivity", "Excitatory x Connectivity"])
    ann = pd.read_csv(ANNOTATIONS, sep="\t", low_memory=False)
    ann = ann.set_index(ann["root_id"].astype("int64"))
    with open(SEZ_PICKLE, "rb") as handle:
        sez = pickle.load(handle)
    shiu_names: dict[int, list[str]] = defaultdict(list)
    for name, ids in sez.items():
        for root_id in ids:
            shiu_names[int(root_id)].append(str(name))
    cells = json.loads(CELLS.read_text(encoding="utf-8"))
    grn = {name: {int(x) for x in cells["sets"][name]["ids"]} for name in GRN_SETS}
    for name, ids in grn.items():
        if not conn["Presynaptic_ID"].isin(ids).any():
            sys.exit(f"GRN set {name!r} from data/cells.json has no presynaptic rows in the connectivity table; ids mismatch")
    mn9 = cells["sets"]["mn9"]
    if int(mn9["left"]) != MN9_LEFT or int(mn9["right"]) != MN9_RIGHT:
        sys.exit(f"MN9 ids in data/cells.json ({mn9['left']}, {mn9['right']}) differ from this script's constants")
    return conn, ann, shiu_names, grn


def candidates(conn, ann, shiu_names, grn, top: int):
    inhibitory = conn[conn["Excitatory x Connectivity"] < 0]
    onto_left = inhibitory[inhibitory["Postsynaptic_ID"] == MN9_LEFT].groupby("Presynaptic_ID")["Connectivity"].sum()
    onto_right = inhibitory[inhibitory["Postsynaptic_ID"] == MN9_RIGHT].groupby("Presynaptic_ID")["Connectivity"].sum()
    pre_ids = sorted(set(onto_left.index) | set(onto_right.index))

    out_rows = conn[conn["Presynaptic_ID"].isin(pre_ids)]
    out_partners = out_rows.groupby("Presynaptic_ID")["Postsynaptic_ID"].nunique()
    out_synapses = out_rows.groupby("Presynaptic_ID")["Connectivity"].sum()
    in_rows = conn[conn["Postsynaptic_ID"].isin(pre_ids)]
    in_partners = in_rows.groupby("Postsynaptic_ID")["Presynaptic_ID"].nunique()
    grn_inputs = {}
    for name, ids in grn.items():
        sub = in_rows[in_rows["Presynaptic_ID"].isin(ids)]
        grn_inputs[name] = sub.groupby("Postsynaptic_ID")["Connectivity"].sum()

    rows = []
    for pre in pre_ids:
        record = {
            "root_id": int(pre),
            "syn_left": int(onto_left.get(pre, 0)),
            "syn_right": int(onto_right.get(pre, 0)),
            "shiu": ", ".join(sorted(shiu_names.get(int(pre), []))) or "",
            "out_partners": int(out_partners.get(pre, 0)),
            "out_synapses": int(out_synapses.get(pre, 0)),
            "in_partners": int(in_partners.get(pre, 0)),
        }
        for name in GRN_SETS:
            record[f"grn_{name}"] = int(grn_inputs[name].get(pre, 0))
        if pre in ann.index:
            for column in ANNOTATION_COLUMNS:
                value = ann.at[pre, column]
                record[column] = "" if value != value else str(value)  # NaN -> ""
        else:
            for column in ANNOTATION_COLUMNS:
                record[column] = ""
            record["cell_type"] = "(not in annotation table)"
        rows.append(record)
    rows.sort(key=lambda r: (-r["syn_left"], -r["syn_right"], r["root_id"]))
    gaba = [r for r in rows if r["top_nt"] == "gaba"]
    glut = [r for r in rows if r["top_nt"] == "glutamate"]
    other = [r for r in rows if r["top_nt"] not in ("gaba", "glutamate")]
    return rows, gaba[:top], glut[:top], other


def fmt_conf(value: str) -> str:
    try:
        return f"{float(value):.2f}"
    except (TypeError, ValueError):
        return value or "–"


def table(rows: list[dict]) -> list[str]:
    head = ("| # | root_id | syn → L MN9 | syn → R MN9 | side | super_class | cell_class | cell_type | hemibrain_type | top_nt (conf) | Shiu name | "
            "GRN in: sugar / bitter / water / ir94e | out partners (synapses) | in partners |")
    lines = [head, "|" + "---|" * 14]
    for i, r in enumerate(rows, 1):
        grn = " / ".join(str(r[f"grn_{n}"]) for n in GRN_SETS)
        lines.append(
            f"| {i} | {r['root_id']} | {r['syn_left']} | {r['syn_right']} | {r['side'] or '–'} | {r['super_class'] or '–'} | "
            f"{r['cell_class'] or '–'} | {r['cell_type'] or '–'} | {r['hemibrain_type'] or '–'} | {r['top_nt'] or '–'} ({fmt_conf(r['top_nt_conf'])}) | "
            f"{r['shiu'] or '–'} | {grn} | {r['out_partners']} ({r['out_synapses']}) | {r['in_partners']} |"
        )
    return lines


def render(all_rows, gaba, glut, other, top: int, notes: str) -> str:
    n_left = sum(1 for r in all_rows if r["syn_left"] > 0)
    n_right = sum(1 for r in all_rows if r["syn_right"] > 0)
    nt_counts = defaultdict(int)
    for r in all_rows:
        if r["syn_left"] > 0:
            nt_counts[r["top_nt"] or "(none)"] += 1
    nt_summary = ", ".join(f"{k} {v}" for k, v in sorted(nt_counts.items(), key=lambda kv: -kv[1]))
    lines = [
        "# Tonic-inhibition candidates: inhibitory inputs to MN9",
        "",
        f"Generated {date.today().isoformat()} by `scripts/tonic_candidates.py`. Analysis only; no simulation was run.",
        "",
        "## Method",
        "",
        "Tastekin et al. 2026 (Fig S17) hold MN9 down by driving an inhibitory premotor neuron (GNG015) continuously, then test sugar with and without a disinhibition node silenced. "
        "GNG015 has no FlyWire v783 match in the sources we hold (docs/open_questions.md, OQ-5), so the brake is chosen from the connectome instead. "
        "Inputs: `vendor/fly-brain/data/2025_Connectivity_783.parquet` (FlyWire v783 connectivity as used by the model; sign from the `Excitatory x Connectivity` column, the same signed column `sim/network.py` multiplies by `w_syn`; synapse count from `Connectivity`), "
        "`data/external/Supplemental_file1_neuron_annotations.tsv` (Schlegel et al. 2024: `super_class`, `cell_class`, `cell_type`, `hemibrain_type`, `top_nt`, `top_nt_conf`, `side`), "
        "`vendor/fly-brain/data/sez_neurons.pickle` (Shiu et al. 2024 named SEZ neurons) and the frozen GRN sets in `data/cells.json` (sugar, bitter, water, ir94e). "
        f"Presynaptic partners of left MN9 `{MN9_LEFT}` and right MN9 `{MN9_RIGHT}` with a negative signed connectivity are ranked by synapses onto left MN9 (the readout). "
        "The primary table keeps `top_nt == gaba` (Tastekin's design assumes a GABAergic brake); glutamatergic ones are listed separately (the model treats both signs as inhibitory). "
        "Per candidate: inhibitory synapses onto right MN9; any Shiu name; direct (1-hop) input synapses from each GRN set; breadth as the number of distinct postsynaptic partners and total output synapses (what a continuous drive would perturb besides MN9) and distinct presynaptic partners.",
        "",
        f"Inhibitory presynaptic partners: {n_left} onto left MN9, {n_right} onto right MN9. By transmitter, onto left MN9: {nt_summary}.",
        "",
        "The drive level is not calibrated: Tastekin's 100 Hz is their choice, and whatever rate we use for the chosen brake will be ours, likewise uncalibrated against any measured firing rate of that neuron. "
        "This document ranks by synapse count only and makes no recommendation.",
        "",
        f"## Primary table: GABAergic inhibitory inputs to MN9 (top {top} by synapses onto left MN9)",
        "",
        *table(gaba),
        "",
        f"## Secondary table: glutamatergic inhibitory inputs to MN9 (top {top})",
        "",
        *table(glut),
        "",
    ]
    if other:
        lines += [
            f"Inhibitory-signed partners with another or missing `top_nt` (not tabulated): {len(other)}; the largest onto left MN9 is `{other[0]['root_id']}` "
            f"({other[0]['syn_left']} synapses, top_nt `{other[0]['top_nt'] or 'none'}`).",
            "",
        ]
    lines += [notes.rstrip("\n") + "\n" if notes else f"{NOTES_HEADING}\n\n(hand-written; see the commit that adds this file)\n"]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Rank inhibitory inputs to MN9 as tonic-inhibition brake candidates")
    parser.add_argument("--top", type=int, default=15)
    parser.add_argument("--out", type=Path, default=ROOT / "docs" / "tonic_candidates.md")
    args = parser.parse_args()
    conn, ann, shiu_names, grn = load_inputs()
    all_rows, gaba, glut, other = candidates(conn, ann, shiu_names, grn, args.top)
    notes = ""
    if args.out.exists():
        text = args.out.read_text(encoding="utf-8")
        if NOTES_HEADING in text:
            notes = text[text.index(NOTES_HEADING):]
    args.out.write_text(render(all_rows, gaba, glut, other, args.top, notes), encoding="utf-8")
    print(f"wrote {args.out}: {len(gaba)} GABA candidates, {len(glut)} glutamatergic, {len(other)} other; "
          f"{sum(1 for r in all_rows if r['syn_left'] > 0)} inhibitory partners of left MN9 in total")
    return 0


if __name__ == "__main__":
    sys.exit(main())
