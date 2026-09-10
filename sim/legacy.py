# SPDX-License-Identifier: MIT
# Derived from Shiu et al. (2024) model.py, used under the MIT License.
"""Fresh-network PoissonInput reference path used only by equivalence tests."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent
from typing import Mapping

import numpy as np
import pandas as pd
from brian2 import (
    Hz,
    Network,
    NeuronGroup,
    PoissonInput,
    PoissonGroup,
    SpikeMonitor,
    Synapses,
    defaultclock,
    mV,
    ms,
    second,
    seed as brian_seed,
)

from sim.network import ROOT, _rooted


def run_trial(
    protocol: dict,
    cells: dict,
    stim_channels: Mapping[str, str],
    rates: Mapping[str, float],
    seed: int,
    duration_ms: float,
) -> dict[int, np.ndarray]:
    """Faithfully run model.py's fresh-network/PoissonInput trial path."""
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
    defaultclock.dt = float(model["dt_ms"]) * ms
    completeness = pd.read_csv(_rooted(protocol["completeness_file"]), index_col=0)
    connectivity = pd.read_parquet(_rooted(protocol["connectivity_file"]))
    flyids = [int(value) for value in completeness.index]
    flyid2i = {flyid: index for index, flyid in enumerate(flyids)}

    neurons = NeuronGroup(
        len(completeness),
        dedent(""" 
                    dv/dt = (v_0 - v + g) / t_mbr : volt (unless refractory)
                    dg/dt = -g / tau               : volt (unless refractory) 
                    rfc                            : second
                    """),
        method=model["integration"],
        threshold="v > v_th",
        reset='v = v_rst; w = 0; g = 0 * mV',
        refractory="rfc",
        namespace=params,
    )
    neurons.v = params["v_0"]
    neurons.g = 0
    neurons.rfc = params["t_rfc"]
    synapses = Synapses(neurons, neurons, "w : volt", on_pre="g += w", delay=params["t_dly"])
    synapses.connect(
        i=connectivity["Presynaptic_Index"].to_numpy(),
        j=connectivity["Postsynaptic_Index"].to_numpy(),
    )
    synapses.w = connectivity["Excitatory x Connectivity"].to_numpy() * params["w_syn"]

    inputs = []
    for channel, cell_set in stim_channels.items():
        rate = float(rates.get(channel, 0.0)) * Hz
        for flyid in cells["sets"][cell_set]["ids"]:
            index = flyid2i[int(flyid)]
            inputs.append(
                PoissonInput(
                    target=neurons[index],
                    target_var="v",
                    N=1,
                    rate=rate,
                    weight=params["w_syn"] * params["f_poi"],
                )
            )
            neurons[index].rfc = 0 * ms

    monitor = SpikeMonitor(neurons)
    net = Network(neurons, synapses, monitor, *inputs)
    brian_seed(int(seed))
    net.run(float(duration_ms) * ms)
    return {
        flyids[int(index)]: np.asarray(times / second, dtype=float)
        for index, times in monitor.spike_trains().items()
        if len(times)
    }


def run_trial_poissongroup(
    protocol: dict,
    cells: dict,
    stim_channels: Mapping[str, str],
    rates: Mapping[str, float],
    seed: int,
    duration_ms: float,
) -> dict[int, np.ndarray]:
    """Run one fresh network using the reusable path's PoissonGroup stimulus."""
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
    defaultclock.dt = float(model["dt_ms"]) * ms
    completeness = pd.read_csv(_rooted(protocol["completeness_file"]), index_col=0)
    connectivity = pd.read_parquet(_rooted(protocol["connectivity_file"]))
    flyids = [int(value) for value in completeness.index]
    flyid2i = {flyid: index for index, flyid in enumerate(flyids)}

    neurons = NeuronGroup(
        len(completeness),
        dedent("""
                    dv/dt = (v_0 - v + g) / t_mbr : volt (unless refractory)
                    dg/dt = -g / tau               : volt (unless refractory)
                    rfc                            : second
                    """),
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
        neurons, neurons, "w : volt", on_pre="g += w",
        delay=params["t_dly"], name="default_synapses",
    )
    synapses.connect(
        i=connectivity["Presynaptic_Index"].to_numpy(),
        j=connectivity["Postsynaptic_Index"].to_numpy(),
    )
    synapses.w = connectivity["Excitatory x Connectivity"].to_numpy() * params["w_syn"]

    target_indices = []
    channel_slices = {}
    for channel, cell_set in stim_channels.items():
        start = len(target_indices)
        target_indices.extend(flyid2i[int(flyid)] for flyid in cells["sets"][cell_set]["ids"])
        channel_slices[channel] = slice(start, len(target_indices))
    poisson = PoissonGroup(len(target_indices), rates=0 * Hz, name="stimulus_poisson")
    stimulus = Synapses(
        poisson, neurons, "w_stim : volt (constant)", on_pre="v += w_stim",
        name="stimulus_synapses",
    )
    stimulus.connect(i=np.arange(len(target_indices)), j=np.asarray(target_indices))
    stimulus.w_stim = params["w_syn"] * params["f_poi"]
    neurons.rfc[np.unique(target_indices)] = 0 * ms
    for channel, rate in rates.items():
        if channel not in channel_slices:
            raise KeyError(f"Unknown stimulus channel: {channel}")
        if float(rate) < 0:
            raise ValueError(f"Negative rate for {channel}: {rate}")
        poisson.rates[channel_slices[channel]] = float(rate) * Hz

    monitor = SpikeMonitor(neurons)
    net = Network(neurons, synapses, poisson, stimulus, monitor)
    brian_seed(int(seed))
    net.run(float(duration_ms) * ms)
    return {
        flyids[int(index)]: np.asarray(times / second, dtype=float)
        for index, times in monitor.spike_trains().items()
        if len(times)
    }
