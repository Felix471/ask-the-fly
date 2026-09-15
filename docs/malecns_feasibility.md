# MaleCNS feasibility

Research checkpoint; no simulation, substrate build, product change, or recommendation. Counts below are source inspection, not model results. The proposed two flies would compute independently; this document does not establish comparable behavioural meaning.

## 1. Data and licence

Verdict: feasible for a public non-commercial site, including redistribution of derived tables with attribution.

[Berg et al., Cell 2026](https://doi.org/10.1016/j.cell.2026.08.015) publishes the complete male CNS. The [v1.0 release](https://male-cns.janelia.org/release/) dates to 2026-06-08. [Official downloads](https://male-cns.janelia.org/download/) provide public flat files and a Neo4j database; neuPrint hosts `male-cns:v1.0`, accessible through its browser, API and Python/R clients (authenticated API access).

The download page licenses the data [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/): sharing and adaptation, including commercial use, are permitted with attribution, a licence link and identification of changes. Consequently derived lookup tables and replays may be redistributed under those conditions; describe them as simulations, not original measurements. Our [FlyWire-derived data](../README.md) instead retain [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/)'s non-commercial restriction. Male licensing does not remove that restriction from female material packaged alongside it.

## 2. Signed edge list

Verdict: feasible with work to construct, validate and version the signed substrate and its unresolved-label policy.

Inspected the v1.0 [weights-file](https://storage.googleapis.com/flyem-male-cns/v1.0/connectome-data/flat-connectome/connectome-weights-male-cns-v1.0-minconf-0.5.feather) schema: `body_pre`, `body_post`, `weight` (integer synapse count). Join presynaptic IDs to [neurotransmitter data](https://storage.googleapis.com/flyem-male-cns/v1.0/connectome-data/flat-connectome/body-neurotransmitters-male-cns-v1.0.feather): `body`, `predicted_nt`, `celltype_predicted_nt`, `consensus_nt`, with confidence/count fields. neuPrint calls these `bodyId`, `predictedNt`, `celltypePredictedNt`, `consensusNt`. Then multiply each count by its presynaptic sign and construct contiguous indices, the equivalent of Shiu's `Excitatory x Connectivity`.

[Berg, neurotransmitter Methods](https://doi.org/10.1016/j.cell.2026.08.015) uses retrained EM-image predictions, type pooling and experimental overrides for consensus. This shares the Eckstein approach, **not the same frozen predictions or aggregation** as our female table ([parameter crosscheck](parameter_crosscheck.md)). Female signs remain Shiu's; 27/29 LB3d have positive outputs despite Tastekin's glutamatergic class annotation ([sign audit](salt_and_refreeze.md)).

Among 166,700 superclass-annotated v1.0 neurons, the downloaded consensus join has 2,999 `unclear` and 178 missing labels; how many have retained outgoing edges remains unchecked. Histamine and monoamines also occur. Tastekin's rule is GABA/glutamate negative, otherwise positive; reproducing it requires explicitly documenting how unresolved labels enter that rule, not silently treating them as known excitation. The weights file includes unproofread segments: filter both endpoints to a versioned proofread roster. Freeze the label mapping, neuron filter, edge confidence threshold and hashes; do not add a minimum-five-synapse edge cutoff.

## 3. Size and cost

Verdict: feasible with work; runtime and brain-only size remain estimates until extraction and benchmarking.

[Berg Fig. 1B and graph Methods](https://doi.org/10.1016/j.cell.2026.08.015) reports 166,700 neurons, 124.2 million proofread-to-proofread synapses and 25.58 million directed edges (166,483 connected neurons). Rounded regional counts are central brain 38.6k, optic lobes 53.4k + 51.8k, VNC 22.8k: approximately **143.8k brain versus 166.7k CNS**, not an exact brain-only model roster. Detection totals, 46 million presynaptic sites and 312 million postsynaptic sites, are not the proofread graph's synapse count.

Our local female files contain 138,639 neurons, 15,091,983 edges and 54,492,922 synapses ([loader and paths](../sim/network.py)). Relative to the owner's 4.4 s/trial baseline, neuron scaling gives `4.4 × 166700/138639 = 5.3 s`; edge scaling gives `4.4 × 25.58M/15.092M = 7.5 s`. Budget **5–8 s/trial**, not a measured interval or bound: activity, compilation, I/O and parallel contention can dominate.

At 25.58M edges, float64 weights plus int32 indices require about **293 MiB CSR** or **390 MiB COO**, excluding IDs, pandas, Brian2 state, queues, restore copies and spike monitors; actual worker RAM is unknown. A dense matrix is unnecessary.

The [Shiu equations/loader](../sim/network.py) can run a brain-only graph, but removing VNC neurons/connections removes feedback. Define crossing-neuron retention and clip synapses by anatomical region; dropping VNC-only bodies alone does not do that. Exact retained synapses/edges require an ROI query or download, and Tastekin tested whole CNS, not this cut.

[Download sizes](https://male-cns.janelia.org/download/): annotations 13 MB and NT 42 MB downloaded; only 64 KiB of weights inspected. Whole-CNS construction still needs the **1.1 GB** weights file. Brain-region extraction may additionally need **6.8 GB** synaptic partners plus **12.7 GB** points/ROI labels, or filtered neuPrint results (size unknown). Body statistics are 780 MB; synapse-level NT predictions 2.7 GB, unnecessary for consensus signing. No full graph was downloaded.

## 4. Cell sets and readout

Verdict: feasible with work to freeze male IDs and explicitly reconcile hemisphere conventions.

Counts from Tastekin's Table S1 workbook, locally named `Tastekin_2025_bioRxiv_v2_SupplTable2_GRN_MN_body_IDs.xlsx`, `maleCNS` rows only ([paper/supplements](https://doi.org/10.1016/j.cell.2026.08.016); [female crosscheck](cell_set_crosscheck.md)). Workbook SHA256: `7b28d5f3ae45d68c510b8a3616700f0df2a5a6f2e2d2dba490d172939f2b64c9`. L/R means XLSX `Root_Side`, not our historical MN9 aliases.

| Class | Male L / R (total) | Female typed total |
|---|---:|---:|
| LB1a, LB1b, LB1c, LB1d | 6/5; 3/3; 9/7; 1/4 | 42 combined |
| Bitter combined | 19/19 (38) | 42 |
| LB1e: Ir94e | 11/8 (19) | 23 |
| LB3a: water | 9/8 (17) | 30 |
| LB3b: sugar | 5/6 (11) | 25 |
| LB3c: sugar | 12/11 (23) | 32 |
| Sugar union | 17/17 (34) | 57 (L 33) |
| MN9 | 10331 / 16949 (2) | 2 |

All four counterparts exist, but sizes are not matched: especially water and sugar are smaller. Current female frozen counts are sugar 23, bitter 42, water 18, Ir94e 18; these are not the typed totals ([cell IDs](cell_ids.md)). Mirroring the female **XLSX-L sugar policy** yields 17 male sugar cells, compared with 33 female typed L cells. Counterpart contralateral MN9 is male XLSX-R **16949**, with L **10331** also recorded; do not mistake Shiu's historical “left” label for XLSX L.

PhG1–16 are all present: **48 cells** versus female 50; male per-type counts are `8,4,2,4,2,2,4,4,4,2,2,2,2,2,2,2`. All 24 female MN type names occur among **67 male MNs**: MN1–13 with their D/V, a/b and M/L subdivisions, CEM and MNx01–05. MN9 has 2, MN11D **3**, MN11V 2, CEM 6. The selected labellar and all MN IDs exist in v1.0 annotations.

These interneuron IDs come from the [v1.0 annotation file](https://storage.googleapis.com/flyem-male-cns/v1.0/connectome-data/flat-connectome/body-annotations-male-cns-v1.0-minconf-0.5.feather), **not** the GRN/MN workbook; `type`/`synonyms` identify them and `somaSide` supplies sides:

| Type | L body IDs | R body IDs |
|---|---|---|
| GNG015 | 523590 | 28181 |
| GNG042 / Quasimodo | 15321 | 15734 |
| GNG016 | 11021 | 16794 |
| GNG510 | 14424 | 13115 |
| GNG087 / Scapula | 12811 | 11896, 12900 |

## 5. Model parameters

Verdict: feasible with work; running Shiu's equations is demonstrated, but transfer of calibration is unknown.

[Tastekin Fig. S17A–B, main text and modelling Methods](https://doi.org/10.1016/j.cell.2026.08.016) used all proofread MaleCNS neurons/connections, 1-second trials, 30 repetitions: LB3 stimulation at 200 Hz drove MN9; GNG015 at 100 Hz suppressed that response. Clavicle/Quasimodo silencing reduced responses in the tested conditions. This establishes a MaleCNS LIF implementation, not our four-axis gates, a brain-only implementation, behavioural calibration or equivalence to frozen v783 outputs. Their printed `w_syn = 275 μs` is dimensionally inconsistent; the Shiu-source interpretation is 0.275 mV ([parameter audit](parameter_crosscheck.md)), not verified from their executable build.

Every field of [our frozen protocol](../data/stim_protocol.json) is covered below. “Unchanged” means reusable as a model/design assumption, not male-validated.

| Parameter(s), current value | Transfer status |
|---|---|
| `protocol_version`, `data_version`, `connectivity_file`, `completeness_file` | Re-derive: new version, MaleCNS snapshot, signed edges and indexed roster |
| `model.source` | Unchanged equations/MIT attribution; version the adapter |
| `v_0_mV`, `v_rst_mV`, `v_th_mV`: −52, −52, −45 | Unchanged |
| `t_mbr_ms`, `tau_ms`, `t_rfc_ms`, `t_dly_ms`: 20, 5, 2.2, 1.8 | Unchanged |
| `w_syn_mV=.275`, `f_poi=250` | Unchanged starting values; male calibration unknown |
| `integration=linear`, `dt_ms=.1` | Unchanged implementation; not specified by Tastekin |
| Trial `duration_ms=1000`, `n_trials=30`, `sanity_n_trials=5`, `seed_rule=20260910+i` | Unchanged experimental design; distinct versioned condition ledger |
| Stimulus `type`: Poisson per GRN, N=1, weight=`w_syn*f_poi`, driven refractory=0 | Unchanged; retain tested implementation |
| Channels' `cell_set`, `count`: sugar23/bitter42/water18/ir94e18 | Re-derive: sugar17 L, bitter38, water17, Ir94e19 both sides |
| Water/Ir94e `phase=1` | Unchanged staging label |
| Readout `neuron=MN9`, `rate_definition` | Unchanged: spikes/second, trial mean and SD |
| Readout `left`, `right`, `aggregation=left_only`, `aggregation_rationale` | Re-derive IDs/aliases and contralateral aggregation explicitly (§4) |
| Phase0 A sugar25/50/100/200, bitter0; B sugar200, bitter0/25/50/100/200; C sugar0, bitter25/50/100/200; D both0 | Unchanged test levels |
| A′ `cell_set=sugar_bench21`, sugar25/50/100/200 | Unknown male analogue; requires re-derivation, excluded below |
| Phase1 sugar/bitter/Ir94e0:20:200; water0:20:260; `pairs` sugar×bitter/water/Ir94e | Unchanged optional experimental design, not authorised here |
| `notes`: v630 calibration; zero intrinsic baseline | Retain provenance; male validity unknown; zero baseline unchanged by construction |

## 6. Phase 0 plan — not executed

| Gate / scope | Stimulus and sets | Runs | Estimated serial trial time |
|---|---|---:|---:|
| Verdict | Feasible with work to build and freeze the substrate first. | — | — |
| A: sugar rises | §4 sugar17 L, 25/50/100/200 Hz; others0 | 4×30=120 | 10–16 min |
| B: bitter vetoes | Sugar17 L at200; bitter38 at0/25/50/100/200 | 5×30=150 | 12.5–20 min |
| C: bitter alone zero | Bitter38 at25/50/100/200; others0 | 4×30=120 | 10–16 min |
| D: baseline zero | All inputs0 | 30 | 2.5–4 min |
| Total | Whole CNS; MN9 R16949 primary, L10331 secondary; same seeds across conditions | 420 | 35–56 min, plus build/I/O |
| Definitions | Existing [Phase0 gate checks](phase0_report.md), unchanged; C's numerical tolerance remains ≤1 Hz. Water17/Ir94e19 undriven. Separate B0 replicate retained; no A′. | 30/condition | §3 size estimate, not benchmark |

## 7. Interpretation risks

Verdict: not feasible with current data to identify a difference between these two model flies as a sex effect.

Sex, reconstruction/typing differences, sign assignment and parameters not tuned for the male brain can each change outputs; this two-specimen pipeline cannot separate them ([Berg](https://doi.org/10.1016/j.cell.2026.08.015), [parameter crosscheck](parameter_crosscheck.md), [typed-set pilot](salt_and_refreeze.md)). Passing Phase 0 would establish only those model checks, not calibration against behaviour.

Draft honesty-table sentence, **not added to the product**: “Each fly's choice is computed independently by a connectome-based model; the cell-set, stimulus and scoring mappings are our design, and differences between the two outputs cannot be attributed to sex or treated as calibrated behavioural preferences.”
