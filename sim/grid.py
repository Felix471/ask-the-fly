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
    """Expand the confirmed grid in declared dimension order, one cell per unique Hz vector.

    Level names that map to identical Hz on every dimension share one cell (for
    example water low and medium, both 60 Hz). The first combination in product
    order is the canonical cell; the others are listed under ``alias_levels``.
    """
    dimensions = tuple(levels["dimensions"])
    if dimensions != EXPECTED_DIMENSIONS:
        raise ValueError(
            f"Grid dimensions must be {EXPECTED_DIMENSIONS}, got {dimensions}"
        )
    mappings = levels["levels"]
    choices = [tuple(mappings[dimension]) for dimension in dimensions]
    conditions: list[dict] = []
    by_rates: dict[tuple, dict] = {}
    for names in itertools.product(*choices):
        level_names = dict(zip(dimensions, names))
        rates = {
            dimension: mappings[dimension][level_names[dimension]]
            for dimension in dimensions
        }
        rate_key = tuple(float(rates[dimension]) for dimension in dimensions)
        canonical = by_rates.get(rate_key)
        if canonical is not None:
            canonical["alias_levels"].append(level_names)
            continue
        condition = {
            "cond_id": grid_cell_id(level_names),
            "cell_set_override": {},
            "rates": rates,
            "levels": level_names,
            "alias_levels": [],
            # Position in canonical product order: the seed identity of the
            # cell, independent of how the run is batched (seed scheme v2, D02).
            "global_index": len(conditions),
        }
        by_rates[rate_key] = condition
        conditions.append(condition)

    expected = 1
    for dimension in dimensions:
        expected *= len(set(mappings[dimension].values()))
    ids = {condition["cond_id"] for condition in conditions}
    if len(conditions) != expected or len(ids) != expected:
        raise ValueError(
            f"Expected {expected} unique grid cells, got {len(conditions)} "
            f"({len(ids)} unique IDs)"
        )
    return conditions


def resolve_levels(levels: dict, selected: dict) -> dict:
    """Map any level-name combination to the canonical level names of its cell."""
    mappings = levels["levels"]
    for dimension in EXPECTED_DIMENSIONS:
        if selected.get(dimension) not in mappings[dimension]:
            raise ValueError(
                f"Unknown {dimension} level {selected.get(dimension)!r}; "
                f"expected one of {list(mappings[dimension])}"
            )
    wanted = tuple(
        float(mappings[dimension][selected[dimension]]) for dimension in EXPECTED_DIMENSIONS
    )
    for condition in expand_grid_conditions(levels):
        rates = tuple(float(condition["rates"][d]) for d in EXPECTED_DIMENSIONS)
        if rates == wanted:
            return dict(condition["levels"])
    raise ValueError(f"No grid cell for {selected}")
