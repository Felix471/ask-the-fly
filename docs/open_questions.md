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

## OQ-4: Berg et al. 2026 revised 4.6% of FlyWire cell types

Berg et al. 2026: "we revised just 4.6% of FlyWire types (Figure S1H)"; updated annotations at https://github.com/flyconnectome/flywire_annotations. Our cell sets are root-ID based, not type based, so v1 stimulation is unaffected, but Phase 1.5 Task A.3 must check whether any of our IDs were retyped.

## v3 note (updated 2026-09-10): MaleCNS as a substrate

Constraints (user): v1 and Phase 0/1 stay on FlyWire v783 + the Shiu run_exp() protocol; the 2026 papers are anatomy and pathway hypotheses, not a simulation backend; product copy fixed: "Scores come from a published female-brain LIF model (Shiu 2024 / FlyWire v783). The September 2026 papers describe a more complete taste wiring diagram that is not part of this simulation."

Precedent: Tastekin et al. ran the Shiu model on MaleCNS with Shiu's default parameters and no recalibration, and reproduced sugar (LB3, 200 Hz) → MN9 (Figure S17). Parameters are in their STAR Methods (quoted in OQ-2b). What is NOT shipped: neither github.com/philshiu/Drosophila_brain_model (ships only FlyWire v630/v783 connectivity and completeness files) nor Tastekin's Data and code availability section ("The Body IDs of GRN and MN cell types are shared in Table S1. The MaleCNS connectome dataset is publicly available (https://male-cns.janelia.org/)") provides the MaleCNS edge list. Remaining work for a v3 would be rebuilding that edge list from male-cns.janelia.org with synapse signs from the `consensusNt` field, which Berg et al. 2026 STAR Methods call "the recommended property to use in most analyses". Support for expecting the two datasets to mostly agree on taste→feeding: Berg et al. 2026 Figure 6K — labellar, pharyngeal and ascending-leg gustatory sensory neurons send only ∼1% of their output to sex-specific/dimorphic types (leg-local bristles 11%, wing bristles 6%), so early labellar taste processing in the brain is largely sex-shared. The fly-brain-minecraft project also runs a Shiu-style LIF on MaleCNS. Still would require redoing Phase 0 calibration. **Not planned.**

Neurotransmitter sign in our v1 pipeline (Berg item F.2): we consume the `Excitatory x Connectivity` column of Shiu's `Connectivity_783.parquet` unchanged. Per Shiu et al. 2024 Methods, that sign comes from per-synapse predictions of Eckstein et al. 2024 (cleft score cutoff 50), aggregated per neuron: a neuron is inhibitory if more than half of its presynaptic sites are predicted GABA or glutamate; dopamine, octopamine and serotonin are treated as excitatory. It is therefore **not** `consensusNt` (a MaleCNS / updated-annotation property) and predates the 2026 revised FlyWire annotations.

## OQ-5: disinhibition-pathway neurons await Table S1 body IDs (2026-09-11)

Quasimodo (GNG042), Scapula (GNG087), GNG016 and GNG510 (Tastekin et al. 2026) have no FlyWire v783 match in either source we hold: the Shiu et al. 2024 SEZ neuron dictionary (paper figure code) and the Schlegel et al. 2024 annotation table, whose `cell_type`, `hemibrain_type` and `synonyms` columns carry none of these GNG-series names. `data/named_neurons.json` records the four as unmatched and the site lists them as "no FlyWire v783 match, not run". They will be resolved from Tastekin Table S1 body IDs once the table's FlyWire materialization is confirmed (map via flywire_annotations if it is not v783). Until then the disinhibition pathway (LB3 → Quasimodo → MN, Fig 6I/6J) cannot be shown or silenced; only the feedforward Clavicle path and the other named SEZ neurons with v783 IDs (Bract I/II, Roundup, Sink and Synch, Fdg, Bluebell, DNg103) are covered by recorded silencing runs.

2026-09-12: GNG015, the inhibitory premotor neuron Tastekin et al. drive for the tonic-inhibition condition (Fig S17), was checked in both sources: not in `vendor/fly-brain/data/sez_neurons.pickle` under any Shiu name, and not in `data/external/Supplemental_file1_neuron_annotations.tsv` (`cell_type`, `hemibrain_type`, `synonyms`; the table carries no GNG-series name except GNG800). GNG-series names are MaleCNS nomenclature absent from Schlegel et al. 2024, so this is expected, not a lookup error. Resolution waits on Table S1 body IDs. Until then the brake neuron for that condition is chosen from the connectome: `docs/tonic_candidates.md` (analysis only, no runs).

## OQ-6: the model's Ir94e suppression is far stronger than the "mild aversion" of Tastekin et al. (2026-09-12)

Tastekin et al. 2026 describe Ir94e (LB1e) as a mild amino-acid aversion. In the grid (`data/lookup_table.json`, 30 trials per cell) the same channel is a strong suppressor: at sugar low / water low, MN9 goes 61.8 → 9.3 → 1.6 → 0.5 Hz across ir94e none / low / medium / high (60 / 120 / 200 Hz input), and at sugar 200 Hz MN9 is non-increasing along the axis (docs/phase1_characterization.md, sugar × ir94e). The magnitude is uncalibrated against behaviour and has not been investigated (no parameter, synapse-weight or input-rate study; no comparison with the paper's PER assays). Product decision 2026-09-12: ship it as the model produced it, no remapping of encoder levels to grid levels and no softening; the README honesty row and the site's amino-acid explanation say so.

What the axis did to the dictionary when enabled (encoder v2.3, `--only-dimension ir94e`, 174 dishes): ir94e cross-language agreement 121/133 on the batch2 dishes and 39/41 on the stability foods, within-language 100%; levels over 174 dishes none 88 / low 35 / medium 50 / high 1 (natto); among the 70 savory dishes (sugar ≤ low, bitter none) none 22 / low 26 / medium 22, i.e. the savory bucket split rather than moved. Occupied grid cells 35 → 55 of 174 dishes, dishes sharing a cell 160 → 146, largest cell 32 → 16, tied pairs 1179 → 535; dishes under 5 Hz MN9 47 → 76. In this model a fly ranks plain starches above every meat or soy-seasoned dish. Open: whether any input-rate or weight calibration would reconcile the model's suppression with the paper's behavioural magnitude, and whether the four ir94e levels should map to lower input rates once such a calibration exists (that would be a grid change, not an encoder change).
