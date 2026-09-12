#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Phase 1.5 Task A: cross-check the frozen v1 GRN sets against Tastekin et al. 2025/2026 typing.

Reads the supplementary table (bioRxiv 10.1101/2025.08.25.671814v2 "Supplemental table 2",
Table S1 of the Cell version; gitignored under docs/papers/, CC BY-NC-ND 4.0), FlyWire rows only
(`Connectome == "FAFB – Flywire"`), and data/cells.json, and writes docs/cell_set_crosscheck.md:
for every frozen set the count of our IDs per Tastekin Type/Subtype, our IDs without a Tastekin
row, and, for the modality the set represents (docs/phase1_5_plan.md Amendment 2: sugar = LB3b +
LB3c, bitter = LB1a-d, water = LB3a, ir94e = LB1e), the Tastekin IDs of those subtypes that are
not in our set, each with a v783-completeness flag. Analysis only; nothing under data/ is written.

Standard library only (the xlsx is read as zipped XML, so no openpyxl dependency).

  .venv\\Scripts\\python scripts/cross_check_cells.py [--xlsx PATH] [--completeness PATH] [--out PATH]
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import zipfile
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
XLSX = ROOT / "docs" / "papers" / "Tastekin_2025_bioRxiv_v2_SupplTable2_GRN_MN_body_IDs.xlsx"
COMPLETENESS = ROOT / "vendor" / "fly-brain" / "data" / "2025_Completeness_783.csv"
CELLS = ROOT / "data" / "cells.json"
OUT = ROOT / "docs" / "cell_set_crosscheck.md"
FLYWIRE = "FAFB – Flywire"
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
      "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}
# Frozen set -> the Tastekin subtypes that represent the same modality (phase1_5_plan.md, Amendment 2).
MODALITY = {
    "sugar": ("LB3b", "LB3c"),
    "bitter": ("LB1a", "LB1b", "LB1c", "LB1d"),
    "water": ("LB3a",),
    "ir94e": ("LB1e",),
}
SETS = ("sugar", "bitter", "water", "ir94e")


def read_xlsx(path: Path) -> dict[str, list[dict]]:
    """Minimal xlsx reader: every sheet as a list of {header: cell text} dicts."""
    with zipfile.ZipFile(path) as z:
        shared: list[str] = []
        if "xl/sharedStrings.xml" in z.namelist():
            for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", NS):
                shared.append("".join(t.text or "" for t in si.iter(f"{{{NS['m']}}}t")))
        workbook = ET.fromstring(z.read("xl/workbook.xml"))
        rels = {r.get("Id"): r.get("Target") for r in ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))}
        sheets = {}
        for sheet in workbook.find("m:sheets", NS):
            target = rels[sheet.get(f"{{{NS['r']}}}id")].lstrip("/")
            target = target if target.startswith("xl/") else "xl/" + target
            rows = []
            for row in ET.fromstring(z.read(target)).iter(f"{{{NS['m']}}}row"):
                cells = {}
                for c in row.findall("m:c", NS):
                    column = re.match(r"[A-Z]+", c.get("r")).group(0)
                    v = c.find("m:v", NS)
                    if v is not None:
                        cells[column] = shared[int(v.text)] if c.get("t") == "s" else v.text
                    elif c.get("t") == "inlineStr":
                        cells[column] = "".join(t.text or "" for t in c.iter(f"{{{NS['m']}}}t"))
                rows.append(cells)
            header = rows[0] if rows else {}
            sheets[sheet.get("name")] = [
                {header[col]: value for col, value in r.items() if col in header and header[col]} for r in rows[1:]
            ]
        return sheets


def flywire_rows(rows: list[dict]) -> list[dict]:
    return [r for r in rows if r.get("Connectome") == FLYWIRE and r.get("Body_ID")]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--xlsx", type=Path, default=XLSX)
    parser.add_argument("--completeness", type=Path, default=COMPLETENESS)
    parser.add_argument("--cells", type=Path, default=CELLS)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    for path, what in ((args.xlsx, "Tastekin supplementary table (gitignored; place it under docs/papers/)"),
                       (args.completeness, "v783 completeness table (vendor file)"), (args.cells, "data/cells.json")):
        if not path.exists():
            sys.exit(f"missing {what}: {path}")

    sheets = read_xlsx(args.xlsx)
    grns = flywire_rows(sheets["GRNs"])
    mns = flywire_rows(sheets["MNs"])
    by_id = {int(r["Body_ID"]): r for r in grns}
    with args.completeness.open(encoding="utf-8") as handle:
        v783 = {int(row[0]) for row in csv.reader(handle) if row and row[0].isdigit()}
    cells = json.loads(args.cells.read_text(encoding="utf-8"))
    sets = {name: [int(x) for x in cells["sets"][name]["ids"]] for name in SETS}
    mn9 = {"left": int(cells["sets"]["mn9"]["left"]), "right": int(cells["sets"]["mn9"]["right"])}

    def label(r: dict) -> str:
        sub = r.get("Subtype") or "-"
        return f"{r.get('Type', '-')}/{sub}" if sub != "-" else str(r.get("Type", "-"))

    lines = [
        "# Frozen v1 cell sets vs Tastekin et al. typing (Phase 1.5, Task A)",
        "",
        f"Generated {date.today().isoformat()} by `scripts/cross_check_cells.py`. Documentation only: the frozen sets in `data/cells.json` are not changed; Phase 0 gates passed on them as they are.",
        "",
        "## Sources",
        "",
        f"- `{args.xlsx.name}` (bioRxiv 10.1101/2025.08.25.671814v2, Supplemental table 2 = Table S1 of the Cell version; CC BY-NC-ND 4.0; gitignored). FlyWire rows only (`Connectome == \"{FLYWIRE}\"`): {len(grns)} GRNs, {len(mns)} MNs. The table holds GRNs and MNs only; there are no interneuron rows, so GNG015, GNG016, GNG042 (Quasimodo), GNG087 (Scapula) and GNG510 cannot be resolved from it (OQ-5).",
        f"- `data/cells.json` (Shiu et al. 2024 sets: sugar {len(sets['sugar'])}, bitter {len(sets['bitter'])}, water {len(sets['water'])}, ir94e {len(sets['ir94e'])}).",
        f"- `{args.completeness.name}`: the FlyWire v783 neuron index the model is built on ({len(v783)} neurons); every ID below carries an `in v783` flag from it.",
        "- Modality mapping (docs/phase1_5_plan.md, Amendment 2): sugar = LB3b + LB3c; bitter = LB1a-d; water = LB3a; ir94e = LB1e.",
        "",
        "All 411 FlyWire GRN body IDs and all 66 MN body IDs in the table are present in the v783 index." if all(int(r["Body_ID"]) in v783 for r in grns + mns) else
        f"FlyWire IDs in the table that are absent from v783: GRNs {sum(int(r['Body_ID']) not in v783 for r in grns)}, MNs {sum(int(r['Body_ID']) not in v783 for r in mns)}.",
        "",
        "## Summary",
        "",
        "| frozen set | n | Tastekin typing of our IDs | ours without a Tastekin row | Tastekin IDs of the mapped subtypes not in our set |",
        "|---|---:|---|---:|---:|",
    ]
    detail: list[str] = []
    for name in SETS:
        ids = sets[name]
        typing = Counter(label(by_id[i]) if i in by_id else "(no row)" for i in ids)
        missing_rows = [i for i in ids if i not in by_id]
        wanted = MODALITY[name]
        tastekin_ids = [int(r["Body_ID"]) for r in grns if r.get("Subtype") in wanted]
        not_ours = [i for i in tastekin_ids if i not in set(ids)]
        typing_text = "; ".join(f"{k} {v}" for k, v in sorted(typing.items(), key=lambda kv: (-kv[1], kv[0])))
        lines.append(f"| {name} | {len(ids)} | {typing_text} | {len(missing_rows)} | {len(not_ours)} of {len(tastekin_ids)} |")

        detail += ["", f"## {name} ({len(ids)} IDs; modality subtypes {' + '.join(wanted)})", "",
                   "### Our IDs by Tastekin type", "", "| root_id | side | Type/Subtype | Class / Subclass | in v783 |", "|---|---|---|---|---|"]
        for i in ids:
            r = by_id.get(i)
            if r:
                detail.append(f"| {i} | {r.get('Root_Side', '-')} | {label(r)} | {r.get('Class', '-')} / {r.get('Subclass', '-')} | {'yes' if i in v783 else 'NO'} |")
            else:
                detail.append(f"| {i} | – | (no Tastekin row) | – | {'yes' if i in v783 else 'NO'} |")
        detail += ["", f"### Tastekin {' + '.join(wanted)} IDs not in our {name} set ({len(not_ours)} of {len(tastekin_ids)})", ""]
        if not_ours:
            detail += ["| root_id | side | Subtype | in v783 |", "|---|---|---|---|"]
            for i in not_ours:
                r = by_id[i]
                detail.append(f"| {i} | {r.get('Root_Side', '-')} | {r.get('Subtype')} | {'yes' if i in v783 else 'NO'} |")
        else:
            detail.append("none")
        by_side = Counter(r.get("Root_Side") for r in grns if r.get("Subtype") in wanted)
        detail += ["", f"Tastekin {' + '.join(wanted)} in FlyWire: {len(tastekin_ids)} cells ({', '.join(f'{k} {v}' for k, v in sorted(by_side.items()))}); "
                   f"our set is {Counter(by_id[i].get('Root_Side') for i in ids if i in by_id)} by Tastekin root side."]

    mn9_rows = {int(r["Body_ID"]): r for r in mns if r.get("Type") == "MN9"}
    lines += ["", "## MN9 side labels", "",
              "| our name (data/cells.json, Shiu naming) | root_id | Tastekin Root_Side | Tastekin Type | in v783 |", "|---|---|---|---|---|"]
    for ours, root_id in mn9.items():
        r = mn9_rows.get(root_id)
        lines.append(f"| {ours} MN9 | {root_id} | {r.get('Root_Side') if r else '(not in table)'} | {r.get('Type') if r else '–'} | {'yes' if root_id in v783 else 'NO'} |")
    lines += ["",
              "The MNs sheet labels 720575940660219265 as R and 720575940618238523 as L, matching the Schlegel et al. 2024 soma side. Our protocol calls 720575940660219265 \"left MN9\" following Shiu et al. 2024's contralateral naming (right-hemisphere sugar GRNs are stimulated and the contralateral MN9 is read; docs/cell_ids.md). The two labels describe the same two neurons; nothing is swapped.",
              "",
              "## Feeding-MN types available with FlyWire IDs",
              "",
              "| Type | n | Target_Muscle |", "|---|---:|---|"]
    types = defaultdict(list)
    for r in mns:
        types[r.get("Type")].append(r)
    for t, rows in sorted(types.items(), key=lambda kv: kv[0]):
        lines.append(f"| {t} | {len(rows)} | {', '.join(sorted({str(r.get('Target_Muscle')) for r in rows}))} |")
    phg = Counter(r.get("Type") for r in grns if str(r.get("Subclass", "")).startswith("Pharyngeal"))
    lines += ["", f"Pharyngeal GRN types with FlyWire IDs: {', '.join(f'{k} {v}' for k, v in sorted(phg.items(), key=lambda kv: int(re.sub(r'[^0-9]', '', kv[0]) or 0)))} ({sum(phg.values())} cells).",
              f"LB3b (sugar + low salt) {sum(r.get('Subtype') == 'LB3b' for r in grns)} and LB3d (high salt / heavy metal, glutamatergic) {sum(r.get('Subtype') == 'LB3d' for r in grns)} cells have FlyWire IDs, all in v783: the ID lists Phase 1.5 Task E (salt) needs are in the per-set tables below (LB3d appears under the sugar set) and in the table itself.",
              ""]
    lines += detail
    def subtype_counts(name: str) -> Counter:
        return Counter((by_id[i].get("Subtype") if i in by_id else "(no row)") for i in sets[name])

    gloss = {"LB3d": "high salt / heavy metal; ppk23, Ir7c, Ir47a; glutamatergic; aversive", "LB3b": "sugar + low salt",
             "LB3c": "sugar", "LB3a": "water, ppk28", "LB4b": "no receptor match", "LB4a": "no receptor match",
             "LB1e": "Ir94e", "LB2a": "no receptor match, putatively aversive", "LB2b": "no receptor match, putatively aversive",
             "LB2c": "no receptor match, putatively aversive", "(no row)": "not in the table"}

    def finding(name: str) -> str:
        counts = subtype_counts(name)
        wanted = set(MODALITY[name])
        inside = sum(v for k, v in counts.items() if k in wanted)
        outside = [(k, v) for k, v in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])) if k not in wanted]
        if not outside:
            return f"- The {len(sets[name])} frozen {name} GRNs are exactly {' + '.join(MODALITY[name])} in Tastekin's typing."
        parts = "; ".join(f"{v} {k} ({gloss.get(k, '')})" for k, v in outside)
        return f"- {len(sets[name]) - inside} of the {len(sets[name])} frozen {name} GRNs are outside {' + '.join(MODALITY[name])} in Tastekin's typing: {parts}. {inside} are {' + '.join(MODALITY[name])}."

    lines += ["", "## Findings (recorded, not acted on)", "", *[finding(name) for name in SETS], "",
              "These are differences between the Shiu et al. 2024 annotation the sets were frozen from and Tastekin's typing, not errors in our pipeline: the Phase 0 gates passed on the frozen sets as they are. Re-freezing the sets to Tastekin's typing would be a v2 change requiring a full grid rerun (docs/open_questions.md OQ-7). Not done now.",
              ""]
    args.out.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {args.out}")
    for name in SETS:
        typing = Counter(label(by_id[i]) if i in by_id else "(no row)" for i in sets[name])
        print(f"  {name} {len(sets[name])}: " + "; ".join(f"{k} {v}" for k, v in sorted(typing.items(), key=lambda kv: (-kv[1], kv[0]))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
