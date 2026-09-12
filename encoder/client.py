"""Minimal Gemini client for the v1 dish encoder."""

from __future__ import annotations

import os
import random
import re
import sys
import time
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from google import genai
from google.genai import types

from .levels import LEVELS, levels_for, prompt_has_ir94e


RESPONSE_SCHEMA_VERSION = "schema_v1"
_CORE_DIMENSIONS = ("sugar", "bitter", "water")


def _schema(dimensions: tuple[str, ...]) -> types.Schema:
    return types.Schema(
        type=types.Type.OBJECT,
        properties={
        "key": types.Schema(type=types.Type.STRING),
        "aliases": types.Schema(
            type=types.Type.ARRAY,
            items=types.Schema(type=types.Type.STRING),
        ),
        "display": types.Schema(
            type=types.Type.OBJECT,
            properties={
                "zh": types.Schema(type=types.Type.STRING),
                "en": types.Schema(type=types.Type.STRING),
            },
            required=["zh", "en"],
        ),
        **{
            dimension: types.Schema(type=types.Type.STRING, enum=list(levels_for(dimension)))
            for dimension in dimensions
        },
        "reason": types.Schema(
            type=types.Type.OBJECT,
            properties={
                dimension: types.Schema(type=types.Type.STRING)
                for dimension in dimensions
            },
            required=list(dimensions),
        ),
        "confidence": types.Schema(
            type=types.Type.OBJECT,
            properties={
                dimension: types.Schema(type=types.Type.NUMBER)
                for dimension in dimensions
            },
            required=list(dimensions),
        ),
        },
        required=["key", "aliases", "display", *dimensions, "reason", "confidence"],
    )


schema_v1 = _schema(_CORE_DIMENSIONS)
schema_v2 = _schema((*_CORE_DIMENSIONS, "ir94e"))
RESPONSE_SCHEMAS = {"schema_v1": schema_v1, "schema_v2": schema_v2}
RESPONSE_SCHEMA = schema_v1


def schema_version_for(prompt_version: str) -> str:
    return "schema_v2" if prompt_has_ir94e(prompt_version) else "schema_v1"

_CLIENT: genai.Client | None = None


class GeminiEncoder:
    """Call the configured Gemini model with bounded transient retries."""

    def __init__(self) -> None:
        load_dotenv(Path(__file__).resolve().parents[1] / ".env")
        self.model_id = os.getenv("ENCODER_MODEL") or ""
        api_key = os.getenv("GEMINI_API_KEY")
        if not self.model_id.strip():
            raise RuntimeError("ENCODER_MODEL is not set")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is not set")
        global _CLIENT
        if _CLIENT is None:
            _CLIENT = genai.Client(api_key=api_key)
        self._client = _CLIENT

    @staticmethod
    def _status_code(exc: Exception) -> int | None:
        for attr in ("status_code", "code"):
            value: Any = getattr(exc, attr, None)
            if callable(value):
                try:
                    value = value()
                except TypeError:
                    value = None
            try:
                return int(value)
            except (TypeError, ValueError):
                pass
        response = getattr(exc, "response", None)
        try:
            return int(getattr(response, "status_code", None))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _retry_after(exc: Exception) -> float | None:
        """Extract a retry delay from headers, structured details, or the message."""
        candidates: list[str] = []
        response = getattr(exc, "response", None)
        headers = getattr(response, "headers", None)
        if headers:
            value = headers.get("retry-after") or headers.get("Retry-After")
            if value is not None:
                candidates.append(str(value))

        seen: set[int] = set()

        def collect(value: Any) -> None:
            if value is None or id(value) in seen:
                return
            seen.add(id(value))
            if isinstance(value, dict):
                for key, child in value.items():
                    if str(key).lower() in {"retrydelay", "retry-after", "retry_after"}:
                        candidates.append(str(child))
                    collect(child)
            elif isinstance(value, (list, tuple)):
                for child in value:
                    collect(child)

        for value in (getattr(exc, "details", None), getattr(exc, "args", None)):
            collect(value)
        message = str(exc)
        candidates.extend(
            match.group(1)
            for match in re.finditer(
                r"(?:retryDelay['\"\s:=-]*|retry(?:-|\s)?after['\"\s:=-]*|retry\s+in\s+)"
                r"(\d+(?:\.\d+)?\s*(?:ms|s|seconds?)?)",
                message,
                flags=re.IGNORECASE,
            )
        )
        delays = []
        for candidate in candidates:
            match = re.search(r"(\d+(?:\.\d+)?)\s*(ms|s|seconds?)?", candidate, re.I)
            if match:
                delay = float(match.group(1))
                if match.group(2) and match.group(2).lower() == "ms":
                    delay /= 1000
                delays.append(delay)
        return min(120.0, max(delays)) if delays else None

    @classmethod
    def _retryable(cls, exc: Exception) -> bool:
        status = cls._status_code(exc)
        message = str(exc).upper()
        network_error = isinstance(exc, (ConnectionError, TimeoutError, OSError)) or any(
            token in type(exc).__name__.upper()
            for token in ("CONNECTERROR", "READTIMEOUT", "WRITETIMEOUT", "REMOTEPROTOCOLERROR", "CONNECTTIMEOUT")
        )
        return (
            network_error
            or status == 429
            or status is not None and 500 <= status < 600
            or "RESOURCE_EXHAUSTED" in message
            or "UNAVAILABLE" in message
            or "FORCIBLY CLOSED" in message
        )

    def generate(self, prompt: str, schema_version: str = RESPONSE_SCHEMA_VERSION) -> str:
        for attempt in range(8):
            try:
                response = self._client.models.generate_content(
                    model=self.model_id,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0,
                        response_mime_type="application/json",
                        response_schema=RESPONSE_SCHEMAS[schema_version],
                    ),
                )
                if not response.text:
                    raise ValueError("Gemini returned an empty response")
                return response.text
            except Exception as exc:
                if attempt == 7 or not self._retryable(exc):
                    raise
                wait = min(60, 2**attempt) + random.uniform(0, 1)
                retry_after = self._retry_after(exc)
                if retry_after is not None:
                    wait = max(wait, retry_after)
                print(
                    f"Gemini transient error; retry {attempt + 1}/7 in {wait:.1f}s",
                    file=sys.stderr,
                )
                time.sleep(wait)
        raise AssertionError("unreachable")
