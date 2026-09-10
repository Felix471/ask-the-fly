# SPDX-License-Identifier: MIT
# Independent PyTorch implementation of the equations in Shiu et al. (2024)
# model.py, used under the MIT License.
"""Batched PyTorch backend for the Shiu et al. fly-brain LIF network."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

import numpy as np
import pandas as pd
import torch


ROOT = Path(__file__).resolve().parents[1]


def _rooted(path: str | Path) -> Path:
    path = Path(path)
    return path if path.is_absolute() else ROOT / path


@dataclass
class TorchSimNet:
    """A connectome resident on one torch device, reusable across conditions."""

    weights: torch.Tensor
    flyids: np.ndarray
    flyid2i: dict[int, int]
    channel_targets: dict[str, torch.Tensor]
    stimulated: torch.Tensor
    device: torch.device
    dt_ms: float
    v_0: float
    v_rst: float
    v_th: float
    integration_a: float
    integration_b: float
    integration_A: float
    refractory_steps: int
    delay_steps: int
    stimulus_weight: float
    duplicate_edges: int

    @property
    def n_neurons(self) -> int:
        return len(self.flyids)

    def run_batched(
        self,
        rates: Mapping[str, float],
        seeds: list[int],
        duration_ms: float,
        *,
        recording_chunk_steps: int = 1000,
    ) -> pd.DataFrame:
        """Run independent trial columns and return the Brian2-compatible spike table."""
        if not seeds:
            raise ValueError("At least one trial seed is required")
        unknown = set(rates) - set(self.channel_targets)
        if unknown:
            raise KeyError(f"Unknown stimulus channel(s): {sorted(unknown)}")
        if any(float(rate) < 0 for rate in rates.values()):
            raise ValueError("Stimulus rates must be non-negative")

        steps_float = float(duration_ms) / self.dt_ms
        n_steps = int(round(steps_float))
        if not np.isclose(n_steps, steps_float, rtol=0.0, atol=1e-9):
            raise ValueError("duration_ms must be an integer multiple of dt_ms")
        batch = len(seeds)

        target_parts: list[torch.Tensor] = []
        probability_parts: list[torch.Tensor] = []
        for channel, targets in self.channel_targets.items():
            target_parts.append(targets)
            probability_parts.append(
                torch.full(
                    (targets.numel(),),
                    float(rates.get(channel, 0.0)) * self.dt_ms / 1000.0,
                    dtype=torch.float32,
                    device=self.device,
                )
            )
        targets = torch.cat(target_parts) if target_parts else torch.empty(0, dtype=torch.long, device=self.device)
        probabilities = (
            torch.cat(probability_parts)
            if probability_parts
            else torch.empty(0, dtype=torch.float32, device=self.device)
        )
        if probabilities.numel() and bool(torch.any(probabilities > 1.0).item()):
            raise ValueError("rate * dt must not exceed one")

        # Generate each trial from its own global torch seed, as specified by the
        # frozen protocol. Keeping the events boolean limits a 30-trial run to a
        # modest amount of device memory.
        event_trials = []
        for seed in seeds:
            torch.manual_seed(int(seed))
            event_trials.append(
                torch.rand((n_steps, targets.numel()), device=self.device) < probabilities
            )
        events = torch.stack(event_trials, dim=2)
        del event_trials

        shape = (self.n_neurons, batch)
        v = torch.full(shape, self.v_0, dtype=torch.float32, device=self.device)
        g = torch.zeros(shape, dtype=torch.float32, device=self.device)
        countdown = torch.zeros(shape, dtype=torch.int16, device=self.device)
        # The extra slot lets us push this step before reading step-delay,
        # matching Brian2's schedule without cloning a full spike matrix.
        ring_size = self.delay_steps + 1
        spike_ring = torch.zeros(
            (ring_size, self.n_neurons, batch),
            dtype=torch.float32,
            device=self.device,
        )
        ring_active = [False] * ring_size
        normal_refractory = (
            (~self.stimulated).to(torch.int16).unsqueeze(1) * self.refractory_steps
        )

        gpu_coords: list[torch.Tensor] = []
        gpu_steps: list[torch.Tensor] = []
        cpu_coords: list[torch.Tensor] = []
        cpu_steps: list[torch.Tensor] = []

        def flush_records() -> None:
            if gpu_coords:
                cpu_coords.append(torch.cat(gpu_coords).cpu())
                cpu_steps.append(torch.cat(gpu_steps).cpu())
                gpu_coords.clear()
                gpu_steps.clear()

        with torch.inference_mode():
            for step in range(n_steps):
                active = countdown == 0
                old_g = g
                new_g = old_g * self.integration_b
                old_u = v - self.v_0
                new_u = (
                    (old_u - self.integration_A * old_g) * self.integration_a
                    + self.integration_A * old_g * self.integration_b
                )
                v = torch.where(active, new_u + self.v_0, v)
                g = torch.where(active, new_g, g)

                spikes = (v > self.v_th) & active
                coords = torch.nonzero(spikes, as_tuple=False)
                if coords.numel():
                    gpu_coords.append(coords)
                    gpu_steps.append(
                        torch.full(
                            (coords.shape[0],), step, dtype=torch.int32, device=self.device
                        )
                    )

                current_pos = step % ring_size
                spike_ring[current_pos].copy_(spikes)
                ring_active[current_pos] = bool(coords.numel())
                delayed_step = step - self.delay_steps
                if delayed_step >= 0:
                    delayed_pos = delayed_step % ring_size
                    if ring_active[delayed_pos]:
                        g.add_(torch.sparse.mm(self.weights, spike_ring[delayed_pos]))

                if targets.numel():
                    stimulus_delta = events[step].to(torch.float32) * self.stimulus_weight
                    v.index_add_(0, targets, stimulus_delta)

                v.masked_fill_(spikes, self.v_rst)
                g.masked_fill_(spikes, 0.0)
                countdown.sub_(1).clamp_min_(0)
                countdown = torch.where(spikes, normal_refractory, countdown)

                if (step + 1) % recording_chunk_steps == 0:
                    flush_records()
            flush_records()

        if not cpu_coords:
            return pd.DataFrame(
                {
                    "t": pd.Series(dtype="float64"),
                    "trial": pd.Series(dtype="int64"),
                    "flywire_id": pd.Series(dtype="int64"),
                }
            )
        coords_np = torch.cat(cpu_coords).numpy()
        steps_np = torch.cat(cpu_steps).numpy()
        return pd.DataFrame(
            {
                "t": steps_np.astype(np.float64) * self.dt_ms / 1000.0,
                "trial": coords_np[:, 1].astype(np.int64),
                "flywire_id": self.flyids[coords_np[:, 0]].astype(np.int64),
            }
        )


def build_torch_network(
    protocol: dict,
    cells: dict,
    stim_channels: Mapping[str, str],
    device: str | torch.device | None = None,
) -> TorchSimNet:
    """Load, coalesce, and transfer the v783 connectome as sparse CSR."""
    selected = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))
    if selected.type == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but torch.cuda.is_available() is false")

    completeness = pd.read_csv(_rooted(protocol["completeness_file"]), index_col=0)
    connectivity = pd.read_parquet(_rooted(protocol["connectivity_file"]))
    flyids = completeness.index.to_numpy(dtype=np.int64)
    flyid2i = {int(flyid): index for index, flyid in enumerate(flyids)}
    n_neurons = len(flyids)

    columns = ["Presynaptic_Index", "Postsynaptic_Index", "Excitatory x Connectivity"]
    edges = connectivity.loc[:, columns].copy()
    original_edge_count = len(edges)
    edges = (
        edges.groupby(columns[:2], as_index=False, sort=True)[columns[2]]
        .sum()
        .sort_values([columns[1], columns[0]], kind="stable")
    )
    duplicate_edges = original_edge_count - len(edges)
    pre = edges[columns[0]].to_numpy(dtype=np.int64)
    post = edges[columns[1]].to_numpy(dtype=np.int64)
    if len(edges) and (
        pre.min() < 0
        or post.min() < 0
        or pre.max() >= n_neurons
        or post.max() >= n_neurons
    ):
        raise ValueError("Connectivity contains a neuron index outside the completeness table")
    counts = np.bincount(post, minlength=n_neurons)
    crow = np.empty(n_neurons + 1, dtype=np.int64)
    crow[0] = 0
    np.cumsum(counts, out=crow[1:])
    w_syn = float(protocol["model"]["w_syn_mV"])
    values = edges[columns[2]].to_numpy(dtype=np.float32) * w_syn
    weights = torch.sparse_csr_tensor(
        torch.from_numpy(crow).to(selected),
        torch.from_numpy(pre).to(selected),
        torch.from_numpy(values).to(selected),
        size=(n_neurons, n_neurons),
        dtype=torch.float32,
        device=selected,
    )

    channel_targets: dict[str, torch.Tensor] = {}
    stimulated_indices: list[int] = []
    for channel, cell_set in stim_channels.items():
        ids = [int(value) for value in cells["sets"][cell_set]["ids"]]
        missing = [flyid for flyid in ids if flyid not in flyid2i]
        if missing:
            raise ValueError(f"{cell_set} contains IDs absent from the connectome: {missing}")
        indices = [flyid2i[flyid] for flyid in ids]
        channel_targets[channel] = torch.tensor(indices, dtype=torch.long, device=selected)
        stimulated_indices.extend(indices)
    stimulated = torch.zeros(n_neurons, dtype=torch.bool, device=selected)
    if stimulated_indices:
        stimulated[torch.tensor(stimulated_indices, dtype=torch.long, device=selected)] = True

    model = protocol["model"]
    dt_ms = float(model["dt_ms"])
    t_mbr_ms = float(model["t_mbr_ms"])
    tau_ms = float(model["tau_ms"])
    return TorchSimNet(
        weights=weights,
        flyids=flyids,
        flyid2i=flyid2i,
        channel_targets=channel_targets,
        stimulated=stimulated,
        device=selected,
        dt_ms=dt_ms,
        v_0=float(model["v_0_mV"]),
        v_rst=float(model["v_rst_mV"]),
        v_th=float(model["v_th_mV"]),
        integration_a=float(np.exp(-dt_ms / t_mbr_ms)),
        integration_b=float(np.exp(-dt_ms / tau_ms)),
        integration_A=tau_ms / (tau_ms - t_mbr_ms),
        refractory_steps=int(round(float(model["t_rfc_ms"]) / dt_ms)),
        delay_steps=int(round(float(model["t_dly_ms"]) / dt_ms)),
        stimulus_weight=w_syn * float(model["f_poi"]),
        duplicate_edges=duplicate_edges,
    )
