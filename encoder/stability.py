"""Measure repeat and cross-language stability of the dish encoder."""

from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

from .client import RESPONSE_SCHEMA_VERSION
from .encode import PROMPT_VERSION, _PROMPT_PATH_FOR, encode_dish
from .levels import LEVELS
from .normalize import normalize_name

DIMENSIONS = ("sugar", "bitter", "water")
ROOT = Path(__file__).resolve().parents[1]
FOODS_PATH = Path(__file__).with_name("foods_stability.json")
RAW_PATH = ROOT / "results" / "encoder" / "stability_raw.jsonl"
REPORT_PATH = ROOT / "docs" / "encoder_stability.md"


def _mode(values: list[str]) -> str | None:
    if not values:
        return None
    counts = Counter(values)
    return max(LEVELS, key=lambda level: (counts[level], -LEVELS.index(level)))


def _fake_entry(food: dict[str, str], prompt_version: str) -> dict:
    en = food["en"].lower()
    sugar = "none"
    bitter = "none"
    water = "low"
    if any(x in en for x in ("honey", "candy")):
        sugar = "very_high"
    elif any(x in en for x in ("cake", "ice cream", "bubble tea", "mooncake")):
        sugar = "high"
    elif any(x in en for x in ("cola", "sweet red bean", "orange juice")):
        sugar = "medium"
    elif any(x in en for x in ("fruit", "watermelon", "apple", "banana", "braised")):
        sugar = "low"
    if any(x in en for x in ("bitter melon", "espresso", "tonic")):
        bitter = "very_high"
    elif any(x in en for x in ("black coffee", "dark chocolate")):
        bitter = "high"
    elif "ipa beer" in en:
        bitter = "medium"
    elif any(x in en for x in ("green tea", "beer", "endive", "gai lan", "grapefruit", "latte")):
        bitter = "low"
    if prompt_version == "encode_v1":
        if en == "water" or en.endswith(" tea"):
            water = "very_high"
        elif any(x in en for x in ("juice", "milk", "cola", "beer", "coffee", "latte", "espresso", "tonic", "soup", "broth")):
            water = "high"
        elif any(x in en for x in ("mapo", "curry")):
            water = "medium"
        elif any(x in en for x in ("chips", "crackers", "nuts", "jerky")):
            water = "none"
    else:
        if any(x in en for x in ("bubble tea", "cola", "juice", "miso soup", "sauce")):
            water = "medium"
        elif en == "water" or en.endswith(" tea") or "clear broth" in en:
            water = "very_high"
        elif any(x in en for x in ("milk", "soup", "broth")):
            water = "high"
        elif any(x in en for x in ("chips", "crackers", "nuts", "jerky")):
            water = "none"
    return {
        "key": normalize_name(food["en"]),
        "aliases": [normalize_name(food["zh"]), normalize_name(food["en"])],
        "display": dict(food),
        "sugar": sugar,
        "bitter": bitter,
        "water": water,
        "reason": {dimension: "deterministic dry-run heuristic" for dimension in DIMENSIONS},
        "confidence": {dimension: 0.9 for dimension in DIMENSIONS},
        "review": "llm_v1",
        "encoder_version": f"dry-run@{prompt_version}",
    }


def _pct(value: float) -> str:
    return f"{100 * value:.1f}%"


def _markdown_cell(value: object) -> str:
    return " ".join(str(value).split()).replace("|", "\\|")


def _write_report(
    foods: list[dict[str, str]],
    records: list[dict],
    repeats: int,
    langs: list[str],
    model_id: str,
    encoder_version: str,
    prompt_version: str,
    dimensions: list[str],
    report_path: Path,
) -> None:
    grouped: dict[tuple[int, str], list[dict]] = defaultdict(list)
    for record in records:
        if "entry" in record:
            grouped[(record["food_index"], record["lang"])].append(record["entry"])

    modes: dict[tuple[int, str, str], str | None] = {}
    consistencies: dict[tuple[int, str, str], float] = {}
    for index in range(len(foods)):
        for lang in langs:
            for dimension in dimensions:
                values = [entry[dimension] for entry in grouped[(index, lang)]]
                modal = _mode(values)
                modes[(index, lang, dimension)] = modal
                consistencies[(index, lang, dimension)] = (
                    values.count(modal) / repeats if modal else 0.0
                )

    lines = [
        "# Encoder stability",
        "",
        f"- Model id: `{model_id}`",
        f"- Encoder version: `{encoder_version}`",
        f"- Prompt version: `{prompt_version}`",
        f"- Response schema version: `{RESPONSE_SCHEMA_VERSION}`",
        f"- Date: {datetime.now(timezone.utc).date().isoformat()}",
        f"- Foods: {len(foods)}",
        f"- Repeats: {repeats}",
        f"- Languages: {', '.join(langs)}",
        f"- Report dimensions: {', '.join(dimensions)}",
        f"- Total calls: {len(records)}",
        f"- Error count: {sum('error' in record for record in records)}",
        "",
        "## Cross-language agreement",
        "",
        "Headline metric: fraction of foods whose zh and en modal levels agree.",
        "",
        "| Dimension | Agreeing foods | Cross-language agreement |",
        "|---|---:|---:|",
    ]
    for dimension in dimensions:
        agreeing = 0
        if {"zh", "en"} <= set(langs):
            for index in range(len(foods)):
                zh_mode = modes[(index, "zh", dimension)]
                en_mode = modes[(index, "en", dimension)]
                agreeing += zh_mode is not None and zh_mode == en_mode
        total = len(foods)
        agreement = agreeing / total if total and {"zh", "en"} <= set(langs) else 0.0
        lines.append(f"| {dimension} | {agreeing}/{total} | {_pct(agreement)} |")

    lines.extend([
        "", "## Within-language consistency", "",
        "Errors have no level and count as zero consistency for their food/language group.",
        "",
        "| Dimension | Mean level-consistency | 100% consistent groups |",
        "|---|---:|---:|",
    ])
    for dimension in dimensions:
        group_scores = [
            consistencies[(index, lang, dimension)]
            for index in range(len(foods))
            for lang in langs
        ]
        perfect = sum(score == 1.0 for score in group_scores)
        mean = sum(group_scores) / len(group_scores) if group_scores else 0.0
        perfect_fraction = perfect / len(group_scores) if group_scores else 0.0
        lines.append(f"| {dimension} | {_pct(mean)} | {_pct(perfect_fraction)} |")

    lines.extend(["", "## Cross-language disagreements", ""])
    disagreements: list[str] = []
    if {"zh", "en"} <= set(langs):
        for index, food in enumerate(foods):
            for dimension in dimensions:
                zh_mode = modes[(index, "zh", dimension)]
                en_mode = modes[(index, "en", dimension)]
                if zh_mode is None or en_mode is None or zh_mode == en_mode:
                    continue

                def reason_example(lang: str, modal: str) -> str:
                    for entry in grouped[(index, lang)]:
                        if entry[dimension] == modal:
                            return _markdown_cell(entry["reason"][dimension])
                    return "—"

                disagreements.append(
                    f"| {_markdown_cell(food['zh'])} / {_markdown_cell(food['en'])} | "
                    f"{dimension} | {zh_mode} | {en_mode} | "
                    f"{reason_example('zh', zh_mode)} | {reason_example('en', en_mode)} |"
                )
    if disagreements:
        lines.extend([
            "| Food (zh / en) | Dimension | zh modal | en modal | zh reasons (one example) | en reason (one example) |",
            "|---|---|---|---|---|---|",
            *disagreements,
        ])
    else:
        lines.append("none")

    detail_header = ["Food (zh / en)"]
    detail_rule = ["---"]
    for dimension in dimensions:
        detail_header.extend((f"{dimension.title()} modal zh/en", f"{dimension.title()} consistency"))
        detail_rule.extend(("---", "---:"))
    detail_header.append("Flag")
    detail_rule.append("---")
    lines.extend([
        "", "## Food detail", "",
        "Consistency cells show `zh/en`; a dash means that language was not requested.", "",
        "| " + " | ".join(detail_header) + " |",
        "|" + "|".join(detail_rule) + "|",
    ])
    for index, food in enumerate(foods):
        row: list[str] = []
        mismatch = False
        for dimension in dimensions:
            lang_modes = [modes.get((index, lang, dimension)) for lang in ("zh", "en")]
            rendered_modes = "/".join(value or "—" for value in lang_modes)
            scores = [consistencies.get((index, lang, dimension)) for lang in ("zh", "en")]
            rendered_scores = "/".join(_pct(value) if value is not None else "—" for value in scores)
            mismatch |= all(value is not None for value in lang_modes) and lang_modes[0] != lang_modes[1]
            row.extend((rendered_modes, rendered_scores))
        lines.append(
            f"| {_markdown_cell(food['zh'])} / {_markdown_cell(food['en'])} | "
            + " | ".join(row)
            + f" | {'zh != en' if mismatch else ''} |"
        )

    liquid_words = ("water", "tea", "juice", "milk", "soup", "broth", "cola", "beer", "coffee", "latte", "espresso", "tonic")
    bitter_words = ("bitter melon", "black coffee", "espresso", "tonic", "dark chocolate")
    sugar_words = ("honey", "candy", "cake", "ice cream", "cola", "bubble tea", "cookies")
    flags = []
    for index, food in enumerate(foods):
        en = food["en"].lower()
        for lang in langs:
            tests = (
                ("water", liquid_words, "none despite liquid-name keyword"),
                ("bitter", bitter_words, "none despite bitter-case keyword"),
                ("sugar", sugar_words, "none despite sweet-case keyword"),
            )
            for dimension, words, message in tests:
                if (
                    dimension in dimensions
                    and any(re.search(rf"\b{re.escape(word)}\b", en, re.IGNORECASE) for word in words)
                    and modes.get((index, lang, dimension)) == "none"
                ):
                    flags.append(f"- {_markdown_cell(food['zh'])} / {_markdown_cell(food['en'])} ({lang}): {dimension} is {message}.")
    lines.extend([
        "", "## Obvious errors", "",
        "Heuristic keyword flags only; these are candidates for human review, not ground truth.", "",
    ])
    lines.extend(flags or ["No heuristic obvious errors found."])

    lines.extend(["", "## Errors", ""])
    errors = []
    for record in records:
        if "error" not in record:
            continue
        index = int(record["food_index"])
        food = foods[index] if 0 <= index < len(foods) else {"zh": "?", "en": f"index {index}"}
        errors.append(
            f"- {_markdown_cell(food['zh'])} / {_markdown_cell(food['en'])}; "
            f"lang={record['lang']}; repeat={record['repeat']}; "
            f"error={_markdown_cell(record['error'][:100])}"
        )
    lines.extend(errors or ["none"])
    lines.extend(["", "Purpose: estimate how much of the llm_v1 dictionary needs human review. Not a gate.", ""])
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")


def _read_records(raw_path: Path) -> list[dict]:
    if not raw_path.exists():
        raise FileNotFoundError(f"stability data not found: {raw_path}")
    return [json.loads(line) for line in raw_path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _atomic_write_records(records: list[dict], raw_path: Path) -> None:
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=raw_path.parent, delete=False, newline="\n"
        ) as raw_file:
            temp_path = raw_file.name
            for record in records:
                raw_file.write(json.dumps(record, ensure_ascii=False) + "\n")
            raw_file.flush()
            os.fsync(raw_file.fileno())
        os.replace(temp_path, raw_path)
    finally:
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)


def _run_observation(
    food: dict[str, str],
    food_index: int,
    lang: str,
    repeat: int,
    dry_run: bool,
    prompt_version: str,
) -> dict:
    started = time.perf_counter()
    record = {"food_index": food_index, "food": dict(food), "lang": lang, "repeat": repeat}
    configured_model = "dry-run" if dry_run else (os.getenv("ENCODER_MODEL") or "")
    try:
        entry = (
            _fake_entry(food, prompt_version)
            if dry_run
            else encode_dish(food[lang], lang, prompt_version)
        )
        record["entry"] = entry
        current_model = entry["encoder_version"].rsplit("@", 1)[0]
        version = entry["encoder_version"]
    except Exception as exc:
        record["error"] = f"{type(exc).__name__}: {exc}"
        current_model = configured_model
        version = f"{configured_model}@{prompt_version}"
    record.update({
        "latency_s": round(time.perf_counter() - started, 6),
        "model_id": current_model,
        "encoder_version": version,
        "prompt_version": prompt_version,
        "schema_version": RESPONSE_SCHEMA_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    return record


def _report_metadata(records: list[dict]) -> tuple[int, list[str], str, str]:
    repeats = max((int(record["repeat"]) for record in records), default=1)
    langs = [lang for lang in ("zh", "en") if any(record.get("lang") == lang for record in records)]
    model_ids = list(dict.fromkeys(
        str(record.get("model_id", "")) for record in records if record.get("model_id")
    ))
    versions = list(dict.fromkeys(
        str(record.get("encoder_version", "")) for record in records if record.get("encoder_version")
    ))
    return repeats, langs, ", ".join(model_ids), ", ".join(versions)


def _report_foods(configured_foods: list[dict[str, str]], records: list[dict]) -> list[dict[str, str]]:
    """Recover food labels from legacy rows when the configured list has since changed."""
    count = max((int(record["food_index"]) for record in records), default=-1) + 1
    foods = []
    for index in range(count):
        matching = [record for record in records if int(record["food_index"]) == index]
        explicit = next((record.get("food") for record in matching if record.get("food")), None)
        if explicit:
            foods.append(dict(explicit))
            continue
        food = dict(configured_foods[index])
        for lang in ("zh", "en"):
            for record in matching:
                if record.get("lang") != lang or "entry" not in record:
                    continue
                display = record["entry"].get("display", {})
                if isinstance(display.get(lang), str):
                    food[lang] = display[lang]
                    break
        foods.append(food)
    return foods


def main() -> None:
    parser = argparse.ArgumentParser(description="Run encoder stability measurements")
    parser.add_argument("--repeats", type=int, default=6)
    parser.add_argument("--langs", default="zh,en")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--retry-errors", action="store_true")
    parser.add_argument("--report-only", action="store_true")
    parser.add_argument(
        "--resume", action="store_true",
        help="reuse error-free observations already in --raw for the same prompt version and "
             "run only the missing (food, lang, repeat) cells",
    )
    parser.add_argument("--prompt-version", default=PROMPT_VERSION)
    parser.add_argument("--dimensions", default=",".join(DIMENSIONS))
    parser.add_argument("--raw", type=Path, default=RAW_PATH)
    parser.add_argument("--report", type=Path, default=REPORT_PATH)
    parser.add_argument("--foods", type=Path, default=FOODS_PATH, help="food list JSON (default: encoder/foods_stability.json)")
    args = parser.parse_args()
    if args.retry_errors and args.report_only:
        parser.error("--retry-errors and --report-only are mutually exclusive")
    if args.resume and (args.retry_errors or args.report_only):
        parser.error("--resume cannot be combined with --retry-errors or --report-only")
    if args.repeats < 1:
        parser.error("--repeats must be at least 1")
    langs = [value.strip() for value in args.langs.split(",") if value.strip()]
    if not langs or any(value not in ("zh", "en") for value in langs) or len(langs) != len(set(langs)):
        parser.error("--langs must be a unique comma-separated subset of zh,en")
    dimensions = [value.strip() for value in args.dimensions.split(",") if value.strip()]
    if (
        not dimensions
        or any(value not in DIMENSIONS for value in dimensions)
        or len(dimensions) != len(set(dimensions))
    ):
        parser.error("--dimensions must be a unique comma-separated subset of sugar,bitter,water")
    if (
        not re.fullmatch(r"encode_v[0-9]+(?:\.[0-9]+)?", args.prompt_version)
        or args.prompt_version not in _PROMPT_PATH_FOR
        or not _PROMPT_PATH_FOR[args.prompt_version].is_file()
    ):
        parser.error(f"unknown prompt version: {args.prompt_version}")

    foods = json.loads(args.foods.read_text(encoding="utf-8"))
    if args.limit is not None and not (args.retry_errors or args.report_only):
        if args.limit < 1:
            parser.error("--limit must be at least 1")
        foods = foods[: args.limit]

    if args.report_only:
        records = _read_records(args.raw)
        foods = _report_foods(foods, records)
        repeats, langs, model_id, encoder_version = _report_metadata(records)
        prompt_version = next(
            (str(record["prompt_version"]) for record in records if record.get("prompt_version")),
            args.prompt_version,
        )
        _write_report(
            foods, records, repeats, langs, model_id, encoder_version,
            prompt_version, dimensions, args.report,
        )
        print(f"Wrote report to {args.report}")
        return

    if not args.dry_run:
        load_dotenv(ROOT / ".env")

    if args.retry_errors:
        records = _read_records(args.raw)
        for record in records:
            record.setdefault(
                "prompt_version",
                str(record.get("encoder_version", "")).rsplit("@", 1)[-1]
                or args.prompt_version,
            )
        error_count = sum("error" in record for record in records)
        for position, old_record in enumerate(records):
            if "error" not in old_record:
                continue
            index = int(old_record["food_index"])
            records[position] = _run_observation(
                foods[index], index, old_record["lang"], int(old_record["repeat"]),
                args.dry_run, args.prompt_version,
            )
        _atomic_write_records(records, args.raw)
        repeats, langs, model_id, encoder_version = _report_metadata(records)
        report_foods = _report_foods(foods, records)
        _write_report(
            report_foods, records, repeats, langs, model_id, encoder_version,
            args.prompt_version, dimensions, args.report,
        )
        print(f"Retried {error_count} error observations in {args.raw}")
        print(f"Wrote report to {args.report}")
        return

    model_id = "dry-run" if args.dry_run else (os.getenv("ENCODER_MODEL") or "")
    existing: dict[tuple[int, str, int], dict] = {}
    if args.resume and args.raw.exists():
        for record in _read_records(args.raw):
            if "error" in record or record.get("prompt_version") != args.prompt_version:
                continue
            index = int(record["food_index"])
            if index >= len(foods) or record.get("food") != foods[index]:
                raise ValueError(
                    f"{args.raw}: food_index {index} does not match the configured food list"
                )
            existing[(index, str(record["lang"]), int(record["repeat"]))] = record
    records = []
    reused = 0
    args.raw.parent.mkdir(parents=True, exist_ok=True)
    with args.raw.open("a", encoding="utf-8") as raw_file:
        for index, food in enumerate(foods):
            for lang in langs:
                for repeat in range(1, args.repeats + 1):
                    previous = existing.get((index, lang, repeat))
                    if previous is not None:
                        records.append(previous)
                        reused += 1
                        continue
                    record = _run_observation(
                        food, index, lang, repeat, args.dry_run, args.prompt_version
                    )
                    raw_file.write(json.dumps(record, ensure_ascii=False) + "\n")
                    raw_file.flush()
                    records.append(record)
    encoder_version = next(
        (record["encoder_version"] for record in records), f"{model_id}@{args.prompt_version}"
    )
    _write_report(
        foods, records, args.repeats, langs, model_id, encoder_version,
        args.prompt_version, dimensions, args.report,
    )
    if args.resume:
        print(f"Reused {reused} existing observations; ran {len(records) - reused} new ones")
    print(f"Wrote {len(records)} observations to {args.raw}")
    print(f"Wrote report to {args.report}")


if __name__ == "__main__":
    main()
