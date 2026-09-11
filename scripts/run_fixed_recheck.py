#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Run and analyze the post-refractory-fix characterization recheck."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import socket
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sim.phase1 import CHANNELS, expand_phase1_conditions, phase1_alias_map
from scripts.phase1_report import curve_stats


MEAN = "mn9_aggregated_mean_hz"
STD = "mn9_aggregated_std_hz"
RATE_COLUMNS = [f"{channel}_hz" for channel in CHANNELS]


def rooted(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git_commit() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True,
        capture_output=True, check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else "unknown"


def selected_conditions(protocol: dict) -> list[dict]:
    """Return canonical conditions covering the requested curves.

    The Phase 1 expander deduplicates rate-identical conditions. In particular,
    all-zero and sugar-only pair endpoints retain their first canonical S_* ID.
    Selecting by the rate vectors as well as IDs retains those endpoints.
    """
    wanted = {
        f"S_{channel}_{float(frequency):g}Hz"
        for channel in CHANNELS
        for frequency in protocol["phase1_characterization"][f"{channel}_hz"]
    }
    wanted.update(
        f"P_sugar200Hz_{channel}{float(frequency):g}Hz"
        for channel in CHANNELS[1:]
        for frequency in protocol["phase1_characterization"][f"{channel}_hz"]
    )
    wanted.add("P_sugar200Hz_bitter30Hz")
    wanted.update(
        f"P_sugar{sugar}Hz_water{water}Hz"
        for sugar in (60, 100)
        for water in (0, 60, 120, 180, 240)
    )

    expanded = expand_phase1_conditions(protocol)
    aliases = phase1_alias_map(protocol)
    by_id = {condition["cond_id"]: condition for condition in expanded}
    selected_ids = {
        aliases.get(cond_id, cond_id)
        for cond_id in wanted
        if aliases.get(cond_id, cond_id) in by_id
    }
    conditions = [
        condition for condition in expanded if condition["cond_id"] in selected_ids
    ]

    available_ids = set(by_id) | set(aliases)
    for cond_id in sorted(wanted - available_ids):
        if cond_id == "P_sugar200Hz_bitter30Hz":
            rates = {"sugar": 200.0, "bitter": 30.0, "water": 0.0, "ir94e": 0.0}
        elif cond_id.startswith("P_sugar60Hz_water"):
            rates = {
                "sugar": 60.0, "bitter": 0.0,
                "water": float(cond_id.removeprefix("P_sugar60Hz_water").removesuffix("Hz")),
                "ir94e": 0.0,
            }
        elif cond_id.startswith("P_sugar100Hz_water"):
            rates = {
                "sugar": 100.0, "bitter": 0.0,
                "water": float(cond_id.removeprefix("P_sugar100Hz_water").removesuffix("Hz")),
                "ir94e": 0.0,
            }
        else:
            raise ValueError(f"Cannot construct requested condition {cond_id}")
        conditions.append(
            {"cond_id": cond_id, "cell_set_override": {}, "rates": rates, "aliases": []}
        )
    return conditions


def run_recheck(args: argparse.Namespace) -> int:
    from sim.network import load_cells, load_protocol
    from sim.runner import run_conditions

    if args.n_proc <= 0 or args.batch_size <= 0 or args.n_trials <= 0:
        raise ValueError("--n-proc, --batch-size, and --n-trials must be positive")
    protocol, cells = load_protocol(), load_cells()
    conditions = selected_conditions(protocol)
    print(f"Fixed-path recheck: {len(conditions)} deduplicated conditions")
    if args.list:
        for condition in conditions:
            print(condition["cond_id"])
        return 0

    import brian2

    output_dir = ROOT / "results" / "phase1_fixed" / "characterize"
    output_dir.mkdir(parents=True, exist_ok=True)
    meta = {
        "git_commit": git_commit(),
        "protocol_sha256": sha256(ROOT / "data" / "stim_protocol.json"),
        "cells_sha256": sha256(ROOT / "data" / "cells.json"),
        "brian2_version": brian2.__version__,
        "codegen_target": str(brian2.prefs.codegen.target),
        "n_proc": args.n_proc,
        "hostname": socket.gethostname(),
        "start_time": datetime.now(timezone.utc).isoformat(),
        "end_time": None,
        "n_conditions": len(conditions),
        "path": "fixed per-channel refractory rule",
    }
    try:
        summaries = []
        batches = [
            conditions[start:start + args.batch_size]
            for start in range(0, len(conditions), args.batch_size)
        ]
        for index, batch in enumerate(batches, start=1):
            print(
                f"batch {index}/{len(batches)}: {len(batch)} conditions x "
                f"{args.n_trials} trials", flush=True,
            )
            summaries.append(run_conditions(
                batch, args.n_trials, args.n_proc, protocol=protocol, cells=cells,
                stage="characterize", duration_ms=1000.0, force=args.force,
                channels=list(CHANNELS), results_subdir="phase1_fixed",
            ))
        summary = pd.concat(summaries, ignore_index=True)
        rates_by_id = {item["cond_id"]: item["rates"] for item in conditions}
        for channel in CHANNELS:
            summary[f"{channel}_hz"] = summary["cond_id"].map(
                lambda cond_id, name=channel: rates_by_id[cond_id][name]
            )
        summary.to_csv(output_dir / "summary.csv", index=False)
        print(summary.to_string(index=False))
    finally:
        meta["end_time"] = datetime.now(timezone.utc).isoformat()
        (output_dir / "run_meta.json").write_text(
            json.dumps(meta, indent=2) + "\n", encoding="utf-8"
        )
    return 0


def load_summary(directory: Path) -> pd.DataFrame:
    path = rooted(directory) / "summary.csv"
    frame = pd.read_csv(path)
    required = {"cond_id", MEAN, STD}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"{path}: missing columns {sorted(missing)}")
    return frame


def pooled_two(a: float, b: float) -> float:
    return math.sqrt((a * a + b * b) / 2.0)


def fmt_ratio(value: float) -> str:
    if math.isinf(value):
        return "+inf" if value > 0 else "-inf"
    return f"{value:+.2f}"


def delta_table(fixed: pd.DataFrame, prefix: pd.DataFrame) -> list[str]:
    joined = prefix[["cond_id", MEAN, STD]].merge(
        fixed[["cond_id", MEAN, STD]], on="cond_id", suffixes=("_pre", "_fixed")
    ).sort_values("cond_id")
    lines = [
        "| cond_id | pre-fix mean ± std | fixed mean ± std | Δ (Hz) | Δ / pooled std |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in joined.itertuples(index=False):
        pre_mean, pre_std = float(row[1]), float(row[2])
        fixed_mean, fixed_std = float(row[3]), float(row[4])
        delta = fixed_mean - pre_mean
        pooled = pooled_two(pre_std, fixed_std)
        ratio = delta / pooled if pooled else (0.0 if delta == 0 else math.copysign(math.inf, delta))
        delta_text = f"{delta:+.1f}"
        if abs(delta) > 3.0:
            delta_text = f"**{delta_text}**"
        lines.append(
            f"| {row[0]} | {pre_mean:.1f} ± {pre_std:.1f} | "
            f"{fixed_mean:.1f} ± {fixed_std:.1f} | {delta_text} | {fmt_ratio(ratio)} |"
        )
    if joined.empty:
        lines.append("| _No conditions present in both summaries_ | — | — | — | — |")
    return lines


def phase0_delta_lines(fixed_dir: Path) -> list[str]:
    fixed_path = rooted(fixed_dir) / "summary.csv"
    prefix_path = ROOT / "results" / "phase0" / "full" / "summary.csv"
    lines = [
        "| Sugar (Hz) | pre-fix mean ± std | fixed mean ± std | Δ (Hz) | Δ / pooled std |",
        "|---:|---:|---:|---:|---:|",
    ]
    if not fixed_path.exists():
        return lines + ["| — | — | pending | — | — |"]
    fixed, prefix = pd.read_csv(fixed_path), pd.read_csv(prefix_path)
    for frequency in (25, 50, 100, 200):
        cond_id = f"A_sugar_dose_sugar{frequency}Hz_bitter0Hz"
        pre_rows = prefix[prefix.cond_id == cond_id]
        fixed_rows = fixed[fixed.cond_id == cond_id]
        if pre_rows.empty or fixed_rows.empty:
            lines.append(f"| {frequency} | missing | missing | — | — |")
            continue
        pre, new = pre_rows.iloc[0], fixed_rows.iloc[0]
        delta = float(new[MEAN]) - float(pre[MEAN])
        pooled = pooled_two(float(pre[STD]), float(new[STD]))
        ratio = delta / pooled if pooled else (0.0 if delta == 0 else math.copysign(math.inf, delta))
        delta_text = f"{delta:+.1f}"
        if abs(delta) > 3.0:
            delta_text = f"**{delta_text}**"
        lines.append(
            f"| {frequency} | {float(pre[MEAN]):.1f} ± {float(pre[STD]):.1f} | "
            f"{float(new[MEAN]):.1f} ± {float(new[STD]):.1f} | {delta_text} | "
            f"{fmt_ratio(ratio)} |"
        )
    return lines


def curve_rows(frame: pd.DataFrame, varying: str, fixed_rates: dict[str, float]) -> pd.DataFrame:
    missing = set(RATE_COLUMNS) - set(frame.columns)
    if missing:
        raise ValueError(f"Summary lacks rate columns: {sorted(missing)}")
    mask = pd.Series(True, index=frame.index)
    for channel in CHANNELS:
        if channel != varying:
            mask &= frame[f"{channel}_hz"].astype(float).eq(float(fixed_rates.get(channel, 0.0)))
    rows = frame.loc[mask].sort_values(f"{varying}_hz")
    if rows.empty:
        raise ValueError(f"No rows for {varying} curve with fixed rates {fixed_rates}")
    return rows


def requested_cond_id(varying: str, fixed_rates: dict[str, float], frequency: float) -> str:
    active_fixed = {
        channel: float(rate) for channel, rate in fixed_rates.items() if float(rate) != 0.0
    }
    if set(active_fixed) == {"sugar"} and varying != "sugar":
        return (
            f"P_sugar{active_fixed['sugar']:g}Hz_"
            f"{varying}{float(frequency):g}Hz"
        )
    return f"S_{varying}_{float(frequency):g}Hz"


def point_at(
    rows: pd.DataFrame, varying: str, fixed_rates: dict[str, float], frequency: float,
) -> dict:
    rate_col = f"{varying}_hz"
    exact = rows[rows[rate_col].astype(float).eq(float(frequency))]
    if not exact.empty:
        row = exact.iloc[0]
        return {"frequency": frequency, "mean": float(row[MEAN]), "std": float(row[STD]), "note": ""}
    cond_id = requested_cond_id(varying, fixed_rates, frequency)
    raise ValueError(
        f"Missing fixed-path condition {cond_id}; chosen levels must be measured "
        "directly (interpolation is disabled)"
    )


def point_text(point: dict) -> str:
    text = f"{point['mean']:.1f} ± {point['std']:.1f}"
    return f"{text} ({point['note']})" if point["note"] else text


def evaluated_curve(
    label: str, frame: pd.DataFrame, varying: str, fixed_rates: dict[str, float],
) -> dict:
    rows = curve_rows(frame, varying, fixed_rates)
    _, threshold = curve_stats([row for _, row in rows.iterrows()])
    return {
        "label": label, "rows": rows, "varying": varying,
        "fixed_rates": fixed_rates, "threshold": threshold,
    }


def pair_pass(curve: dict, a: float, b: float) -> tuple[bool, dict, dict, float]:
    pa = point_at(curve["rows"], curve["varying"], curve["fixed_rates"], a)
    pb = point_at(curve["rows"], curve["varying"], curve["fixed_rates"], b)
    delta = pb["mean"] - pa["mean"]
    return abs(delta) >= curve["threshold"], pa, pb, delta


def _pair_pass_if_measured(curve: dict, a: float, b: float) -> bool:
    """A candidate pair counts only on curves where both points were measured directly."""
    try:
        return pair_pass(curve, a, b)[0]
    except ValueError:
        return False


def adjustment_for_pair(
    levels: list[float], pair_index: int, curves: list[dict]
) -> dict | None:
    measured = sorted({
        float(value)
        for curve in curves
        for value in curve["rows"][f"{curve['varying']}_hz"]
    })
    candidates = []
    for level_index in (pair_index, pair_index + 1):
        old = levels[level_index]
        lower = levels[level_index - 1] if level_index else -math.inf
        upper = levels[level_index + 1] if level_index + 1 < len(levels) else math.inf
        for new in measured:
            if new == old or not (lower < new < upper):
                continue
            changed = levels.copy()
            changed[level_index] = new
            a, b = changed[pair_index:pair_index + 2]
            if any(_pair_pass_if_measured(curve, a, b) for curve in curves):
                candidates.append((abs(new - old), new, level_index, old))
    if not candidates:
        return None
    _, new, level_index, old = min(candidates)
    return {"level_index": level_index, "old": old, "new": new}


def distinguishability_sections(
    fixed: pd.DataFrame, levels_config: dict,
) -> tuple[list[str], bool, list[dict]]:
    configurations = {
        "sugar": [evaluated_curve("S_sugar alone (fixed)", fixed, "sugar", {})],
        "bitter": [evaluated_curve("P_sugar200Hz_bitter (fixed)", fixed, "bitter", {"sugar": 200})],
        "water": [
            evaluated_curve("S_water alone (fixed)", fixed, "water", {}),
            evaluated_curve("P_sugar200Hz_water (fixed)", fixed, "water", {"sugar": 200}),
            evaluated_curve("P_sugar60Hz_water (fixed)", fixed, "water", {"sugar": 60}),
            evaluated_curve("P_sugar100Hz_water (fixed)", fixed, "water", {"sugar": 100}),
        ],
        "ir94e": [evaluated_curve("P_sugar200Hz_ir94e (fixed)", fixed, "ir94e", {"sugar": 200})],
    }
    lines: list[str] = []
    all_dimensions_pass = True
    suggestions: list[dict] = []
    for dimension in CHANNELS:
        mapping = levels_config["levels"][dimension]
        names = list(mapping.keys())
        frequencies = [float(value) for value in mapping.values()]
        curves = configurations[dimension]
        lines += [f"### {dimension}", "", "| pair | curve | value_a | value_b | Δ | threshold | distinguishable? |", "|---|---|---:|---:|---:|---:|---|"]
        dimension_pass = True
        for index, (a, b) in enumerate(zip(frequencies, frequencies[1:])):
            if a == b:
                lines.append(
                    f"| {names[index]} {a:g}→{names[index + 1]} {b:g} | shared grid cell "
                    f"(identical Hz; levels deliberately not separated) | — | — | — | — | n/a |"
                )
                continue
            passes = []
            for curve in curves:
                passed, pa, pb, delta = pair_pass(curve, a, b)
                passes.append(passed)
                lines.append(
                    f"| {names[index]} {a:g}→{names[index + 1]} {b:g} | "
                    f"{curve['label']} | {point_text(pa)} | {point_text(pb)} | "
                    f"{delta:+.1f} | {curve['threshold']:.1f} | {'yes' if passed else 'no'} |"
                )
            if not any(passes):
                dimension_pass = False
                suggestion = adjustment_for_pair(frequencies, index, curves)
                suggestions.append({
                    "dimension": dimension,
                    "pair": f"{names[index]}→{names[index + 1]}",
                    "suggestion": suggestion,
                    "names": names,
                })
        lines += ["", f"all chosen levels pairwise distinguishable: {'yes' if dimension_pass else 'no'}", ""]
        all_dimensions_pass &= dimension_pass
    return lines, all_dimensions_pass, suggestions


def suggestion_lines(suggestions: list[dict]) -> list[str]:
    lines = ["## Suggested minimal adjustments", ""]
    if not suggestions:
        return lines + ["No adjustments suggested; every adjacent chosen pair passes.", ""]
    lines += ["| dimension | collapsed pair | suggested one-level move |", "|---|---|---|"]
    for item in suggestions:
        suggestion = item["suggestion"]
        if suggestion is None:
            text = "no single measured-point move restores this pair while preserving order"
        else:
            level = item["names"][suggestion["level_index"]]
            text = f"move {level} from {suggestion['old']:g} Hz to {suggestion['new']:g} Hz"
        lines.append(f"| {item['dimension']} | {item['pair']} | {text} |")
    return lines + [""]


def analyze(args: argparse.Namespace) -> int:
    fixed = load_summary(args.results)
    prefix = load_summary(args.prefix)
    levels = json.loads((ROOT / "data" / "grid_levels.json").read_text(encoding="utf-8"))
    distinguishability, all_pass, suggestions = distinguishability_sections(fixed, levels)
    lines = [
        "# Fixed-path recheck", "",
        "## Fixed versus pre-fix Phase 1 deltas (informational; not part of the verdict)", "",
        *delta_table(fixed, prefix), "", "Values with |Δ| > 3 Hz are bold.", "",
        "## Phase 0 condition A deltas", "", *phase0_delta_lines(args.phase0_fixed), "",
        "## Chosen-level distinguishability", "", *distinguishability,
        *suggestion_lines(suggestions),
        f"Grid may start: {'YES' if all_pass else 'NO — see adjustments'}",
    ]
    output = rooted(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(["## Chosen-level distinguishability", "", *distinguishability, f"Grid may start: {'YES' if all_pass else 'NO — see adjustments'}"]))
    print(f"wrote {output}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--n-proc", type=int, default=14)
    run_parser.add_argument("--batch-size", type=int, default=40)
    run_parser.add_argument("--n-trials", type=int, default=30)
    run_parser.add_argument("--force", action="store_true")
    run_parser.add_argument(
        "--list", action="store_true",
        help="list the final deduplicated condition IDs without running them",
    )
    run_parser.set_defaults(function=run_recheck)
    analyze_parser = subparsers.add_parser("analyze")
    analyze_parser.add_argument("--results", type=Path, default=Path("results/phase1_fixed/characterize"))
    analyze_parser.add_argument("--prefix", type=Path, default=Path("results/phase1/characterize"))
    analyze_parser.add_argument("--phase0-fixed", type=Path, default=Path("results/phase0_fixed/full"))
    analyze_parser.add_argument("--out", type=Path, default=Path("docs/fixed_path_recheck.md"))
    analyze_parser.set_defaults(function=analyze)
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if "--analyze-only" in arguments:
        arguments.remove("--analyze-only")
        if arguments and arguments[0] in ("run", "analyze"):
            raise ValueError("--analyze-only is an alias for the analyze subcommand")
        arguments.insert(0, "analyze")
    args = build_parser().parse_args(arguments)
    return args.function(args)


if __name__ == "__main__":
    raise SystemExit(main())
