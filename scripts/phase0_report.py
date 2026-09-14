#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Generate the Markdown report for Phase-0 sanity or full results."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "phase0_report.md"
COND_RE = re.compile(
    r"^(?:"
    r"A_sugar_dose_sugar(?P<a>\d+(?:\.\d+)?)Hz_bitter0Hz|"
    r"B_bitter_suppression_sugar200Hz_bitter(?P<b>\d+(?:\.\d+)?)Hz|"
    r"C_bitter_alone_sugar0Hz_bitter(?P<c>\d+(?:\.\d+)?)Hz|"
    r"(?P<d>D_baseline)|"
    r"A_prime_sugar_bench21_sugar(?P<ap>\d+(?:\.\d+)?)Hz"
    r")$"
)
REQUIRED_COLUMNS = {
    "cond_id", "mn9_left_mean_hz", "mn9_left_std_hz",
    "mn9_right_mean_hz", "mn9_right_std_hz",
    "mn9_aggregated_mean_hz", "mn9_aggregated_std_hz",
    "n_trials", "walltime_s",
}


def fmt(value: float) -> str:
    return f"{value:.1f}"


def pm(row: pd.Series, prefix: str = "mn9_aggregated") -> str:
    return f"{fmt(row[f'{prefix}_mean_hz'])} ± {fmt(row[f'{prefix}_std_hz'])}"


def ratio(numerator: float, denominator: float) -> str:
    return "N/A" if denominator == 0 else fmt(numerator / denominator)


def sequence(rows: list[tuple[float, pd.Series]]) -> str:
    return ", ".join(f"{freq:g} Hz: {fmt(row.mn9_aggregated_mean_hz)} Hz" for freq, row in rows)


def parse_rows(frame: pd.DataFrame) -> dict[str, list[tuple[float, pd.Series]]]:
    groups = {key: [] for key in ("A", "B", "C", "D", "A_prime")}
    for _, row in frame.iterrows():
        match = COND_RE.fullmatch(str(row.cond_id))
        if not match:
            raise ValueError(f"Unrecognized cond_id: {row.cond_id}")
        if match["a"] is not None:
            key, freq = "A", float(match["a"])
        elif match["b"] is not None:
            key, freq = "B", float(match["b"])
        elif match["c"] is not None:
            key, freq = "C", float(match["c"])
        elif match["ap"] is not None:
            key, freq = "A_prime", float(match["ap"])
        else:
            key, freq = "D", 0.0
        groups[key].append((freq, row))
    for rows in groups.values():
        rows.sort(key=lambda item: item[0])
    return groups


def elapsed(meta: dict) -> str:
    if not meta.get("start_time") or not meta.get("end_time"):
        return "not available"
    try:
        seconds = (datetime.fromisoformat(meta["end_time"]) -
                   datetime.fromisoformat(meta["start_time"])).total_seconds()
        return f"{fmt(seconds)} s"
    except (TypeError, ValueError):
        return "not available"


def provenance_note() -> list[str]:
    pre_path = ROOT / "results" / "phase0" / "full" / "summary.csv"
    fixed_path = ROOT / "results" / "phase0_fixed" / "full" / "summary.csv"
    measurement = "pending"
    if pre_path.exists() and fixed_path.exists():
        cond_id = "A_sugar_dose_sugar100Hz_bitter0Hz"
        pre = pd.read_csv(pre_path).set_index("cond_id")
        fixed = pd.read_csv(fixed_path).set_index("cond_id")
        if cond_id in pre.index and cond_id in fixed.index:
            pre_mean = float(pre.loc[cond_id, "mn9_aggregated_mean_hz"])
            fixed_mean = float(fixed.loc[cond_id, "mn9_aggregated_mean_hz"])
            measurement = (
                f"{fixed_mean - pre_mean:+.1f} Hz (pre-fix {pre_mean:.1f}, "
                f"fixed {fixed_mean:.1f})"
            )
    return [
        "## Provenance note (2026-09-10)", "",
        "This report was produced with the reusable Brian2 path BEFORE the refractory fix of 2026-09-10: every stimulable GRN (sugar, bitter) had its refractory period set to 0 at build time, whereas the paper's model.py sets rfc = 0 only for neurons that receive Poisson input. The equivalence study (docs/equivalence_study.md) measured the pure effect of this rule with the random stream held fixed: zero (10/10 seeds spike-for-spike identical at sugar 100 Hz, bitter 0 Hz), i.e. the undriven GRNs never fired in that condition. The rule was corrected for fidelity to model.py, not because it changes results. Any difference between pre-fix and fixed runs is sampling noise from different random streams (the stimulus group size changed the draws). The lookup grid uses the corrected per-channel rule. Measured delta at sugar 100 Hz, fixed minus pre-fix (condition A, 30 trials each): "
        + measurement + ". See docs/fixed_path_recheck.md.", "",
    ]


def results_table(groups: dict[str, list[tuple[float, pd.Series]]]) -> list[str]:
    lines = [
        "| Gate | Stimulus | Aggregated mean ± std (Hz) | Left mean ± std (Hz) | Right mean ± std (Hz) | Right/left | n trials |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    labels = {
        "A": "sugar", "B": "bitter (sugar 200 Hz)", "C": "bitter alone",
        "D": "baseline", "A_prime": "sugar (benchmark 21 IDs)",
    }
    for key in ("A", "B", "C", "D", "A_prime"):
        for freq, row in groups[key]:
            stimulus = "0 Hz" if key == "D" else f"{freq:g} Hz {labels[key]}"
            gate = "A'" if key == "A_prime" else key
            lr = ratio(row.mn9_right_mean_hz, row.mn9_left_mean_hz)
            lines.append(
                f"| {gate} | {stimulus} | {pm(row)} | {pm(row, 'mn9_left')} | "
                f"{pm(row, 'mn9_right')} | {lr} | {int(row.n_trials)} |"
            )
    return lines


def generate(stage: str) -> str:
    protocol = json.loads((ROOT / "data" / "stim_protocol.json").read_text(encoding="utf-8"))
    stage_dir = ROOT / "results" / "phase0" / stage
    frame = pd.read_csv(stage_dir / "summary.csv")
    missing = REQUIRED_COLUMNS - set(frame.columns)
    if missing:
        raise ValueError("Missing summary columns: " + ", ".join(sorted(missing)))
    meta = json.loads((stage_dir / "run_meta.json").read_text(encoding="utf-8"))
    groups = parse_rows(frame)
    expected_trials = int(protocol["trial"]["sanity_n_trials" if stage == "sanity" else "n_trials"])

    baseline = groups["D"][0][1] if len(groups["D"]) == 1 else None
    d_pass = baseline is not None and int(baseline.n_trials) >= expected_trials
    d_mean = float(baseline.mn9_aggregated_mean_hz) if baseline is not None else float("nan")
    d_std = float(baseline.mn9_aggregated_std_hz) if baseline is not None else float("nan")

    a_values = [float(row.mn9_aggregated_mean_hz) for _, row in groups["A"]]
    a_ordered = bool(a_values) and all(
        right > left or (left == 0 and right == 0)
        for left, right in zip(a_values, a_values[1:])
    )
    a_200 = next((value for (freq, _), value in zip(groups["A"], a_values) if freq == 200), None)
    a_pass = baseline is not None and a_ordered and a_200 is not None and a_200 > d_mean + 5 * d_std + 5

    b_values = [float(row.mn9_aggregated_mean_hz) for _, row in groups["B"]]
    b_ordered = bool(b_values) and all(right <= left for left, right in zip(b_values, b_values[1:]))
    b0 = next((value for (freq, _), value in zip(groups["B"], b_values) if freq == 0), None)
    strongest = b_values[-1] if b_values else None
    b_pass = b_ordered and b0 is not None and strongest is not None and strongest < 0.5 * b0

    c_limit = d_mean + 2 * d_std + 1 if baseline is not None else float("nan")
    c_pass = baseline is not None and bool(groups["C"]) and all(
        float(row.mn9_aggregated_mean_hz) <= c_limit for _, row in groups["C"]
    )
    passes = {"A": a_pass, "B": b_pass, "C": c_pass, "D": d_pass}

    start = str(meta.get("start_time", "unknown"))
    lines = [
        f"# Phase 0 report — {stage}", "", "## Run metadata", "",
        "| Field | Value |", "|---|---|",
        f"| Stage | {stage} |", f"| Run date | {start} |",
        f"| Git commit | {meta.get('git_commit', 'unknown')} |",
        f"| brian2 version | {meta.get('brian2_version', 'unknown')} |",
        f"| Codegen target | {meta.get('codegen_target', 'unknown')} |",
        f"| n_proc | {meta.get('n_proc', 'unknown')} |",
        f"| Protocol sha256 | {meta.get('protocol_sha256', 'unknown')} |",
        f"| Cells sha256 | {meta.get('cells_sha256', 'unknown')} |",
        f"| Total simulated trials | {int(frame.n_trials.sum())} |",
        f"| Parallel walltime | {elapsed(meta)} |", "",
        *provenance_note(),
        "The paper calibrated w_syn on FlyWire v630; all runs here use v783 only. Absolute Hz may therefore differ from the paper; directions are the acceptance criteria.", "",
        "MN9 aggregation = left_only (contralateral to the right-hemisphere sugar GRNs), frozen in data/stim_protocol.json.", "",
        "## Results", "", *results_table(groups), "", "## Hard gates", "",
        f"- **Gate A: {'PASS' if a_pass else 'FAIL'}.** Sugar sequence: {sequence(groups['A']) or 'missing'}. The 200 Hz response must be far above baseline (> D + 5×sd_D + 5 Hz).",
    ]
    suppressions = "missing"
    if b0 is not None:
        suppressions = ", ".join(
            f"{freq:g} Hz: {fmt(100 * (1 - float(row.mn9_aggregated_mean_hz) / b0))}%"
            if b0 != 0 else f"{freq:g} Hz: N/A"
            for freq, row in groups["B"]
        )
    lines += [
        f"- **Gate B: {'PASS' if b_pass else 'FAIL'}.** Bitter sequence: {sequence(groups['B']) or 'missing'}. Percent suppression: {suppressions}.",
        f"- **Gate C: {'PASS' if c_pass else 'FAIL'}.** Bitter-alone sequence: {sequence(groups['C']) or 'missing'}. Limit: {fmt(c_limit)} Hz." if baseline is not None else f"- **Gate C: FAIL.** Baseline is missing, so the bitter-alone limit cannot be calculated.",
        f"- **Gate D: {'PASS' if d_pass else 'FAIL'}.** Baseline aggregated MN9: {pm(baseline) if baseline is not None else 'missing'} Hz; required trials: {expected_trials}. The model has no intrinsic activity, so 0 Hz is expected.", "",
        f"**Overall: {'PASS' if all(passes.values()) else 'FAIL'}** (A–D must all pass).", "", "## Soft indicators", "",
    ]
    amap = {freq: row for freq, row in groups["A"]}
    if 100 in amap and 200 in amap and float(amap[200].mn9_aggregated_mean_hz) != 0:
        sugar_value = float(amap[100].mn9_aggregated_mean_hz) / float(amap[200].mn9_aggregated_mean_hz)
        sugar_ratio = f"{fmt(sugar_value)} ({fmt(100 * sugar_value)}%)"
    else:
        sugar_ratio = "N/A"
    bitter_200 = next((row for freq, row in groups["B"] if freq == 200), None)
    bitter_soft = "N/A" if b0 in (None, 0) or bitter_200 is None else f"{fmt(100 * (1 - float(bitter_200.mn9_aggregated_mean_hz) / b0))}%"
    lines += [
        f"- Sugar@100 / sugar@200 = {sugar_ratio}, compared with the paper's calibration statement: \"W_syn chosen so that sugar GRN activation at 100 Hz gives roughly 80% of maximal MN9 firing\" (Shiu et al. 2024 Methods). The paper does not define \"maximal\"; we use the 200 Hz value as the denominator, so this comparison is provisional.",
        f"- Bitter suppression at 200/200 Hz = {bitter_soft}, versus the ≥70% target. This is provisional because the paper gives no number in text (Fig. 3b heatmap only).",
        "- Right/left ratios are shown per condition in the Results table. The paper reports contralateral (left) MN9 responding more strongly to right-hemisphere sugar GRNs.",
    ]

    if stage == "full":
        lines += ["", "## Appendix A'", "", "A' uses benchmark.py's 21 sugar IDs instead of the notebook's 23 (20 IDs in common). It does not affect gates.", "",
                  "| Sugar frequency | A aggregated mean ± std (Hz) | A' aggregated mean ± std (Hz) | Absolute difference (Hz) | Percent difference vs A |",
                  "|---:|---:|---:|---:|---:|"]
        apmap = {freq: row for freq, row in groups["A_prime"]}
        for freq in sorted(set(amap) | set(apmap)):
            arow, aprow = amap.get(freq), apmap.get(freq)
            if arow is None or aprow is None:
                lines.append(f"| {freq:g} Hz | {pm(arow) if arow is not None else 'missing'} | {pm(aprow) if aprow is not None else 'missing'} | N/A | N/A |")
            else:
                diff = abs(float(aprow.mn9_aggregated_mean_hz) - float(arow.mn9_aggregated_mean_hz))
                pct = "N/A" if float(arow.mn9_aggregated_mean_hz) == 0 else f"{fmt(100 * diff / float(arow.mn9_aggregated_mean_hz))}%"
                lines.append(f"| {freq:g} Hz | {pm(arow)} | {pm(aprow)} | {fmt(diff)} | {pct} |")

    equiv_path = ROOT / "results" / "phase0" / "equiv" / "summary.csv"
    lines += ["", "## Equivalence", ""]
    consumed = [stage_dir / f"{cond_id}.parquet" for cond_id in frame.cond_id]
    if equiv_path.exists():
        equiv = pd.read_csv(equiv_path).set_index("cond_id")
        names = ("reusable_sugar100Hz", "legacy_sugar100Hz")
        if all(name in equiv.index for name in names):
            one, two = (equiv.loc[name] for name in names)
            overlap = max(one.mn9_aggregated_mean_hz - one.mn9_aggregated_std_hz, two.mn9_aggregated_mean_hz - two.mn9_aggregated_std_hz) <= min(one.mn9_aggregated_mean_hz + one.mn9_aggregated_std_hz, two.mn9_aggregated_mean_hz + two.mn9_aggregated_std_hz)
            lines += ["| Implementation | Aggregated mean ± std (Hz) | Left mean ± std (Hz) | Right mean ± std (Hz) | Walltime (s) |", "|---|---:|---:|---:|---:|",
                      f"| Reusable | {pm(one)} | {pm(one, 'mn9_left')} | {pm(one, 'mn9_right')} | {fmt(one.walltime_s)} |",
                      f"| Legacy | {pm(two)} | {pm(two, 'mn9_left')} | {pm(two, 'mn9_right')} | {fmt(two.walltime_s)} |", "",
                      f"The ±1 std intervals {'overlap' if overlap else 'do not overlap'}." ]
            consumed += [equiv_path.parent / f"{name}.parquet" for name in names]
        else:
            lines.append("Equivalence summary is incomplete.")
    else:
        lines.append("not run yet")

    torch_path = ROOT / "results" / "phase0_torch" / "full" / "summary.csv"
    lines += ["", "## Backend cross-check (PyTorch CUDA, conditions A and D)", ""]
    if torch_path.exists() and stage == "full":
        torch_frame = pd.read_csv(torch_path)
        torch_groups = parse_rows(torch_frame)
        torch_meta_path = torch_path.parent / "run_meta.json"
        torch_meta = json.loads(torch_meta_path.read_text(encoding="utf-8")) if torch_meta_path.exists() else {}
        t_values = [float(row.mn9_aggregated_mean_hz) for _, row in torch_groups["A"]]
        t_ordered = bool(t_values) and all(
            right > left or (left == 0 and right == 0) for left, right in zip(t_values, t_values[1:])
        )
        b2_200 = a_200
        t_200 = next((value for (freq, _), value in zip(torch_groups["A"], t_values) if freq == 200), None)
        same_magnitude = (
            b2_200 is not None and t_200 is not None and b2_200 > 0 and t_200 > 0
            and 0.1 <= t_200 / b2_200 <= 10.0
        )
        within_15 = b2_200 is not None and t_200 is not None and b2_200 > 0 and abs(t_200 / b2_200 - 1) <= 0.15
        lines += [
            f"Device: {torch_meta.get('device_name', 'unknown')}; torch {torch_meta.get('torch_version', 'unknown')}; float32; batched trials.",
            "",
            "| Condition | Brian2 aggregated (Hz) | PyTorch aggregated (Hz) | PyTorch / Brian2 |",
            "|---|---:|---:|---:|",
        ]
        b2_lookup = {freq: row for freq, row in groups["A"]}
        for freq, trow in torch_groups["A"]:
            brow = b2_lookup.get(freq)
            if brow is None:
                continue
            lines.append(
                f"| {freq:g} Hz sugar | {pm(brow)} | {pm(trow)} | {ratio(float(trow.mn9_aggregated_mean_hz), float(brow.mn9_aggregated_mean_hz))} |"
            )
        if torch_groups["D"] and baseline is not None:
            lines.append(f"| baseline | {pm(baseline)} | {pm(torch_groups['D'][0][1])} | N/A |")
        lines += [
            "",
            f"- **Hard gate (same monotonic direction and same order of magnitude at 200 Hz): {'PASS' if (t_ordered and same_magnitude) else 'FAIL'}.**",
            f"- Soft reference (within ±15% at 200 Hz): {'met' if within_15 else 'not met'}"
            + (f" (PyTorch/Brian2 = {ratio(t_200, b2_200)})." if t_200 is not None and b2_200 else "."),
            "- The soft reference is informational only, not a veto. Brian2 CPU remains ground truth.",
        ]
        consumed += [torch_path.parent / f"{cond_id}.parquet" for cond_id in torch_frame.cond_id]
    else:
        lines.append("not run yet")

    lines += ["", "## Files", ""] + [f"- `{path.relative_to(ROOT).as_posix()}`" for path in consumed]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=("sanity", "full"), default="full")
    args = parser.parse_args()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(generate(args.stage), encoding="utf-8")
    print(f"wrote {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
