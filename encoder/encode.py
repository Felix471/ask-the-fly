"""Encode one dish with Gemini and validate its v1 schema."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Literal

from .client import GeminiEncoder
from .levels import LEVELS
from .normalize import normalize_name

PROMPT_VERSION = "encode_v1"
_PROMPT_PATH = Path(__file__).parent / "prompts" / f"{PROMPT_VERSION}.md"
_DIMENSIONS = ("sugar", "bitter", "water")
_MODEL_FIELDS = {"key", "aliases", "display", *_DIMENSIONS, "reason", "confidence"}


def _validate_model_entry(value: object, model_id: str) -> dict:
    if not isinstance(value, dict) or set(value) != _MODEL_FIELDS:
        raise ValueError(f"response fields must be exactly {sorted(_MODEL_FIELDS)}")
    key = normalize_name(value["key"])
    if not key:
        raise ValueError("key must be non-empty")
    aliases = value["aliases"]
    if not isinstance(aliases, list) or not all(isinstance(x, str) for x in aliases):
        raise ValueError("aliases must be a list of strings")
    display = value["display"]
    if not isinstance(display, dict) or set(display) != {"zh", "en"} or not all(
        isinstance(display[x], str) for x in ("zh", "en")
    ):
        raise ValueError("display must contain string zh and en fields")
    reason = value["reason"]
    confidence = value["confidence"]
    if not isinstance(reason, dict) or set(reason) != set(_DIMENSIONS):
        raise ValueError("reason must contain exactly sugar, bitter, and water")
    if not isinstance(confidence, dict) or set(confidence) != set(_DIMENSIONS):
        raise ValueError("confidence must contain exactly sugar, bitter, and water")
    for dimension in _DIMENSIONS:
        if value[dimension] not in LEVELS:
            raise ValueError(f"invalid {dimension} level: {value[dimension]!r}")
        if not isinstance(reason[dimension], str) or not reason[dimension].strip():
            raise ValueError(f"reason.{dimension} must be a non-empty string")
        score = confidence[dimension]
        if isinstance(score, bool) or not isinstance(score, (int, float)) or not 0 <= score <= 1:
            raise ValueError(f"confidence.{dimension} must be between 0 and 1")
    entry = dict(value)
    entry["key"] = key
    entry["aliases"] = list(dict.fromkeys(filter(None, (normalize_name(x) for x in aliases))))
    entry["review"] = "llm_v1"
    entry["encoder_version"] = f"{model_id}@{PROMPT_VERSION}"
    return entry


def encode_dish(name: str, lang: Literal["zh", "en"]) -> dict:
    if lang not in ("zh", "en"):
        raise ValueError("lang must be 'zh' or 'en'")
    if not normalize_name(name):
        raise ValueError("name must be non-empty")
    client = GeminiEncoder()
    template = _PROMPT_PATH.read_text(encoding="utf-8")
    prompt = template.replace("{dish}", name).replace("{input_language}", lang)
    last_error: Exception | None = None
    for _ in range(2):
        try:
            return _validate_model_entry(json.loads(client.generate(prompt)), client.model_id)
        except (json.JSONDecodeError, ValueError, TypeError, KeyError) as exc:
            last_error = exc
    raise ValueError(f"model output failed validation twice: {last_error}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Encode one dish into v1 taste levels")
    parser.add_argument("name")
    parser.add_argument("--lang", choices=("zh", "en"), required=True)
    args = parser.parse_args()
    print(json.dumps(encode_dish(args.name, args.lang), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
