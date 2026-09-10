# SPDX-License-Identifier: MIT
"""Pure-Python expansion helpers for Phase 1 characterization."""

from __future__ import annotations

import itertools


CHANNELS = ("sugar", "bitter", "water", "ir94e")


def _raw_phase1_conditions(protocol: dict) -> list[dict]:
    spec = protocol["phase1_characterization"]
    conditions: list[dict] = []

    def add(cond_id: str, **active_rates: float) -> None:
        rates = {channel: 0.0 for channel in CHANNELS}
        rates.update({channel: float(rate) for channel, rate in active_rates.items()})
        conditions.append(
            {"cond_id": cond_id, "cell_set_override": {}, "rates": rates}
        )

    for channel in CHANNELS:
        for frequency in spec[f"{channel}_hz"]:
            value = float(frequency)
            add(f"S_{channel}_{value:g}Hz", **{channel: value})

    for pair in spec["pairs"]:
        first, separator, other = pair.partition("_x_")
        if separator != "_x_" or first != "sugar" or other not in CHANNELS[1:]:
            raise ValueError(f"Unsupported Phase 1 pair: {pair}")
        for sugar, modifier in itertools.product(spec["sugar_hz"], spec[f"{other}_hz"]):
            sugar_value, modifier_value = float(sugar), float(modifier)
            add(
                f"P_sugar{sugar_value:g}Hz_{other}{modifier_value:g}Hz",
                sugar=sugar_value,
                **{other: modifier_value},
            )
    return conditions


def expand_phase1_conditions(protocol: dict) -> list[dict]:
    """Expand and deduplicate characterization conditions by four-channel rates."""
    canonical_by_rates: dict[tuple[float, ...], dict] = {}
    expanded: list[dict] = []
    for condition in _raw_phase1_conditions(protocol):
        signature = tuple(condition["rates"][channel] for channel in CHANNELS)
        canonical = canonical_by_rates.get(signature)
        if canonical is None:
            condition["aliases"] = []
            canonical_by_rates[signature] = condition
            expanded.append(condition)
        else:
            canonical["aliases"].append(condition["cond_id"])
    return expanded


def phase1_alias_map(protocol: dict) -> dict[str, str]:
    """Map every non-canonical Phase 1 ID to its first-seen canonical ID."""
    return {
        alias: condition["cond_id"]
        for condition in expand_phase1_conditions(protocol)
        for alias in condition["aliases"]
    }


def phase1_condition_counts(protocol: dict) -> tuple[int, int]:
    """Return raw and deduplicated expansion counts."""
    return len(_raw_phase1_conditions(protocol)), len(expand_phase1_conditions(protocol))
