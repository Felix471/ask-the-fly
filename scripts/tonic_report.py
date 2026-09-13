#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Tables for docs/tonic_inhibition.md from results/tonic/full/summary_tonic.csv (Phase T).

Reads the sweep summary written by sim/run_tonic.py, the frozen lookup table (for the drive-0
row check) and the replay run metadata, and rewrites the generated part of
docs/tonic_inhibition.md. The document's "## Reading" section and everything after it are
hand-written and kept verbatim.

  .venv\\Scripts\\python scripts/tonic_report.py
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "results" / "tonic" / "full" / "summary_tonic.csv"
RUN_META = ROOT / "results" / "tonic" / "full" / "run_meta.json"
REPLAY_META = ROOT / "results" / "tonic" / "replays" / "run_meta.json"
LOOKUP = ROOT / "data" / "lookup_table.json"
TONIC = ROOT / "data" / "stim_protocol_tonic.json"
OUT = ROOT / "docs" / "tonic_inhibition.md"
READING = "## Reading"
LEVELS = ["none", "low", "medium", "high", "very_high"]


def frozen_sugar_column() -> dict[str, dict]:
    table = json.loads(LOOKUP.read_text(encoding="utf-8"))
    return {c["sugar"]: c for c in table["cells"] if c["hz"]["bitter"] == 0 and c["hz"]["water"] == 0 and c["hz"]["ir94e"] == 0}


def grid(df: pd.DataFrame, brake: str, mean: str, std: str | None, fmt: str = "{:.1f}") -> list[str]:
    sub = df[df["brake"] == brake]
    drives = sorted(sub["drive_hz"].unique())
    head = "| drive (Hz) | " + " | ".join(f"sugar {lvl} ({int(sub[sub.sugar_level == lvl].sugar_hz.iloc[0])} Hz)" for lvl in LEVELS) + " |"
    lines = [head, "|---|" + "---:|" * len(LEVELS)]
    for d in drives:
        cells = []
        for lvl in LEVELS:
            row = sub[(sub.drive_hz == d) & (sub.sugar_level == lvl)].iloc[0]
            cells.append(fmt.format(row[mean]) + (f" ± {row[std]:.1f}" if std else ""))
        lines.append(f"| {int(d)} | " + " | ".join(cells) + " |")
    return lines


def main() -> int:
    for path, what in ((SUMMARY, "sweep summary"), (RUN_META, "sweep run_meta"), (REPLAY_META, "replay run_meta")):
        if not path.exists():
            sys.exit(f"missing {what}: {path} (run sim/run_tonic.py --stage full and --stage replays first)")
    df = pd.read_csv(SUMMARY)
    meta = json.loads(RUN_META.read_text(encoding="utf-8"))
    replays = json.loads(REPLAY_META.read_text(encoding="utf-8"))
    tonic = json.loads(TONIC.read_text(encoding="utf-8"))
    frozen = frozen_sugar_column()
    brakes = list(tonic["brakes"])
    n_trials = int(df["n_trials"].iloc[0])

    lines = [
        "# Phase T: tonic inhibition of MN9 (designed condition, uncalibrated)",
        "",
        f"Generated {date.today().isoformat()} by `scripts/tonic_report.py` from `results/tonic/full/summary_tonic.csv` "
        f"(run {meta['start_time'][:19]}Z, git {meta['git_commit'][:7]}, {meta['n_conditions']} conditions × {n_trials} trials, "
        f"{meta['n_proc']} workers, {meta['walltime_s']:.0f} s). The frozen protocol, cell sets, grid levels and lookup table were read, not written.",
        "",
        "## Method",
        "",
        "Tastekin et al. 2026 (Fig S17) hold MN9 down by driving an inhibitory premotor neuron (GNG015) continuously, then test sugar with and without a disinhibition node silenced. "
        "GNG015 has no FlyWire v783 match (OQ-5), so three brakes were chosen from the connectome by synapse count onto left MN9 (`docs/tonic_candidates.md`): "
        + "; ".join(f"**{name}** = {b['cell_type']} ({len(b['ids'])} cell{'s' if len(b['ids']) > 1 else ''}: {', '.join(str(i) for i in b['ids'])})" for name, b in tonic["brakes"].items())
        + ". Every choice here is ours and uncalibrated: the brake selection, the pairing with sugar only (bitter, water and ir94e at 0 Hz), and the drive level; 100 Hz is Tastekin's Fig S17 level for GNG015, their choice, and the 0 / 50 / 100 / 150 Hz sweep only shows sensitivity to it.",
        "",
        "Protocol: `data/stim_protocol_tonic.json` on top of the frozen `data/stim_protocol.json` (same dt, w_syn, f_poi, 1 s trials, seed base, connectome, GRN sets, MN9 readout). "
        "The brake cells are driven with the same mechanism as the GRN channels (one Poisson input per cell, weight w_syn × f_poi, refractory zeroed while driven). "
        f"Sugar takes the five grid levels; {n_trials} trials per condition, seed scheme v2 over the (brake, drive, sugar) product order. "
        "Runner: `sim/run_tonic.py` (one batch per brake through `sim.runner.run_conditions`, with its ledgers). Readouts per trial: left and right MN9 rate, mean rate of the brake cells, "
        "latency to the first left-MN9 spike, rate of the frozen sugar GRN set. Results: `results/tonic/full/` (gitignored). "
        "Adding the brake units to the stimulus PoissonGroup changes the random stream, so the drive-0 row is compared with the frozen grid statistically, not spike for spike.",
        "",
    ]

    lines += ["## Drive-0 row against the frozen grid (sugar-only column)", "",
              "| sugar | frozen grid left MN9 (30 trials) | " + " | ".join(f"{b} drive 0" for b in brakes) + " |",
              "|---|---:|" + "---:|" * len(brakes)]
    for lvl in LEVELS:
        f = frozen[lvl]
        cells = []
        for b in brakes:
            row = df[(df.brake == b) & (df.drive_hz == 0) & (df.sugar_level == lvl)].iloc[0]
            cells.append(f"{row.mn9_left_mean_hz:.1f} ± {row.mn9_left_std_hz:.1f}")
        lines.append(f"| {lvl} ({int(f['hz']['sugar'])} Hz) | {f['mn9_left_mean']:.1f} ± {f['mn9_left_std']:.1f} | " + " | ".join(cells) + " |")
    lines.append("")

    for b in brakes:
        lines += [f"## {b} ({tonic['brakes'][b]['cell_type']})", "",
                  f"### Left MN9 rate (Hz, mean ± sd over {n_trials} trials), drive × sugar", "", *grid(df, b, "mn9_left_mean_hz", "mn9_left_std_hz"), "",
                  "### Right MN9 rate (Hz, mean)", "", *grid(df, b, "mn9_right_mean_hz", None), "",
                  "### Brake cells' own rate (Hz, mean ± sd; mean over the brake's cells)", "", *grid(df, b, "brake_rate_mean_hz", "brake_rate_std_hz"), "",
                  "### Latency to the first left-MN9 spike (ms, median over trials with a spike; silent trials in brackets)", ""]
        sub = df[df.brake == b]
        head = "| drive (Hz) | " + " | ".join(f"sugar {lvl}" for lvl in LEVELS) + " |"
        lines += [head, "|---|" + "---:|" * len(LEVELS)]
        for d in sorted(sub.drive_hz.unique()):
            cells = []
            for lvl in LEVELS:
                row = sub[(sub.drive_hz == d) & (sub.sugar_level == lvl)].iloc[0]
                lat = "–" if pd.isna(row.latency_left_median_ms) else f"{row.latency_left_median_ms:.0f}"
                cells.append(f"{lat} [{int(row.trials_without_left_spike)}]")
            lines.append(f"| {int(d)} | " + " | ".join(cells) + " |")
        lines += ["", "### Sugar GRN set rate (Hz, sanity: follows the sugar drive, not the brake)", "", *grid(df, b, "sugar_grn_rate_mean_hz", None), ""]

    lines += ["## Replays", "",
              f"One whole-network trial per condition, `results/tonic/replays/<cond_id>.npz` (grid replay layout; seed rule {replays['seed_rule']}); not packed, not shipped.", "",
              "| cond_id | seed | spikes | left MN9 spikes |", "|---|---:|---:|---:|"]
    for r in replays["replays"]:
        lines.append(f"| {r['cond_id']} | {r['seed']} | {r['n_spikes']} | {r['left_mn9_spikes']} |")
    lines.append("")

    existing = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
    tail = existing[existing.index(READING):] if READING in existing else f"{READING}\n\n(hand-written)\n"
    OUT.write_text("\n".join(lines) + "\n" + tail, encoding="utf-8")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
