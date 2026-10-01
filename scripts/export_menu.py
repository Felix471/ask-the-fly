#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Build the deterministic menu view from the shipped lookup sources."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AXES = ("sugar", "bitter", "water", "ir94e")
INPUTS = {
    "dishes": "data/dishes.json", "sections": "data/dish_sections.json",
    "female": "data/lookup_table_v1_2.json", "male": "data/lookup_table_male.json",
    "fly_lines": "copy/fly_lines.json", "fallbacks": "site/assets/dishes/fallbacks.json",
}
SITE_COPIES = {
    "dishes": "site/data/dishes.json", "sections": "site/data/sections.json",
    "female": "site/data/lookup_table_v1_2.json", "male": "site/data/lookup_table_male.json",
}


def slug_for(key: str) -> str:
    ascii_key = unicodedata.normalize("NFKD", key).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"^-|-$", "", re.sub(r"[^a-z0-9]+", "-", ascii_key.lower())) or "dish"


def lookup(table: dict, levels: dict) -> dict:
    # Same Hz vector key as app.js buildLookup. Water low/medium share 60 Hz.
    def vector(hz):
        return tuple(float(hz[axis]) for axis in AXES)
    by_hz = {vector(cell["hz"]): cell for cell in table["cells"]}
    if len(by_hz) != len(table["cells"]):
        raise ValueError("duplicate lookup Hz vector")
    key = tuple(float(table["levels"][axis][levels[axis]]) for axis in AXES)
    return by_hz[key]


def speech_line(lines: dict, state: str, levels: dict, seed: int, lang: str) -> str:
    canonical = {**levels, "water": "low" if levels["water"] == "medium" else levels["water"]}
    for bucket in lines["buckets"]:
        if bucket["state"] == state and all(canonical[axis] in allowed for axis, allowed in bucket["when"].items()):
            return bucket[lang][seed % 3]
    raise ValueError(f"No speech bucket: {state} {levels}")


def tiers(entries: list[dict], field: str, minimum: int = 10) -> list[dict]:
    groups = []
    count = 0
    for entry in entries:
        value = entry[field]
        if not groups or groups[-1][field] != value:
            if count >= minimum:
                break
            groups.append({field: value, "keys": []})
        groups[-1]["keys"].append(entry["key"])
        count += 1
    return groups


def build_menu(root: Path = ROOT) -> dict:
    raw = {name: (root / path).read_bytes() for name, path in INPUTS.items()}
    for name, path in SITE_COPIES.items():
        if raw[name] != (root / path).read_bytes():
            raise ValueError(f"site copy differs from source: {path}")
    data = {name: json.loads(value) for name, value in raw.items()}
    dishes, sections, lines = data["dishes"], data["sections"]["sections"], data["fly_lines"]
    section_of = {key: index for index, section in enumerate(sections) for key in section["keys"]}
    if len(section_of) != len(dishes) or set(section_of) != {d["key"] for d in dishes}:
        raise ValueError("sections do not cover dictionary exactly")
    fallbacks = data["fallbacks"]["fallbacks"]
    output = []
    for dish in dishes:
        key = dish["key"]
        levels = {axis: dish.get(axis, "none") for axis in AXES}
        seed = zlib.crc32(key.encode("utf-8"))
        slug = slug_for(key)
        item = {
            "key": key, "slug": slug, "sprite": fallbacks.get(slug, slug),
            "display": dish["display"], "section": section_of[key],
            "not_food": sections[section_of[key]].get("not_food", False),
            "levels": levels, "seed": seed,
        }
        for fly in ("female", "male"):
            cell = lookup(data[fly], levels)
            state = cell["state"]
            item[fly] = {
                "mn9": cell["mn9_mean"], "mn11d": cell["mn11d_mean"],
                "mn11v": cell["mn11v_mean"], "state": state, "rank": 0,
                "line": {lang: speech_line(lines, state, levels, seed, lang) for lang in ("zh", "en")},
            }
        output.append(item)
    for fly in ("female", "male"):
        sorted_items = sorted(output, key=lambda item: -item[fly]["mn9"])
        rank = 0
        last = None
        for position, item in enumerate(sorted_items, 1):
            mean = item[fly]["mn9"]
            if mean != last:
                rank = position
                last = mean
            item[fly]["rank"] = rank
    lists = {}
    for fly in ("female", "male"):
        ranked = sorted(output, key=lambda item: -item[fly]["mn9"])
        plain = [{"key": item["key"], "rank": item[fly]["rank"]} for item in ranked]
        lists[f"{fly}_top"] = [
            {"rank": tier["rank"], "mn9": next(item[fly]["mn9"] for item in ranked if item[fly]["rank"] == tier["rank"]), "keys": tier["keys"]}
            for tier in tiers(plain, "rank")
        ]
    differing = [{"key": item["key"], "diff": abs(item["female"]["rank"] - item["male"]["rank"])} for item in output]
    lists["divergence"] = tiers(sorted((item for item in differing if item["diff"]), key=lambda item: -item["diff"]), "diff")
    lists["not_food"] = {}
    for fly in ("female", "male"):
        ranked = sorted((item for item in output if item["not_food"]), key=lambda item: -item[fly]["mn9"])
        lists["not_food"][fly] = tiers([{"key": item["key"], "rank": item[fly]["rank"]} for item in ranked], "rank", len(ranked))
    lists["section_tops"] = []
    for index in range(len(sections)):
        members = [item for item in output if item["section"] == index]
        entry = {}
        for fly in ("female", "male"):
            maximum = max((item[fly]["mn9"] for item in members), default=None)
            entry[fly] = {"mn9": maximum, "keys": [item["key"] for item in members if item[fly]["mn9"] == maximum]}
        lists["section_tops"].append(entry)
    return {
        "schema": "menu_v1",
        "seed_note": "Presentation only: zlib.crc32(key.encode('utf-8')); never used for scoring.",
        "sources": {
            **{name: hashlib.sha256(raw[name]).hexdigest() for name in ("dishes", "sections", "fly_lines", "fallbacks")},
            "female_cells_sha256": data["female"]["cells_sha256"],
            "male_cells_sha256": data["male"]["cells_sha256"],
        },
        "dishes": output, "lists": lists,
    }


def render_menu(root: Path = ROOT) -> bytes:
    return (json.dumps(build_menu(root), ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    target = ROOT / "site/data/menu.json"
    expected = render_menu(ROOT)
    if args.check:
        if not target.exists() or target.read_bytes() != expected:
            print(f"stale menu: {target}")
            return 1
        print("menu current")
        return 0
    target.write_bytes(expected)
    print(f"wrote {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

