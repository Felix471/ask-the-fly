#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Feed-forward path search: excitatory neurons <= 2 hops downstream of the frozen sugar GRN set
that are presynaptic to CB0465 (720575940636809646), ranked by synapses onto CB0465.

Names the path behind the feed-forward inhibition seen in Phase T (sugar raises CB0465's firing,
CB0465 is the strongest inhibitory input to left MN9). Connectivity only, no simulation.
Sign from `Excitatory x Connectivity` as in sim/network.py; synapse count from `Connectivity`.

  .venv\\Scripts\\python scripts/tonic_ffi_path.py [--target 720575940636809646] [--top 20]

Writes results/tonic/ffi_path.md (gitignored) and prints the table; the table is pasted into
docs/tonic_inhibition.md under its own heading.
"""

from __future__ import annotations

import argparse
import json
import pickle
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONNECTIVITY = ROOT / "vendor" / "fly-brain" / "data" / "2025_Connectivity_783.parquet"
SEZ_PICKLE = ROOT / "vendor" / "fly-brain" / "data" / "sez_neurons.pickle"
ANNOTATIONS = ROOT / "data" / "external" / "Supplemental_file1_neuron_annotations.tsv"
CELLS = ROOT / "data" / "cells.json"
DEFAULT_TARGET = 720575940636809646  # CB0465, right


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--target", type=int, default=DEFAULT_TARGET)
    parser.add_argument("--top", type=int, default=20)
    parser.add_argument("--out", type=Path, default=ROOT / "results" / "tonic" / "ffi_path.md")
    args = parser.parse_args()
    for path, what in ((CONNECTIVITY, "connectivity parquet"), (SEZ_PICKLE, "SEZ neuron pickle"), (ANNOTATIONS, "annotation table")):
        if not path.exists():
            sys.exit(f"missing {what}: {path}")
    import pandas as pd

    conn = pd.read_parquet(CONNECTIVITY, columns=["Presynaptic_ID", "Postsynaptic_ID", "Connectivity", "Excitatory x Connectivity"])
    exc = conn[conn["Excitatory x Connectivity"] > 0]
    cells = json.loads(CELLS.read_text(encoding="utf-8"))
    sugar = {int(x) for x in cells["sets"]["sugar"]["ids"]}
    ann = pd.read_csv(ANNOTATIONS, sep="\t", low_memory=False)
    ann = ann.set_index(ann["root_id"].astype("int64"))
    with open(SEZ_PICKLE, "rb") as handle:
        sez = pickle.load(handle)
    shiu = defaultdict(list)
    for name, ids in sez.items():
        for i in ids:
            shiu[int(i)].append(str(name))

    def note(i: int) -> tuple[str, str, str]:
        if i in ann.index:
            r = ann.loc[i]
            f = lambda v: "" if v != v else str(v)  # noqa: E731
            return f(r["cell_type"]), f(r["top_nt"]), f(r["side"])
        return "(not in table)", "", ""

    # excitatory inputs to the target
    onto = exc[exc["Postsynaptic_ID"] == args.target].groupby("Presynaptic_ID")["Connectivity"].sum()
    inputs = set(int(i) for i in onto.index)
    # hop 1: sugar GRN -> N (excitatory)
    sugar_out = exc[exc["Presynaptic_ID"].isin(sugar)].groupby("Postsynaptic_ID")["Connectivity"].sum()
    hop1 = {int(i): int(v) for i, v in sugar_out.items()}
    # hop 2: sugar GRN -> M (excitatory) -> N (excitatory); best M per N by min(sugar->M, M->N)
    m_to_n = exc[exc["Presynaptic_ID"].isin(hop1.keys()) & exc["Postsynaptic_ID"].isin(inputs)]
    best_m: dict[int, tuple[int, int, int]] = {}
    for (m, n), syn in m_to_n.groupby(["Presynaptic_ID", "Postsynaptic_ID"])["Connectivity"].sum().items():
        m, n, syn = int(m), int(n), int(syn)
        score = (min(hop1[m], syn), hop1[m], syn)
        if n not in best_m or score > (min(best_m[n][1], best_m[n][2]), best_m[n][1], best_m[n][2]):
            best_m[n] = (m, hop1[m], syn)

    rows = []
    for n in inputs:
        syn_target = int(onto[n])
        if n in hop1 and n not in sugar:
            rows.append({"n": n, "hops": 1, "syn_target": syn_target, "sugar_to": hop1[n], "via": None})
        elif n in sugar:
            rows.append({"n": n, "hops": 0, "syn_target": syn_target, "sugar_to": None, "via": None})
        elif n in best_m:
            m, s2m, m2n = best_m[n]
            rows.append({"n": n, "hops": 2, "syn_target": syn_target, "sugar_to": s2m, "via": (m, m2n)})
    rows.sort(key=lambda r: (-r["syn_target"], r["hops"], r["n"]))
    total_exc = int(onto.sum())
    covered = sum(r["syn_target"] for r in rows)
    lines = [
        f"Excitatory inputs to `{args.target}` ({note(args.target)[0]}, {note(args.target)[2]}): {len(inputs)} neurons, {total_exc} synapses; "
        f"{len(rows)} of them lie within two excitatory hops of the frozen sugar GRN set (23 cells) and carry {covered} synapses ({100 * covered / total_exc:.0f}%). "
        f"Direct sugar-GRN → target synapses: {int(onto[[i for i in onto.index if int(i) in sugar]].sum()) if any(int(i) in sugar for i in onto.index) else 0}.",
        "",
        "| # | presynaptic to CB0465 | hops from sugar GRNs | syn → CB0465 | sugar GRN → this neuron (1 hop) or → intermediate (2 hops) | via (2 hops: intermediate, its syn → this neuron) | cell_type | top_nt | side | Shiu name |",
        "|---:|---|---:|---:|---:|---|---|---|---|---|",
    ]
    for i, r in enumerate(rows[: args.top], 1):
        ct, nt, side = note(r["n"])
        via = "–"
        if r["via"]:
            m, m2n = r["via"]
            mct, mnt, mside = note(m)
            via = f"{m} ({mct or '?'}, {mside or '?'}; {m2n} syn)"
        sugar_to = "direct" if r["hops"] == 0 else str(r["sugar_to"])
        lines.append(f"| {i} | {r['n']} | {r['hops']} | {r['syn_target']} | {sugar_to} | {via} | {ct or '–'} | {nt or '–'} | {side or '–'} | {', '.join(shiu.get(r['n'], [])) or '–'} |")
    text = "\n".join(lines) + "\n"
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
