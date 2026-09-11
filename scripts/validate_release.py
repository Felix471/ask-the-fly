#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Read-only acceptance of the production data bundle (Q06). Exit 1 with every reason found.

Checks, each with its own reason text:
  * lookup table: present, not a stub, every MN9 mean/std finite, std >= 0, integer n_trials
    that is the same for every cell, cells listed once, cells_sha256 matches the cells
  * dictionary: no needs_review / draft entries, valid review values and levels, unique keys
  * source and site copies identical (dishes, lookup table, sections, named neurons)
  * replay bundle: manifest n_cells == cells; every cell x variant file present; no orphan
    .bin; every lookup cell and every dictionary dish has a recorded baseline replay
  * neurons layout is not the placeholder; config.json carries an https site_url;
    strings.js exists and index.html loads app.js

  python scripts/validate_release.py            # repo layout (data/ and site/)
  python scripts/validate_release.py --root DIR  # another checkout or a staging copy
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIMENSIONS = ("sugar", "bitter", "water", "ir94e")
REVIEW_PUBLISHABLE = {"llm_v1", "human_checked", "proxy"}
REVIEW_BLOCKED = {"needs_review", "draft"}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def cells_sha256(cells: list[dict]) -> str:
    """The lookup builder's cells hash: sha256 of the cells array as compact, sorted JSON."""
    payload = json.dumps(cells, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def cell_id(levels: dict) -> str:
    return f"G_s{levels['sugar']}_b{levels['bitter']}_w{levels['water']}_i{levels['ir94e']}"


def check_lookup(root: Path) -> tuple[list[str], dict | None]:
    problems = []
    path = root / "site" / "data" / "lookup_table.json"
    if not path.exists():
        return [f"lookup: {path} missing"], None
    table = load_json(path)
    if table.get("stub"):
        problems.append("lookup: table is flagged stub (placeholder values)")
    cells = table.get("cells")
    if not isinstance(cells, list) or not cells:
        problems.append("lookup: no cells")
        return problems, table
    trials = set()
    ids = []
    for i, cell in enumerate(cells):
        for field in ("mn9_mean", "mn9_std", "mn9_left_mean", "mn9_left_std"):
            value = cell.get(field)
            if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value):
                problems.append(f"lookup: cell {i} {field} is not a finite number ({value!r})")
        if isinstance(cell.get("mn9_std"), (int, float)) and cell["mn9_std"] < 0:
            problems.append(f"lookup: cell {i} mn9_std is negative")
        n = cell.get("n_trials")
        if not isinstance(n, int) or isinstance(n, bool) or n < 1:
            problems.append(f"lookup: cell {i} n_trials is not a positive integer ({n!r})")
        else:
            trials.add(n)
        try:
            ids.append(cell_id(cell))
        except KeyError:
            problems.append(f"lookup: cell {i} lacks level names")
    if len(trials) > 1:
        problems.append(f"lookup: n_trials differs between cells: {sorted(trials)}")
    if len(set(ids)) != len(ids):
        problems.append("lookup: duplicate cells")
    recorded = table.get("cells_sha256")
    if recorded and recorded != cells_sha256(cells):
        problems.append("lookup: cells_sha256 does not match the cells in the file")
    if not recorded:
        problems.append("lookup: cells_sha256 missing")
    return problems, table


def check_dictionary(root: Path) -> tuple[list[str], list[dict]]:
    problems = []
    path = root / "site" / "data" / "dishes.json"
    if not path.exists():
        return [f"dictionary: {path} missing"], []
    dishes = load_json(path)
    keys = [d.get("key") for d in dishes]
    if len(set(keys)) != len(keys):
        problems.append("dictionary: duplicate keys")
    for dish in dishes:
        review = dish.get("review")
        if review in REVIEW_BLOCKED:
            problems.append(f"dictionary: {dish.get('key')!r} is {review} (not publishable)")
        elif review not in REVIEW_PUBLISHABLE:
            problems.append(f"dictionary: {dish.get('key')!r} has unknown review {review!r}")
        for dimension in ("sugar", "bitter", "water"):
            if dish.get(dimension) not in ("none", "low", "medium", "high", "very_high"):
                problems.append(f"dictionary: {dish.get('key')!r} {dimension} level {dish.get(dimension)!r} invalid")
        if not dish.get("display", {}).get("zh") or not dish.get("display", {}).get("en"):
            problems.append(f"dictionary: {dish.get('key')!r} lacks a zh or en display name")
    return problems, dishes


def check_sync(root: Path) -> list[str]:
    problems = []
    pairs = [
        ("data/dishes.json", "site/data/dishes.json"),
        ("data/lookup_table.json", "site/data/lookup_table.json"),
        ("data/dish_sections.json", "site/data/sections.json"),
        ("data/named_neurons.json", "site/data/named_neurons.json"),
    ]
    for src, dst in pairs:
        a, b = root / src, root / dst
        if not a.exists() or not b.exists():
            problems.append(f"sync: {src} or {dst} missing")
            continue
        if a.read_bytes() != b.read_bytes():
            problems.append(f"sync: {dst} differs from {src} (run scripts/export_site_data.py)")
    return problems


def check_replays(root: Path, table: dict | None, dishes: list[dict]) -> list[str]:
    problems = []
    replay_dir = root / "site" / "data" / "replay"
    manifest_path = replay_dir / "manifest.json"
    if not manifest_path.exists():
        return [f"replay: {manifest_path} missing"]
    manifest = load_json(manifest_path)
    cells = manifest.get("cells", {})
    variants = manifest.get("variants", [])
    if manifest.get("n_cells") != len(cells):
        problems.append(f"replay: manifest n_cells {manifest.get('n_cells')} != {len(cells)} cells listed")
    if "baseline" not in variants:
        problems.append("replay: manifest has no baseline variant")
    expected = set()
    for cell in cells:
        for variant in variants:
            name = f"{cell}.bin" if variant == "baseline" else f"{cell}_{variant}.bin"
            expected.add(name)
            if not (replay_dir / name).exists():
                problems.append(f"replay: missing {name}")
    present = {p.name for p in replay_dir.glob("*.bin")}
    for orphan in sorted(present - expected):
        problems.append(f"replay: orphan file {orphan} not in manifest x variants")
    if table:
        for cell in table.get("cells", []):
            try:
                cid = cell_id(cell)
            except KeyError:
                continue
            if cid not in cells:
                problems.append(f"replay: lookup cell {cid} has no recorded replay")
        levels = table.get("levels", {})
        by_hz = {}
        for cell in table.get("cells", []):
            hz = tuple(cell.get("hz", {}).get(d) for d in DIMENSIONS)
            by_hz[hz] = cell
        for dish in dishes:
            try:
                hz = tuple(levels[d][dish[d] if d != "ir94e" else "none"] for d in DIMENSIONS)
            except KeyError:
                problems.append(f"replay: dish {dish.get('key')!r} has a level outside the lookup table")
                continue
            cell = by_hz.get(hz)
            if cell is None:
                problems.append(f"replay: dish {dish.get('key')!r} maps to no lookup cell")
            elif cell_id(cell) not in cells:
                problems.append(f"replay: dish {dish.get('key')!r} cell {cell_id(cell)} has no replay")
    return problems


def check_site(root: Path) -> list[str]:
    problems = []
    neurons = root / "site" / "data" / "neurons.json"
    if neurons.exists():
        layout = load_json(neurons).get("layout")
        if layout == "placeholder":
            problems.append("neurons: placeholder layout, not soma coordinates")
    else:
        problems.append("neurons: site/data/neurons.json missing")
    config = root / "site" / "config.json"
    if config.exists():
        url = load_json(config).get("site_url", "")
        if not str(url).startswith("https://"):
            problems.append(f"config: site_url is not https ({url!r})")
    else:
        problems.append("config: site/config.json missing")
    if not (root / "site" / "strings.js").exists():
        problems.append("site: strings.js missing (run scripts/import_copy.py)")
    index = root / "site" / "index.html"
    if not index.exists() or 'src="app.js"' not in index.read_text(encoding="utf-8"):
        problems.append("site: index.html missing or does not load app.js")
    return problems


def validate(root: Path) -> list[str]:
    problems, table = check_lookup(root)
    dict_problems, dishes = check_dictionary(root)
    problems += dict_problems
    problems += check_sync(root)
    problems += check_replays(root, table, dishes)
    problems += check_site(root)
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    problems = validate(args.root)
    if problems:
        print(f"RELEASE INVALID: {len(problems)} problem(s)")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print("release valid: lookup table, dictionary, source/site sync, replay bundle, site files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
