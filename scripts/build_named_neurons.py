#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Resolve the named SEZ neurons to FlyWire v783 root IDs and write data/named_neurons.json.

Sources, in order of preference:
  1. Shiu et al. 2024 SEZ neuron dictionary (vendor/fly-brain/data/sez_neurons.pickle,
     the file the paper's figures.ipynb loads; MIT) — names as used in that paper.
  2. FlyWire annotations table (Schlegel et al. 2024, CC BY 4.0; data/external/) by
     cell_type / hemibrain_type / synonyms.
Every ID is checked against the v783 completeness list the model is built from. Names
with no v783 match are recorded with "root_ids": [] and a note, and the site skips them.
"""

from __future__ import annotations

import json
import pickle
import re
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PICKLE = ROOT / "vendor" / "fly-brain" / "data" / "sez_neurons.pickle"
ANNOTATIONS = ROOT / "data" / "external" / "Supplemental_file1_neuron_annotations.tsv"
COMPLETENESS = ROOT / "vendor" / "fly-brain" / "data" / "2025_Completeness_783.csv"
OUT = ROOT / "data" / "named_neurons.json"

# name -> (label, code from Tastekin 2026 / hemibrain, pickle keys, annotation patterns)
WANTED = [
    ("clavicle", "Clavicle", "ANXXX462a", ["clavicle"], ["ANXXX462a", "clavicle"]),
    ("quasimodo", "Quasimodo", "GNG042", ["quasimodo"], ["GNG042", "quasimodo"]),
    ("bract", "Bract I/II", None, ["bract"], ["bract"]),
    ("roundup", "Roundup", None, ["roundup"], ["roundup"]),
    ("sink_synch", "Sink and Synch", None, ["sink_sync", "sink", "synch"], ["sink", "synch"]),
    ("scapula", "Scapula", "GNG087", ["scapula"], ["GNG087", "scapula"]),
    ("gng016", "GNG016", "GNG016", ["GNG016"], ["GNG016"]),
    ("gng510", "GNG510", "GNG510", ["GNG510"], ["GNG510"]),
    ("fdg", "Fdg", "GNG588", ["Fdg", "fdg"], ["GNG588", "fdg"]),
    ("dng103", "DNg103", "DNg103", ["DNg103"], ["DNg103"]),
    ("bluebell", "Bluebell", None, ["bluebell"], ["bluebell"]),
]


def main() -> int:
    v783 = set(pd.read_csv(COMPLETENESS, index_col=0).index.astype("int64"))
    sez = pickle.load(open(PICKLE, "rb"))
    ann = pd.read_csv(ANNOTATIONS, sep="\t", low_memory=False,
                      usecols=["root_id", "cell_type", "hemibrain_type", "synonyms", "side"])
    ann["root_id"] = ann["root_id"].astype("int64")
    ann_index = ann.set_index("root_id")

    def annotation_hits(patterns: list[str]) -> list[int]:
        hits: list[int] = []
        for col in ("cell_type", "hemibrain_type", "synonyms"):
            series = ann[col].astype(str)
            for pat in patterns:
                regex = rf"(?:^|[^A-Za-z0-9]){re.escape(pat)}(?:[^A-Za-z0-9]|$)"
                for rid in ann.loc[series.str.contains(regex, case=False, regex=True), "root_id"]:
                    if int(rid) not in hits:
                        hits.append(int(rid))
        return hits

    entries = []
    for key, label, code, pickle_keys, patterns in WANTED:
        ids: list[int] = []
        source = None
        for pk in pickle_keys:
            value = sez.get(pk)
            if value:
                ids = [int(v) for v in value]
                source = f"Shiu et al. 2024 sez_neurons.pickle key '{pk}' (MIT)"
                break
        if not ids:
            ids = annotation_hits(patterns)
            if ids:
                source = "FlyWire annotations (Schlegel et al. 2024, CC BY 4.0), cell_type/hemibrain_type/synonyms match"
        in_v783 = [i for i in ids if i in v783]
        dropped = [i for i in ids if i not in v783]
        cells = []
        for rid in in_v783:
            row = ann_index.loc[rid] if rid in ann_index.index else None
            cells.append({
                "root_id": str(rid),
                "side": (str(row["side"]) if row is not None and isinstance(row["side"], str) else None),
                "annotation_cell_type": (str(row["cell_type"]) if row is not None and isinstance(row["cell_type"], str) else None),
            })
        note = None
        if not in_v783:
            note = ("no FlyWire v783 match in the Shiu 2024 SEZ dictionary or the Schlegel 2024 annotation table "
                    "(cell_type / hemibrain_type / synonyms); skipped on the site")
        elif dropped:
            note = f"{len(dropped)} id(s) from the source are not in v783 and were dropped"
        entries.append({
            "key": key, "label": label, "code": code, "root_ids": [c["root_id"] for c in cells],
            "cells": cells, "source": source, "note": note,
        })
    payload = {
        "schema_version": "named_neurons_v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "data_version": "flywire_v783",
        "sources": {
            "shiu_2024_sez_pickle": "vendor/fly-brain/data/sez_neurons.pickle (loaded by the paper's figures.ipynb; MIT)",
            "flywire_annotations": "data/external/Supplemental_file1_neuron_annotations.tsv (Schlegel et al. 2024, CC BY 4.0)",
        },
        "neurons": entries,
    }
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    for e in entries:
        print(f"{e['label']:16s} {len(e['root_ids'])} id(s)  {e['source'] or ''}  {e['note'] or ''}")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
