# Male fly v2.0.0 — program record

## Program and honesty commitments

The owner program adds an independently computed male fly alongside the frozen female pipeline as two different experiments. Only Phase 0 file preparation is in scope here. No simulation has run for this program. Female protocols, lookup, replays, scoring, copy and READMEs are unchanged.

These four owner commitments are recorded verbatim for Phase 3 honesty rows and result-page wording; they do not change the product in Phase 0.

1. The male brain uses MaleCNS v1.0 with connections of >= 5 synapses and a synaptic weight of 0.65 x Shiu's (0.17875 mV), a calibration taken from an independent project (blendi-remade/fly-brain-minecraft) and replicated by us; the female uses FlyWire v783, all connections, Shiu's 0.275 mV.
2. The male is stimulated bilaterally with Tastekin-typed GRN sets; the female unilaterally with Shiu's sets. The two flies do not share one stimulus protocol.
3. The male brain misses one of our four behavioural gates: bitter alone at 25 Hz gives 1.07 Hz on MN9 against our 1.0 Hz limit (docs/malecns_phase0.md, M1j); invisible in the product below the 5 Hz activity threshold, but recorded.
4. When the two flies disagree, the cause may be sex, reconstruction, cell typing, sign assignment, weight, or stimulus protocol; this pipeline cannot separate them. This sentence appears on the result page whenever they disagree, not only in the README.

## Phase 0 protocol freeze

Files: [male cells](../data/malecns/cells_male_v1.json), [male protocol](../data/malecns/stim_protocol_male_v1.json), [resolver](../sim/malecns/male_v1_cells.py), and [file-only tests](../sim/malecns/test_male_v1.py). The decision point is the owner's go: `frozen_after_owner_go` is true and `owner_go` records the go of 2026-09-19 (local 2026-09-18 evening); the two files are frozen from that commit. No later phase is authorized by these files.

Sources: local Tastekin Table S1 (SHA256 `7b28d5f3ae45d68c510b8a3616700f0df2a5a6f2e2d2dba490d172939f2b64c9`), maleCNS rows on both Root_Side values, and the unchanged M1i roster. All 108 stimulus IDs and all 13 readout IDs are in the roster. Source file sizes and hashes are in the cells file.

Historical context: [M1i results](malecns_phase0.md#m1i-results-checkpoint--2026-09-18), [post-M1c primary-readout decision](malecns_phase0.md), and [M1j policy report](bilateral_sugar_policy.md). The sugar set equals M1j's `sugar_bilateral` in `data/malecns/cells_m1j.json` (cross-checked); bitter, water and ir94e exactly match the existing male cells file.

### Stimulus sets

| Set | Tastekin subtypes | Count | XLSX L | XLSX R |
|---|---|---:|---:|---:|
| sugar | LB3b, LB3c | 34 | 17 | 17 |
| bitter | LB1a, LB1b, LB1c, LB1d | 38 | 19 | 19 |
| water | LB3a | 17 | 9 | 8 |
| ir94e | LB1e | 19 | 11 | 8 |

The four sets are pairwise disjoint. Layout: sugar, bitter, water, ir94e; ascending numeric Body_ID within each channel; 108 physical units. Driven units have refractory 0 ms, inactive units retain ordinary model refractory 2.2 ms. The external kick remains `w_syn*f_poi`. Ir94e is amino-acid aversion.

### Readouts

| Readout | Count | IDs (XLSX side) | Target_Muscle (verbatim) |
|---|---:|---|---|
| mn9 | 2 | 10331 (L), 16949 (R) | 9 |
| mn11d | 3 | 11269 (R), 11393 (R), 551398 (L) | 11D |
| mn11v | 2 | 49829 (L), 492462351 (R) | 11V |
| cem | 6 | 19823 (L), 20518 (L), 23511 (R), 32852 (L), 34597 (R), 482595 (L) | Crop Entry |

MN9 primary is 10331 (XLSX L), secondary 16949 (XLSX R); aggregation is `primary_only`, reflecting the explicitly post-M1c owner decision on reconstruction completeness. MN11D, MN11V and CEM are recorded for the product's four-state rule and replay pack, not dish ranking. State uses the 30-trial mean of the per-trial mean over all three male MN11D cells, together with the primary MN9 mean. Our threshold remains >=5.0 Hz: `eats`, `mouth_moves`, `proboscis_only`, `no_response`; MN9 right and MN11V remain not deciding for state.

### Differences from the female protocol

The reference mechanics are [stim_protocol.json](../data/stim_protocol.json); the additive female state/readout reference is [lookup_table_v1_2.json](../data/lookup_table_v1_2.json).

| Field | Frozen female | Male v1 |
|---|---|---|
| Protocol / data version | 1.0 / flywire_v783 | male-v1.0 / male-cns:v1.0-fbm-ge5-1 |
| Substrate | FlyWire v783 | MaleCNS v1.0 whole CNS; M1i roster and consensus signs |
| Connectivity / completeness files | vendor/fly-brain/data/2025_Connectivity_783.parquet; 2025_Completeness_783.csv | data/malecns/derived/fbm/connectivity.parquet; completeness.csv |
| Connection threshold | All connections (minimum 1 synapse) | >=5 synapses; 33 autapses removed |
| Substrate record | Existing frozen v783 inputs | substrate_record_fbm.json: 166,700 neurons, 6,242,085 edges, 89,859,938 synapses |
| Synaptic weight | 0.275 mV | 0.65 * 0.275 = 0.17875 mV (exact decimal in the frozen file) |
| External kick (same formula) | 68.75 mV | 44.6875 mV; w_syn*f_poi |
| Stimulus policy | Shiu frozen sets; unilateral protocol | Bilateral Tastekin typing |
| Sugar / bitter / water / ir94e counts | 23 / 42 / 18 / 18 | 34 / 38 / 17 / 19 |
| Physical input units | 101 | 108; fixed channel order and ascending Body_ID |
| Primary / secondary MN9 | 720575940660219265 / 720575940618238523; Shiu left/right, XLSX R/L | 10331 / 16949; XLSX L/R |
| Ranking aggregation / rationale | left_only; Shiu contralateral readout | primary_only; post-M1c completeness decision |
| MN11D IDs / count | 720575940618165019, 720575940630868793 / 2 | 11269, 11393, 551398 / 3 |
| MN11V IDs / count | 720575940635360924, 720575940636165624 / 2 | 49829, 492462351 / 2 |
| CEM recording | Not in product lookup_v1_2; six in feeding-MN research | Six IDs listed above in extra_readouts |
| MN11D state statistic | 30-trial mean of per-trial two-cell mean | 30-trial mean of per-trial three-cell mean |
| Characterization plan | Original four-channel Phase 1 dose/pair plan | Water and ir94e at inherited grid drives; 35 unique conditions, 1,050 trials |
| Historical Phase 0 conditions | Original female A-D and sugar_bench21 definitions | Not adopted as a new run plan; historical M1i/M1j referenced |
| Provenance / commitments / notes | Female reference and existing notes | Male source hashes, historical anchors, owner decision point and four commitments; female notes inherited with male comparison caveat |

All other model fields equal the female values, including dt 0.1 ms and f_poi 250. The entire trial block is unchanged (1,000 ms, 30 trials, sanity_n_trials 5 and original seed text); the grid and Phase 1 blocks state their explicit seed rules. The rate definition, four state names, threshold, not-deciding list and other state-rule fields are inherited.

### Grid levels inherited

| Dimension | none | low | medium | high | very_high |
|---|---:|---:|---:|---:|---:|
| sugar | 0 | 60 | 80 | 120 | 200 |
| bitter | 0 | 30 | 60 | 100 | 160 |
| water | 0 | 60 | 60 | 180 | 240 |
| ir94e | 0 | 60 | 120 | 200 | not defined |

All drives are Hz. [grid_levels.json](../data/grid_levels.json) SHA256 is `33a1dab4a03a440298d12c7ba2365e88457268b4ee3a220f15981b2702350780`, equal to the frozen lookup_v1_2 record. There are 400 unique cells. Cell coordinates and order are the female grid's so dish encodings map unchanged. Grid seeds: `20260910 + 1000 * (cell_index % 40) + trial, trial 0..29, cell_index in the female grid's cell order`.

### Phase 1 plan (not executed)

| Block | Drives (Hz) | Unique conditions in block | Trials at 30 each |
|---|---|---:|---:|
| Water | Alone 0/60/180/240; sugar 0/60/80/120/200 x water 60/180/240; water-0 is sugar alone | 20 | 600 |
| Ir94e | Alone 0/60/120/200; sugar 0/60/80/120/200 x ir94e 60/120/200; ir94e-0 is sugar alone | 20 | 600 |
| Shared baseline and sugar-alone row | sugar 0/60/80/120/200; all other channels 0; run once | 5 shared | 150 shared |
| Total union | 20 + 20 - 5 | 35 | 1,050 |

Channel-alone nonzero conditions already appear at sugar 0 in each pair block. The sugar-alone row at 60/80/120/200 is shared by both blocks and run once, as is baseline. Each condition uses seeds `20260910 + trial`, trials 0..29, shared across conditions (M1 seeds), and records whole-network counts. The protocol lists every unique condition explicitly. This is a plan only; no runner or simulation is part of Phase 0.

## Phase 1

Completed and independently audited 35 conditions × 30 = 1,050 trials; see the [Phase 1 characterisation report](malecns_phase1.md). Water is not observed as an appetitive driver under this design; ir94e suppresses.

## Phase 2

not started

## Phase 3

not started

## Phase 4

not started
