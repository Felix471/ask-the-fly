# SPDX-License-Identifier: MIT
# Derived from Shiu et al. (2024) model.py, used under the MIT License.
"""MN9 readout calculations for simulation spike tables."""

from __future__ import annotations

import numpy as np
import pandas as pd


def mn9_rate(df_spikes: pd.DataFrame, protocol: dict, n_trials: int, completed_trials=None) -> dict:
    """Return per-side and protocol-aggregated MN9 rates across trials.

    A trial with no MN9 spike leaves no row, so the frame alone cannot tell a
    silent trial from a trial that never ran. When `completed_trials` (the run
    ledger) is given, it must be exactly range(n_trials); otherwise a missing
    trial would be counted as zero firing (D01)."""
    if n_trials <= 0:
        raise ValueError("n_trials must be positive")
    if completed_trials is not None:
        completed = sorted(int(t) for t in completed_trials)
        if completed != list(range(n_trials)):
            raise ValueError(
                f"completed trials {completed} do not cover n_trials={n_trials}; "
                "missing trials are not zero firing"
            )
        if not df_spikes.empty:
            extra = sorted(set(int(t) for t in df_spikes["trial"].unique()) - set(completed))
            if extra:
                raise ValueError(f"spike rows for trials outside the ledger: {extra}")
    duration_s = float(protocol["trial"]["duration_ms"]) / 1000.0
    readout = protocol["readout"]

    def side(flywire_id: int) -> dict:
        rates = np.zeros(n_trials, dtype=float)
        if not df_spikes.empty:
            selected = df_spikes.loc[df_spikes["flywire_id"] == int(flywire_id)]
            counts = selected.groupby("trial").size()
            for trial, count in counts.items():
                trial = int(trial)
                if 0 <= trial < n_trials:
                    rates[trial] = float(count) / duration_s
        return {"mean": float(rates.mean()), "std": float(rates.std()), "trials": rates}

    left = side(int(readout["left"]))
    right = side(int(readout["right"]))
    aggregation = readout["aggregation"]
    if aggregation == "left_only":
        aggregated = left
    elif aggregation == "right_only":
        aggregated = right
    elif aggregation == "mean_sides":
        values = (left["trials"] + right["trials"]) / 2.0
        aggregated = {"mean": float(values.mean()), "std": float(values.std()), "trials": values}
    else:
        raise ValueError(f"Unsupported readout aggregation: {aggregation}")
    return {"left": left, "right": right, "aggregated": aggregated}

