"""Merge encoded dishes into the normalized JSON dictionary."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from .levels import LEVELS
from .normalize import normalize_name

ROOT = Path(__file__).resolve().parents[1]
FOODS_PATH = Path(__file__).with_name("foods_stability.json")
DIMENSIONS = ("sugar", "bitter", "water")
REVIEWS = {"llm_v1", "human_checked", "proxy"}


class MergeError(ValueError):
    pass


def _mode(values: list[str]) -> str:
    counts = Counter(values)
    return max(LEVELS, key=lambda level: (counts[level], -LEVELS.index(level)))


def _normalized_entry(entry: object, label: str) -> dict:
    if not isinstance(entry, dict):
        raise MergeError(f"{label} is not a JSON object")
    result = dict(entry)
    try:
        result["key"] = normalize_name(result["key"])
        result["aliases"] = list(dict.fromkeys(
            name for name in (normalize_name(x) for x in result.get("aliases", [])) if name
        ))
    except (KeyError, TypeError) as exc:
        raise MergeError(f"{label} has an invalid key or aliases: {exc}") from exc
    if not result["key"]:
        raise MergeError(f"{label} has an empty key")
    if result.get("review") not in REVIEWS:
        raise MergeError(f"{label} has invalid review {result.get('review')!r}")
    for dimension in DIMENSIONS:
        if result.get(dimension) not in LEVELS:
            raise MergeError(f"{label} has invalid {dimension} level {result.get(dimension)!r}")
    return result


def _names(entry: dict) -> set[str]:
    return {entry["key"], *entry["aliases"]}


def _assert_unique(entries: list[dict], context: str) -> dict[str, int]:
    owner: dict[str, int] = {}
    collisions: list[str] = []
    for index, entry in enumerate(entries):
        for name in _names(entry):
            previous = owner.get(name)
            if previous is not None and previous != index:
                collisions.append(
                    f"{name!r} maps to both {entries[previous]['key']!r} and {entry['key']!r}"
                )
            else:
                owner[name] = index
    if collisions:
        raise MergeError(f"normalized-name collision in {context}: " + "; ".join(collisions))
    return owner


def _from_stability(records: list[object]) -> list[dict]:
    foods = json.loads(FOODS_PATH.read_text(encoding="utf-8"))
    groups: dict[int, list[dict]] = defaultdict(list)
    for row_number, record in enumerate(records, 1):
        if not isinstance(record, dict):
            raise MergeError(f"JSONL row {row_number} is not an object")
        if "entry" not in record:
            continue
        try:
            groups[int(record["food_index"])].append(record["entry"])
        except (KeyError, TypeError, ValueError) as exc:
            raise MergeError(f"JSONL row {row_number} has invalid food_index") from exc
    merged = []
    for food_index, entries in sorted(groups.items()):
        if not entries:
            continue
        if not 0 <= food_index < len(foods):
            raise MergeError(f"food_index {food_index} is outside foods_stability.json")
        food = foods[food_index]
        normalized = [_normalized_entry(e, f"food_index {food_index} result") for e in entries]
        aliases = [food["zh"], food["en"]]
        for entry in normalized:
            aliases.extend([entry["key"], *entry["aliases"]])
        aliases = list(dict.fromkeys(filter(None, (normalize_name(x) for x in aliases))))
        key = normalize_name(food["en"])
        encoder_version = Counter(e.get("encoder_version", "unknown@encode_v1") for e in normalized).most_common(1)[0][0]
        result = {
            "key": key,
            "aliases": aliases,
            "display": {"zh": food["zh"], "en": food["en"]},
            **{dimension: _mode([e[dimension] for e in normalized]) for dimension in DIMENSIONS},
            "reason": {
                dimension: "modal level across zh/en stability runs" for dimension in DIMENSIONS
            },
            "confidence": {
                dimension: round(sum(float(e.get("confidence", {}).get(dimension, 0.0)) for e in normalized) / len(normalized), 4)
                for dimension in DIMENSIONS
            },
            "review": "llm_v1",
            "encoder_version": encoder_version,
        }
        merged.append(result)
    return merged


def _read_source(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        records = []
        for line_number, line in enumerate(text.splitlines(), 1):
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise MergeError(f"invalid JSON on line {line_number}: {exc}") from exc
        return _from_stability(records)
    if not isinstance(value, list):
        raise MergeError("input JSON must be an array of entries")
    return [_normalized_entry(entry, f"input entry {i}") for i, entry in enumerate(value)]


def merge(source: Path, destination: Path) -> tuple[int, int, list[dict]]:
    incoming = [_normalized_entry(e, f"incoming entry {i}") for i, e in enumerate(_read_source(source))]
    _assert_unique(incoming, "incoming entries")
    if destination.exists():
        try:
            existing_value = json.loads(destination.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise MergeError(f"invalid destination JSON: {exc}") from exc
        if not isinstance(existing_value, list):
            raise MergeError("destination JSON must be an array")
    else:
        existing_value = []
    existing = [_normalized_entry(e, f"existing entry {i}") for i, e in enumerate(existing_value)]
    owner = _assert_unique(existing, "destination")

    skipped = 0
    result = list(existing)
    for candidate in incoming:
        matched = {owner[name] for name in _names(candidate) if name in owner}
        human = [i for i in matched if result[i]["review"] == "human_checked"]
        if human:
            skipped += 1
            print(f"Skipping {candidate['key']!r}: matches human_checked entry {result[human[0]]['key']!r}")
            continue
        if len(matched) > 1:
            targets = ", ".join(repr(result[i]["key"]) for i in sorted(matched))
            raise MergeError(f"incoming {candidate['key']!r} maps to multiple existing entries: {targets}")
        if matched:
            result[next(iter(matched))] = candidate
        else:
            result.append(candidate)
        owner = _assert_unique(result, "merged dictionary")
    result.sort(key=lambda entry: entry["key"])
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return len(incoming) - skipped, skipped, result


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge encoded entries into the dish dictionary")
    parser.add_argument("source", type=Path)
    parser.add_argument("--into", type=Path, default=ROOT / "data" / "dishes.json")
    args = parser.parse_args()
    try:
        merged, skipped, result = merge(args.source, args.into)
    except (OSError, MergeError) as exc:
        parser.exit(1, f"merge error: {exc}\n")
    print(f"Merged {merged} entries; skipped {skipped}; dictionary count: {len(result)}")


if __name__ == "__main__":
    main()
