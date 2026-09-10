# SPDX-License-Identifier: MIT
"""Pure-Python access to a generated MN9 lookup table."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


DIMENSIONS = ("sugar", "bitter", "water", "ir94e")


def _cells_sha256(cells: list[dict]) -> str:
    encoded = json.dumps(
        cells, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


class LookupTable:
    """Validated lookup-table data with level-name based accessors."""

    def __init__(self, data: dict):
        self.data = data
        self.levels = data["levels"]
        self.cells = data["cells"]
        self._index = {
            tuple(cell[dimension] for dimension in DIMENSIONS): cell
            for cell in self.cells
        }
        if len(self._index) != len(self.cells):
            raise ValueError("Lookup table contains duplicate cells")

    @classmethod
    def load(cls, path: str | Path) -> "LookupTable":
        """Load a table and reject corruption of its cells payload."""
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if tuple(data.get("dimensions", ())) != DIMENSIONS:
            raise ValueError(f"Lookup dimensions must be {DIMENSIONS}")
        expected = data.get("cells_sha256")
        actual = _cells_sha256(data.get("cells", []))
        if not expected or actual != expected:
            raise ValueError(
                f"Lookup cells_sha256 mismatch: expected {expected!r}, got {actual}"
            )
        table = cls(data)
        for cell in table.cells:
            table._validate_levels(
                **{dimension: cell.get(dimension) for dimension in DIMENSIONS}
            )
        return table

    def _validate_levels(self, **selected: str) -> None:
        for dimension in DIMENSIONS:
            name = selected[dimension]
            if name not in self.levels[dimension]:
                raise ValueError(
                    f"Unknown {dimension} level {name!r}; "
                    f"expected one of {list(self.levels[dimension])}"
                )

    def get(
        self, sugar: str, bitter: str, water: str, ir94e: str = "none"
    ) -> dict:
        """Get one cell by its four level names."""
        selected = {
            "sugar": sugar, "bitter": bitter, "water": water, "ir94e": ir94e
        }
        self._validate_levels(**selected)
        key = tuple(selected[dimension] for dimension in DIMENSIONS)
        try:
            return self._index[key]
        except KeyError as exc:
            raise KeyError(f"Lookup cell is absent: {selected}") from exc

    def slice(self, ir94e: str = "none") -> list[dict]:
        """Return cells from one ir94e slice, preserving lookup order."""
        if ir94e not in self.levels["ir94e"]:
            raise ValueError(
                f"Unknown ir94e level {ir94e!r}; "
                f"expected one of {list(self.levels['ir94e'])}"
            )
        return [cell for cell in self.cells if cell["ir94e"] == ir94e]
