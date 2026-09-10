"""Normalization used for dictionary keys and aliases."""

import re
import unicodedata


def normalize_name(name: str) -> str:
    """Normalize a dish name for storage and exact dictionary lookup."""
    if not isinstance(name, str):
        raise TypeError("dish name must be a string")
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", name).strip().lower())
