"""Merge encoded dishes into the normalized JSON dictionary."""

from __future__ import annotations

import argparse
import json
import sys
import random
from collections import Counter, defaultdict
from pathlib import Path

from .levels import IR94E_LEVELS, LEVELS, levels_for
from .normalize import normalize_name

ROOT = Path(__file__).resolve().parents[1]
FOODS_PATH = Path(__file__).with_name("foods_stability.json")
AMBIGUOUS_PATH = ROOT / "data" / "ambiguous_names.json"
DIMENSIONS = ("sugar", "bitter", "water", "ir94e")
CORE_DIMENSIONS = ("sugar", "bitter", "water")
OPTIONAL_DIMENSIONS = ("ir94e",)
REVIEWS = {"llm_v1", "needs_review", "human_checked", "proxy", "draft"}  # draft: never merged, never published


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


def _mode(values: list[str], dimension: str) -> str:
    counts = Counter(values)
    allowed = levels_for(dimension)
    return max(allowed, key=lambda level: (counts[level], -allowed.index(level)))


def _normalized_entry(entry: object, label: str, *, require: tuple[str, ...] = ()) -> dict:
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
    for dimension in CORE_DIMENSIONS:
        if result.get(dimension) not in LEVELS:
            raise MergeError(f"{label} has invalid {dimension} level {result.get(dimension)!r}")
    if "ir94e" in result and result["ir94e"] not in IR94E_LEVELS:
        raise MergeError(f"{label} has invalid ir94e level {result['ir94e']!r}")
    for dimension in require:
        if dimension not in result:
            raise MergeError(
                f"{label} lacks {dimension} (required by --only-dimension {dimension})"
            )
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


def _modal_reason(
    records: list[dict], normalized: list[dict], dimension: str, modal: str
) -> str:
    """Return a real model reason for the selected level, preferring the English run."""
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


def _arbitrate_dimension(
    records: list[dict], normalized: list[dict], dimension: str
) -> tuple[str, dict[str, str] | None]:
    """Choose a level from per-language modes and describe any disagreement."""
    by_language = {
        lang: [
            entry
            for record, entry in zip(records, normalized)
            if record.get("lang") == lang
        ]
        for lang in ("zh", "en")
    }
    if not by_language["zh"] or not by_language["en"]:
        return _mode([entry[dimension] for entry in normalized], dimension), None

    zh_level = _mode([entry[dimension] for entry in by_language["zh"]], dimension)
    en_level = _mode([entry[dimension] for entry in by_language["en"]], dimension)
    if zh_level == en_level:
        return zh_level, None

    allowed = levels_for(dimension)
    distance = abs(allowed.index(zh_level) - allowed.index(en_level))
    if distance >= 2:
        chosen = en_level
        rule = "needs_review"
    else:
        mean_confidence = {
            lang: sum(
                float(entry.get("confidence", {}).get(dimension, 0.0))
                for entry in entries
            ) / len(entries)
            for lang, entries in by_language.items()
        }
        # Product-owner rule (2026-09-10): one step apart -> higher mean confidence;
        # if the confidences differ by less than 0.1, take the LOWER level.
        # Never default to English on a tie.
        if abs(mean_confidence["zh"] - mean_confidence["en"]) < 0.1:
            chosen = min((zh_level, en_level), key=allowed.index)
            rule = "lower_level"
        else:
            chosen = max(mean_confidence, key=mean_confidence.get)
            chosen = zh_level if chosen == "zh" else en_level
            rule = "confidence"
    return chosen, {"zh": zh_level, "en": en_level, "chosen": chosen, "rule": rule}


FOODS_OVERRIDE: Path | None = None
STABILITY_LANGS: tuple[str, ...] = ("zh", "en")
STABILITY_REPEATS = 6


def validate_stability(records: list[object], foods: list[dict], langs=None, repeats=None) -> list[str]:
    """Problems that make a stability batch unfit for merging (D07): every food needs
    `repeats` distinct repeat ids per language, error rows do not count, and the
    batch must carry one encoder/prompt/schema version. Empty list = complete."""
    langs = tuple(langs or STABILITY_LANGS)
    repeats = int(repeats or STABILITY_REPEATS)
    problems: list[str] = []
    seen: dict[tuple[int, str], list[int]] = defaultdict(list)
    versions: Counter = Counter()
    prompts: Counter = Counter()
    schemas: Counter = Counter()
    errors = 0
    for row, record in enumerate(records, 1):
        if not isinstance(record, dict):
            problems.append(f"row {row}: not an object")
            continue
        if "error" in record or "entry" not in record:
            errors += 1
            continue
        try:
            key = (int(record["food_index"]), str(record["lang"]))
            repeat = int(record["repeat"])
        except (KeyError, TypeError, ValueError):
            problems.append(f"row {row}: invalid food_index / lang / repeat")
            continue
        seen[key].append(repeat)
        versions[record.get("encoder_version")] += 1
        prompts[record.get("prompt_version")] += 1
        schemas[record.get("schema_version")] += 1
    if errors:
        problems.append(f"{errors} error rows (not counted as samples)")
    expected = set(range(1, repeats + 1))
    for index in range(len(foods)):
        for lang in langs:
            reps = seen.get((index, lang), [])
            dup = sorted(r for r, c in Counter(reps).items() if c > 1)
            if dup:
                problems.append(f"food {index} {lang}: duplicate repeat ids {dup}")
            missing = sorted(expected - set(reps))
            if missing:
                problems.append(f"food {index} {lang}: missing repeats {missing} ({len(set(reps) & expected)}/{repeats})")
            extra = sorted(set(reps) - expected)
            if extra:
                problems.append(f"food {index} {lang}: repeat ids outside 1..{repeats}: {extra}")
    for name, counter in (("encoder_version", versions), ("prompt_version", prompts), ("schema_version", schemas)):
        if None in counter:
            problems.append(f"records without {name}")
        if len(counter) > 1:
            problems.append(f"mixed {name}: {dict(counter)}")
    return problems


def _from_stability(
    records: list[object], draft: bool = False, require: tuple[str, ...] = ()
) -> list[dict]:
    foods = json.loads((FOODS_OVERRIDE or FOODS_PATH).read_text(encoding="utf-8"))
    problems = validate_stability(records, foods)
    if problems and not draft:
        shown = "\n  ".join(problems[:25])
        more = f"\n  ... {len(problems) - 25} more" if len(problems) > 25 else ""
        raise MergeError(
            "stability batch incomplete or mixed; it cannot be merged (use --draft PATH to write a draft):\n  "
            + shown + more
        )
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
            _normalized_entry(
                record["entry"], f"food_index {food_index} result", require=require
            )
            for record in food_records
        ]
        dimensions = [
            dimension
            for dimension in DIMENSIONS
            if all(dimension in entry for entry in normalized)
        ]
        aliases = [food["zh"], food["en"]]
        for entry in normalized:
            aliases.extend([entry["key"], *entry["aliases"]])
        aliases = list(dict.fromkeys(filter(None, (normalize_name(x) for x in aliases))))
        key = normalize_name(food.get("key") or food["en"])
        encoder_version = Counter(
            record.get("encoder_version")
            or entry.get("encoder_version", "unknown@encode_v1")
            for record, entry in zip(food_records, normalized)
        ).most_common(1)[0][0]
        levels = {}
        arbitration = {}
        for dimension in dimensions:
            levels[dimension], detail = _arbitrate_dimension(
                food_records, normalized, dimension
            )
            if detail is not None:
                arbitration[dimension] = detail
        result = {
            "key": key,
            "aliases": aliases,
            "display": {"zh": food["zh"], "en": food["en"]},
            **levels,
            "reason": {
                dimension: _modal_reason(
                    food_records, normalized, dimension, levels[dimension]
                )
                for dimension in dimensions
            },
            "confidence": {
                dimension: round(
                    sum(float(e.get("confidence", {}).get(dimension, 0.0)) for e in normalized)
                    / len(normalized),
                    4,
                )
                for dimension in dimensions
            },
            "review": (
                "needs_review"
                if any(detail["rule"] == "needs_review" for detail in arbitration.values())
                else "llm_v1"
            ),
            "encoder_version": encoder_version,
        }
        if arbitration:
            result["arbitration"] = arbitration
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


def _paired_entry(pair: dict, index: int, require: tuple[str, ...] = ()) -> dict:
    label = f"paired input {index}"
    if set(pair) != {"zh_entry", "en_entry"}:
        raise MergeError(f"{label} must contain exactly zh_entry and en_entry")
    zh_entry = _normalized_entry(pair["zh_entry"], f"{label} zh_entry", require=require)
    en_entry = _normalized_entry(pair["en_entry"], f"{label} en_entry", require=require)
    dimensions = [
        dimension for dimension in DIMENSIONS
        if dimension in zh_entry and dimension in en_entry
    ]
    disagreements = [
        f"{dimension}: zh={zh_entry[dimension]!r}, en={en_entry[dimension]!r}"
        for dimension in dimensions
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
        **{dimension: en_entry[dimension] for dimension in dimensions},
        "reason": {
            dimension: (
                f"zh: {zh_entry.get('reason', {}).get(dimension, '')}; "
                f"en: {en_entry.get('reason', {}).get(dimension, '')}"
            ).strip()
            for dimension in dimensions
        },
        "confidence": {
            dimension: min(
                float(zh_entry.get("confidence", {}).get(dimension, 0.0)),
                float(en_entry.get("confidence", {}).get(dimension, 0.0)),
            )
            for dimension in dimensions
        },
        "review": "llm_v1",
        "encoder_version": en_entry.get("encoder_version", zh_entry.get("encoder_version")),
    }
    return _normalized_entry(result, label)


def _read_source(
    path: Path, draft: bool = False, require: tuple[str, ...] = ()
) -> list[dict]:
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
        return _from_stability(records, draft=draft, require=require)
    if not isinstance(value, list):
        raise MergeError("input JSON must be an array of entries")
    paired = [isinstance(entry, dict) and ("zh_entry" in entry or "en_entry" in entry) for entry in value]
    if any(paired):
        if not all(paired):
            raise MergeError("input JSON cannot mix complete entries and paired raw encodings")
        return [_paired_entry(entry, i, require=require) for i, entry in enumerate(value)]
    return [
        _normalized_entry(entry, f"input entry {i}", require=require)
        for i, entry in enumerate(value)
    ]


def _read_dictionary(path: Path) -> list[dict]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise MergeError(f"invalid destination JSON: {exc}") from exc
    if not isinstance(value, list):
        raise MergeError("destination JSON must be an array")
    return [_normalized_entry(entry, f"existing entry {i}") for i, entry in enumerate(value)]


def write_draft(source: Path, draft_path: Path) -> int:
    """Write the entries an incomplete or mixed stability batch would produce, marked
    review = "draft", to `draft_path`. A draft never enters the dictionary: merge()
    rejects entries with that review value (D07)."""
    entries = _read_source(source, draft=True)
    for entry in entries:
        entry["review"] = "draft"
    draft_path.parent.mkdir(parents=True, exist_ok=True)
    draft_path.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return len(entries)


def merge(
    source: Path,
    destination: Path,
    replace_llm: bool = False,
    arbitration_report: bool = False,
    only_dimension: str | None = None,
) -> tuple[int, int, list[dict]]:
    """Merge entries; replace_llm explicitly requests the existing default LLM replacement."""
    if only_dimension is not None and only_dimension not in OPTIONAL_DIMENSIONS:
        raise MergeError(
            f"--only-dimension must be one of {', '.join(OPTIONAL_DIMENSIONS)}"
        )
    require = (only_dimension,) if only_dimension else ()
    incoming = _read_source(source, require=require)
    drafts = [entry["key"] for entry in incoming if entry.get("review") == "draft"]
    if drafts:
        raise MergeError(f"draft entries cannot be merged (re-encode a complete batch): {drafts[:10]}")
    existing = _read_dictionary(destination) if destination.exists() else []
    owner = _assert_unique(existing, "destination")
    # Aliases the model proposed that already name another entry (existing, or earlier
    # in this batch) are dropped, so one name never points at two dishes.
    taken: dict[str, str] = {name: result_key for name, result_key in
                             ((normalize_name(n), e["key"]) for e in existing for n in _names(e))}
    for candidate in incoming:
        own = {normalize_name(candidate["key"]), *(normalize_name(v) for v in candidate.get("display", {}).values())}
        kept = []
        for alias in candidate.get("aliases", []):
            other = taken.get(normalize_name(alias))
            if other and other != candidate["key"] and normalize_name(alias) not in own:
                print(f"dropped alias {alias!r} from {candidate['key']!r}: already names {other!r}")
                continue
            kept.append(alias)
        candidate["aliases"] = kept
        for name in _names(candidate):
            taken.setdefault(normalize_name(name), candidate["key"])
    _assert_unique(incoming, "incoming entries")

    if only_dimension:
        matches = []
        for candidate in incoming:
            matched = {owner[name] for name in _names(candidate) if name in owner}
            if not matched:
                raise MergeError(
                    f"--only-dimension {only_dimension}: {candidate['key']!r} is not in "
                    "the dictionary; encode it fully instead"
                )
            if len(matched) > 1:
                targets = ", ".join(repr(existing[i]["key"]) for i in sorted(matched))
                raise MergeError(
                    f"incoming {candidate['key']!r} maps to multiple existing entries: {targets}"
                )
            matches.append(next(iter(matched)))

        changed_entries: set[str] = set()
        level_changes: list[tuple[str, str, str, str]] = []
        for candidate, target in zip(incoming, matches):
            current = existing[target]
            old_level = current.get(only_dimension, "(absent)")
            new_level = candidate[only_dimension]
            if old_level != new_level:
                changed_entries.add(current["key"])
                level_changes.append((current["key"], only_dimension, old_level, new_level))
            if only_dimension not in current:
                rebuilt = {}
                for key, value in current.items():
                    rebuilt[key] = value
                    if key == "water":
                        rebuilt[only_dimension] = None
                current.clear()
                current.update(rebuilt)
            current[only_dimension] = new_level
            current.setdefault("reason", {})[only_dimension] = candidate["reason"][only_dimension]
            current.setdefault("confidence", {})[only_dimension] = candidate["confidence"][only_dimension]

            candidate_detail = candidate.get("arbitration", {}).get(only_dimension)
            if candidate_detail is not None:
                current.setdefault("arbitration", {})[only_dimension] = candidate_detail
            elif "arbitration" in current:
                current["arbitration"].pop(only_dimension, None)
                if not current["arbitration"]:
                    del current["arbitration"]

            version_map = current.get("encoder_version_by_dimension")
            if version_map is None:
                rebuilt = {}
                for key, value in current.items():
                    rebuilt[key] = value
                    if key == "encoder_version":
                        rebuilt["encoder_version_by_dimension"] = {}
                current.clear()
                current.update(rebuilt)
                version_map = current["encoder_version_by_dimension"]
            version_map[only_dimension] = candidate["encoder_version"]

            rule = candidate_detail.get("rule") if candidate_detail else None
            if rule == "needs_review" and current["review"] == "llm_v1":
                current["review"] = "needs_review"
            if current["review"] == "human_checked":
                print(
                    f"filled {only_dimension} on human_checked entry {current['key']!r}: "
                    f"{new_level} (rule: {rule or 'agreed'})"
                )

        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            json.dumps(existing, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"Entries changed level on any dimension: {len(changed_entries)}")
        if level_changes:
            print("key | dimension | old -> new")
            for key, dimension, old, new in level_changes:
                print(f"{key} | {dimension} | {old} -> {new}")
        if arbitration_report:
            print("dish | dimension | zh | en | chosen | rule")
            for entry in incoming:
                for dimension, detail in entry.get("arbitration", {}).items():
                    print(
                        f"{entry['key']} | {dimension} | {detail['zh']} | {detail['en']} | "
                        f"{detail['chosen']} | {detail['rule']}"
                    )
        return len(incoming), 0, existing

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
                if dimension in old_entry and dimension not in candidate:
                    # A full re-encode at a prompt without this dimension removes it;
                    # scripts/validate_release.py refuses to publish such a dictionary.
                    print(f"dropped {dimension} from {old_entry['key']!r}: incoming batch has no {dimension}")
                    changed_entries.add(old_entry["key"])
                    level_changes.append((old_entry["key"], dimension, old_entry[dimension], "(absent)"))
                    continue
                if (
                    dimension in old_entry
                    and dimension in candidate
                    and old_entry[dimension] != candidate[dimension]
                ):
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
    if arbitration_report:
        print("dish | dimension | zh | en | chosen | rule")
        for entry in incoming:
            for dimension, detail in entry.get("arbitration", {}).items():
                print(
                    f"{entry['key']} | {dimension} | {detail['zh']} | {detail['en']} | "
                    f"{detail['chosen']} | {detail['rule']}"
                )
    return len(incoming) - skipped, skipped, result


def _print_split_list() -> None:
    for detail in AMBIGUOUS_NAMES.values():
        print(f"{detail['source_name']}:")
        for dish in detail["split_into"]:
            print(f"  - {dish['zh']} / {dish['en']}")


def _review_counts(entries: list[dict]) -> str:
    counts = Counter(entry["review"] for entry in entries)
    return "; ".join(
        f"{review}: {counts[review]}"
        for review in ("llm_v1", "needs_review", "human_checked", "proxy")
    )


def _sample(path: Path, count: int, seed: int | None) -> None:
    if count < 0:
        raise MergeError("--sample must be non-negative")
    entries = _read_dictionary(path)
    _assert_unique(entries, "destination")
    needs_review = [entry for entry in entries if entry["review"] == "needs_review"]
    llm_entries = [entry for entry in entries if entry["review"] == "llm_v1"]
    candidates = [*needs_review, *llm_entries]
    if count > len(candidates):
        raise MergeError(
            f"--sample requested {count}, but only {len(candidates)} review candidates exist"
        )
    rng = random.Random(seed)
    selected_needs_review = rng.sample(needs_review, min(count, len(needs_review)))
    selected_llm = rng.sample(llm_entries, count - len(selected_needs_review))
    print(_review_counts(entries))
    print("review | key | display zh / en | sugar | bitter | water | ir94e | min confidence | one-line reasons")
    for entry in [*selected_needs_review, *selected_llm]:
        display = entry.get("display", {})
        confidence = entry.get("confidence", {})
        reasons = entry.get("reason", {})
        one_line = "; ".join(
            f"{dimension}: {' '.join(str(reasons.get(dimension, '')).split())}"
            for dimension in DIMENSIONS
        ).replace("|", "\\|")
        print(
            f"{entry['review']} | {entry['key']} | {display.get('zh', '')} / {display.get('en', '')} | "
            f"{entry['sugar']} | {entry['bitter']} | {entry['water']} | "
            f"{entry.get('ir94e', '-')} | "
            f"{min(float(confidence.get(dimension, 0.0)) for dimension in CORE_DIMENSIONS):.4f} | "
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
        if by_key[key]["review"] not in {"llm_v1", "needs_review"}:
            raise MergeError(
                f"cannot mark {key!r}: review is {by_key[key]['review']!r}, "
                "expected llm_v1 or needs_review"
            )
        by_key[key]["review"] = "human_checked"
    path.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Marked human_checked: " + ", ".join(requested))


def main() -> None:
    global FOODS_OVERRIDE, STABILITY_REPEATS, STABILITY_LANGS
    parser = argparse.ArgumentParser(description="Merge encoded entries into the dish dictionary")
    parser.add_argument("source", nargs="?", type=Path)
    parser.add_argument("--into", type=Path, default=ROOT / "data" / "dishes.json")
    parser.add_argument("--foods", type=Path, help="food list the raw JSONL was produced from (default: encoder/foods_stability.json)")
    parser.add_argument("--repeats", type=int, default=STABILITY_REPEATS, help="repeats per food and language a stability batch must have")
    parser.add_argument("--langs", default=",".join(STABILITY_LANGS), help="languages a stability batch must cover")
    parser.add_argument("--draft", type=Path, metavar="PATH", help="write an incomplete/mixed batch as a draft file instead of merging")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--split-list", action="store_true")
    modes.add_argument("--sample", type=int, metavar="N")
    modes.add_argument("--mark-checked", nargs="+", metavar="KEY")
    parser.add_argument("--seed", type=int)
    parser.add_argument(
        "--replace-llm",
        action="store_true",
        help="replace matching llm_v1 and needs_review entries (the merge default)",
    )
    parser.add_argument(
        "--arbitration-report",
        action="store_true",
        help="print every cross-language arbitration performed by the merge",
    )
    parser.add_argument(
        "--only-dimension",
        choices=OPTIONAL_DIMENSIONS,
        help="write only this dimension (level, reason, confidence, arbitration, "
             "encoder_version_by_dimension) into entries that already exist; every other "
             "field is left untouched",
    )
    args = parser.parse_args()
    FOODS_OVERRIDE = args.foods
    STABILITY_REPEATS = args.repeats
    STABILITY_LANGS = tuple(part.strip() for part in args.langs.split(",") if part.strip())
    if args.draft:
        if args.source is None:
            parser.error("--draft needs a source")
        try:
            count = write_draft(args.source, args.draft)
        except MergeError as exc:
            print(f"error: {exc}")
            sys.exit(1)
        print(f"Wrote {count} draft entries to {args.draft} (review = draft; not merged)")
        return
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
            merged, skipped, result = merge(
                args.source, args.into, args.replace_llm, args.arbitration_report,
                args.only_dimension,
            )
            print(f"Merged {merged} entries; skipped {skipped}; dictionary count: {len(result)}")
    except (OSError, MergeError) as exc:
        parser.exit(1, f"merge error: {exc}\n")


if __name__ == "__main__":
    main()
