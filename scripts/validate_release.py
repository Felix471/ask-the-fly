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
import re
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
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
    problems, dishes = check_dictionary_file(root / "site" / "data" / "dishes.json")
    return problems, dishes


def check_dictionary_file(path: Path) -> tuple[list[str], list[dict]]:
    problems = []
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
        if dish.get("ir94e") not in ("none", "low", "medium", "high"):
            problems.append(f"dictionary: {dish.get('key')!r} ir94e level {dish.get('ir94e')!r} invalid")
        if not dish.get("display", {}).get("zh") or not dish.get("display", {}).get("en"):
            problems.append(f"dictionary: {dish.get('key')!r} lacks a zh or en display name")
    return problems, dishes


def check_source_dictionary(root: Path) -> list[str]:
    problems, _ = check_dictionary_file(root / "data" / "dishes.json")
    return problems


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
            if "ir94e" not in dish:
                problems.append(f"replay: dish {dish.get('key')!r} lacks ir94e")
                continue
            try:
                hz = tuple(levels[d][dish[d]] for d in DIMENSIONS)
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


RELEASE_HEADING = re.compile(r"^## (v\d+\.\d+\.\d+) \S+ (\d{4}-\d{2}-\d{2})\s*$", re.M)


def check_release(root: Path) -> list[str]:
    """site/data/release.json must name the top CHANGELOG.md entry (version and date) and a
    summary key that exists in site/strings.js for both languages, so the footer's
    "what's new" line cannot go stale at a release."""
    problems = []
    release_path = root / "site" / "data" / "release.json"
    changelog_path = root / "CHANGELOG.md"
    if not release_path.exists():
        return [f"release: {release_path} missing"]
    if not changelog_path.exists():
        return [f"release: {changelog_path} missing"]
    try:
        release = load_json(release_path)
    except (OSError, ValueError) as exc:
        return [f"release: {release_path} unreadable: {exc}"]
    version, date_, key = release.get("version"), release.get("date"), release.get("summary_key")
    if not isinstance(version, str) or not re.fullmatch(r"v\d+\.\d+\.\d+", version):
        problems.append(f"release: version {version!r} is not vX.Y.Z")
    if not isinstance(date_, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date_):
        problems.append(f"release: date {date_!r} is not YYYY-MM-DD")
    headings = RELEASE_HEADING.findall(changelog_path.read_text(encoding="utf-8"))
    if not headings:
        problems.append("release: CHANGELOG.md has no '## vX.Y.Z — YYYY-MM-DD' heading")
    else:
        top_version, top_date = headings[0]
        if version != top_version:
            problems.append(f"release: release.json version {version!r} != CHANGELOG.md top entry {top_version!r}")
        if date_ != top_date:
            problems.append(f"release: release.json date {date_!r} != CHANGELOG.md top entry date {top_date!r}")
    strings_path = root / "site" / "strings.js"
    if not isinstance(key, str) or not key:
        problems.append(f"release: summary_key {key!r} missing")
    elif strings_path.exists():
        count = strings_path.read_text(encoding="utf-8").count(f'"{key}":')
        if count < 2:
            problems.append(f"release: summary_key {key!r} is not defined for both languages in site/strings.js ({count} found)")
    return problems


def check_v12(root: Path) -> list[str]:
    """Additive v1.2 assets cannot silently fall back to v1-only validation."""
    app = root / 'site/app.js'
    active = app.exists() and 'data/lookup_table_v1_2.json' in app.read_text(encoding='utf-8')
    if not active:
        return []
    problems = []
    table_path = root / 'data/lookup_table_v1_2.json'
    site_path = root / 'site/data/lookup_table_v1_2.json'
    if not table_path.exists() or not site_path.exists():
        return ['v1.2: active table missing']
    if table_path.read_bytes() != site_path.read_bytes():
        problems.append('v1.2: source/site table bytes differ')
    table = load_json(site_path)
    old = load_json(root / 'data/lookup_table.json')
    if len(table['cells']) != 400 or table['cells_sha256'] != cells_sha256(table['cells']):
        problems.append('v1.2: invalid cell count/hash')
    old_by_id = {cell_id(c): c for c in old['cells']}
    for cell in table['cells']:
        legacy = old_by_id.get(cell_id(cell))
        if not legacy or any(cell.get(k) != v for k, v in legacy.items()):
            problems.append('v1.2: frozen cell projection changed')
        for key in ['mn11d_mean','mn11d_sd','mn11v_mean','mn11v_sd','mn9_r_mean','mn9_r_sd']:
            v = cell.get(key)
            if isinstance(v, bool) or not isinstance(v, (int,float)) or not math.isfinite(v) or v < 0:
                problems.append(f'v1.2: invalid {key}')
        means = [cell.get('mn9_mean'), cell.get('mn11d_mean')]
        if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in means):
            problems.append('v1.2: invalid state inputs')
            continue
        a, b = (v >= 5 for v in means)
        expected = ('eats' if b else 'proboscis_only') if a else ('mouth_moves' if b else 'no_response')
        if cell.get('state') != expected:
            problems.append('v1.2: state rule mismatch')
    source = root / 'data/replay_v1_2'
    packed = root / 'site/data/replay_v1_2'
    for path in source.glob('*'):
        target = packed / path.name
        if not target.exists() or target.read_bytes() != path.read_bytes():
            problems.append(f'v1.2: replay sync {path.name}')
    if len(list(packed.glob('*.bin'))) != 400:
        problems.append('v1.2: expected 400 baseline packs')
    for state in ('eats','mouth_moves','proboscis_only','no_response'):
        for prefix in ('','inset_'):
            for i in range(1,5):
                if not (root / f'site/assets/response/{prefix}{state}_{i}.png').exists():
                    problems.append('v1.2: response asset missing')
    return problems


def check_male(root: Path) -> list[str]:
    """Validate additive male data before activation; require it once the app uses it.

    Unlike check_sync's unconditional legacy whitelist, this bundle is optional in
    older releases. The app marker gates missing assets, never checks of present data.
    """
    from scripts.export_male_site import check_export

    app = root / 'site/app.js'
    active = app.exists() and 'lookup_table_male.json' in app.read_text(encoding='utf-8')
    site_path = root / 'site/data/lookup_table_male.json'
    if not active and not site_path.exists():
        return []
    problems = []
    try:
        table = load_json(site_path)
        female = load_json(root / 'data/lookup_table_v1_2.json')
        if table.get('schema_version') != 'lookup_male_v1':
            problems.append('male: invalid lookup schema')
        cells = table.get('cells', [])
        if len(cells) != 400 or table.get('cells_sha256') != cells_sha256(cells):
            problems.append('male: invalid cell count/hash')
        if table.get('levels') != female.get('levels'):
            problems.append('male: level mapping differs from female grid')
        for i, cell in enumerate(cells):
            old = female['cells'][i] if i < len(female['cells']) else {}
            if any(cell.get(k) != old.get(k) for k in (*DIMENSIONS, 'hz')):
                problems.append(f'male: cell {i} coordinates differ from female grid')
            fields = ['mn9_mean', 'mn9_std', 'mn9_left_mean', 'mn9_left_std',
                      'mn9_right_mean', 'mn9_right_std', 'mn11d_mean', 'mn11d_sd',
                      'mn11v_mean', 'mn11v_sd', 'mn9_r_mean', 'mn9_r_sd', 'cem_mean', 'cem_sd']
            for key in fields:
                v = cell.get(key)
                if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v < 0:
                    problems.append(f'male: cell {i} invalid {key}')
            means = [cell.get('mn9_mean'), cell.get('mn11d_mean')]
            if all(type(v) in (float, int) and math.isfinite(v) for v in means):
                a, b = (v >= 5 for v in means)
                state = ('eats' if b else 'proboscis_only') if a else ('mouth_moves' if b else 'no_response')
                if cell.get('state') != state:
                    problems.append(f'male: cell {i} state rule mismatch')
        if not isinstance(table.get('product_commitments'), list) or len(table['product_commitments']) != 4:
            problems.append('male: expected four product commitments')
    except (OSError, ValueError, KeyError, TypeError) as exc:
        problems.append(f'male: lookup missing or invalid: {exc}')
    try:
        problems += check_export(root, research_optional=True)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        problems.append(f'male: replay export missing or invalid: {exc}')
    try:
        path = root / 'site/data/neurons_male.json'
        neurons = load_json(path)
        index = load_json(root / 'data/replay_neurons_male.json')
        if neurons.get('schema_version') != 'neurons_v1' or neurons.get('layout') != 'malecns_v1_soma':
            problems.append('male: invalid neurons schema/layout')
        if neurons.get('n_indexed') != index['n_neurons']:
            problems.append('male: neurons n_indexed differs from replay index')
        if path.stat().st_size >= 300000:
            problems.append('male: neurons size must be under 300 KB')
    except (OSError, ValueError, KeyError, TypeError) as exc:
        problems.append(f'male: neurons missing or invalid: {exc}')
    return problems


def validate(root: Path) -> list[str]:
    problems, table = check_lookup(root)
    dict_problems, dishes = check_dictionary(root)
    problems += dict_problems
    problems += check_source_dictionary(root)
    problems += check_sync(root)
    problems += check_replays(root, table, dishes)
    problems += check_site(root)
    problems += check_release(root)
    problems += check_v12(root)
    problems += check_male(root)
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
