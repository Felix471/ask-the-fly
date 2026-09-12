# Tonic-inhibition candidates: inhibitory inputs to MN9

Generated 2026-09-12 by `scripts/tonic_candidates.py`. Analysis only; no simulation was run.

## Method

Tastekin et al. 2026 (Fig S17) hold MN9 down by driving an inhibitory premotor neuron (GNG015) continuously, then test sugar with and without a disinhibition node silenced. GNG015 has no FlyWire v783 match in the sources we hold (docs/open_questions.md, OQ-5), so the brake is chosen from the connectome instead. Inputs: `vendor/fly-brain/data/2025_Connectivity_783.parquet` (FlyWire v783 connectivity as used by the model; sign from the `Excitatory x Connectivity` column, the same signed column `sim/network.py` multiplies by `w_syn`; synapse count from `Connectivity`), `data/external/Supplemental_file1_neuron_annotations.tsv` (Schlegel et al. 2024: `super_class`, `cell_class`, `cell_type`, `hemibrain_type`, `top_nt`, `top_nt_conf`, `side`), `vendor/fly-brain/data/sez_neurons.pickle` (Shiu et al. 2024 named SEZ neurons) and the frozen GRN sets in `data/cells.json` (sugar, bitter, water, ir94e). Presynaptic partners of left MN9 `720575940660219265` and right MN9 `720575940618238523` with a negative signed connectivity are ranked by synapses onto left MN9 (the readout). The primary table keeps `top_nt == gaba` (Tastekin's design assumes a GABAergic brake); glutamatergic ones are listed separately (the model treats both signs as inhibitory). Per candidate: inhibitory synapses onto right MN9; any Shiu name; direct (1-hop) input synapses from each GRN set; breadth as the number of distinct postsynaptic partners and total output synapses (what a continuous drive would perturb besides MN9) and distinct presynaptic partners.

Inhibitory presynaptic partners: 121 onto left MN9, 125 onto right MN9. By transmitter, onto left MN9: gaba 77, glutamate 42, acetylcholine 1, serotonin 1.

The drive level is not calibrated: Tastekin's 100 Hz is their choice, and whatever rate we use for the chosen brake will be ours, likewise uncalibrated against any measured firing rate of that neuron. This document ranks by synapse count only and makes no recommendation.

## Primary table: GABAergic inhibitory inputs to MN9 (top 15 by synapses onto left MN9)

| # | root_id | syn → L MN9 | syn → R MN9 | side | super_class | cell_class | cell_type | hemibrain_type | top_nt (conf) | Shiu name | GRN in: sugar / bitter / water / ir94e | out partners (synapses) | in partners |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 720575940636809646 | 448 | 10 | right | central | – | CB0465 | – | gaba (0.65) | – | 0 / 0 / 0 / 0 | 131 (1546) | 191 |
| 2 | 720575940620156209 | 267 | 115 | right | central | – | CB0862 | – | gaba (0.44) | – | 0 / 0 / 0 / 0 | 195 (1850) | 281 |
| 3 | 720575940641281013 | 257 | 11 | right | central | – | CB0903 | – | gaba (0.65) | – | 0 / 0 / 0 / 0 | 122 (1639) | 231 |
| 4 | 720575940626961241 | 185 | 39 | right | central | – | CB0806 | – | gaba (0.72) | buddy | 0 / 0 / 0 / 0 | 134 (1778) | 149 |
| 5 | 720575940618028125 | 183 | 43 | right | central | – | CB0806 | – | gaba (0.71) | buddy | 0 / 0 / 0 / 0 | 126 (1728) | 154 |
| 6 | 720575940649829241 | 173 | 80 | right | descending | – | DNge051 | – | gaba (0.54) | – | 0 / 0 / 0 / 0 | 204 (1589) | 246 |
| 7 | 720575940611167842 | 155 | 273 | left | central | – | CB0862 | – | gaba (0.56) | – | 0 / 0 / 0 / 0 | 183 (2360) | 278 |
| 8 | 720575940632726220 | 100 | 34 | right | central | – | CB0857 | – | gaba (0.65) | – | 0 / 0 / 0 / 0 | 203 (2172) | 205 |
| 9 | 720575940610677828 | 82 | 252 | left | descending | – | DNge051 | – | gaba (0.57) | – | 0 / 0 / 0 / 0 | 217 (1988) | 246 |
| 10 | 720575940605513649 | 75 | 0 | right | descending | – | DNg90 | – | gaba (0.72) | – | 0 / 0 / 0 / 0 | 189 (1980) | 357 |
| 11 | 720575940625111223 | 65 | 0 | right | central | – | CB0047 | – | gaba (0.49) | – | 0 / 0 / 0 / 0 | 150 (1841) | 148 |
| 12 | 720575940625002936 | 63 | 17 | right | central | – | CB0817 | – | gaba (0.62) | – | 0 / 0 / 0 / 0 | 119 (1339) | 225 |
| 13 | 720575940627015196 | 63 | 0 | left | descending | – | DNg108 | – | gaba (0.53) | – | 0 / 0 / 0 / 0 | 361 (2478) | 661 |
| 14 | 720575940647010356 | 48 | 161 | left | central | – | CB0806 | – | gaba (0.74) | buddy | 0 / 0 / 0 / 0 | 139 (1966) | 170 |
| 15 | 720575940627293540 | 48 | 151 | left | central | – | CB0806 | – | gaba (0.69) | – | 0 / 0 / 0 / 0 | 129 (1836) | 160 |

## Secondary table: glutamatergic inhibitory inputs to MN9 (top 15)

| # | root_id | syn → L MN9 | syn → R MN9 | side | super_class | cell_class | cell_type | hemibrain_type | top_nt (conf) | Shiu name | GRN in: sugar / bitter / water / ir94e | out partners (synapses) | in partners |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 720575940624986300 | 96 | 35 | right | descending | – | DNge055 | – | glutamate (0.72) | – | 0 / 0 / 0 / 0 | 184 (1616) | 279 |
| 2 | 720575940622021637 | 71 | 0 | right | central | – | CB0912 | – | glutamate (0.62) | – | 0 / 0 / 0 / 0 | 129 (1021) | 163 |
| 3 | 720575940615410911 | 38 | 1 | right | central | – | CB0827 | – | glutamate (0.75) | – | 0 / 0 / 0 / 0 | 136 (1304) | 148 |
| 4 | 720575940629412682 | 23 | 2 | right | central | – | CB0909 | – | glutamate (0.70) | – | 0 / 0 / 0 / 0 | 98 (912) | 144 |
| 5 | 720575940623918121 | 20 | 87 | left | descending | – | DNge055 | – | glutamate (0.70) | – | 0 / 0 / 0 / 0 | 190 (1637) | 285 |
| 6 | 720575940622018309 | 11 | 0 | right | central | – | CB0898 | – | glutamate (0.80) | – | 0 / 0 / 0 / 0 | 250 (2412) | 133 |
| 7 | 720575940626860421 | 10 | 0 | left | central | – | CB0733 | – | glutamate (0.77) | – | 0 / 0 / 0 / 0 | 101 (1434) | 130 |
| 8 | 720575940621354736 | 9 | 0 | left | central | – | CB2177 | – | glutamate (0.67) | – | 0 / 0 / 0 / 0 | 182 (1921) | 191 |
| 9 | 720575940627234069 | 9 | 0 | right | descending | – | DNge069 | – | glutamate (0.83) | – | 0 / 0 / 0 / 0 | 101 (870) | 155 |
| 10 | 720575940617097684 | 7 | 0 | left | central | – | CB0069 | – | glutamate (0.83) | – | 0 / 0 / 0 / 0 | 170 (1778) | 238 |
| 11 | 720575940630181852 | 7 | 0 | right | central | – | CB0557 | – | glutamate (0.79) | – | 0 / 0 / 0 / 0 | 241 (1543) | 193 |
| 12 | 720575940612206810 | 5 | 0 | left | descending | – | DNge034 | – | glutamate (0.71) | handup | 0 / 0 / 0 / 0 | 72 (417) | 72 |
| 13 | 720575940616194610 | 5 | 0 | right | central | – | CB0819 | – | glutamate (0.63) | – | 0 / 0 / 0 / 0 | 185 (2631) | 211 |
| 14 | 720575940623676394 | 3 | 0 | right | central | – | CB0716 | – | glutamate (0.60) | – | 0 / 0 / 0 / 0 | 214 (2533) | 164 |
| 15 | 720575940626826288 | 3 | 0 | right | central | – | CB0219 | – | glutamate (0.73) | – | 0 / 249 / 0 / 0 | 271 (2779) | 436 |

Inhibitory-signed partners with another or missing `top_nt` (not tabulated): 3; the largest onto left MN9 is `720575940628826128` (1 synapses, top_nt `acetylcholine`).

## Notes on the top five

Plain readings of the annotation fields only (Schlegel et al. 2024 columns, the Shiu et al. 2024 dictionary, and the connectivity counts above). No recommendation is made here.

1. **720575940636809646 (CB0465, right).** Central-brain intrinsic neuron, GABA (confidence 0.65), one of a left/right pair in this cell type. It is the single strongest inhibitory input to left MN9 (448 synapses) and barely touches right MN9 (10), so it is a one-sided brake. It has no direct GRN input, 131 postsynaptic partners over 1546 output synapses, and the annotation carries one synonym, `fru-F-300125`, so it was flagged in a fruitless-expression dataset. Not in the Shiu dictionary.

2. **720575940620156209 (CB0862, right).** Central-brain intrinsic neuron, GABA at low confidence (0.44). Strong onto left MN9 (267) and substantial onto right MN9 (115); its left partner (row 7, 720575940611167842) mirrors this with 155 left / 273 right, so the pair inhibits both MN9s. No direct GRN input; 195 postsynaptic partners, the second-broadest output in the table. Not in the Shiu dictionary.

3. **720575940641281013 (CB0903, right).** Central-brain intrinsic neuron, GABA (0.65), one of a pair. Like CB0465 it is one-sided: 257 synapses onto left MN9, 11 onto right. No direct GRN input; 122 postsynaptic partners, the narrowest output among the top five. Not in the Shiu dictionary.

4. and 5. **720575940626961241 and 720575940618028125 (CB0806, right).** Two cells of a four-cell type (two per side), central-brain intrinsic, GABA at the highest confidence in the table (0.72 and 0.71). Both carry the Shiu et al. 2024 name **buddy**, so they are neurons the Shiu model already names in the SEZ feeding circuit; the two left CB0806 cells are rows 14 and 15 (one of them also "buddy"), inhibiting right MN9 more than left. Each right cell puts about 184 synapses onto left MN9 and about 40 onto right MN9, has no direct GRN input, and reaches about 130 postsynaptic partners. Driving one of them would leave its three siblings free; driving the type would inhibit both MN9s.

Common to all five: none receives a single direct synapse from the sugar, bitter, water or ir94e GRN sets, so a continuous drive on any of them is a pure premotor brake, not a taste-pathway manipulation, and each contacts 120 to 200 other neurons, which a 1 s drive at any rate will also affect.
