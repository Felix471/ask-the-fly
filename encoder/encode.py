"""Encode one dish with Gemini and validate its taste-level schema."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Literal

from .levels import levels_for, prompt_has_ir94e
from .normalize import normalize_name

PROMPT_VERSION = "encode_v2.3"
_PROMPTS_DIR = Path(__file__).parent / "prompts"
_PROMPT_PATH_FOR = {
    version: _PROMPTS_DIR / f"{version.replace('.', '_')}.md"
    for version in ("encode_v1", "encode_v2", "encode_v2.1", "encode_v2.2", "encode_v2.3")
}
_DIMENSIONS = ("sugar", "bitter", "water", "ir94e")


def dimensions_for(prompt_version: str) -> tuple[str, ...]:
    return _DIMENSIONS if prompt_has_ir94e(prompt_version) else _DIMENSIONS[:3]


def _loads_model_json(text: str) -> object:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        cleaned = re.sub(r",(?=\s*[}\]])", "", text)
        if cleaned == text:
            raise
        return json.loads(cleaned)


def _validate_model_entry(value: object, model_id: str, prompt_version: str = PROMPT_VERSION) -> dict:
    dimensions = dimensions_for(prompt_version)
    model_fields = {"key", "aliases", "display", *dimensions, "reason", "confidence"}
    if not isinstance(value, dict) or not model_fields <= set(value):
        raise ValueError(f"response must contain fields {sorted(model_fields)}")
    value = {field: value[field] for field in model_fields}
    key = normalize_name(value["key"])
    if not key:
        raise ValueError("key must be non-empty")
    aliases = value["aliases"]
    if not isinstance(aliases, list) or not all(isinstance(x, str) for x in aliases):
        raise ValueError("aliases must be a list of strings")
    display = value["display"]
    if not isinstance(display, dict) or not {"zh", "en"} <= set(display) or not all(
        isinstance(display[x], str) for x in ("zh", "en")
    ):
        raise ValueError("display must contain string zh and en fields")
    reason = value["reason"]
    confidence = value["confidence"]
    required_dimensions = ", ".join(dimensions)
    if not isinstance(reason, dict) or not set(dimensions) <= set(reason):
        raise ValueError(f"reason must contain {required_dimensions}")
    if not isinstance(confidence, dict) or not set(dimensions) <= set(confidence):
        raise ValueError(f"confidence must contain {required_dimensions}")
    for dimension in dimensions:
        if value[dimension] not in levels_for(dimension):
            raise ValueError(f"invalid {dimension} level: {value[dimension]!r}")
        if not isinstance(reason[dimension], str) or not reason[dimension].strip():
            raise ValueError(f"reason.{dimension} must be a non-empty string")
        score = confidence[dimension]
        if isinstance(score, bool) or not isinstance(score, (int, float)) or not 0 <= score <= 1:
            raise ValueError(f"confidence.{dimension} must be between 0 and 1")
    entry = dict(value)
    entry["key"] = key
    entry["aliases"] = list(dict.fromkeys(filter(None, (normalize_name(x) for x in aliases))))
    entry["display"] = {field: display[field] for field in ("zh", "en")}
    entry["reason"] = {dimension: reason[dimension] for dimension in dimensions}
    entry["confidence"] = {dimension: confidence[dimension] for dimension in dimensions}
    entry["review"] = "llm_v1"
    entry["encoder_version"] = f"{model_id}@{prompt_version}"
    return entry


def encode_dish(
    name: str, lang: Literal["zh", "en"], prompt_version: str | None = None
) -> dict:
    if lang not in ("zh", "en"):
        raise ValueError("lang must be 'zh' or 'en'")
    if not normalize_name(name):
        raise ValueError("name must be non-empty")
    selected_prompt = prompt_version or PROMPT_VERSION
    if not re.fullmatch(r"encode_v[0-9]+(?:\.[0-9]+)?", selected_prompt):
        raise ValueError("prompt_version must look like 'encode_vN' or 'encode_vN.N'")
    prompt_path = _PROMPT_PATH_FOR.get(selected_prompt)
    if prompt_path is None or not prompt_path.is_file():
        raise ValueError(f"unknown prompt version: {selected_prompt}")
    from .client import GeminiEncoder, schema_version_for

    client = GeminiEncoder()
    schema_version = schema_version_for(selected_prompt)
    template = prompt_path.read_text(encoding="utf-8")
    prompt = template.replace("{dish}", name).replace("{input_language}", lang)
    last_error: Exception | None = None
    for _ in range(2):
        try:
            return _validate_model_entry(
                _loads_model_json(client.generate(prompt, schema_version)), client.model_id, selected_prompt
            )
        except (json.JSONDecodeError, ValueError, TypeError, KeyError) as exc:
            last_error = exc
    raise ValueError(f"model output failed validation twice: {last_error}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Encode one dish into qualitative taste levels")
    parser.add_argument("name")
    parser.add_argument("--lang", choices=("zh", "en"), required=True)
    parser.add_argument("--prompt-version", default=PROMPT_VERSION)
    args = parser.parse_args()
    print(
        json.dumps(
            encode_dish(args.name, args.lang, args.prompt_version), ensure_ascii=False, indent=2
        )
    )


if __name__ == "__main__":
    main()
