# SPDX-License-Identifier: MIT
# Derived from Shiu et al. (2024) model.py, used under the MIT License.
"""Reusable Brian2 implementation of the Shiu et al. fly-brain model."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from textwrap import dedent
from typing import Mapping, Sequence

import numpy as np
import pandas as pd
from brian2 import (
    Hz,
    Network,
    NeuronGroup,
    PoissonGroup,
    SpikeMonitor,
    Synapses,
    defaultclock,
    mV,
    ms,
    prefs,
    second,
    seed as brian_seed,
)


# Compiling on drvfs is extremely slow. This assignment deliberately happens at
# module import, before this module can construct any Brian object.
prefs.codegen.runtime.cython.cache_dir = os.path.expanduser("~/.cache/brian2_flybrain")
prefs.codegen.target = "cython"

ROOT = Path(__file__).resolve().parents[1]


def _rooted(path: str | Path) -> Path:
    path = Path(path)
    return path if path.is_absolute() else ROOT / path


def load_protocol(path: str | Path = "data/stim_protocol.json") -> dict:
    """Load the frozen stimulation protocol."""
    return json.loads(_rooted(path).read_text(encoding="utf-8"))


def load_cells(path: str | Path = "data/cells.json") -> dict:
    """Load the frozen FlyWire cell sets."""
    return json.loads(_rooted(path).read_text(encoding="utf-8"))


def channel_cell_sets(protocol: dict, overrides: Mapping[str, str] | None = None) -> dict[str, str]:
    """Return channel-to-cell-set mappings, with optional condition overrides."""
    result = {
        channel: description["cell_set"]
        for channel, description in protocol["stimulus"]["channels"].items()
    }
    if overrides:
        result.update(overrides)
    return result


@dataclass
class SimNet:
    """A compiled network whose initial state is restored before every trial."""

    net: Network
    neurons: NeuronGroup
    poisson: PoissonGroup
    monitor: SpikeMonitor
    channel_slices: dict[str, slice]
    i2flyid: dict[int, int]
    target_indices: np.ndarray = None
    t_rfc: object = None
    rate_based_refractory: bool = True

    def set_rates(self, rates: Mapping[str, float]) -> None:
        """Set stimulus rates and, by default, apply model.py's refractory rule.

        model.py sets rfc = 0 only for neurons that receive Poisson input in the
        current experiment. The reusable network holds every stimulable GRN, so
        the rule is applied per trial: channels with a nonzero rate get rfc = 0,
        every other stimulable GRN keeps t_rfc. (Equivalence study, 2026-09-10.)
        """
        unknown = set(rates) - set(self.channel_slices)
        if unknown:
            raise KeyError(f"Unknown stimulus channel(s): {sorted(unknown)}")
        self.poisson.rates = 0 * Hz
        for channel, hz in rates.items():
            if hz < 0:
                raise ValueError(f"Negative rate for {channel}: {hz}")
            self.poisson.rates[self.channel_slices[channel]] = float(hz) * Hz
        if self.rate_based_refractory:
            for channel, sl in self.channel_slices.items():
                driven = float(rates.get(channel, 0.0)) > 0
                idx = np.unique(self.target_indices[sl])
                self.neurons.rfc[idx] = 0 * ms if driven else self.t_rfc

    def run_trial(self, rates: dict[str, float], seed: int, duration_ms: float) -> dict[int, np.ndarray]:
        """Restore, stimulate, run, and return seconds keyed by FlyWire ID."""
        self.net.restore("init")
        self.set_rates(rates)
        brian_seed(int(seed))
        self.net.run(float(duration_ms) * ms)
        return {
            self.i2flyid[int(index)]: np.asarray(times / second, dtype=float)
            for index, times in self.monitor.spike_trains().items()
            if len(times)
        }


def build_network(
    protocol: dict,
    cells: dict,
    stim_channels: Mapping[str, str] | Sequence[str],
    zero_refractory_for: Sequence[str] | set[str] | None = None,
    silence_ids: Sequence[int] | None = None,
) -> SimNet:
    """Build and store one resettable connectome network.

    By default every built stimulus channel retains the historical ``rfc=0``
    behaviour.  Passing channel names limits that change to those channels.

    ``silence_ids``: FlyWire IDs whose synapses are removed from the network
    (every incoming and outgoing weight set to 0, as in the silencing experiments
    of Tastekin et al. 2026). The neurons stay in the group but can neither drive
    nor be driven; the network's own dynamics are otherwise untouched.
    """
    if isinstance(stim_channels, Mapping):
        channels = dict(stim_channels)
    else:
        defaults = channel_cell_sets(protocol)
        channels = {channel: defaults[channel] for channel in stim_channels}

    model = protocol["model"]
    params = {
        "v_0": float(model["v_0_mV"]) * mV,
        "v_rst": float(model["v_rst_mV"]) * mV,
        "v_th": float(model["v_th_mV"]) * mV,
        "t_mbr": float(model["t_mbr_ms"]) * ms,
        "tau": float(model["tau_ms"]) * ms,
        "t_rfc": float(model["t_rfc_ms"]) * ms,
        "t_dly": float(model["t_dly_ms"]) * ms,
        "w_syn": float(model["w_syn_mV"]) * mV,
        "f_poi": float(model["f_poi"]),
    }
    eqs = dedent(""" 
                    dv/dt = (v_0 - v + g) / t_mbr : volt (unless refractory)
                    dg/dt = -g / tau               : volt (unless refractory) 
                    rfc                            : second
                    """)
    defaultclock.dt = float(model["dt_ms"]) * ms

    completeness = pd.read_csv(_rooted(protocol["completeness_file"]), index_col=0)
    connectivity = pd.read_parquet(_rooted(protocol["connectivity_file"]))
    flyids = [int(value) for value in completeness.index]
    flyid2i = {flyid: index for index, flyid in enumerate(flyids)}
    i2flyid = dict(enumerate(flyids))

    neurons = NeuronGroup(
        N=len(completeness),
        model=eqs,
        method=model["integration"],
        threshold="v > v_th",
        reset='v = v_rst; w = 0; g = 0 * mV',
        refractory="rfc",
        name="default_neurons",
        namespace=params,
    )
    neurons.v = params["v_0"]
    neurons.g = 0
    neurons.rfc = params["t_rfc"]

    synapses = Synapses(
        neurons,
        neurons,
        "w : volt",
        on_pre="g += w",
        delay=params["t_dly"],
        name="default_synapses",
    )
    synapses.connect(
        i=connectivity["Presynaptic_Index"].to_numpy(),
        j=connectivity["Postsynaptic_Index"].to_numpy(),
    )
    weights = connectivity["Excitatory x Connectivity"].to_numpy() * params["w_syn"]
    if silence_ids:
        missing = [int(flyid) for flyid in silence_ids if int(flyid) not in flyid2i]
        if missing:
            raise ValueError(f"silence_ids absent from the connectome: {missing}")
        silenced = np.array([flyid2i[int(flyid)] for flyid in silence_ids])
        pre = connectivity["Presynaptic_Index"].to_numpy()
        post = connectivity["Postsynaptic_Index"].to_numpy()
        mask = np.isin(pre, silenced) | np.isin(post, silenced)
        weights = np.where(mask, 0.0, weights / mV) * mV
    synapses.w = weights

    target_indices: list[int] = []
    channel_slices: dict[str, slice] = {}
    for channel, cell_set in channels.items():
        ids = cells["sets"][cell_set]["ids"]
        missing = [int(flyid) for flyid in ids if int(flyid) not in flyid2i]
        if missing:
            raise ValueError(f"{cell_set} contains IDs absent from the connectome: {missing}")
        start = len(target_indices)
        target_indices.extend(flyid2i[int(flyid)] for flyid in ids)
        channel_slices[channel] = slice(start, len(target_indices))

    poisson = PoissonGroup(len(target_indices), rates=0 * Hz, name="stimulus_poisson")
    stimulus = Synapses(
        poisson,
        neurons,
        "w_stim : volt (constant)",
        on_pre="v += w_stim",
        name="stimulus_synapses",
    )
    stimulus.connect(i=np.arange(len(target_indices)), j=np.asarray(target_indices))
    stimulus.w_stim = params["w_syn"] * params["f_poi"]
    # Default (zero_refractory_for=None): no build-time zeroing; SimNet.set_rates
    # applies model.py's rule per trial (rfc = 0 only for driven channels).
    # Explicit zero_refractory_for = experiment mode: fixed build-time zeroing,
    # and set_rates leaves rfc alone.
    rate_based = zero_refractory_for is None
    if not rate_based:
        zero_channels = set(zero_refractory_for)
        unknown = zero_channels - set(channels)
        if unknown:
            raise KeyError(f"Unknown zero-refractory channel(s): {sorted(unknown)}")
        zero_indices = [
            index
            for channel in zero_channels
            for index in target_indices[channel_slices[channel]]
        ]
        if zero_indices:
            neurons.rfc[np.unique(zero_indices)] = 0 * ms

    monitor = SpikeMonitor(neurons)
    net = Network(neurons, synapses, poisson, stimulus, monitor)
    net.store("init")
    return SimNet(
        net, neurons, poisson, monitor, channel_slices, i2flyid,
        target_indices=np.asarray(target_indices), t_rfc=params["t_rfc"],
        rate_based_refractory=rate_based,
    )
