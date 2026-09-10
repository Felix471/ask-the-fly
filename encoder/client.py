"""Minimal Gemini client for the v1 dish encoder."""

from __future__ import annotations

import os
import time
from typing import Any

from dotenv import load_dotenv
from google import genai
from google.genai import types


class GeminiEncoder:
    """Call the configured Gemini model with bounded transient retries."""

    def __init__(self) -> None:
        load_dotenv()
        self.model_id = os.getenv("ENCODER_MODEL") or ""
        api_key = os.getenv("GEMINI_API_KEY")
        if not self.model_id.strip():
            raise RuntimeError("ENCODER_MODEL is not set")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is not set")
        self._client = genai.Client(api_key=api_key)

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

    def generate(self, prompt: str) -> str:
        for attempt in range(5):
            try:
                response = self._client.models.generate_content(
                    model=self.model_id,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0,
                        response_mime_type="application/json",
                    ),
                )
                if not response.text:
                    raise ValueError("Gemini returned an empty response")
                return response.text
            except Exception as exc:
                status = self._status_code(exc)
                if attempt == 4 or status != 429 and (status is None or status < 500):
                    raise
                time.sleep(2**attempt)
        raise AssertionError("unreachable")
