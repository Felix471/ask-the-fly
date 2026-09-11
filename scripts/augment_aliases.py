#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Add deterministic aliases to dictionary entries: pinyin, traditional characters, spelling variants.

For each entry in the given batch (keys listed in a batch file, or every entry with
--all): traditional form of every Chinese name (zhconv, zh-tw), pinyin of every
Chinese name with and without spaces (pypinyin, no tones), the key with hyphens as
spaces and vice versa, and a few English spelling variants (hyphen/space, -ise/-ize,
common plural/singular). Aliases already owned by another entry are not added, so
one name never points at two dishes. Generated aliases are ordinary aliases; the
merge tool keeps them on later re-encodes unless the entry is replaced.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from pypinyin import lazy_pinyin
from zhconv import convert

ROOT = Path(__file__).resolve().parents[1]
DISHES = ROOT / "data" / "dishes.json"


def normalize(name: str) -> str:
    import unicodedata
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", name).strip().lower())


def has_cjk(text: str) -> bool:
    return any("㐀" <= ch <= "鿿" for ch in text)


def english_variants(name: str) -> set[str]:
    out = set()
    if "-" in name:
        out.add(name.replace("-", " "))
    if " " in name:
        out.add(name.replace(" ", "-"))
    if name.endswith("ies"):
        out.add(name[:-3] + "y")
    elif name.endswith("es") and not name.endswith("ss"):
        out.add(name[:-2])
    elif name.endswith("s") and not name.endswith("ss"):
        out.add(name[:-1])
    else:
        out.add(name + "s")
    out.add(name.replace("ise", "ize")) if "ise" in name else None
    out.add(name.replace("ize", "ise")) if "ize" in name else None
    return {v for v in out if v and v != name}


def chinese_variants(name: str) -> set[str]:
    out = set()
    trad = convert(name, "zh-tw")
    if trad != name:
        out.add(trad)
    syllables = lazy_pinyin(name)
    if syllables:
        out.add(" ".join(syllables))
        out.add("".join(syllables))
    return out


def augment(entries: list[dict], keys: set[str] | None) -> int:
    taken: dict[str, str] = {}
    for entry in entries:
        for name in (entry["key"], *entry["aliases"], *entry["display"].values()):
            taken.setdefault(normalize(name), entry["key"])
    added = 0
    for entry in entries:
        if keys is not None and entry["key"] not in keys:
            continue
        candidates: set[str] = set()
        for name in {entry["key"], *entry["display"].values(), *entry["aliases"]}:
            if has_cjk(name):
                candidates |= chinese_variants(name)
            else:
                candidates |= english_variants(normalize(name))
        for alias in sorted(candidates):
            norm = normalize(alias)
            if not norm or norm in taken:
                continue
            entry["aliases"].append(norm)
            taken[norm] = entry["key"]
            added += 1
    return added


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch", type=Path, help="batch file whose keys get aliases (data/batch2_dishes.json)")
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()
    if not args.batch and not args.all:
        parser.error("pass --batch FILE or --all")
    entries = json.loads(DISHES.read_text(encoding="utf-8"))
    keys = None if args.all else {d["key"] for d in json.loads(args.batch.read_text(encoding="utf-8"))["dishes"]}
    added = augment(entries, keys)
    DISHES.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"added {added} aliases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
