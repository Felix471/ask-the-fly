# SPDX-License-Identifier: MIT
"""Read-only LB3b/LB3d outgoing-sign audit; no simulation or model edits.

python -B -m scripts.salt_output_signs
Prints source-bound JSON; reads the existing salt IDs and local annotations.
"""
from collections import Counter
import json
from pathlib import Path

import pandas as pd

from scripts.cem_inputs import PRE, POST, SYN, SIGN, WEIGHT, exact_id, validate_edges
from sim.run_mn_readouts import sha256

ROOT = Path(__file__).resolve().parents[1]
ANNOTATIONS = ROOT / "data/external/Supplemental_file1_neuron_annotations.tsv"
NT_SIGN = {"glutamate": -1, "gaba": -1, "acetylcholine": 1,
           "dopamine": 1, "octopamine": 1, "serotonin": 1}


def audit_signs(rows, edges, annotations):
    validate_edges(edges)
    ids = [str(exact_id(row["Body_ID"])) for row in rows]
    if len(ids) != len(set(ids)) or any(r["Subtype"] not in {"LB3b", "LB3d"} for r in rows):
        raise ValueError("duplicate source ID or unexpected salt subtype")
    selected = annotations[annotations.root_id.isin(ids)]
    if selected.root_id.duplicated().any() or set(selected.root_id) != set(ids):
        raise ValueError("annotation must contain exactly one row per source ID")
    selected = selected.set_index("root_id")
    neurons = []
    for row, root in zip(rows, ids):
        outgoing = edges[edges[PRE] == int(root)]
        if outgoing.empty:
            raise ValueError(f"no saved output edges for {root}")
        nt = selected.loc[root, "top_nt"]
        if nt not in NT_SIGN:
            raise ValueError(f"unknown annotation transmitter for {root}: {nt}")
        sign = int(outgoing[SIGN].iloc[0])
        neurons.append({"Body_ID": root, "Subtype": row["Subtype"], "top_nt": nt,
                        "Excitatory": sign, "annotation_derived_sign": NT_SIGN[nt],
                        "disagrees_with_top_nt_sign": sign != NT_SIGN[nt],
                        "output_partners": len(outgoing), "output_synapses": int(outgoing[SYN].sum())})
    summary = {}
    for kind in ("LB3b", "LB3d"):
        group = [r for r in neurons if r["Subtype"] == kind]
        summary[kind] = {"cells": len(group),
                         "positive_cells": sum(r[SIGN] == 1 for r in group),
                         "negative_cells": sum(r[SIGN] == -1 for r in group),
                         "top_nt_counts": dict(Counter(r["top_nt"] for r in group)),
                         "top_nt_sign_disagreements": sum(r["disagrees_with_top_nt_sign"] for r in group),
                         "disagreement_ids": [r["Body_ID"] for r in group if r["disagrees_with_top_nt_sign"]]}
    return {"summary": summary, "neurons": neurons}


def main():
    from sim.run_salt_screen import load_design, SPEC
    spec, protocol, _ = load_design()  # source-bound XLSX/v783 checks, no Brian2 import
    rows = spec["salt_neurons"]
    if Counter(r["Subtype"] for r in rows) != {"LB3b": 25, "LB3d": 29}:
        raise ValueError("expected all 25 LB3b and 29 LB3d FlyWire cells")
    connectivity = ROOT / protocol["connectivity_file"]
    edges = pd.read_parquet(connectivity, columns=[PRE, POST, SYN, SIGN, WEIGHT],
                            filters=[(PRE, "in", [exact_id(r["Body_ID"]) for r in rows])])
    annotations = pd.read_csv(ANNOTATIONS, sep="\t", dtype=str, usecols=["root_id", "top_nt"])
    result = audit_signs(rows, edges, annotations)
    result["source_sha256"] = {p.relative_to(ROOT).as_posix(): sha256(p) for p in
                               [SPEC, ROOT / spec["salt_source"]["file"], connectivity, ANNOTATIONS, Path(__file__)]}
    result["definitions"] = {
        "model_sign": "Excitatory, checked on every outgoing edge; Excitatory x Connectivity must equal that sign times Connectivity.",
        "annotation_comparison": "Per-neuron Schlegel local TSV top_nt mapped with the documented Shiu sign convention: GABA/glutamate negative, other listed transmitters positive. Not a comparison of transmitter identity and not consensusNt.",
        "tastekin_class_comparison": "Separately, the Tastekin LB3d glutamatergic class label implies negative under that convention: every positive LB3d cell disagrees with this class-level expectation.",
        "scope": "Counts are neurons, not synapses. No simulation, sign replacement or explanation of firing outcomes."}
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
