"""Merge encoded dishes into the normalized JSON dictionary."""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

from .levels import LEVELS
from .normalize import normalize_name

ROOT = Path(__file__).resolve().parents[1]
FOODS_PATH = Path(__file__).with_name("foods_stability.json")
AMBIGUOUS_PATH = ROOT / "data" / "ambiguous_names.json"
DIMENSIONS = ("sugar", "bitter", "water")
REVIEWS = {"llm_v1", "human_checked", "proxy"}


class MergeError(ValueError):
    pass


def _load_ambiguous_names() -> tuple[dict[str, dict], dict[str, list[str]]]:
    try:
        value = json.loads(AMBIGUOUS_PATH.read_text(encoding="utf-8"))
        names = value["names"]
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
        raise MergeError(f"cannot load {AMBIGUOUS_PATH}: {exc}") from exc
    if not isinstance(names, dict):
        raise MergeError(f"{AMBIGUOUS_PATH} names must be an object")

    ambiguous: dict[str, dict] = {}
    split_aliases: dict[str, list[str]] = {}
    for raw_name, detail in names.items():
        name = normalize_name(raw_name)
        if not name or not isinstance(detail, dict):
            raise MergeError(f"invalid ambiguous name entry {raw_name!r}")
        split_into = detail.get("split_into")
        if not isinstance(split_into, list) or not split_into:
            raise MergeError(f"ambiguous name {raw_name!r} has no split_into dishes")
        normalized_splits = []
        for index, dish in enumerate(split_into):
            if not isinstance(dish, dict):
                raise MergeError(f"split {index} for {raw_name!r} is not an object")
            try:
                zh = normalize_name(dish["zh"])
                en = normalize_name(dish["en"])
                aliases = [normalize_name(alias) for alias in dish.get("aliases", [])]
            except (KeyError, TypeError) as exc:
                raise MergeError(f"invalid split {index} for {raw_name!r}: {exc}") from exc
            suggestions = list(dict.fromkeys([zh, en, *filter(None, aliases)]))
            normalized_splits.append({**dish, "zh": zh, "en": en, "aliases": aliases})
            for identifier in (zh, en):
                split_aliases[identifier] = suggestions
        ambiguous[name] = {**detail, "source_name": raw_name, "split_into": normalized_splits}
    return ambiguous, split_aliases


AMBIGUOUS_NAMES, SPLIT_ALIASES = _load_ambiguous_names()


def _mode(values: list[str]) -> str:
    counts = Counter(values)
    return max(LEVELS, key=lambda level: (counts[level], -LEVELS.index(level)))


def _normalized_entry(entry: object, label: str) -> dict:
    if not isinstance(entry, dict):
        raise MergeError(f"{label} is not a JSON object")
    result = dict(entry)
    try:
        original_key = normalize_name(result["key"])
        aliases = list(dict.fromkeys(
            name for name in (normalize_name(x) for x in result.get("aliases", [])) if name
        ))
    except (KeyError, TypeError) as exc:
        raise MergeError(f"{label} has an invalid key or aliases: {exc}") from exc

    safe_aliases = []
    for alias in aliases:
        if alias in AMBIGUOUS_NAMES:
            print(f"stripped ambiguous alias {alias!r} from {label}")
        else:
            safe_aliases.append(alias)
    if original_key in AMBIGUOUS_NAMES:
        print(f"stripped ambiguous key {original_key!r} from {label}")
        if not safe_aliases:
            raise MergeError(
                f"{label} has ambiguous key {original_key!r} and no non-ambiguous alias to use as a key"
            )
        result["key"] = safe_aliases[0]
    else:
        result["key"] = original_key
    if not result["key"]:
        raise MergeError(f"{label} has an empty key")

    display = result.get("display", {})
    identifiers = {result["key"], *safe_aliases}
    if isinstance(display, dict):
        for value in display.values():
            if isinstance(value, str):
                identifiers.add(normalize_name(value))
    for identifier in identifiers:
        safe_aliases.extend(SPLIT_ALIASES.get(identifier, []))
    result["aliases"] = list(dict.fromkeys(safe_aliases))

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


def _raw_food(records: list[dict], fallback: dict[str, str]) -> dict[str, str]:
    """Recover inputs represented by old raw data after the configured list changes."""
    food = dict(fallback)
    for lang in ("zh", "en"):
        for record in records:
            if record.get("lang") != lang:
                continue
            entry = record["entry"]
            display = entry.get("display")
            if isinstance(display, dict) and isinstance(display.get(lang), str):
                food[lang] = display[lang]
                break
    return food


def _modal_reason(records: list[dict], normalized: list[dict], dimension: str) -> str:
    """Return a real model reason for the modal level, preferring the English run."""
    modal = _mode([entry[dimension] for entry in normalized])
    candidates = []
    for record, entry in zip(records, normalized):
        if entry[dimension] == modal:
            reason = " ".join(str(entry.get("reason", {}).get(dimension, "")).split())
            if reason:
                candidates.append((0 if record.get("lang") == "en" else 1, reason))
    if not candidates:
        return "modal level across zh/en stability runs"
    candidates.sort(key=lambda item: item[0])
    return candidates[0][1]


def _from_stability(records: list[object]) -> list[dict]:
    foods = json.loads(FOODS_PATH.read_text(encoding="utf-8"))
    groups: dict[int, list[dict]] = defaultdict(list)
    for row_number, record in enumerate(records, 1):
        if not isinstance(record, dict):
            raise MergeError(f"JSONL row {row_number} is not an object")
        if "entry" not in record:
            continue
        try:
            groups[int(record["food_index"])].append(record)
        except (KeyError, TypeError, ValueError) as exc:
            raise MergeError(f"JSONL row {row_number} has invalid food_index") from exc
    merged = []
    for food_index, food_records in sorted(groups.items()):
        if not food_records:
            continue
        if not 0 <= food_index < len(foods):
            raise MergeError(f"food_index {food_index} is outside foods_stability.json")
        food = dict(food_records[0].get("food", {})) or _raw_food(food_records, foods[food_index])
        ambiguous_inputs = {
            normalize_name(food.get(lang, "")) for lang in ("zh", "en")
        } & AMBIGUOUS_NAMES.keys()
        if ambiguous_inputs:
            print(
                f"skipped ambiguous food: {food['zh']} / {food['en']} -> "
                "encode its split dishes separately (data/ambiguous_names.json)"
            )
            continue
        normalized = [
            _normalized_entry(record["entry"], f"food_index {food_index} result")
            for record in food_records
        ]
        aliases = [food["zh"], food["en"]]
        for entry in normalized:
            aliases.extend([entry["key"], *entry["aliases"]])
        aliases = list(dict.fromkeys(filter(None, (normalize_name(x) for x in aliases))))
        key = normalize_name(food["en"])
        encoder_version = Counter(
            record.get("encoder_version")
            or entry.get("encoder_version", "unknown@encode_v1")
            for record, entry in zip(food_records, normalized)
        ).most_common(1)[0][0]
        result = {
            "key": key,
            "aliases": aliases,
            "display": {"zh": food["zh"], "en": food["en"]},
            **{dimension: _mode([e[dimension] for e in normalized]) for dimension in DIMENSIONS},
            "reason": {
                dimension: _modal_reason(food_records, normalized, dimension)
                for dimension in DIMENSIONS
            },
            "confidence": {
                dimension: round(
                    sum(float(e.get("confidence", {}).get(dimension, 0.0)) for e in normalized)
                    / len(normalized),
                    4,
                )
                for dimension in DIMENSIONS
            },
            "review": "llm_v1",
            "encoder_version": encoder_version,
        }
        merged.append(_normalized_entry(result, f"food_index {food_index} merged entry"))
    canonical_owner = {
        normalize_name(name): entry["key"]
        for entry in merged
        for name in (entry["key"], *entry.get("display", {}).values())
        if isinstance(name, str) and normalize_name(name)
    }
    for entry in merged:
        entry["aliases"] = [
            alias
            for alias in entry["aliases"]
            if canonical_owner.get(alias, entry["key"]) == entry["key"]
        ]
    return merged


def _paired_entry(pair: dict, index: int) -> dict:
    label = f"paired input {index}"
    if set(pair) != {"zh_entry", "en_entry"}:
        raise MergeError(f"{label} must contain exactly zh_entry and en_entry")
    zh_entry = _normalized_entry(pair["zh_entry"], f"{label} zh_entry")
    en_entry = _normalized_entry(pair["en_entry"], f"{label} en_entry")
    disagreements = [
        f"{dimension}: zh={zh_entry[dimension]!r}, en={en_entry[dimension]!r}"
        for dimension in DIMENSIONS
        if zh_entry[dimension] != en_entry[dimension]
    ]
    if disagreements:
        raise MergeError(f"{label} disagrees with itself: " + "; ".join(disagreements))
    try:
        display = {
            "zh": zh_entry["display"]["zh"],
            "en": en_entry["display"]["en"],
        }
    except (KeyError, TypeError) as exc:
        raise MergeError(f"{label} is missing display.zh or display.en: {exc}") from exc
    result = {
        "key": en_entry["key"],
        "aliases": list(dict.fromkeys([
            zh_entry["key"], *zh_entry["aliases"], en_entry["key"], *en_entry["aliases"]
        ])),
        "display": display,
        **{dimension: en_entry[dimension] for dimension in DIMENSIONS},
        "reason": {
            dimension: (
                f"zh: {zh_entry.get('reason', {}).get(dimension, '')}; "
                f"en: {en_entry.get('reason', {}).get(dimension, '')}"
            ).strip()
            for dimension in DIMENSIONS
        },
        "confidence": {
            dimension: min(
                float(zh_entry.get("confidence", {}).get(dimension, 0.0)),
                float(en_entry.get("confidence", {}).get(dimension, 0.0)),
            )
            for dimension in DIMENSIONS
        },
        "review": "llm_v1",
        "encoder_version": en_entry.get("encoder_version", zh_entry.get("encoder_version")),
    }
    return _normalized_entry(result, label)


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
    paired = [isinstance(entry, dict) and ("zh_entry" in entry or "en_entry" in entry) for entry in value]
    if any(paired):
        if not all(paired):
            raise MergeError("input JSON cannot mix complete entries and paired raw encodings")
        return [_paired_entry(entry, i) for i, entry in enumerate(value)]
    return [_normalized_entry(entry, f"input entry {i}") for i, entry in enumerate(value)]


def _read_dictionary(path: Path) -> list[dict]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise MergeError(f"invalid destination JSON: {exc}") from exc
    if not isinstance(value, list):
        raise MergeError("destination JSON must be an array")
    return [_normalized_entry(entry, f"existing entry {i}") for i, entry in enumerate(value)]


def merge(
    source: Path, destination: Path, replace_llm: bool = False
) -> tuple[int, int, list[dict]]:
    """Merge entries; replace_llm explicitly requests the existing default LLM replacement."""
    incoming = _read_source(source)
    _assert_unique(incoming, "incoming entries")
    existing = _read_dictionary(destination) if destination.exists() else []
    owner = _assert_unique(existing, "destination")

    skipped = 0
    changed_entries: set[str] = set()
    level_changes: list[tuple[str, str, str, str]] = []
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
            target = next(iter(matched))
            old_entry = result[target]
            for dimension in DIMENSIONS:
                if old_entry[dimension] != candidate[dimension]:
                    changed_entries.add(old_entry["key"])
                    level_changes.append(
                        (old_entry["key"], dimension, old_entry[dimension], candidate[dimension])
                    )
            result[target] = candidate
        else:
            result.append(candidate)
        owner = _assert_unique(result, "merged dictionary")
    result.sort(key=lambda entry: entry["key"])
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Entries changed level on any dimension: {len(changed_entries)}")
    if level_changes:
        print("key | dimension | old -> new")
        for key, dimension, old, new in level_changes:
            print(f"{key} | {dimension} | {old} -> {new}")
    return len(incoming) - skipped, skipped, result


def _print_split_list() -> None:
    for detail in AMBIGUOUS_NAMES.values():
        print(f"{detail['source_name']}:")
        for dish in detail["split_into"]:
            print(f"  - {dish['zh']} / {dish['en']}")


def _review_counts(entries: list[dict]) -> str:
    counts = Counter(entry["review"] for entry in entries)
    return "; ".join(f"{review}: {counts[review]}" for review in ("llm_v1", "human_checked", "proxy"))


def _sample(path: Path, count: int, seed: int | None) -> None:
    if count < 0:
        raise MergeError("--sample must be non-negative")
    entries = _read_dictionary(path)
    _assert_unique(entries, "destination")
    candidates = [entry for entry in entries if entry["review"] == "llm_v1"]
    if count > len(candidates):
        raise MergeError(f"--sample requested {count}, but only {len(candidates)} llm_v1 entries exist")
    print(_review_counts(entries))
    print("key | display zh / en | sugar | bitter | water | min confidence | one-line reasons")
    for entry in random.Random(seed).sample(candidates, count):
        display = entry.get("display", {})
        confidence = entry.get("confidence", {})
        reasons = entry.get("reason", {})
        one_line = "; ".join(
            f"{dimension}: {' '.join(str(reasons.get(dimension, '')).split())}"
            for dimension in DIMENSIONS
        ).replace("|", "\\|")
        print(
            f"{entry['key']} | {display.get('zh', '')} / {display.get('en', '')} | "
            f"{entry['sugar']} | {entry['bitter']} | {entry['water']} | "
            f"{min(float(confidence.get(dimension, 0.0)) for dimension in DIMENSIONS):.4f} | "
            f"{one_line}"
        )


def _mark_checked(path: Path, keys: list[str]) -> None:
    entries = _read_dictionary(path)
    _assert_unique(entries, "destination")
    requested = [normalize_name(key) for key in keys]
    by_key = {entry["key"]: entry for entry in entries}
    missing = [key for key in requested if key not in by_key]
    if missing:
        raise MergeError("cannot mark missing key(s): " + ", ".join(repr(key) for key in missing))
    for key in requested:
        by_key[key]["review"] = "human_checked"
    path.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Marked human_checked: " + ", ".join(requested))


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge encoded entries into the dish dictionary")
    parser.add_argument("source", nargs="?", type=Path)
    parser.add_argument("--into", type=Path, default=ROOT / "data" / "dishes.json")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--split-list", action="store_true")
    modes.add_argument("--sample", type=int, metavar="N")
    modes.add_argument("--mark-checked", nargs="+", metavar="KEY")
    parser.add_argument("--seed", type=int)
    parser.add_argument(
        "--replace-llm",
        action="store_true",
        help="replace matching llm_v1 entries even when encoder_version differs (the merge default)",
    )
    args = parser.parse_args()
    try:
        if args.split_list:
            _print_split_list()
        elif args.sample is not None:
            _sample(args.into, args.sample, args.seed)
        elif args.mark_checked is not None:
            _mark_checked(args.into, args.mark_checked)
        else:
            if args.source is None:
                parser.error("source is required unless --split-list, --sample, or --mark-checked is used")
            merged, skipped, result = merge(args.source, args.into, args.replace_llm)
            print(f"Merged {merged} entries; skipped {skipped}; dictionary count: {len(result)}")
    except (OSError, MergeError) as exc:
        parser.exit(1, f"merge error: {exc}\n")


if __name__ == "__main__":
    main()
