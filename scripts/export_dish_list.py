#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Print every dictionary entry as: <key> | <display en> | <display zh> | <suggested asset filename>."""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def asset_filename(key: str) -> str:
    """ASCII-safe sprite name for site/assets/dishes/: lowercase, hyphens, .png."""
    ascii_key = unicodedata.normalize("NFKD", key).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_key.lower()).strip("-")
    return f"{slug or 'dish'}.png"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dishes", type=Path, default=ROOT / "data" / "dishes.json")
    args = parser.parse_args()
    entries = json.loads(args.dishes.read_text(encoding="utf-8"))
    names = [asset_filename(entry["key"]) for entry in entries]
    if len(set(names)) != len(names):
        raise SystemExit("asset filenames collide; make the keys distinct")
    for entry, name in zip(entries, names):
        print(f"{entry['key']} | {entry['display']['en']} | {entry['display']['zh']} | {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
