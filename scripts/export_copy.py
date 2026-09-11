#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Export copy for review.

--readme: split README.md and README.zh.md into copy/readme_sections.md, one block per
"##" section with a marker line carrying the file, the order and a context note. Edit
the prose under each marker, then `scripts/import_copy.py --readme` rebuilds both files.

--strings: refresh copy/site_strings.json `en` / `zh` from the shipped site/strings.js
(keeps key, context and max_length from the existing JSON; adds any key present in the
site but missing from the JSON with an empty context, so it is not forgotten).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from import_copy import COPY_JSON, COPY_README, LANGS, current_strings, flatten  # noqa: E402

README_CONTEXT = {
    "README.md": "English README (GitHub landing page)",
    "README.zh.md": "Chinese README (mirror of the English one)",
}


def split_sections(text: str) -> list[tuple[str, str]]:
    """Return (heading, body) pairs; the preamble before the first '## ' is section 0."""
    lines = text.splitlines()
    sections: list[tuple[str, list[str]]] = [("(preamble: title, tagline, language link)", [])]
    for line in lines:
        if line.startswith("## "):
            sections.append((line[3:].strip(), [line]))
        else:
            sections[-1][1].append(line)
    return [(heading, "\n".join(body).strip("\n")) for heading, body in sections if "\n".join(body).strip()]


def export_readme() -> None:
    out = ["<!-- Copy review: edit the prose under each marker. Keep the marker lines and the '## ' headings;",
           "     scripts/import_copy.py --readme rebuilds README.md and README.zh.md from this file. -->", ""]
    for name in ("README.md", "README.zh.md"):
        text = (ROOT / name).read_text(encoding="utf-8")
        for index, (heading, body) in enumerate(split_sections(text), start=1):
            context = f"{README_CONTEXT[name]} — section '{heading}'"
            out.append(f"<!-- section: {index} | file: {name} | context: {context} -->")
            out.append(body)
            out.append("")
    COPY_README.parent.mkdir(parents=True, exist_ok=True)
    COPY_README.write_text("\n".join(out).rstrip("\n") + "\n", encoding="utf-8")
    print(f"wrote {COPY_README}")


def export_strings() -> None:
    shipped = {lang: flatten(current_strings().get(lang, {})) for lang in LANGS}
    existing = json.loads(COPY_JSON.read_text(encoding="utf-8"))["strings"] if COPY_JSON.exists() else []
    by_key = {entry["key"]: entry for entry in existing}
    entries = []
    for key in sorted(set(shipped["en"]) | set(shipped["zh"]) | {k for k in by_key if k.startswith("meta.")}):
        entry = by_key.get(key, {"key": key, "context": ""})
        if not key.startswith("meta."):
            entry["en"] = shipped["en"].get(key, entry.get("en", ""))
            entry["zh"] = shipped["zh"].get(key, entry.get("zh", ""))
        entries.append({k: entry[k] for k in ("key", "context", "en", "zh", "max_length") if k in entry})
    COPY_JSON.write_text(json.dumps({"schema": "site_strings_v1", "strings": entries}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {COPY_JSON} ({len(entries)} entries)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--readme", action="store_true")
    parser.add_argument("--strings", action="store_true")
    args = parser.parse_args()
    if not (args.readme or args.strings):
        parser.error("pass --readme and/or --strings")
    if args.readme:
        export_readme()
    if args.strings:
        export_strings()
    return 0


if __name__ == "__main__":
    sys.exit(main())
