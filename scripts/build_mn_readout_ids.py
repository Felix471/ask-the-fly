#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Extract the feeding-MN research inventory from Tastekin Table S1, without simulation.

The local workbook is bioRxiv v2 Supplemental table 2 (Table S1 in the Cell
version). Only the MNs sheet's FAFB/FlyWire rows are retained. Body IDs remain
strings throughout: converting these 18-digit IDs through float loses precision.
The source's Root_Side convention is retained, including MN9: the frozen Shiu
"left MN9" is Tastekin Root_Side R. No frozen data or site asset is written.

    .venv\\Scripts\\python scripts/build_mn_readout_ids.py
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.cross_check_cells import COMPLETENESS, FLYWIRE, XLSX, flywire_rows, read_xlsx

OUT = ROOT / "data/mn_readout_ids.json"
FIELDS = ("Body_ID", "Root_Side", "Type", "Target_Muscle")
FROZEN_FILES = {
    (ROOT / "data" / name).resolve()
    for name in (
        "stim_protocol.json",
        "grid_levels.json",
        "lookup_table.json",
        "cells.json",
        "replay_neurons.json",
    )
}


def select_mn_rows(rows: list[dict], v783_ids: set[str]) -> list[dict]:
    """Validate every selected source row before the shared filter can skip an ID."""
    selected = [r for r in rows if r.get("Connectome") == FLYWIRE]
    if not selected:
        raise ValueError("MNs sheet has no FlyWire rows")
    seen: set[str] = set()
    for number, row in enumerate(selected, 1):
        for field in FIELDS:
            value = row.get(field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"FlyWire MN row {number}: missing/non-string {field}")
        body_id = row["Body_ID"]
        if not re.fullmatch(r"[1-9][0-9]*", body_id):
            raise ValueError(f"FlyWire MN row {number}: Body_ID must be an exact integer string")
        if row["Root_Side"] not in {"L", "R"}:
            raise ValueError(f"FlyWire MN row {number}: unexpected Root_Side {row['Root_Side']!r}")
        if body_id in seen:
            raise ValueError(f"duplicate FlyWire MN Body_ID {body_id}")
        seen.add(body_id)
    return [
        {**{field: row[field] for field in FIELDS}, "in_v783": row["Body_ID"] in v783_ids}
        for row in flywire_rows(selected)
    ]


def read_v783_ids(path: Path) -> set[str]:
    ids: set[str] = set()
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for number, row in enumerate(csv.reader(handle), 1):
            if not row:
                continue
            if number == 1 and row[0] in {"", "root_id", "Body_ID"}:
                continue
            if not re.fullmatch(r"[1-9][0-9]*", row[0]):
                raise ValueError(f"v783 CSV row {number}: invalid root ID")
            if row[0] in ids:
                raise ValueError(f"v783 CSV row {number}: duplicate root ID {row[0]}")
            ids.add(row[0])
    if not ids:
        raise ValueError("v783 index is empty")
    return ids


def source_path(path: Path) -> str:
    resolved = path.resolve()
    return resolved.relative_to(ROOT).as_posix() if resolved.is_relative_to(ROOT) else resolved.as_posix()


def build_document(xlsx: Path, completeness: Path) -> dict:
    sheets = read_xlsx(xlsx)
    if "MNs" not in sheets:
        raise ValueError("workbook has no MNs sheet")
    neurons = select_mn_rows(sheets["MNs"], read_v783_ids(completeness))
    return {
        "schema_version": "mn_readout_ids_v1",
        "source": {
            "file": source_path(xlsx),
            "sheet": "MNs",
            "filter": {"Connectome": FLYWIRE},
            "citation": (
                "Tastekin et al., bioRxiv 10.1101/2025.08.25.671814v2, Supplemental table 2; "
                "Table S1 of Cell 189 (2026), doi:10.1016/j.cell.2026.08.016. "
                "Source workbook is local/gitignored; this is a FlyWire MN-row extract."
            ),
            "biorxiv_url": "https://www.biorxiv.org/content/10.1101/2025.08.25.671814v2",
            "sha256": hashlib.sha256(xlsx.read_bytes()).hexdigest(),
            "completeness_file": source_path(completeness),
            "completeness_sha256": hashlib.sha256(completeness.read_bytes()).hexdigest(),
        },
        "n_neurons": len(neurons),
        "neurons": neurons,
    }


def validate_output_path(out: Path, xlsx: Path, completeness: Path) -> None:
    resolved = out.resolve()
    if resolved in FROZEN_FILES:
        raise ValueError(f"refusing to overwrite frozen scientific data: {out}")
    if any(resolved.is_relative_to((ROOT / folder).resolve()) for folder in ("site", "sim")):
        raise ValueError(f"research output must not write site or simulation files: {out}")
    if resolved in {xlsx.resolve(), completeness.resolve()}:
        raise ValueError(f"refusing to overwrite an input: {out}")
    if resolved.suffix.lower() != ".json":
        raise ValueError("output must be a JSON file")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--xlsx", type=Path, default=XLSX)
    parser.add_argument("--completeness", type=Path, default=COMPLETENESS)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args(argv)
    validate_output_path(args.out, args.xlsx, args.completeness)
    document = build_document(args.xlsx, args.completeness)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    count = sum(row["in_v783"] for row in document["neurons"])
    print(f"wrote {args.out}: {document['n_neurons']} FlyWire MNs; {count} present in v783")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
