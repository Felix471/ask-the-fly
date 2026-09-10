# Parameter cross-check: Tastekin et al. 2026 STAR Methods vs our frozen protocol

Written comparison only (user instruction, 2026-09-10). No change to `data/stim_protocol.json`.

Source: Tastekin et al. (2026), *Cell* 189(18):5527–5551.e5, STAR Methods, "Connectome-based integrate-and-fire model" (quoted in full in docs/open_questions.md, OQ-2b). They ran the Shiu et al. 2024 model (github.com/philshiu/Drosophila_brain_model) on the MaleCNS edge list with the model's default parameters.

| Parameter | Tastekin 2026 (verbatim) | Ours (`data/stim_protocol.json`) | Match |
|---|---|---|---|
| t_run | 1 s | 1000 ms | yes |
| n_run | 30 | 30 (sanity stage 5) | yes |
| v_0 | −52 mV | −52 mV | yes |
| v_rst | −52 mV | −52 mV | yes |
| v_th | −45 mV | −45 mV | yes |
| t_mbr | 20 ms | 20 ms | yes |
| tau | 5 ms | 5 ms | yes |
| t_rfc | 2.2 ms | 2.2 ms | yes |
| t_dly | 1.8 ms | 1.8 ms | yes |
| w_syn | "275 μs" | 0.275 mV | value matches; the printed unit "μs" is almost certainly a typesetting error for mV (model.py defines `w_syn = .275 * mV`; a time unit is dimensionally impossible for a synaptic weight added to a voltage). Our value is unchanged on the strength of that line. |
| r_poi | 200 Hz (model default) | per condition (Phase 0: 25/50/100/200; Phase 1: 0–200 step 20) | not a fixed parameter in our protocol; 200 Hz is our top level |
| r_poi2 | 100 Hz (model default) | per condition | same |
| f_poi | 250 | 250 | yes |
| dt | not stated (model default 0.1 ms) | 0.1 ms | assumed yes |
| integration | not stated (model.py: `method='linear'`) | linear | assumed yes |
| reset | "v = v rst; w = 0; g = 0 ∗mV" | `v = v_rst; w = 0; g = 0 * mV` (kept byte-identical) | yes |
| synapse sign | inhibitory if presynaptic neuron predicted glutamatergic or GABAergic, else excitatory (MaleCNS neurotransmitter predictions) | inherited from Shiu's `Connectivity_783.parquet` (per-neuron majority of per-synapse Eckstein 2024 predictions; GABA/Glu inhibitory) | same rule, different dataset and prediction source |
| silencing | "setting its synaptic weights (both input and output) to zero" | model.py `silence()` zeroes only outgoing weights of the silenced neuron; we do not silence in Phase 0/1 | differs in definition; irrelevant to our runs |
| stimulation | LB3s at 200 Hz for the MN9 test | our sugar set (23 notebook IDs) at 25–200 Hz | different cell set (their LB3 = sugar+water+high-salt subtypes on MaleCNS) |

Conclusion: every model constant matches. The only textual discrepancy is the "μs" unit on w_syn, treated as a typo. The differences that matter are the dataset (MaleCNS vs FlyWire v783), the neurotransmitter prediction source, and the stimulated cell set; none of these are parameters of the frozen protocol.
