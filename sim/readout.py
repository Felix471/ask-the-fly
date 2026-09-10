# SPDX-License-Identifier: MIT
# Derived from Shiu et al. (2024) model.py, used under the MIT License.
"""MN9 readout calculations for simulation spike tables."""

from __future__ import annotations

import numpy as np
import pandas as pd


def mn9_rate(df_spikes: pd.DataFrame, protocol: dict, n_trials: int) -> dict:
    """Return per-side and protocol-aggregated MN9 rates across trials."""
    if n_trials <= 0:
        raise ValueError("n_trials must be positive")
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

