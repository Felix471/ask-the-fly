#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Water-anchor check for an encoder stability run. Fails loudly, corrects nothing.

The water definition in the encode prompts names anchor foods per level
(plain water / clear tea / clear broth = very_high; milk = high; cola, juice,
bubble tea, miso soup, watermelon, orange, grapes = medium; honey, cake, apple,
banana, steamed rice = low). A run drifts when a language's modal water level
for one of those foods differs from its anchor. Checkpoint 2 of the Ir94e work
saw miso soup move medium -> high in both languages under encode_v2.3 with
the water wording unchanged; this script measures that on demand.

  .venv\\Scripts\\python scripts/check_water_anchors.py results/encoder/stability_raw_v2_3.jsonl
  .venv\\Scripts\\python scripts/check_water_anchors.py RAW --foods encoder/foods_dictionary.json

Exit 0 when every anchor food present in the run sits at its anchor level in
every language; exit 1 with one line per drifted (food, language); exit 2 when
no anchor food is in the run at all (nothing was checked).
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from encoder.levels import levels_for  # noqa: E402
from encoder.normalize import normalize_name  # noqa: E402

# English names as they appear in the prompt's water definition (encode_v2.2 / v2.3);
# matched against the food's en name after normalization.
ANCHORS = {
    "water": "very_high", "clear tea": "very_high", "clear broth": "very_high",
    "milk": "high",
    "cola": "medium", "juice": "medium", "orange juice": "medium", "bubble tea": "medium",
    "miso soup": "medium", "watermelon": "medium", "orange": "medium", "grapes": "medium",
    "honey": "low", "cake": "low", "apple": "low", "banana": "low", "steamed rice": "low",
    "steamed white rice": "low",
}


def modal(values: list[str]) -> str | None:
    if not values:
        return None
    counts = Counter(values)
    allowed = levels_for("water")
    return max(allowed, key=lambda level: (counts[level], -allowed.index(level)))


def check(raw_path: Path) -> tuple[list[str], int]:
    """Return (drift lines, anchor foods checked)."""
    grouped: dict[tuple[str, str], list[str]] = defaultdict(list)
    for line_number, line in enumerate(raw_path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        record = json.loads(line)
        if "entry" not in record:
            continue
        food = record.get("food") or {}
        en = normalize_name(str(food.get("en") or record["entry"].get("display", {}).get("en", "")))
        if en not in ANCHORS:
            continue
        grouped[(en, str(record.get("lang")))].append(record["entry"]["water"])
    drift = []
    for (en, lang), values in sorted(grouped.items()):
        level = modal(values)
        if level != ANCHORS[en]:
            drift.append(f"{en} [{lang}]: water modal {level}, anchor {ANCHORS[en]} ({values.count(level)}/{len(values)} runs)")
    return drift, len({en for en, _ in grouped})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("raw", type=Path, help="stability raw JSONL (rows carry food, lang, entry)")
    args = parser.parse_args()
    drift, checked = check(args.raw)
    if checked == 0:
        print(f"no anchor food found in {args.raw}; nothing checked")
        return 2
    if drift:
        print(f"water anchors drifted in {args.raw} ({len(drift)} of {checked} anchor foods x languages):")
        for line in drift:
            print("  " + line)
        return 1
    print(f"water anchors hold in {args.raw}: {checked} anchor foods, every language at its anchor level")
    return 0


if __name__ == "__main__":
    sys.exit(main())
