#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Open one GitHub issue per deferred audit ticket, body = the audit's own text, label = backlog.

  python scripts/backlog_issues.py --audit PATH/TO/audit.md --dry-run
  python scripts/backlog_issues.py --audit PATH/TO/audit.md

Idempotent: a ticket whose title already exists as an open or closed issue is skipped.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys

TICKETS = ["F10", "F11", "F12", "F14", "F15", "F16", "D03", "D04", "D05", "D06", "D09", "Q01", "Q02", "Q03", "Q05"]
NOTES = {
    "F15": "Done in 2026-09-11 batch: IME only (Enter during composition never submits). Remaining: explicit labels, combobox/tab keyboard relations and aria-activedescendant, touch paths for candidates, focus management, reduced motion.",
}


def sections(text: str) -> dict[str, tuple[str, str]]:
    found = {}
    for match in re.finditer(r"^## (F\d\d|D\d\d|Q\d\d) · (.+?)\n(.*?)(?=^## |\Z)", text, re.S | re.M):
        found[match.group(1)] = (match.group(2).strip(), match.group(3).strip())
    return found


def existing_titles() -> set[str]:
    out = subprocess.run(["gh", "issue", "list", "--state", "all", "--limit", "200", "--json", "title"], capture_output=True, text=True, encoding="utf-8")
    if out.returncode != 0:
        raise SystemExit(f"gh issue list failed: {out.stderr}")
    return {item["title"] for item in json.loads(out.stdout)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--audit", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    text = open(args.audit, encoding="utf-8").read()
    found = sections(text)
    missing = [t for t in TICKETS if t not in found]
    if missing:
        print(f"tickets not found in the audit: {missing}")
        return 1
    have = set() if args.dry_run else existing_titles()
    if not args.dry_run:
        subprocess.run(["gh", "label", "create", "backlog", "--description", "Deferred audit items (fix list cfb1864)", "--color", "C2E0C6"], capture_output=True, text=True)
    for ticket in TICKETS:
        title_text, body = found[ticket]
        title = f"{ticket} · {title_text}"
        if title in have:
            print(f"skip (exists): {title}")
            continue
        note = NOTES.get(ticket)
        full = (f"> {note}\n\n" if note else "") + f"From the audit fix list at baseline `cfb1864` (2026-09-11). Text as written in the audit:\n\n{body}"
        if args.dry_run:
            print(f"would create: {title} ({len(full)} chars)")
            continue
        out = subprocess.run(["gh", "issue", "create", "--title", title, "--label", "backlog", "--body", full], capture_output=True, text=True, encoding="utf-8")
        if out.returncode != 0:
            print(f"FAILED {title}: {out.stderr.strip()}")
            return 1
        print(f"created: {out.stdout.strip()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
