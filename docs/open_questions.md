# Open questions

Observed, logged, and deliberately not investigated unless a later phase needs the answer.

## OQ-1: PyTorch backend runs hotter than Brian2, and the gap grows with drive

Observed 2026-09-10 in the Phase 0 backend cross-check (condition A, 30 trials each, same protocol, same seeds rule, left MN9):

| sugar Hz | Brian2 MN9 (Hz) | PyTorch CUDA MN9 (Hz) | PyTorch / Brian2 |
|---:|---:|---:|---:|
| 25 | 0.1 | 0.03 | both ≈ 0 |
| 50 | 17.6 | 19.7 | 1.12 |
| 100 | 67.2 | 78.3 | 1.16 |
| 200 | 93.3 | 120.7 | 1.29 |

The ratio is not a constant scale factor; it increases with input drive. Both backends agree on direction and order of magnitude (hard gate passed). The closed-form integration step was verified against an ODE solve to 1e-14, and the schedule (state update → threshold → delayed synaptic delivery and stimulus → reset, 22-step refractory, 18-step delay) was reviewed to match Brian2's. Untested candidates: float32 accumulation in the sparse matmul, Brian2's exact refractory/threshold timing at the step boundary, PoissonInput vs Bernoulli-per-step event semantics.

Decision (user, 2026-09-10): unexplained; Brian2 CPU is the only ground truth and Phase 1 uses Brian2 only. Do not investigate.

## OQ-2 (resolved 2026-09-10): the two claims attributed to Tastekin et al. 2026

Sources (metadata from Crossref; full text read from the PDFs in docs/papers/, gitignored):
- Berg et al., "Sexual dimorphism in the complete Drosophila male central nervous system connectome", Cell 189(18):5504–5526.e15, doi:10.1016/j.cell.2026.08.015. MaleCNS: 166,700 neurons spanning brain and nerve cord (Summary).
- Tastekin et al., "The complete gustatory connectome of adult Drosophila reveals how taste guides feeding, foraging, and social behavior", Cell 189(18):5527–5551.e5, doi:10.1016/j.cell.2026.08.016.

(a) **Disinhibition — confirmed.** Results and Figure 6I: "approximately 48% of the 3-hop motifs connecting LB3s to proboscis-positioning MNs were disinhibitory (16/31), significantly higher than the ∼2.9% expected by chance (p = 1.669 × 10⁻¹⁵, binomial test)". Key node: the GABAergic interneuron Quasimodo (GNG042), "participating in 12/16 of the disinhibitory pathways" (Figures 6G, 6I). The Discussion frames feeding-MN control as combining "sustained disinhibition and feedforward excitation". The paper does not literally say "feeding is default-inhibited"; it shows an enriched disinhibitory motif and tests it under an artificially induced tonic inhibition (see OQ-3).

(b) **Shiu-model validation — confirmed, on MaleCNS, not FlyWire.** Results, Figure S17: "we used a recently described connectome-based computational brain model to simulate activation of specific GRNs while silencing individual neurons ... Simulating the activation of LB3s at 200 Hz led to robust MN9 firing (Figure S17), consistent with previous FAFB/FlyWire findings, and silencing Clavicle while activating LB3s significantly decreased it". STAR Methods, "Connectome-based integrate-and-fire model", verbatim: "we generated an edge list with all proofread neurons and synaptic weights of all existing connections in MaleCNS. A connection was assumed to be inhibitory if the neurotransmitter prediction of the presynaptic neuron is glutamatergic or GABAergic, and excitatory if otherwise. We used the following default parameters and equations for the model: t_run = 1 s, n_run: 30, v_0 = - 52 mV, v_rst = - 52 mV, v_th = - 45 mV, t_mbr = 20 ms, tau = 5 ms, t_rfc = 2.2 ms, t_dly = 1.8 ms, w_syn = 275 μs, r_poi = 200 Hz, r_poi2 = 100 Hz, f_poi = 250." Equations 1–4 are model.py's (reset printed as "v = v rst; w = 0; g = 0 ∗mV"). "Thirty different simulations were run for each condition. A neuron was silenced by setting its synaptic weights (both input and output) to zero." Comparison with our frozen protocol: docs/parameter_crosscheck.md (all constants match; "μs" is a typesetting error for mV).

## OQ-3: the LIF model has zero basal firing, so v1 cannot express disinhibition

Tastekin et al. 2026, Results (Figure S17): "Testing the disinhibition motif presented a challenge, as the model assigns a basal firing rate of zero to all neurons and thus no tonic inhibition can be released by disinhibition. We therefore drove the inhibitory premotor neuron GNG015 at 100 Hz to establish tonic MN9 inhibition (Figure S17A), leading to the predicted significant decrease in the MN9 firing rate upon LB3 activation (Figure S17B)."

Consequence for us: our v1 (same model, FlyWire v783) captures the **feedforward excitation** path from sugar GRNs to MN9 — Tastekin Figure 6J, mediated by the cholinergic ascending neuron Clavicle (ANXXX462a) — and **not the disinhibition path** through Quasimodo (GNG042). Our baseline condition D = 0 Hz is this same zero-basal-firing property. Listed in the README honesty section. Not planned to fix in v1; a v2/v3 could add a tonic-inhibition background as Tastekin did, but that is a modelling choice with no calibration of its own.

2026-09-12, Phase T (`docs/tonic_inhibition.md`, `sim/run_tonic.py`, `data/stim_protocol_tonic.json`; results under `results/tonic/`, not shipped): the tonic-inhibition background was tried as a designed, uncalibrated condition. GNG015 has no v783 match (OQ-5), so three inhibitory inputs to left MN9 chosen by synapse count served as brakes (CB0806 "buddy", CB0862, CB0465), driven at 0 / 50 / 100 / 150 Hz with the GRN stimulation mechanism, against sugar alone at the five grid levels, 30 trials each. Outcome: CB0806 and CB0862 at 100 Hz hold MN9 down (sugar high recovers 0.1% and 4% of its no-brake rate; very_high 0.3% and 18%), CB0465 does not (50% and 59%); the drive-0 rows reproduce the frozen sugar-only column. No brake's own firing falls when sugar arrives, so disinhibition (sugar → silence of the brake → MN9 release) was not observed under these three brakes at these drive levels; the sweep says nothing about other brakes, drives or a real GNG015 match. Separate finding: sugar *raises* CB0465's firing (0 → 25.6 Hz across the sugar levels with no drive; +8.5 Hz on top of a 100 Hz drive), i.e. the sugar pathway recruits the strongest inhibitory input to left MN9 in parallel with exciting MN9: feed-forward inhibition (sugar → CB0465 → MN9), the opposite direction from the disinhibition motif, and already contained in every sugar curve of the frozen grid. Everything in the condition is designed (brake choice, drive level, sugar-only pairing) and calibrated against nothing. The path behind the CB0465 recruitment (excitatory neurons within two hops of the sugar GRNs that synapse onto CB0465) is tabulated in `docs/tonic_inhibition.md`; it is connectivity, not a run.

## OQ-4: Berg et al. 2026 revised 4.6% of FlyWire cell types

Berg et al. 2026: "we revised just 4.6% of FlyWire types (Figure S1H)"; updated annotations at https://github.com/flyconnectome/flywire_annotations. Our cell sets are root-ID based, not type based, so v1 stimulation is unaffected, but Phase 1.5 Task A.3 must check whether any of our IDs were retyped.

## v3 note (updated 2026-09-10): MaleCNS as a substrate

Constraints (user): v1 and Phase 0/1 stay on FlyWire v783 + the Shiu run_exp() protocol; the 2026 papers are anatomy and pathway hypotheses, not a simulation backend; product copy fixed: "Scores come from a published female-brain LIF model (Shiu 2024 / FlyWire v783). The September 2026 papers describe a more complete taste wiring diagram that is not part of this simulation."

Precedent: Tastekin et al. ran the Shiu model on MaleCNS with Shiu's default parameters and no recalibration, and reproduced sugar (LB3, 200 Hz) → MN9 (Figure S17). Parameters are in their STAR Methods (quoted in OQ-2b). What is NOT shipped: neither github.com/philshiu/Drosophila_brain_model (ships only FlyWire v630/v783 connectivity and completeness files) nor Tastekin's Data and code availability section ("The Body IDs of GRN and MN cell types are shared in Table S1. The MaleCNS connectome dataset is publicly available (https://male-cns.janelia.org/)") provides the MaleCNS edge list. Remaining work for a v3 would be rebuilding that edge list from male-cns.janelia.org with synapse signs from the `consensusNt` field, which Berg et al. 2026 STAR Methods call "the recommended property to use in most analyses". Support for expecting the two datasets to mostly agree on taste→feeding: Berg et al. 2026 Figure 6K — labellar, pharyngeal and ascending-leg gustatory sensory neurons send only ∼1% of their output to sex-specific/dimorphic types (leg-local bristles 11%, wing bristles 6%), so early labellar taste processing in the brain is largely sex-shared. The fly-brain-minecraft project also runs a Shiu-style LIF on MaleCNS. Still would require redoing Phase 0 calibration. **Not planned.**

Neurotransmitter sign in our v1 pipeline (Berg item F.2): we consume the `Excitatory x Connectivity` column of Shiu's `Connectivity_783.parquet` unchanged. Per Shiu et al. 2024 Methods, that sign comes from per-synapse predictions of Eckstein et al. 2024 (cleft score cutoff 50), aggregated per neuron: a neuron is inhibitory if more than half of its presynaptic sites are predicted GABA or glutamate; dopamine, octopamine and serotonin are treated as excitatory. It is therefore **not** `consensusNt` (a MaleCNS / updated-annotation property) and predates the 2026 revised FlyWire annotations.

## OQ-5: disinhibition-pathway neurons await Table S1 body IDs (2026-09-11)

Quasimodo (GNG042), Scapula (GNG087), GNG016 and GNG510 (Tastekin et al. 2026) have no FlyWire v783 match in either source we hold: the Shiu et al. 2024 SEZ neuron dictionary (paper figure code) and the Schlegel et al. 2024 annotation table, whose `cell_type`, `hemibrain_type` and `synonyms` columns carry none of these GNG-series names. `data/named_neurons.json` records the four as unmatched and the site lists them as "no FlyWire v783 match, not run". They will be resolved from Tastekin Table S1 body IDs once the table's FlyWire materialization is confirmed (map via flywire_annotations if it is not v783). Until then the disinhibition pathway (LB3 → Quasimodo → MN, Fig 6I/6J) cannot be shown or silenced; only the feedforward Clavicle path and the other named SEZ neurons with v783 IDs (Bract I/II, Roundup, Sink and Synch, Fdg, Bluebell, DNg103) are covered by recorded silencing runs.

2026-09-12: GNG015, the inhibitory premotor neuron Tastekin et al. drive for the tonic-inhibition condition (Fig S17), was checked in both sources: not in `vendor/fly-brain/data/sez_neurons.pickle` under any Shiu name, and not in `data/external/Supplemental_file1_neuron_annotations.tsv` (`cell_type`, `hemibrain_type`, `synonyms`; the table carries no GNG-series name except GNG800). GNG-series names are MaleCNS nomenclature absent from Schlegel et al. 2024, so this is expected, not a lookup error. Resolution waits on Table S1 body IDs. Until then the brake neuron for that condition is chosen from the connectome: `docs/tonic_candidates.md` (analysis only, no runs).

2026-09-12, later: the supplementary table was obtained (`docs/papers/Tastekin_2025_bioRxiv_v2_SupplTable2_GRN_MN_body_IDs.xlsx`, bioRxiv v2 "Supplemental table 2" = Table S1 of the Cell version; gitignored) and checked: it contains GRNs (411 FlyWire rows) and MNs (66 FlyWire rows) only, no interneuron rows, so none of the five GNG-series names can be resolved from it. The cross-check of the frozen GRN sets against it is in `docs/cell_set_crosscheck.md`.

## OQ-6: the model's Ir94e suppression is far stronger than the "mild aversion" of Tastekin et al. (2026-09-12)

Tastekin et al. 2026 describe Ir94e (LB1e) as a mild amino-acid aversion. In the grid (`data/lookup_table.json`, 30 trials per cell) the same channel is a strong suppressor: at sugar low / water low, MN9 goes 61.8 → 9.3 → 1.6 → 0.5 Hz across ir94e none / low / medium / high (60 / 120 / 200 Hz input), and at sugar 200 Hz MN9 is non-increasing along the axis (docs/phase1_characterization.md, sugar × ir94e). The magnitude is uncalibrated against behaviour and has not been investigated (no parameter, synapse-weight or input-rate study; no comparison with the paper's PER assays). Product decision 2026-09-12: ship it as the model produced it, no remapping of encoder levels to grid levels and no softening; the README honesty row and the site's amino-acid explanation say so.

What the axis did to the dictionary when enabled (encoder v2.3, `--only-dimension ir94e`, 174 dishes): ir94e cross-language agreement 121/133 on the batch2 dishes and 39/41 on the stability foods, within-language 100%; levels over 174 dishes none 88 / low 35 / medium 50 / high 1 (natto); among the 70 savory dishes (sugar ≤ low, bitter none) none 22 / low 26 / medium 22, i.e. the savory bucket split rather than moved. Occupied grid cells 35 → 55 of 174 dishes, dishes sharing a cell 160 → 146, largest cell 32 → 16, tied pairs 1179 → 535; dishes under 5 Hz MN9 47 → 76. In this model a fly ranks plain starches above every meat or soy-seasoned dish. Open: whether any input-rate or weight calibration would reconcile the model's suppression with the paper's behavioural magnitude, and whether the four ir94e levels should map to lower input rates once such a calibration exists (that would be a grid change, not an encoder change).

## OQ-7: 25 of 101 frozen v1 GRNs fall outside the mapped Tastekin subtypes (2026-09-12)

The count is 25: 11 sugar GRNs outside LB3b + LB3c (7 LB3d + 4 LB4b), 7 water GRNs outside LB3a, and 7 Ir94e GRNs outside LB1e; all 42 bitter GRNs match LB1a-d. The earlier count of 21 omitted the four sugar-set LB4b cells. The one sugar-set LB3b cell is within the mapped sugar subtypes and is not counted as a mismatch.

Cross-checking `data/cells.json` against Tastekin et al. 2025/2026 Supplemental table 2 (FlyWire rows; `docs/cell_set_crosscheck.md`, `scripts/cross_check_cells.py`): the 42 bitter GRNs are exactly LB1a-d, but seven of the 23 sugar GRNs are LB3d (high salt / heavy metal; ppk23, Ir7c, Ir47a; glutamatergic; aversive, per Tastekin), one is LB3b and four are LB4b (no receptor match), with only 11 LB3c; seven of the 18 water GRNs are LB3c (sugar); and seven of the 18 Ir94e GRNs are LB2a/b/c (no receptor match, putatively aversive), with 11 LB1e. These are differences between the Shiu et al. 2024 annotation the sets were frozen from and Tastekin's typing, not errors in our pipeline: the sets were frozen from the paper's own notebooks (docs/cell_ids.md) and the Phase 0 gates passed on them as they are. Consequences are not investigated: whether the seven LB3d cells in the sugar channel change the sugar curves, whether the seven LB3c cells in the water channel are part of why water acts as a second appetitive drive (README honesty table, water row), and whether the LB2 cells contribute to the Ir94e suppression (OQ-6) are all open. Re-freezing the sets to Tastekin's typing would be a v2 change requiring a full grid rerun and new replays; not done now. Also recorded there: the LB3b (25 cells) and LB3d (29 cells) FlyWire ID lists that Phase 1.5 salt work needs are now available, every one of them in v783.

## OQ-8: MN9/MN11 bitter separation replicated; CEM input audit (2026-09-13)

The [feeding-MN report](feeding_mn_readouts.md) contains C1 (400 existing
single-trial replays), C2 (thirteen selected cells × 30 freshly rerun trials),
and C2b (connectome only, no simulation). All sixty-six C1 MNs are monitored
in v783; C2 records twelve source neurons. Target labels come only from
the XLSX `MNs` sheet, FlyWire rows, `Target_Muscle` column:
MN9 = `9`, MN11D = `11D`, MN11V = `11V`, CEM = `Crop Entry`;
[the inventory](../data/mn_readout_ids.json) cites the workbook and its hash.

C2 reproduces the original grid seeds and exact spike trains for all
twelve neurons in all 390 trials; these are the same stochastic trials,
not an additional independent sample to pool with the original grid.
The C1 extra replay seeds are different. Frozen protocol/network/GRN sets
and product scores remain unchanged.

### C2 bitter separation

At sugar 120 Hz and water/Ir94e zero, mean rates (population SD, 30 trials)
are MN9 L/R 74.633 ± 4.476 / 54.700 ± 4.713 Hz without bitter, versus
1.700 ± 1.509 / 1.667 ± 1.193 Hz at bitter 100 Hz; MN11D/V are
92.733 ± 8.514 / 37.383 ± 3.991 Hz without bitter, versus
61.383 ± 13.992 / 24.950 ± 5.508 Hz at bitter 100 Hz.

| Bitter input Hz | MN9 L ratio | MN9 R ratio | MN11D ratio | MN11V ratio |
|---:|---:|---:|---:|---:|
| 0 | 1.000000 | 1.000000 | 1.000000 | 1.000000 |
| 60 | 0.317552 | 0.299208 | 0.914091 | 0.936246 |
| 100 | 0.022778 | 0.030469 | 0.661934 | 0.667410 |
| 160 | 0.000000 | 0.000000 | 0.009885 | 0.008471 |

Ratios divide cell means by the no-bitter mean, not trial-wise ratios.
The bitter veto acts on MN9 before it acts comparably on MN11 along the
**bitter-drive axis**; this does not prove temporal or causal ordering.
At bitter 160 Hz both MN9s are silent in 30/30 trials, while MN11D/V
retain means 0.917/0.317 Hz (5/30 and 2/30 active trials).
C2's per-cell mean±SD and conditional latency medians with active counts
are in the [C2 tables](feeding_mn_readouts.md#c2-thirteen-cell-30-trial-rerun).

CEM remains silent in every neuron/trial in C1 and C2, including Ir94e
alone. Ir94e is the unchanged mixed LB1e/LB2 input, not isolated LB2.
MN11 readouts can separate from MN9 under this design, but a serial
checkpoint chain or an active CEM checkpoint is not established.

### C2b CEM input table

CEM target `Crop Entry` and sides below are the literal XLSX values
cited above. The fifty PhG1–16 FlyWire IDs come from the same workbook's
`GRNs` sheet. All source and target IDs are in v783. Counts use unsigned
`Connectivity` from the frozen protocol's parquet: actual synapses on
each directed edge, not products of weights or duplicated convergent paths.
Source-group unions are recomputed; individual group rows are not additive.
Full source hashes, definitions and edge audit are in the
[C2b report](feeding_mn_readouts.md#c2b-cem-input-connectivity-no-simulation).

<!-- BEGIN COMPUTED CEM INPUT TABLE -->
D / A / B = direct source->CEM synapses / unique source->intermediate synapses on two-edge paths / unique intermediate->CEM synapses on those paths. The totals row instead gives unique presynaptic partners / total input synapses.

| Source (n) | 720575940620008112 (L) | 720575940625799513 (L) | 720575940640681680 (L) | 720575940621126384 (R) | 720575940621169690 (R) | 720575940628781333 (R) | All six (union) |
|---|---:|---:|---:|---:|---:|---:|---:|
| All presynaptic input: partners / synapses | 70 / 660 | 55 / 510 | 47 / 445 | 64 / 555 | 66 / 494 | 73 / 634 | 143 / 3298 |
| sugar (23) | 0 / 5 / 17 | 0 / 10 / 16 | 0 / 5 / 20 | 0 / 0 / 0 | 0 / 3 / 2 | 0 / 4 / 4 | 0 / 13 / 59 |
| bitter (42) | 0 / 15 / 5 | 0 / 119 / 5 | 0 / 1 / 2 | 0 / 1 / 2 | 0 / 0 / 0 | 0 / 70 / 14 | 0 / 189 / 28 |
| water (18) | 0 / 4 / 17 | 0 / 16 / 16 | 0 / 4 / 20 | 0 / 0 / 0 | 0 / 2 / 2 | 0 / 3 / 3 | 0 / 18 / 58 |
| ir94e (18) | 0 / 31 / 19 | 0 / 155 / 19 | 0 / 24 / 10 | 0 / 4 / 2 | 0 / 1 / 1 | 0 / 8 / 7 | 0 / 162 / 58 |
| Labellar union (101) | 0 / 55 / 31 | 0 / 300 / 26 | 0 / 34 / 29 | 0 / 5 / 2 | 0 / 6 / 3 | 0 / 85 / 24 | 0 / 382 / 115 |
| PhG1 (8) | 0 / 673 / 309 | 0 / 829 / 262 | 0 / 1044 / 241 | 0 / 820 / 276 | 0 / 1008 / 252 | 0 / 978 / 343 | 0 / 1553 / 1683 |
| PhG2 (5) | 0 / 8 / 24 | 0 / 19 / 14 | 0 / 9 / 17 | 0 / 18 / 60 | 0 / 16 / 56 | 0 / 20 / 47 | 0 / 39 / 218 |
| PhG3 (2) | 0 / 81 / 16 | 0 / 85 / 15 | 0 / 77 / 20 | 0 / 124 / 81 | 0 / 96 / 44 | 0 / 252 / 66 | 0 / 358 / 242 |
| PhG4 (4) | 0 / 23 / 48 | 0 / 27 / 67 | 0 / 25 / 42 | 0 / 26 / 45 | 0 / 34 / 30 | 0 / 68 / 51 | 0 / 99 / 283 |
| PhG5 (2) | 0 / 15 / 12 | 0 / 48 / 13 | 0 / 6 / 13 | 0 / 11 / 17 | 0 / 14 / 19 | 0 / 49 / 49 | 0 / 95 / 123 |
| PhG6 (2) | 0 / 112 / 39 | 0 / 266 / 49 | 0 / 111 / 30 | 0 / 52 / 26 | 0 / 52 / 15 | 0 / 185 / 44 | 0 / 440 / 203 |
| PhG7 (5) | 0 / 51 / 20 | 0 / 119 / 24 | 0 / 54 / 21 | 0 / 28 / 28 | 0 / 13 / 30 | 0 / 108 / 56 | 0 / 238 / 179 |
| PhG8 (4) | 0 / 7 / 13 | 0 / 24 / 14 | 0 / 26 / 25 | 0 / 33 / 44 | 0 / 47 / 46 | 0 / 79 / 67 | 0 / 112 / 209 |
| PhG9 (4) | 0 / 20 / 19 | 0 / 157 / 17 | 0 / 168 / 19 | 0 / 191 / 19 | 0 / 208 / 20 | 0 / 330 / 30 | 0 / 596 / 124 |
| PhG10 (2) | 0 / 45 / 22 | 0 / 15 / 23 | 0 / 6 / 20 | 0 / 23 / 14 | 0 / 4 / 21 | 0 / 152 / 35 | 0 / 168 / 135 |
| PhG11 (2) | 0 / 43 / 23 | 0 / 51 / 27 | 0 / 46 / 31 | 0 / 42 / 35 | 0 / 32 / 40 | 0 / 164 / 65 | 0 / 218 / 221 |
| PhG12 (2) | 0 / 0 / 0 | 0 / 28 / 2 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 1 / 9 | 0 / 29 / 11 |
| PhG13 (2) | 0 / 2 / 4 | 0 / 3 / 3 | 0 / 2 / 2 | 0 / 3 / 3 | 0 / 1 / 2 | 0 / 1 / 2 | 0 / 4 / 16 |
| PhG14 (2) | 0 / 0 / 0 | 0 / 2 / 7 | 0 / 1 / 5 | 0 / 2 / 2 | 0 / 1 / 2 | 0 / 11 / 5 | 0 / 14 / 21 |
| PhG15 (2) | 0 / 77 / 30 | 0 / 68 / 20 | 0 / 51 / 13 | 0 / 35 / 46 | 0 / 31 / 55 | 0 / 36 / 61 | 0 / 101 / 225 |
| PhG16 (2) | 0 / 149 / 26 | 0 / 126 / 21 | 0 / 94 / 11 | 0 / 64 / 43 | 0 / 63 / 45 | 0 / 90 / 48 | 0 / 212 / 194 |
| Pharyngeal union (50) | 0 / 1306 / 313 | 0 / 1867 / 263 | 0 / 1720 / 247 | 0 / 1472 / 325 | 0 / 1620 / 283 | 0 / 2524 / 376 | 0 / 4276 / 1807 |
<!-- END COMPUTED CEM INPUT TABLE -->

Pharyngeal input is structurally stronger than frozen labellar input at
two hops—1,807 versus 115 unique final-leg synapses onto the six CEMs
(15.7×), with no direct synapses from either group.

The pharyngeal-associated final leg includes 488 positive and 1,319
negative synapses under the model's signs, so larger unsigned input does
not predict CEM firing. This informs the design of a later pharyngeal
task; no pharyngeal stimulation, additional background, scoring change,
or README honesty-table change was made. The causal chain and CEM response
under other designs remain open.

## OQ-9: pharyngeal screen activates MN9/MN11 but not CEM (2026-09-13)

The [Phase P report](pharyngeal_screen.md) contains P0's source-only PhG1–16
table and P1's **19 conditions × 10 trials = 190 runs**, with all individual CEM
rates, MN9 L/R and MN11D/V mean ± population SD, conditional latency medians and
driven-cell sanity. P0 uses only Tastekin's Cell PDF, distinguishes putative
receptor/valence assignments from observations, and labels unreported properties
“not characterised”; the FlyWire IDs are the fifty Table S1 pharyngeal rows.
MN target labels are literal workbook `Target_Muscle` values: MN9 = `9`,
MN11D = `11D`, MN11V = `11V`, CEM = `Crop Entry`, as cited in
[the inventory](../data/mn_readout_ids.json).

P1 drives each complete type at 100 Hz, all fifty together at 100 Hz, and a
no-input baseline (18 conditions), plus PhG1 at 100 Hz with frozen sugar high
at 120 Hz (one combined condition). All other labellar drives are zero.
The frozen FlyWire v783 network and parameters are unchanged; this is our
uncalibrated stimulation design, not the paper's MaleCNS connectivity metric
or a product change. The explicit Phase P condition indices 0–18 use the
published grid seed formula, with trials 0–9; they are not original grid cells.

### Outcome

No CEM neuron fired in any condition: **0 spikes across 1,140 CEM-neuron-trials**.
Every driven source neuron did fire (1,310/1,310 driven-neuron-trials), so this
was not an omitted/failed input. All six CEM neurons and all ten trials were
explicitly saved and validated, including silent trials.

PhG1, PhG4 and PhG10 activated both MN9s and MN11D/V in 10/10 trials.

| Single type, 100 Hz | MN9 L, Hz | MN9 R, Hz | MN11D, Hz | MN11V, Hz |
|---|---:|---:|---:|---:|
| PhG1 | 53.200 ± 2.400 | 46.900 ± 3.390 | 140.700 ± 7.804 | 70.750 ± 3.970 |
| PhG4 | 37.500 ± 6.087 | 32.000 ± 2.933 | 110.600 ± 11.933 | 58.000 ± 5.527 |
| PhG10 | 11.100 ± 5.009 | 10.900 ± 3.885 | 17.650 ± 10.267 | 8.600 ± 4.898 |

PhG9 produced MN11D/V means 3.650/0.050 Hz (7/10 and 1/10 active trials) with
both MN9s silent; PhG13 produced one MN9 R spike in one trial; PhG16 produced
sparse MN9/MN11 activity. The other ten single types and baseline were silent
at every recorded MN. All-PhG means were MN9 L/R 23.000/18.600 and
MN11D/V 127.550/67.700 Hz, still with zero CEM spikes.

### PhG1 + sugar high does not show suppression in this comparison

The C2b motivation was structural: 1,319 of 1,807 unique final-leg synapses on
two-hop pharyngeal-to-CEM paths are negative under the frozen model's signs.
That count does not establish their activity or a negative net MN response.

| Readout | Existing sugar high only, n=30, Hz | PhG1 + sugar high, n=10, Hz | Combined / sugar-only mean |
|---|---:|---:|---:|
| MN9 L | 74.633 ± 4.476 | 82.800 ± 4.812 | 1.109424 |
| MN9 R | 54.700 ± 4.713 | 57.100 ± 2.982 | 1.043876 |
| MN11D | 92.733 ± 8.514 | 151.000 ± 6.546 | 1.628325 |
| MN11V | 37.383 ± 3.991 | 74.150 ± 3.795 | 1.983504 |

None of these means decreased. This uses the existing verified C2 sugar-only
reference, not an additional control run. It is a descriptive **unpaired**
comparison: Phase P constructs 151 Poisson units, C2 101, and their trial seeds
and random-stream consumption differ. No matched-control effect or statistical
independence is inferred from that layout change. Single-type zero-baseline
conditions cannot reveal suppression below zero.

P1 is **n=10, a screen, not a characterisation**. MN11-without-MN9 under PhG9 is
a candidate dissociation; PhG1/4/10 are active follow-up candidates. A serial
checkpoint chain or firing CEM checkpoint is not established. CEM activation
was not observed under this design, not ruled out for other drives/backgrounds.
P0's proposed valence labels are not rewritten to fit these firing readouts.
Checkpoint P1: await the owner's selection before any 30-trial characterisation
or additional control/background. No frozen data, `site/`, scoring, encoder or
README honesty-table changes.
