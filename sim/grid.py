# SPDX-License-Identifier: MIT
"""Pure-Python helpers for expanding the Phase 1 lookup grid."""

from __future__ import annotations

import itertools
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_DIMENSIONS = ("sugar", "bitter", "water", "ir94e")


def load_grid_levels(path: str | Path | None = None) -> dict:
    """Load and minimally validate the confirmed grid-level specification."""
    source = ROOT / "data" / "grid_levels.json" if path is None else Path(path)
    levels = json.loads(source.read_text(encoding="utf-8"))
    dimensions = tuple(levels.get("dimensions", ()))
    if dimensions != EXPECTED_DIMENSIONS:
        raise ValueError(
            f"Grid dimensions must be {EXPECTED_DIMENSIONS}, got {dimensions}"
        )
    if set(levels.get("levels", {})) != set(EXPECTED_DIMENSIONS):
        raise ValueError("Grid levels must define exactly the four grid dimensions")
    return levels


def grid_cell_id(levels: dict) -> str:
    """Return the stable condition ID for a mapping of dimension to level name."""
    missing = [dimension for dimension in EXPECTED_DIMENSIONS if dimension not in levels]
    extra = sorted(set(levels) - set(EXPECTED_DIMENSIONS))
    if missing or extra:
        raise ValueError(f"Invalid grid levels mapping; missing={missing}, extra={extra}")
    return (
        f"G_s{levels['sugar']}_b{levels['bitter']}_"
        f"w{levels['water']}_i{levels['ir94e']}"
    )


def expand_grid_conditions(levels: dict) -> list[dict]:
    """Expand the confirmed 5 x 5 x 5 x 4 grid in declared dimension order."""
    dimensions = tuple(levels["dimensions"])
    if dimensions != EXPECTED_DIMENSIONS:
        raise ValueError(
            f"Grid dimensions must be {EXPECTED_DIMENSIONS}, got {dimensions}"
        )
    mappings = levels["levels"]
    choices = [tuple(mappings[dimension]) for dimension in dimensions]
    conditions = []
    for names in itertools.product(*choices):
        level_names = dict(zip(dimensions, names))
        rates = {
            dimension: mappings[dimension][level_names[dimension]]
            for dimension in dimensions
        }
        conditions.append(
            {
                "cond_id": grid_cell_id(level_names),
                "cell_set_override": {},
                "rates": rates,
                "levels": level_names,
            }
        )

    ids = {condition["cond_id"] for condition in conditions}
    rate_vectors = {
        tuple(condition["rates"][dimension] for dimension in dimensions)
        for condition in conditions
    }
    assert len(conditions) == 500, f"Expected 500 grid cells, got {len(conditions)}"
    assert len(ids) == 500, f"Expected 500 unique condition IDs, got {len(ids)}"
    assert len(rate_vectors) == 500, (
        f"Expected 500 unique rate vectors, got {len(rate_vectors)}"
    )
    return conditions
