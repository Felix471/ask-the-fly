"""Measure repeat and cross-language stability of the v1 encoder."""

from __future__ import annotations

import argparse
import json
import os
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

from .encode import PROMPT_VERSION, encode_dish
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


def _fake_entry(food: dict[str, str]) -> dict:
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
    if en == "water" or en.endswith(" tea"):
        water = "very_high"
    elif any(x in en for x in ("juice", "milk", "cola", "beer", "coffee", "latte", "espresso", "tonic", "soup", "broth")):
        water = "high"
    elif any(x in en for x in ("mapo", "curry")):
        water = "medium"
    elif any(x in en for x in ("chips", "crackers", "nuts", "jerky")):
        water = "none"
    return {
        "key": normalize_name(food["en"]),
        "aliases": [normalize_name(food["zh"]), normalize_name(food["en"])],
        "display": dict(food),
        "sugar": sugar,
        "bitter": bitter,
        "water": water,
        "reason": {d: "deterministic dry-run heuristic" for d in DIMENSIONS},
        "confidence": {d: 0.9 for d in DIMENSIONS},
        "review": "llm_v1",
        "encoder_version": f"dry-run@{PROMPT_VERSION}",
    }


def _pct(value: float) -> str:
    return f"{100 * value:.1f}%"


def _write_report(
    foods: list[dict[str, str]], records: list[dict], repeats: int, langs: list[str],
    model_id: str, encoder_version: str,
) -> None:
    grouped: dict[tuple[int, str], list[dict]] = defaultdict(list)
    for record in records:
        if "entry" in record:
            grouped[(record["food_index"], record["lang"])].append(record["entry"])
    modes: dict[tuple[int, str, str], str | None] = {}
    consistencies: dict[tuple[int, str, str], float] = {}
    lines = [
        "# Encoder stability",
        "",
        f"- Model id: `{model_id}`",
        f"- Encoder version: `{encoder_version}`",
        f"- Prompt version: `{PROMPT_VERSION}`",
        f"- Date: {datetime.now(timezone.utc).date().isoformat()}",
        f"- Foods: {len(foods)}",
        f"- Repeats: {repeats}",
        f"- Languages: {', '.join(langs)}",
        f"- Total calls: {len(records)}",
        f"- Error count: {sum('error' in r for r in records)}",
        "",
        "## Stability summary",
        "",
        "Errors have no level and count as zero consistency for their food/language group.",
        "",
        "| Dimension | Mean level-consistency | 100% consistent groups | Cross-language modal agreement |",
        "|---|---:|---:|---:|",
    ]
    for dimension in DIMENSIONS:
        group_scores = []
        perfect = 0
        for index in range(len(foods)):
            for lang in langs:
                values = [e[dimension] for e in grouped[(index, lang)]]
                modal = _mode(values)
                score = values.count(modal) / repeats if modal else 0.0
                modes[(index, lang, dimension)] = modal
                consistencies[(index, lang, dimension)] = score
                group_scores.append(score)
                perfect += score == 1.0
        comparable = 0
        agreeing = 0
        if "zh" in langs and "en" in langs:
            for index in range(len(foods)):
                zh = modes[(index, "zh", dimension)]
                en = modes[(index, "en", dimension)]
                if zh is not None and en is not None:
                    comparable += 1
                    agreeing += zh == en
        cross = agreeing / comparable if comparable else 0.0
        lines.append(
            f"| {dimension} | {_pct(sum(group_scores) / len(group_scores))} | "
            f"{_pct(perfect / len(group_scores))} | {_pct(cross)} |"
        )
    lines.extend([
        "", "## Food detail", "",
        "Consistency cells show `zh/en`; a dash means that language was not requested.", "",
        "| Food (zh / en) | Sugar modal zh/en | Sugar consistency | Bitter modal zh/en | Bitter consistency | Water modal zh/en | Water consistency | Flag |",
        "|---|---|---:|---|---:|---|---:|---|",
    ])
    for index, food in enumerate(foods):
        row = []
        mismatch = False
        for dimension in DIMENSIONS:
            lang_modes = [modes.get((index, lang, dimension)) for lang in ("zh", "en")]
            rendered_modes = "/".join(x or "—" for x in lang_modes)
            scores = [consistencies.get((index, lang, dimension)) for lang in ("zh", "en")]
            rendered_scores = "/".join(_pct(x) if x is not None else "—" for x in scores)
            mismatch |= all(x is not None for x in lang_modes) and lang_modes[0] != lang_modes[1]
            row.extend((rendered_modes, rendered_scores))
        lines.append(
            f"| {food['zh']} / {food['en']} | {row[0]} | {row[1]} | {row[2]} | "
            f"{row[3]} | {row[4]} | {row[5]} | {'zh != en' if mismatch else ''} |"
        )
    liquid_words = ("water", "tea", "juice", "milk", "soup", "broth", "cola", "beer", "coffee", "latte", "espresso", "tonic")
    bitter_words = ("bitter melon", "black coffee", "espresso", "tonic", "dark chocolate")
    sugar_words = ("honey", "candy", "cake", "ice cream", "cola", "bubble tea")
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
                if any(word in en for word in words) and modes.get((index, lang, dimension)) == "none":
                    flags.append(f"- {food['zh']} / {food['en']} ({lang}): {dimension} is {message}.")
    lines.extend(["", "## Obvious errors", "", "Heuristic keyword flags only; these are candidates for human review, not ground truth.", ""])
    lines.extend(flags or ["No heuristic obvious errors found."])
    lines.extend(["", "Purpose: estimate how much of the llm_v1 dictionary needs human review. Not a gate.", ""])
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run encoder stability measurements")
    parser.add_argument("--repeats", type=int, default=6)
    parser.add_argument("--langs", default="zh,en")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error("--repeats must be at least 1")
    langs = [x.strip() for x in args.langs.split(",") if x.strip()]
    if not langs or any(x not in ("zh", "en") for x in langs) or len(langs) != len(set(langs)):
        parser.error("--langs must be a unique comma-separated subset of zh,en")
    foods = json.loads(FOODS_PATH.read_text(encoding="utf-8"))
    if args.limit is not None:
        if args.limit < 1:
            parser.error("--limit must be at least 1")
        foods = foods[: args.limit]
    load_dotenv()
    model_id = "dry-run" if args.dry_run else (os.getenv("ENCODER_MODEL") or "")
    records = []
    RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
    with RAW_PATH.open("a", encoding="utf-8") as raw_file:
        for index, food in enumerate(foods):
            for lang in langs:
                for repeat in range(1, args.repeats + 1):
                    started = time.perf_counter()
                    record = {"food_index": index, "lang": lang, "repeat": repeat}
                    try:
                        entry = _fake_entry(food) if args.dry_run else encode_dish(food[lang], lang)
                        record["entry"] = entry
                        current_model = entry["encoder_version"].rsplit("@", 1)[0]
                        version = entry["encoder_version"]
                    except Exception as exc:
                        record["error"] = f"{type(exc).__name__}: {exc}"
                        current_model = model_id
                        version = f"{model_id}@{PROMPT_VERSION}"
                    record.update({
                        "latency_s": round(time.perf_counter() - started, 6),
                        "model_id": current_model,
                        "encoder_version": version,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })
                    raw_file.write(json.dumps(record, ensure_ascii=False) + "\n")
                    raw_file.flush()
                    records.append(record)
    encoder_version = next((r["encoder_version"] for r in records), f"{model_id}@{PROMPT_VERSION}")
    _write_report(foods, records, args.repeats, langs, model_id, encoder_version)
    print(f"Wrote {len(records)} observations to {RAW_PATH}")
    print(f"Wrote report to {REPORT_PATH}")


if __name__ == "__main__":
    main()
