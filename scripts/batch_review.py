#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Review a merged dish batch: needs_review entries, low confidence, and sanity expectations.

Prints (and appends to the batch stability report when --report is given):
  * every batch entry marked needs_review, with levels and the arbitration record
  * every batch entry with any confidence < --min-confidence, with levels
  * sanity checks: expectations for specific dishes; disagreements are listed,
    the model's output is kept unchanged
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEVELS = ["none", "low", "medium", "high", "very_high"]

# key -> (dimension, allowed levels)
SANITY = {
    "durian": [("bitter", ["none", "low"])],
    "cilantro": [("sugar", ["none"])],
    "wasabi": [("sugar", ["none"])],
    "natto": [("sugar", ["none"])],
    "stinky-tofu": [("sugar", ["none"])],
    "century-egg": [("sugar", ["none"])],
    "sparkling-water": [("water", ["very_high", "high"])],
    "black-tea": [("water", ["very_high", "high"])],
    "oolong-tea": [("water", ["very_high", "high"])],
    "americano": [("water", ["very_high", "high"])],
    "whiskey": [("water", ["none", "low", "medium"])],
    "baijiu": [("water", ["none", "low", "medium"])],
    "red-wine": [("water", ["none", "low", "medium"])],
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch", type=Path, required=True)
    parser.add_argument("--dishes", type=Path, default=ROOT / "data" / "dishes.json")
    parser.add_argument("--min-confidence", type=float, default=0.8)
    parser.add_argument("--report", type=Path, help="append the review to this markdown file")
    args = parser.parse_args()
    keys = [d["key"] for d in json.loads(args.batch.read_text(encoding="utf-8"))["dishes"]]
    entries = {e["key"]: e for e in json.loads(args.dishes.read_text(encoding="utf-8"))}
    lines = ["", "## Batch review", ""]
    fmt = lambda e: f"sugar {e['sugar']} · bitter {e['bitter']} · water {e['water']}"

    missing = [k for k in keys if k not in entries]
    lines += [f"Batch keys: {len(keys)}; merged: {len(keys) - len(missing)}" + (f"; missing: {', '.join(missing)}" if missing else ""), ""]

    lines += ["### needs_review", ""]
    nr = [entries[k] for k in keys if k in entries and entries[k]["review"] == "needs_review"]
    if nr:
        lines += ["| key | levels | dimension | zh | en | chosen |", "|---|---|---|---|---|---|"]
        for e in nr:
            for dim, a in e.get("arbitration", {}).items():
                if a["rule"] == "needs_review":
                    lines.append(f"| {e['key']} | {fmt(e)} | {dim} | {a['zh']} | {a['en']} | {a['chosen']} |")
    else:
        lines.append("none")

    lines += ["", f"### confidence < {args.min_confidence}", ""]
    low = [(k, d, entries[k]["confidence"][d]) for k in keys if k in entries for d in ("sugar", "bitter", "water") if entries[k]["confidence"][d] < args.min_confidence]
    if low:
        lines += ["| key | levels | dimension | confidence |", "|---|---|---|---:|"]
        for k, d, c in low:
            lines.append(f"| {k} | {fmt(entries[k])} | {d} | {c:.2f} |")
    else:
        lines.append("none")

    lines += ["", "### sanity checks (model output kept; disagreements listed)", "", "| key | dimension | expected | model | ok |", "|---|---|---|---|---|"]
    disagreements = 0
    for k, checks in SANITY.items():
        e = entries.get(k)
        for dim, allowed in checks:
            if e is None:
                lines.append(f"| {k} | {dim} | {' / '.join(allowed)} | (not merged) | – |")
                continue
            ok = e[dim] in allowed
            disagreements += not ok
            lines.append(f"| {k} | {dim} | {' / '.join(allowed)} | {e[dim]} | {'yes' if ok else '**no**'} |")
    lines += ["", f"Disagreements: {disagreements}", ""]
    text = "\n".join(lines)
    print(text)
    if args.report:
        with args.report.open("a", encoding="utf-8") as fh:
            fh.write(text + "\n")
        print(f"appended to {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
