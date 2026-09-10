#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Generate the Phase 1 characterization report."""

from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sim.phase1 import CHANNELS, phase1_alias_map

RESULTS = ROOT / "results" / "phase1" / "characterize"
OUTPUT = ROOT / "docs" / "phase1_characterization.md"
PAIRS = ("bitter", "water", "ir94e")
MIN_DISTINGUISHABLE_HZ = 3.0
POOLED_STD_MULTIPLIER = 1.5
LEVELS = ("none", "low", "medium", "high", "very_high")
CURRENT_LEVEL_HZ = (0.0, 25.0, 50.0, 100.0, 200.0)
REQUIRED = {
    "cond_id", "mn9_left_mean_hz", "mn9_left_std_hz",
    "mn9_right_mean_hz", "mn9_right_std_hz",
    "mn9_aggregated_mean_hz", "mn9_aggregated_std_hz", "n_trials", "walltime_s",
    *(f"{channel}_hz" for channel in CHANNELS),
}


def fmt(value: float) -> str:
    return f"{float(value):.1f}"


def pm(row: pd.Series, prefix: str) -> str:
    return f"{fmt(row[f'{prefix}_mean_hz'])} ± {fmt(row[f'{prefix}_std_hz'])}"


def elapsed(meta: dict) -> str:
    try:
        seconds = (
            datetime.fromisoformat(meta["end_time"])
            - datetime.fromisoformat(meta["start_time"])
        ).total_seconds()
        return f"{seconds:.1f} s"
    except (KeyError, TypeError, ValueError):
        return "not available"


def direction(values: list[float]) -> str:
    if all(right == left for left, right in zip(values, values[1:])):
        return "flat"
    if all(right >= left for left, right in zip(values, values[1:])):
        return "non-decreasing"
    if all(right <= left for left, right in zip(values, values[1:])):
        return "non-increasing"
    return "non-monotonic"


def alone_assessment(rows: list[pd.Series]) -> tuple[str, str]:
    means = [float(row.mn9_aggregated_mean_hz) for row in rows]
    stds = [float(row.mn9_aggregated_std_hz) for row in rows]
    nondec = all(b >= a for a, b in zip(means, means[1:]))
    noninc = all(b <= a for a, b in zip(means, means[1:]))
    max_delta = max((abs(b - a) for a, b in zip(means, means[1:])), default=0.0)
    pooled = math.sqrt(sum(value * value for value in stds) / len(stds)) if stds else 0.0
    span = max(means) - min(means) if means else 0.0
    if span <= 2.0 and span <= 2.0 * pooled:
        classification = "no effect"
    elif nondec:
        classification = "excitatory"
    elif noninc:
        classification = "inhibitory"
    else:
        classification = "non-monotonic"
    text = (
        f"Monotonic non-decreasing: **{'yes' if nondec else 'no'}**; "
        f"monotonic non-increasing: **{'yes' if noninc else 'no'}**. "
        f"Maximum adjacent |Δ| = {fmt(max_delta)} Hz versus pooled std = {fmt(pooled)} Hz; "
        f"range = {fmt(span)} Hz. Classification: **{classification}**."
    )
    return classification, text


def percent_change(start: float, end: float) -> float:
    if start == 0:
        return 0.0 if end == 0 else math.copysign(math.inf, end - start)
    return 100.0 * (end - start) / start


def modifier_class(changes: list[float]) -> str:
    if changes and all(abs(value) <= 10.0 for value in changes):
        return "no effect"
    if changes and all(value <= 0 for value in changes) and any(value < -10 for value in changes):
        return "suppressive"
    if changes and all(value >= 0 for value in changes) and any(value > 10 for value in changes):
        return "facilitating"
    return "mixed"


def curve_stats(rows: list[pd.Series]) -> tuple[float, float]:
    means = [float(row.mn9_aggregated_mean_hz) for row in rows]
    stds = [float(row.mn9_aggregated_std_hz) for row in rows]
    pooled = math.sqrt(sum(value * value for value in stds) / len(stds))
    threshold = max(MIN_DISTINGUISHABLE_HZ, POOLED_STD_MULTIPLIER * pooled)
    return pooled, threshold


def propose_levels(
    frequencies: list[float], rows: list[pd.Series]
) -> tuple[list[dict], float, float, str]:
    points = sorted(
        zip((float(value) for value in frequencies), rows), key=lambda item: item[0]
    )
    pooled, threshold = curve_stats([row for _, row in points])
    means = [float(row.mn9_aggregated_mean_hz) for _, row in points]
    none_index = next(
        (index for index, (frequency, _) in enumerate(points) if frequency == 0.0), None
    )
    if none_index is None:
        raise ValueError("A proposal curve does not contain the required 0 Hz point")
    none_mean = means[none_index]
    response_range = max(means) - min(means)
    if abs(max(means) - none_mean) >= abs(min(means) - none_mean):
        sign, extreme = 1.0, max(means)
        response_direction = "increasing"
    else:
        sign, extreme = -1.0, min(means)
        response_direction = "decreasing"

    none_frequency, none_row = points[none_index]
    chosen = [{
        "level": "none", "frequency": none_frequency, "row": none_row,
        "delta": None, "distinguishable": None, "note": "",
    }]
    previous_frequency, previous_mean = none_frequency, none_mean
    for level, fraction in zip(LEVELS[1:4], (0.25, 0.5, 0.75)):
        target = none_mean + sign * fraction * response_range
        beyond = [point for point in points if point[0] > previous_frequency]
        eligible = [
            point for point in beyond
            if abs(float(point[1].mn9_aggregated_mean_hz) - previous_mean) >= threshold
        ]
        candidates = eligible or beyond
        if not candidates:
            candidates = [points[-1]]
        frequency, row = min(
            candidates,
            key=lambda point: (
                abs(float(point[1].mn9_aggregated_mean_hz) - target), point[0]
            ),
        )
        mean = float(row.mn9_aggregated_mean_hz)
        distinguishable = (
            frequency > previous_frequency and abs(mean - previous_mean) >= threshold
        )
        chosen.append({
            "level": level, "frequency": frequency, "row": row,
            "delta": mean - previous_mean, "distinguishable": distinguishable,
            "note": "" if distinguishable else f"not distinguishable from {chosen[-1]['level']}",
        })
        previous_frequency, previous_mean = frequency, mean

    saturation_frequency, saturation_row = next(
        point for point in points
        if abs(float(point[1].mn9_aggregated_mean_hz) - extreme) <= threshold
    )
    if saturation_frequency <= previous_frequency:
        saturation_frequency, saturation_row = points[-1]
    saturation_mean = float(saturation_row.mn9_aggregated_mean_hz)
    distinguishable = (
        saturation_frequency > previous_frequency
        and abs(saturation_mean - previous_mean) >= threshold
    )
    chosen.append({
        "level": "very_high", "frequency": saturation_frequency,
        "row": saturation_row, "delta": saturation_mean - previous_mean,
        "distinguishable": distinguishable,
        "note": "" if distinguishable else "not distinguishable from high",
    })
    return chosen, pooled, threshold, response_direction


def current_mapping_text(frequencies: list[float], rows: list[pd.Series]) -> str:
    points = {float(frequency): row for frequency, row in zip(frequencies, rows)}
    values = []
    for level, frequency in zip(LEVELS, CURRENT_LEVEL_HZ):
        row = points.get(frequency)
        outcome = "not measured" if row is None else pm(row, "mn9_aggregated") + " Hz"
        values.append(f"{level}={frequency:g} Hz -> {outcome}")
    return "; ".join(values)


def generate(results_dir: Path = RESULTS) -> str:
    protocol = json.loads((ROOT / "data" / "stim_protocol.json").read_text(encoding="utf-8"))
    frame = pd.read_csv(results_dir / "summary.csv")
    missing = REQUIRED - set(frame.columns)
    if missing:
        raise ValueError("Missing summary columns: " + ", ".join(sorted(missing)))
    meta = json.loads((results_dir / "run_meta.json").read_text(encoding="utf-8"))
    aliases = phase1_alias_map(protocol)
    indexed = frame.set_index("cond_id", drop=False)

    def row_for(cond_id: str) -> pd.Series:
        canonical = aliases.get(cond_id, cond_id)
        if canonical not in indexed.index:
            raise ValueError(f"Missing condition {canonical} (requested as {cond_id})")
        return indexed.loc[canonical]

    lines = [
        "# Phase 1 characterization", "", "## Run metadata", "",
        "| Field | Value |", "|---|---|",
        "| Stage | characterize |",
        f"| Run date | {meta.get('start_time', 'unknown')} |",
        f"| Git commit | {meta.get('git_commit', 'unknown')} |",
        f"| brian2 version | {meta.get('brian2_version', 'unknown')} |",
        f"| Codegen target | {meta.get('codegen_target', 'unknown')} |",
        f"| n_proc | {meta.get('n_proc', 'unknown')} |",
        f"| Conditions (deduplicated/raw) | {meta.get('n_conditions', len(frame))}/{meta.get('n_conditions_raw', 'unknown')} |",
        f"| Protocol sha256 | {meta.get('protocol_sha256', 'unknown')} |",
        f"| Cells sha256 | {meta.get('cells_sha256', 'unknown')} |",
        f"| Total simulated trials | {int(frame.n_trials.sum())} |",
        f"| Parallel walltime | {elapsed(meta)} |", "",
        f"The paper calibrated w_syn on FlyWire v630; this run uses {protocol.get('data_version', 'the configured data version')} only. Absolute Hz may therefore differ from the paper.", "",
        "MN9 aggregation = left_only (contralateral to the right-hemisphere sugar GRNs), frozen in `data/stim_protocol.json`. Right MN9 is recorded and reported but is not the aggregated readout.", "",
        "## Single-channel dose curves", "",
    ]
    alone: dict[str, str] = {}
    for channel in CHANNELS:
        rows = [row_for(f"S_{channel}_{float(freq):g}Hz") for freq in protocol["phase1_characterization"][f"{channel}_hz"]]
        lines += [f"### {channel}", "", "| Hz | MN9 aggregated mean ± std | Left mean ± std | Right mean ± std |", "|---:|---:|---:|---:|"]
        for frequency, row in zip(protocol["phase1_characterization"][f"{channel}_hz"], rows):
            lines.append(f"| {float(frequency):g} | {pm(row, 'mn9_aggregated')} | {pm(row, 'mn9_left')} | {pm(row, 'mn9_right')} |")
        classification, assessment = alone_assessment(rows)
        alone[channel] = classification
        lines += ["", assessment]
        if channel in ("bitter", "ir94e"):
            lines += ["", f"Approximately zero response to {channel} alone is expected and is not a failure."]
        lines.append("")

    lines += ["## Pairwise", ""]
    modifiers: dict[str, str] = {}
    for other in PAIRS:
        sugar_levels = protocol["phase1_characterization"]["sugar_hz"]
        other_levels = protocol["phase1_characterization"][f"{other}_hz"]
        lines += [f"### sugar × {other}", "", "| Sugar Hz \\ " + f"{other} Hz | " + " | ".join(f"{float(value):g}" for value in other_levels) + " |", "|---:|" + "---:|" * len(other_levels)]
        for sugar in sugar_levels:
            values = [float(row_for(f"P_sugar{float(sugar):g}Hz_{other}{float(value):g}Hz").mn9_aggregated_mean_hz) for value in other_levels]
            lines.append(f"| {float(sugar):g} | " + " | ".join(fmt(value) for value in values) + " |")
        lines += ["", f"Percent change from {other}=0 to {other}=max:", ""]
        changes = []
        for sugar in sugar_levels:
            if float(sugar) < 50:
                continue
            start = float(row_for(f"P_sugar{float(sugar):g}Hz_{other}{float(other_levels[0]):g}Hz").mn9_aggregated_mean_hz)
            end = float(row_for(f"P_sugar{float(sugar):g}Hz_{other}{float(other_levels[-1]):g}Hz").mn9_aggregated_mean_hz)
            change = percent_change(start, end)
            changes.append(change)
            shown = "N/A (zero baseline)" if not math.isfinite(change) else f"{change:.1f}%"
            lines.append(f"- Sugar {float(sugar):g} Hz: {shown}")
        at_200 = [float(row_for(f"P_sugar200Hz_{other}{float(value):g}Hz").mn9_aggregated_mean_hz) for value in other_levels]
        classification = modifier_class(changes)
        modifiers[other] = classification
        lines += ["", f"At sugar=200 Hz, MN9 is **{direction(at_200)}** along the {other} axis. Modifier classification: **{classification}**.", ""]

    lines += ["## Channel summary", "", "| Channel | Alone effect | Effect as modifier of sugar | Verdict |", "|---|---|---|---|"]
    verdicts: dict[str, str] = {}
    for channel in CHANNELS:
        modifier = "not assessed" if channel == "sugar" else modifiers[channel]
        if channel == "sugar" and alone[channel] in ("excitatory", "inhibitory"):
            verdict = "stable & interpretable"
        elif alone[channel] == "no effect" and modifier == "no effect":
            verdict = "none"
        elif alone[channel] != "non-monotonic" and modifier in ("suppressive", "facilitating"):
            verdict = "stable & interpretable"
        else:
            verdict = "weak"
        verdicts[channel] = verdict
        lines.append(f"| {channel} | {alone[channel]} | {modifier} | {verdict} |")

    def single_curve(channel: str) -> tuple[list[float], list[pd.Series]]:
        frequencies = [
            float(value)
            for value in protocol["phase1_characterization"][f"{channel}_hz"]
        ]
        return frequencies, [
            row_for(f"S_{channel}_{frequency:g}Hz") for frequency in frequencies
        ]

    def modifier_curve(
        channel: str, sugar_frequency: float
    ) -> tuple[list[float], list[pd.Series]]:
        frequencies = [
            float(value)
            for value in protocol["phase1_characterization"][f"{channel}_hz"]
        ]
        return frequencies, [
            row_for(
                f"P_sugar{sugar_frequency:g}Hz_{channel}{frequency:g}Hz"
            )
            for frequency in frequencies
        ]

    proposal_curves: dict[str, tuple[list[float], list[pd.Series], str]] = {}
    sugar_frequencies, sugar_rows = single_curve("sugar")
    proposal_curves["sugar"] = (
        sugar_frequencies, sugar_rows, "single-channel sugar",
    )
    bitter_frequencies, bitter_rows_200 = modifier_curve("bitter", 200.0)
    _, bitter_rows_100 = modifier_curve("bitter", 100.0)
    proposal_curves["bitter"] = (
        bitter_frequencies, bitter_rows_200, "modifier at sugar=200 Hz",
    )
    selection_explanations = {
        "sugar": "The single-channel sugar curve is used.",
        "bitter": "The proposal uses the modifier curve at sugar=200 Hz.",
    }
    for channel in ("water", "ir94e"):
        frequencies, single_rows = single_curve(channel)
        means = [float(row.mn9_aggregated_mean_hz) for row in single_rows]
        single_pooled, _ = curve_stats(single_rows)
        single_range = max(means) - min(means)
        cutoff = max(2.0, 2.0 * single_pooled)
        if single_range > cutoff:
            proposal_curves[channel] = (
                frequencies, single_rows, f"single-channel {channel}",
            )
            selection_explanations[channel] = (
                f"The single-channel curve is used because its {fmt(single_range)} Hz "
                f"range exceeds max(2 Hz, 2 × pooled std) = {fmt(cutoff)} Hz."
            )
        else:
            modifier_frequencies, modifier_rows = modifier_curve(channel, 200.0)
            proposal_curves[channel] = (
                modifier_frequencies, modifier_rows, "modifier at sugar=200 Hz",
            )
            selection_explanations[channel] = (
                f"The modifier curve at sugar=200 Hz is used because the "
                f"single-channel range is {fmt(single_range)} Hz, which does not "
                f"exceed max(2 Hz, 2 × pooled std) = {fmt(cutoff)} Hz."
            )

    lines += [
        "", "## Proposed level → Hz mapping (provisional, for user confirmation)", "",
        f"A level is distinguishable when adjacent MN9 outcomes differ by at least "
        f"max({MIN_DISTINGUISHABLE_HZ:g} Hz, {POOLED_STD_MULTIPLIER:g} × pooled std). "
        "All selections are measured points; no interpolation is used.", "",
        "### Bitter modifier context", "",
        "| Bitter Hz | MN9 at sugar=100 Hz (mean ± std) | MN9 at sugar=200 Hz (mean ± std) |",
        "|---:|---:|---:|",
    ]
    for frequency, row_100, row_200 in zip(
        bitter_frequencies, bitter_rows_100, bitter_rows_200
    ):
        lines.append(
            f"| {frequency:g} | {pm(row_100, 'mn9_aggregated')} | "
            f"{pm(row_200, 'mn9_aggregated')} |"
        )

    proposals: dict[str, tuple[list[dict], str]] = {}
    for channel in CHANNELS:
        frequencies, rows, curve_label = proposal_curves[channel]
        chosen, pooled, threshold, response_direction = propose_levels(
            frequencies, rows
        )
        proposals[channel] = (chosen, curve_label)
        qualifier = (
            " Measured for completeness; v1 does not encode ir94e."
            if channel == "ir94e" else ""
        )
        lines += [
            "", f"### {channel}", "",
            selection_explanations[channel] + qualifier,
            f"Measured response direction: **{response_direction}** "
            f"(observed trend: **{direction([float(row.mn9_aggregated_mean_hz) for row in rows])}**).",
            "", "| Level | proposed Hz | MN9 at that Hz (mean ± std) | Δ vs previous level | distinguishable? |",
            "|---|---:|---:|---:|---|",
        ]
        for item in chosen:
            delta = "—" if item["delta"] is None else f"{item['delta']:+.1f} Hz"
            if item["distinguishable"] is None:
                distinguishable = "—"
            elif item["distinguishable"]:
                distinguishable = "yes"
            else:
                distinguishable = f"no — {item['note']}"
            lines.append(
                f"| {item['level']} | {item['frequency']:g} | "
                f"{pm(item['row'], 'mn9_aggregated')} | {delta} | {distinguishable} |"
            )
        lines += [
            "",
            "Current provisional mapping comparison: "
            + current_mapping_text(frequencies, rows) + ".",
            f"Noise floor: pooled std = {fmt(pooled)} Hz; distinguishability "
            f"threshold = {fmt(threshold)} Hz.",
        ]

    lines += [
        "", "### Proposal summary", "",
        "| Dimension | none | low | medium | high | very_high | curve used |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for channel in CHANNELS:
        chosen, curve_label = proposals[channel]
        frequencies = " | ".join(f"{item['frequency']:g}" for item in chosen)
        lines.append(f"| {channel} | {frequencies} | {curve_label} |")
    lines += [
        "",
        "These values are proposals from measured points; the frozen protocol covers mechanics only. Level→Hz is confirmed by the user before any grid is generated.",
    ]

    lines += [
        "", "## Dimensionality options", "",
        f"- **3D sugar×bitter×water.** The observed alone effects are sugar={alone['sugar']}, bitter={alone['bitter']}, and water={alone['water']}; bitter is {modifiers['bitter']} and water is {modifiers['water']} as a sugar modifier. The characterization does not measure bitter×water or three-way interactions.",
        f"- **2D sugar×bitter with water as a modifier.** This directly represents the measured sugar×bitter plane ({modifiers['bitter']}) while treating the measured water effect ({modifiers['water']}) outside the two primary axes.",
        f"- **4 channels.** This retains sugar, bitter, water, and ir94e; their verdicts are sugar={verdicts['sugar']}, bitter={verdicts['bitter']}, water={verdicts['water']}, ir94e={verdicts['ir94e']}. Current evidence covers each channel alone and each non-sugar channel paired with sugar, but not other pairings or higher-order interactions.",
        "", "Decision pending user confirmation on both dimensionality and level→Hz mapping; no grid generated. Grid cells will use 30 trials.",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, default=RESULTS)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(generate(args.results_dir), encoding="utf-8")
    try:
        shown = args.output.relative_to(ROOT)
    except ValueError:
        shown = args.output
    print(f"wrote {shown}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
