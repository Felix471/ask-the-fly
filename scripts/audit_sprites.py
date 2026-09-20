#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Audit dictionary sprite ownership; fail on borrowed, missing or shared sprites."""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts.export_dish_list import asset_filename


def audit(root: Path) -> dict:
    directory = root / "site/assets/dishes"
    problems, rows = [], []
    fallbacks = {}
    try:
        document = json.loads((directory / "fallbacks.json").read_text(encoding="utf-8"))
        if not isinstance(document, dict) or not isinstance(document.get("fallbacks"), dict):
            raise ValueError("expected an object with a fallbacks map")
        for key, target in document["fallbacks"].items():
            if not isinstance(target, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", target):
                problems.append(f"sprites: invalid fallback target for {key!r}: {target!r}")
                continue
            fallbacks[key] = target
            if not (directory / f"{target}.png").is_file():
                problems.append(f"sprites: fallback target {target}.png for {key!r} missing")
    except (OSError, ValueError) as exc:
        problems.append(f"sprites: fallbacks.json missing or invalid: {exc}")
    try:
        dishes = json.loads((root / "data/dishes.json").read_text(encoding="utf-8"))
        if not isinstance(dishes, list) or any(
            not isinstance(d, dict) or not isinstance(d.get("key"), str) or not d["key"]
            for d in dishes
        ):
            raise ValueError("expected a list of dishes with nonempty string keys")
    except (OSError, ValueError) as exc:
        problems.append(f"sprites: data/dishes.json missing or invalid: {exc}")
        dishes = []
    owners = defaultdict(list)
    expected = set()
    for dish in dishes:
        key = dish["key"]
        own = asset_filename(key)
        expected.add(own)
        resolved = own
        borrowed = False
        if not (directory / own).is_file() and own[:-4] in fallbacks:
            resolved = fallbacks[own[:-4]] + ".png"
            borrowed = True
            problems.append(f"sprites: {key!r} borrows {resolved} (own {own} missing)")
        exists = (directory / resolved).is_file()
        if not exists:
            problems.append(f"sprites: {key!r} missing sprite {resolved}")
        owners[str((directory / resolved).resolve()).casefold()].append(key)
        rows.append(dict(key=key, own=own, resolved=resolved, borrowed=borrowed, missing=not exists))
    shared = [keys for keys in owners.values() if len(keys) > 1]
    for keys in shared:
        problems.append(f"sprites: shared file for keys {', '.join(keys)}")
    orphans = sorted(p.name for p in directory.glob("*.png") if p.name not in expected)
    return dict(rows=rows, shared=shared, orphans=orphans, problems=problems)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true", help="also run release validator check_sprites")
    args = parser.parse_args()
    result = audit(args.root)
    print("key | own sprite | resolved sprite | status")
    print("--- | --- | --- | ---")
    for row in result["rows"]:
        status = "missing" if row["missing"] else "borrowed" if row["borrowed"] else "own"
        print(f"{row['key']} | {row['own']} | {row['resolved']} | {status}")
    print(f"dishes={len(result['rows'])}; borrows={sum(r['borrowed'] for r in result['rows'])}; "
          f"missing={sum(r['missing'] for r in result['rows'])}; "
          f"shared_files={len(result['shared'])}; orphans={len(result['orphans'])}")
    print("orphans: " + (", ".join(result["orphans"]) or "none"))
    problems = result["problems"]
    if args.check:
        from scripts.validate_release import check_sprites
        problems = list(dict.fromkeys(problems + check_sprites(args.root)))
    for problem in problems:
        print(problem)
    return int(bool(problems))


if __name__ == "__main__":
    raise SystemExit(main())
