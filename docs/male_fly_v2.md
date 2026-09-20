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

### Pre-run declaration — 2026-09-19

The owner's go for Phase 2 was recorded on 2026-09-19 with the pre-declared rules unchanged.
No Phase 2 trial has run at the time of this declaration.

The grid uses the 400 canonical cells of `sim.grid.expand_grid_conditions(sim.grid.load_grid_levels())`
in the female grid's order, with 30 trials per cell (12,000 trials). Cell IDs, global indices,
levels, aliases and all four drive rates are retained. The frozen grid levels and their file
record, the seed-rule text and every cell's Hz coordinates are checked against the frozen
male protocol and the female lookup table. Trial t of global index g uses
`20260910 + 1000 * (g % 40) + t`, t = 0..29, for 1,000 ms after restoring the initial network.
This gives 12,000 cell/trial assignments and 1,200 unique seed values, reused only across
cells with the same g % 40 and the same trial index.

The runner records primary MN9 L10331, secondary R16949, each MN11D/MN11V/CEM cell and
their group means, latencies, whole-network spike counts and neurons fired. Whole-network
body IDs and times and all Poisson-monitor events are saved for every trial, with seeds,
source hashes and condition ledgers. Summaries use population SD (ddof 0), firing-trial
counts and median latencies, plus network-count and neurons-fired median/min/max.
There is no retry, resume or overwrite. Plan and run use WSL; check is file-only and needs
no Brian2. The plan records a single compile-only build (0 simulated seconds, 0 spikes),
source hashes, the comparison and replay rules, and a memory budget based on the larger
of the measured M1j and Phase 1 worker peaks.

### Comparison and replay rules

- R1 Dish set: the 174 dishes of data/dishes.json (sha256 recorded in the comparison file), each mapped to its canonical grid cell with sim.grid.resolve_levels; water medium maps to the 60 Hz cell as in the female table.

- R2 Scores and states: the female score is mn9_left_mean of data/lookup_table_v1_2.json (equal to the site's mn9_mean) and the female state is that table's state field; the male score is the 30-trial mean L10331 rate rounded to 3 decimals as stored in data/lookup_table_male.json, and the male state follows the frozen male state rule (L10331 mean and the three-cell MN11D mean at the 5.0 Hz threshold, applied to unrounded means).

- R3 Distributions: counts of the four states over the 174 dishes and over the 400 cells for each fly; the number of dishes with score below 5.0 Hz for each fly; the 4x4 cross-table of female state by male state over the dishes.

- R4 Pairwise outcome: for every unordered pair of distinct dishes (15,051 pairs) each fly's outcome is the first dish, the second dish, or tie, with tie when the absolute score difference is below 1e-9 (the site rule) and otherwise the higher score winning. The flies agree on a pair when their outcomes are equal. Agreement rate = agreeing pairs / 15,051. Also reported: the 3x3 cross-table of female outcome by male outcome, the agreement rate over pairs where neither fly ties, and the number of pairs where both flies tie.

- R5 Pair-level attribution: for a disagreeing pair, the male outcome is recomputed from the male table with the water level of both dishes set to none and every other level unchanged; if that outcome equals the female outcome the disagreement is removed by water. Likewise with ir94e set to none, and with both set to none. Reported: disagreements removed by water alone, by ir94e alone, by either, only by both together, and by neither. The female table is never modified.

- R6 Dish-level attribution: for dish d, lower(d) is the number of other dishes x for which the female outcome of the pair is d and the male outcome is not d. lower_water(d) and lower_ir94e(d) are the same counts with the male outcome recomputed as in R5. Reported: the number of dishes with lower(d) > 0; the number with lower_water(d) < lower(d) (partly due to water) and with lower_water(d) = 0 < lower(d) (fully due to water); the same two counts for ir94e; the sums of lower, lower_water and lower_ir94e over all dishes; and a per-dish table of all 174 dishes with levels, female score, rank and state, male score, rank and state, lower, lower_water and lower_ir94e. Rank is 1 plus the number of dishes with a strictly higher score within the same fly.

- R7 Sign of each channel over dishes: for every dish whose water level is not none, the sign of (score of the dish) minus (score of the same dish with water set to none), for each fly, counted as lower, equal or higher; the same for ir94e. Counterfactual cells always exist because the grid is complete.

- R8 Replay rule: the whole-network replay of a cell is trial 0 of that cell's 30 grid trials (seed 20260910 + 1000 * (global_index % 40)); no extra trial is simulated. The packed site replay records the same body ids and times, and its MN9 spike counts equal trial 0's rates.

### Report additions and decision point 3

The report will place the male four-state distribution and below-5 Hz dish count next to
the female's 96 / 26 / 2 / 50 dishes (eats / mouth_moves / proboscis_only / no_response)
and 76 dishes below 5 Hz. It will quantify water and Ir94e effects over dishes according
to R5–R7, as well as reporting the distributions and pairwise comparison above.

The owner's amendment makes decision point 3 a report, not a go/no-go: when the grid,
lookup and comparison are built and audited, the numbers are reported and Phase 3 starts
unless the audit finds a technical defect. A male fly that refuses most of the menu is
a product outcome to show, not a reason to stop. The four honesty commitments and the
on-page disagreement sentence remain fixed. Decision points 4 (sprite preview) and
5 (copy) still need the owner.

The Phase 2 audit, lookup builder, comparison code, replay pack and report generator
follow separately; this declaration and the runner do not implement them.

### Results

<!-- male-v1-phase2:begin -->
Completed and independently audited 400 × 30 = 12,000 trials; see the [Phase 2 grid and comparison report](malecns_phase2.md).
The flies agree on 71.244% of the 15051 dish pairs.
The male fly's primary MN9 is below 5 Hz for 72 of 174 dishes (female 76).
Water removes 862 and Ir94e removes 1459 of the 4328 disagreeing pairs; 2664 are removed by neither.
<!-- male-v1-phase2:end -->

## Phase 3

Packages 1–4 are implemented; decision points 4 (sprite choice) and 5 (copy
wording, including the four bilingual honesty commitments) remain pending.

- Package 1 exports the independent lookup, 55 dish-occupied trial-0 replays and the male soma view: `scripts/export_male_site.py`, `scripts/export_neurons_male.py`, `site/data/lookup_table_male.json`, `site/data/replay_male/` and `site/data/neurons_male.json`. Checks live in `scripts/validate_release.py`, `tests/test_male_site_exports.py` and `site/test/male_data.test.mjs`; the full 400-cell research pack stays local.
- Package 2 adds bilingual draft copy and README honesty rows in `copy/site_strings.json` and `copy/readme_sections.md`, imported into `site/strings.js`, `README.md` and `README.zh.md`. `copy/fly_lines.json` and generated `site/fly_lines.js` split proboscis-only speech into sweet, savoury, watery and remainder groups. The 5 Hz state and ranking rules are unchanged; `scripts/import_copy.py`, `tests/test_import_copy.py` and `tests/test_fly_lines.py` cover the copy contract.
- Package 3 supplies three sprite candidates and preview sheets under `assets/male_candidates/`, produced by `scripts/prep_male_sprites.py`. No candidate is selected or promoted while decision point 4 is pending.
- Package 4 adds the female/male/both selector, independent `FlyPanel` instances, brain/replay panels, result tables, disagreement sentence, share parameters and both-mode cards in `site/panel.js`, `site/app.js`, `site/fly.js`, `site/index.html` and `site/style.css`. Verification extends `site/test/male_ui.test.mjs`, `scripts/browser_checks.py` and `scripts/export_share_card.py`. Male art still uses the existing female set until promotion.

## Phase 4

Shipped: v2.0.0 was tagged on main at 641f29b on 2026-09-19, including the four post-merge review fixes (PR #54: synapse-centroid positions, MaleCNS ROI outlines, MN-type readout labels, both-mode headlines and inset alignment). The male fly program is complete; nothing is pending.

Release preparation is implemented with a v2.0.0 CHANGELOG entry and matching
`site/data/release.json`; 2026-09-19 is a placeholder date to update at merge.
The existing bilingual README What's new draft is retained without duplication
or wording changes. `docs/site.md` records a pending-merge release row and the
male-specific release checklist; `.github/workflows/ci.yml` includes male data/UI,
female fixture and file-only male export/copy checks.

`scripts/freeze_female_decisions.py` creates the immutable
`site/test/fixtures/female_v1_2_1_decisions.json` from tag-verified, hash-pinned
female inputs and refuses overwrite. `site/test/female_v121.test.mjs` checks all
174 dish cells/scores/states, all 15,051 unordered pairs in both modes and a
fixed v1.2.1 female share query against live code; the earlier pairwise test stays.

`scripts/prep_male_sprites.py --promote <variant>` is ready to copy 42 approved
PNGs into the sibling `fly_male` and `response_male` asset folders and then
record the chosen variant in `site/config.json`. It refuses either existing
folder; `tests/test_male_sprite_promotion.py` verifies promotion on a temporary
copy, and the male UI tests verify the loader's paths and absent/present states.
No promotion has been run on the real tree. Decision points 4 and 5 remain
pending; no merge, deployment or tag is part of this preparation.
