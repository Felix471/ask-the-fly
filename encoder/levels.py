"""Public v1 taste levels and their fixed firing-rate mapping."""

LEVELS = ("none", "low", "medium", "high", "very_high")

LEVEL_HZ = {
    "none": 0,
    "low": 25,
    "medium": 50,
    "high": 100,
    "very_high": 200,
}

IR94E_LEVELS = ("none", "low", "medium", "high")
IR94E_HZ = {"none": 0, "low": 60, "medium": 120, "high": 200}


def levels_for(dimension: str) -> tuple[str, ...]:
    """Allowed levels of a dimension: ir94e has four, the others five."""
    return IR94E_LEVELS if dimension == "ir94e" else LEVELS


def prompt_has_ir94e(prompt_version: str) -> bool:
    """Whether an encode_v<major>[.<minor>] prompt includes the Ir94e dimension."""
    import re

    match = re.fullmatch(r"encode_v(\d+)(?:\.(\d+))?", prompt_version)
    return bool(match and (int(match.group(1)), int(match.group(2) or 0)) >= (2, 3))
