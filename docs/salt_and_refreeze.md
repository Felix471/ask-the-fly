# Salt screen and sugar-set re-freeze pilot

## Scope and status

S1 and R1 are research experiments on the unchanged Shiu/FlyWire v783 model,
not changes to the product, frozen data or encoder. All 720 approved trials
are complete and independently audited. The owner has reviewed the checkpoint:
salt is Closed as a fifth axis; v1 keeps its frozen sets and v2 adopts
Tastekin typing as a recorded, unexecuted two-brain cell-set policy.

## Source identities and hemisphere policy

Cell identities are from the FlyWire rows of Tastekin's Table S1, supplied as
`Tastekin_2025_bioRxiv_v2_SupplTable2_GRN_MN_body_IDs.xlsx`, sheet `GRNs`.
The source workbook SHA-256 is
`7b28d5f3ae45d68c510b8a3616700f0df2a5a6f2e2d2dba490d172939f2b64c9`.
LB3b, LB3c and LB3d are values of the workbook's `Subtype` field under
`Type = LB3`; no other connectome's rows are used. The labellar associations
are those recorded in the [cell-set cross-check](cell_set_crosscheck.md)
and [Phase 1.5 mapping](phase1_5_plan.md), not a salt-concentration calibration.

| Set | Cells | XLSX L / R | Shared with frozen sugar / water / bitter / Ir94e |
|---|---:|---:|---:|
| LB3b | 25 | 13 / 12 | 1 / 0 / 0 / 0 |
| LB3c | 32 | 20 / 12 | 11 / 7 / 0 / 0 |
| LB3d | 29 | 15 / 14 | 7 / 0 / 0 / 0 |
| R1 candidate: LB3b union LB3c, XLSX L only | 33 | 33 / 0 | 12 / 7 / 0 / 0 |

All these IDs are present in v783. The frozen 23 sugar cells are all XLSX
`Root_Side = L`, corresponding to Shiu's "right" stimulus-side naming;
the confirmed R1 candidate preserves that physical side. Relative to the
frozen sugar set it keeps 12 cells, removes 11 and adds 21. MN9 L/R labels
continue to mean the unchanged frozen readout IDs, not a swap to the XLSX
side convention. [Source and side cross-check](cell_set_crosscheck.md#mn9-side-labels).

MN labels retain the XLSX `MNs` sheet's `Target_Muscle` values: MN9 `9`,
MN11D `11D`, MN11V `11V`; no new functional muscle descriptions are added.
[MN source inventory](../data/mn_readout_ids.json).

## S1 design — ten-trial screen

Six conditions, ten one-second trials each (60 runs): baseline; all 25 LB3b
at 100 Hz; all 29 LB3d at 100 Hz; the 22 LB3d cells outside the frozen sugar
set at 100 Hz; frozen sugar alone at 120 Hz; and frozen sugar at 120 Hz plus
only those 22 non-overlapping LB3d cells at 100 Hz. Other inputs are undriven.
The seven shared cells receive exactly 120 Hz in the combined condition,
not 220 Hz and not a replacement 100 Hz drive. The 22-cell arm is an actual
stimulation omission, not just a subset average from the 29-cell run.

The fixed stimulus layout preserves P1's first 151 physical target IDs and
appends the 46 additional salt-set IDs, for 197 unique Poisson targets.
Each root has one input and one refractory assignment, avoiding duplicate
logical channels for overlapping populations. This extends P1's design;
it is not the same random stream as the historical 151-unit P1 run. All
compared S1 arms use the same extended layout.

MN9 L/R are individual rates; MN11D/V are per-trial two-neuron means including
silent members. Source neurons are recorded individually, with group means
for LB3b, LB3d, the non-overlapping 22, the overlap seven, frozen sugar and
the actual driven union; inactive monitored cells are distinguished from
driven cells. Summary SD is population SD (`ddof = 0`), not standard error.

Seeds use the published grid formula `20260910 + 1000 * seed_index + trial`
with trial 0–9. Baseline/LB3b/LB3d29/LB3d22/sugar/combined have seed indices
0/1/2/2/3/3. Actual input events on the unchanged targets must match in both
pairs: LB3d29 versus LB3d22, and sugar versus sugar plus LB3d22.

## S1 results — n = 10, screen only

Rates are mean ± population SD in Hz. MN11D/V are two-cell means, not sums.

| Condition | MN9 L | MN9 R | MN11D | MN11V |
|---|---:|---:|---:|---:|
| Baseline | 0 ± 0 | 0 ± 0 | 0 ± 0 | 0 ± 0 |
| LB3b25 @100 | 14.700 ± 5.080 | 5.000 ± 4.669 | 0 ± 0 | 0 ± 0 |
| LB3d29 @100 | 61.500 ± 6.037 | 56.100 ± 6.172 | 1.400 ± 1.375 | 0.100 ± 0.200 |
| LB3d22 @100, overlap seven omitted | 18.700 ± 5.178 | 13.800 ± 5.075 | 0 ± 0 | 0 ± 0 |
| Frozen sugar23 @120 | 73.900 ± 3.885 | 53.300 ± 3.976 | 97.700 ± 10.412 | 38.350 ± 4.884 |
| Frozen sugar23 @120 + LB3d22 @100 | 92.300 ± 3.551 | 71.300 ± 6.278 | 113.350 ± 6.697 | 47.100 ± 3.839 |

Driven-cell sanity is measured from the GRNs' own spikes, not their assigned
Poisson drive. Every actually driven GRN fired in every trial (1,440
neuron-trials); 2,700 inactive monitored GRN-trials are kept separate.

| Condition / actually driven group | Own rate, Hz, mean ± SD |
|---|---:|
| LB3b25 @100 | 98.616 ± 1.944 |
| LB3d29 @100, all 29 | 98.821 ± 1.407 |
| LB3d29 @100, non-overlap 22 measured within that run | 98.255 ± 1.867 |
| LB3d29 @100, overlap seven measured within that run | 100.600 ± 4.175 |
| LB3d22 @100, only those 22 stimulated | 98.255 ± 1.867 |
| Sugar23 alone @120 | 118.435 ± 2.423 |
| Sugar23 within combination | 118.426 ± 2.415 |
| LB3d22 within combination | 100.191 ± 1.997 |

First-spike latency is the median among trials with any spike; parentheses
give active trials out of 10. For MN11D/V this is the first of either member.

| Condition | MN9 L, ms | MN9 R, ms | MN11D, ms | MN11V, ms |
|---|---:|---:|---:|---:|
| Baseline | none (0/10) | none (0/10) | none (0/10) | none (0/10) |
| LB3b25 | 61.40 (10/10) | 120.40 (7/10) | none (0/10) | none (0/10) |
| LB3d29 | 55.30 (10/10) | 68.45 (10/10) | 745.65 (8/10) | 664.20 (2/10) |
| LB3d22 | 105.10 (10/10) | 197.05 (10/10) | none (0/10) | none (0/10) |
| Sugar120 | 34.10 (10/10) | 39.65 (10/10) | 45.55 (10/10) | 49.45 (10/10) |
| Sugar120 + LB3d22 | 28.05 (10/10) | 34.20 (10/10) | 42.75 (10/10) | 46.35 (10/10) |

| Combination / sugar-alone comparison | Ratio of means | Mean ± SD of paired trial ratios | Paired difference, Hz, mean ± SD |
|---|---:|---:|---:|
| MN9 L | 1.248985 | 1.253007 ± 0.089814 | 18.400 ± 5.731 |
| MN9 R | 1.337711 | 1.344325 ± 0.147621 | 18.000 ± 7.127 |
| MN11D | 1.160184 | 1.174584 ± 0.158817 | 15.650 ± 12.221 |
| MN11V | 1.228162 | 1.242222 ± 0.144840 | 8.750 ± 4.501 |

**Screen conclusion (two sentences).** LB3b25 and LB3d29 activate MN9 in this
model, and omitting the seven frozen-sugar-overlap neurons reduces but does
not eliminate LB3d-driven MN9 activity (L: 61.500 to 18.700 Hz; R: 56.100 to
13.800 Hz), so the full 29-cell response cannot be treated as independent
of the cells already used by the frozen sugar stimulus. Adding only
LB3d22 @100 to frozen sugar23 @120 increases all four
readouts in 10/10 paired trials: suppression is not observed under this
design, despite the aversive LB3d association recorded in the
[Tastekin mapping](phase1_5_plan.md#task-a-revised-source).

## R1 design — thirty-trial sugar comparison

The approved base design compares frozen sugar23 with candidate sugar33
at 0/60/80/120/200 Hz, 30 trials per set and level, matched seeds within
each old/new pair (300 runs). No bitter-, water-, or Ir94e-designated drive
is applied in those dose comparisons. Candidate-sugar membership determines
the input of the seven frozen-water overlap neurons: they receive sugar
drive when selected, without an inactive water channel overriding them.

Full candidate-set Phase 0 A–D coverage adds eleven conditions at 30 trials
each (330 runs): sugar 25/50/100 Hz; sugar 200 Hz plus bitter
25/50/100/200 Hz; and bitter alone at 25/50/100/200 Hz. Candidate baseline
and sugar200 are explicitly reused from the dose series, giving 630 R1
runs. The adapted A-prime adds only the 20-cell LB3c-only XLSX L subset at
120 Hz, 30 trials; its 33-cell comparator is reused from the paired curve,
with the same layout and seeds. R1 therefore totals 660 runs, S1 plus R1
720. [Original protocol](../data/stim_protocol.json), [Phase 0 gates and A-prime](phase0_report.md).

All R1 arms use one 165-target layout: P1's 151 physical targets plus the
14 candidate IDs not already present, each with one input assignment.
Old/new dose pairs share seed indices 0–4; extra A conditions use 5–7,
B uses 8–11, and C uses 12–15. A-prime shares index 3 with candidate120.
Each block uses the grid seed formula above with trials 0–29. Shared-target
Poisson event trains are checked, not just seed labels.

The report gives absolute rates and each curve normalised to that set's
own 200 Hz response, with the normalisation and trial-spread convention
stated explicitly. At the same per-cell rate, 33 rather than 23 driven cells
imposes 33/23 times as many expected Poisson events, which can contribute
to an increase in output; it does not establish that MN rates must increase.
Membership, cell count and wiring all change, so normalisation alone cannot
isolate a causal population-size effect or establish full-grid dish rankings.

Before running, the descriptive shape comparison is defined as follows.
Each trial rate is divided by its set's **mean** 200 Hz rate; the reported
SD is scaled by that same constant, without denominator-uncertainty
propagation. At the interior levels 60/80/120 Hz, a difference is flagged
when the absolute mean paired normalised difference exceeds twice its
population SD. This is our descriptive screen rule, not a significance
test or a behavioural threshold. The left-MN9 curve is the product-relevant
proxy; a sugar-only pilot cannot establish mixed-taste dish rankings.
A-prime differences are paired subset-minus-candidate rates, with population
SD. The historical 21-versus-23 comparison is a separate reference, not
an additional paired arm or a comparable layout.

## R1 results — n = 30 per condition

### Matched sugar curves

Mean ± population SD, Hz. Baselines were run for both sets; zero/zero ratios are undefined, not zero.

| Set / input Hz | MN9 L | MN9 R | MN11D | MN11V |
|---|---|---|---|---|
| Frozen23 / 0 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| Candidate33 / 0 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| Frozen23 / 60 | 33.833 ± 6.748 | 27.067 ± 5.567 | 33.800 ± 11.080 | 11.417 ± 4.297 |
| Candidate33 / 60 | 49.833 ± 5.184 | 33.833 ± 4.769 | 3.750 ± 5.429 | 1.200 ± 2.015 |
| Frozen23 / 80 | 55.133 ± 5.064 | 41.967 ± 3.507 | 69.783 ± 9.707 | 25.000 ± 3.751 |
| Candidate33 / 80 | 66.400 ± 3.657 | 45.767 ± 4.432 | 36.533 ± 11.165 | 12.917 ± 4.305 |
| Frozen23 / 120 | 72.900 ± 5.350 | 51.900 ± 3.736 | 95.817 ± 10.241 | 37.617 ± 4.266 |
| Candidate33 / 120 | 80.233 ± 4.492 | 51.700 ± 3.761 | 96.183 ± 7.632 | 39.283 ± 2.795 |
| Frozen23 / 200 | 93.500 ± 5.239 | 63.267 ± 4.305 | 124.617 ± 8.592 | 52.800 ± 3.156 |
| Candidate33 / 200 | 94.167 ± 4.872 | 60.633 ± 5.474 | 125.700 ± 7.137 | 55.583 ± 3.233 |

Ratios below are new/old **ratios of means**, not means of trial-wise ratios.

| Input Hz | MN9 L | MN9 R | MN11D | MN11V |
|---|---|---|---|---|
| 0 | undefined | undefined | undefined | undefined |
| 60 | 1.472906 | 1.250000 | 0.110947 | 0.105109 |
| 80 | 1.204353 | 1.090548 | 0.523525 | 0.516667 |
| 120 | 1.100594 | 0.996146 | 1.003827 | 1.044307 |
| 200 | 1.007130 | 0.958377 | 1.008693 | 1.052715 |

### Curves normalised to their own 200 Hz mean

Values are dimensionless mean ± scaled population SD; estimated denominator uncertainty is not propagated. Endpoint means equal one, but their trial SDs do not become zero.

| Set / input Hz | MN9 L | MN9 R | MN11D | MN11V |
|---|---|---|---|---|
| Frozen23 / 0 | 0.000000 ± 0.000000 | 0.000000 ± 0.000000 | 0.000000 ± 0.000000 | 0.000000 ± 0.000000 |
| Candidate33 / 0 | 0.000000 ± 0.000000 | 0.000000 ± 0.000000 | 0.000000 ± 0.000000 | 0.000000 ± 0.000000 |
| Frozen23 / 60 | 0.361854 ± 0.072174 | 0.427819 ± 0.087998 | 0.271232 ± 0.088916 | 0.216225 ± 0.081391 |
| Candidate33 / 60 | 0.529204 ± 0.055050 | 0.557999 ± 0.078645 | 0.029833 ± 0.043194 | 0.021589 ± 0.036251 |
| Frozen23 / 80 | 0.589661 ± 0.054165 | 0.663330 ± 0.055432 | 0.559984 ± 0.077896 | 0.473485 ± 0.071033 |
| Candidate33 / 80 | 0.705133 ± 0.038835 | 0.754810 ± 0.073101 | 0.290639 ± 0.088826 | 0.232384 ± 0.077455 |
| Frozen23 / 120 | 0.779679 ± 0.057220 | 0.820337 ± 0.059049 | 0.768891 ± 0.082179 | 0.712437 ± 0.080786 |
| Candidate33 / 120 | 0.852035 ± 0.047704 | 0.852666 ± 0.062025 | 0.765182 ± 0.060713 | 0.706747 ± 0.050283 |
| Frozen23 / 200 | 1.000000 ± 0.056035 | 1.000000 ± 0.068038 | 1.000000 ± 0.068950 | 1.000000 ± 0.059772 |
| Candidate33 / 200 | 1.000000 ± 0.051741 | 1.000000 ± 0.090282 | 1.000000 ± 0.056782 | 1.000000 ± 0.058162 |

Predeclared descriptive shape check: paired normalised new-minus-old mean ± population SD; a flag requires |mean| > 2 SD at an interior dose.

| Input Hz | MN9 L delta | MN9 R delta | MN11D delta | MN11V delta | Flagged readouts |
|---|---|---|---|---|---|
| 60 | 0.167350 ± 0.089547 | 0.130180 ± 0.112182 | -0.241399 ± 0.091409 | -0.194636 ± 0.085256 | MN11D, MN11V |
| 80 | 0.115471 ± 0.069081 | 0.091481 ± 0.082171 | -0.269345 ± 0.107960 | -0.241101 ± 0.090176 | MN11D, MN11V |
| 120 | 0.072356 ± 0.065537 | 0.032329 ± 0.082948 | -0.003710 ± 0.109010 | -0.005690 ± 0.097863 | none |

MN11D/V meet that rule at 60 and 80 Hz; neither MN9 side does. This is not an equivalence test: left-MN9 mean gains are 47.3%, 20.4%, 10.1%, and 0.7% at 60/80/120/200 Hz, so the means are not a uniform multiplicative rescaling. Driving 33 rather than 23 cells supplies 43.5% more expected external events at equal per-cell Hz, but cannot by itself predict the output: MN11D/V are substantially lower at the two lower drives despite the larger set.

**Ranking-risk conclusion (one sentence).** A material dish-ranking change is not established by this sugar-only pilot: the two left-MN9 mean curves remain monotonic and their normalised differences do not exceed our predeclared two-SD paired-spread threshold, whereas MN11D/V do differ beyond that threshold at 60/80 Hz and mixed-taste rankings were not tested.

### Adapted A-prime: LB3c-only L subset, 20 cells

Both sets receive 120 Hz; all other inputs are zero. Only the subset's 30 trials are additional; the candidate33 comparator is the curve condition above. Differences are paired **subset minus candidate**.

| Readout | Candidate33, Hz | LB3c20, Hz | Paired difference, Hz, mean ± SD | Subset lower / 30 |
|---|---|---|---|---|
| MN9_L | 80.233 ± 4.492 | 69.567 ± 3.547 | -10.667 ± 6.529 | 30 |
| MN9_R | 51.700 ± 3.761 | 43.767 ± 4.039 | -7.933 ± 5.790 | 27 |
| MN11D | 96.183 ± 7.632 | 87.000 ± 7.248 | -9.183 ± 8.412 | 24 |
| MN11V | 39.283 ± 2.795 | 34.267 ± 2.750 | -5.017 ± 3.105 | 28 |

For reference, the original [21-versus-23 A-prime](phase0_report.md#appendix-a) had left-MN9 absolute mean differences of 0.066667, 0.433333, 0.366667, and 0.466667 Hz at 25/50/100/200 Hz: all **< 0.5 Hz** (the last rounds to 0.5 in the published table). These values were checked against `results/phase0/full/summary.csv`; the bound is for left MN9, not both sides. That historical experiment used different stimulus layouts/seeds and predates the refractory correction; it is a reference, not a paired comparison with R1, and did not test 120 Hz.

### Full candidate Phase 0 gates

All four original left-MN9 gates pass with the [original thresholds](../scripts/phase0_report.py); the separately requested literal-zero C/D checks also pass for both MN9 sides. All conditions have 30 completed trials; none is inferred from missing output.

| Gate | Left-MN9 mean sequence, Hz | Criterion | Result |
|---|---|---|---|
| A: sugar25/50/100/200 | 0.400 → 37.933 → 74.000 → 94.167 | Strict increases; 94.167 > baseline + 5 SD + 5 = 5 Hz | PASS |
| B: bitter0/25/50/100/200 at sugar200 | 94.167 → 82.067 → 72.233 → 37.500 → 1.633 | Nonincreasing; 1.633 < half of B0 = 47.083 Hz | PASS |
| C: bitter25/50/100/200 alone | 0 → 0 → 0 → 0 | Original ceiling 1 Hz; additionally every MN9 L/R trial is zero | PASS |
| D: zero stimulus | 0 ± 0 | Original completion gate; additionally every MN9 L/R trial is zero | PASS |

The eleven additional A/B/C conditions are reported here; candidate0 and candidate200 are reused from the dose table, not rerun or counted twice.

| Condition | MN9 L, Hz | MN9 R, Hz | MN11D, Hz | MN11V, Hz |
|---|---|---|---|---|
| R1_A_new_25 | 0.400 ± 1.306 | 0.300 ± 1.130 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| R1_A_new_50 | 37.933 ± 6.207 | 23.900 ± 4.721 | 0.067 ± 0.359 | 0.017 ± 0.090 |
| R1_A_new_100 | 74.000 ± 3.596 | 49.567 ± 4.709 | 78.333 ± 12.888 | 30.267 ± 5.275 |
| R1_B_new200_bitter25 | 82.067 ± 4.939 | 45.833 ± 3.606 | 119.033 ± 8.297 | 53.933 ± 3.655 |
| R1_B_new200_bitter50 | 72.233 ± 5.051 | 35.400 ± 4.432 | 116.483 ± 6.450 | 53.400 ± 3.252 |
| R1_B_new200_bitter100 | 37.500 ± 5.903 | 12.200 ± 2.548 | 87.900 ± 10.403 | 38.650 ± 5.421 |
| R1_B_new200_bitter200 | 1.633 ± 1.303 | 0.000 ± 0.000 | 23.667 ± 8.937 | 8.817 ± 3.567 |
| R1_C_bitter25 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| R1_C_bitter50 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| R1_C_bitter100 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| R1_C_bitter200 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 |

### Latencies and source sanity

First-spike medians in ms among active trials, with active count out of 30; MN11D/V use the earliest member. Silence has no latency, not zero latency.

| Condition | MN9 L | MN9 R | MN11D | MN11V |
|---|---|---|---|---|
| R1_old_0 | none (0/30) | none (0/30) | none (0/30) | none (0/30) |
| R1_old_60 | 81.65 (30/30) | 83.00 (30/30) | 106.65 (30/30) | 122.35 (30/30) |
| R1_old_80 | 51.20 (30/30) | 52.05 (30/30) | 66.90 (30/30) | 75.15 (30/30) |
| R1_old_120 | 34.50 (30/30) | 38.65 (30/30) | 44.50 (30/30) | 48.55 (30/30) |
| R1_old_200 | 28.30 (30/30) | 31.65 (30/30) | 34.35 (30/30) | 37.50 (30/30) |
| R1_new_0 | none (0/30) | none (0/30) | none (0/30) | none (0/30) |
| R1_new_60 | 55.55 (30/30) | 72.85 (30/30) | 308.95 (16/30) | 287.80 (13/30) |
| R1_new_80 | 42.70 (30/30) | 58.25 (30/30) | 128.30 (30/30) | 131.90 (30/30) |
| R1_new_120 | 33.35 (30/30) | 44.20 (30/30) | 50.85 (30/30) | 55.85 (30/30) |
| R1_new_200 | 26.65 (30/30) | 36.25 (30/30) | 34.55 (30/30) | 38.50 (30/30) |
| R1_A_new_25 | 664.20 (5/30) | 739.10 (3/30) | none (0/30) | none (0/30) |
| R1_A_new_50 | 65.70 (30/30) | 83.95 (30/30) | 358.10 (1/30) | 363.60 (1/30) |
| R1_A_new_100 | 36.85 (30/30) | 51.30 (30/30) | 65.70 (30/30) | 70.65 (30/30) |
| R1_B_new200_bitter25 | 26.60 (30/30) | 36.15 (30/30) | 34.40 (30/30) | 38.80 (30/30) |
| R1_B_new200_bitter50 | 28.05 (30/30) | 45.50 (30/30) | 35.25 (30/30) | 40.15 (30/30) |
| R1_B_new200_bitter100 | 29.00 (30/30) | 76.45 (30/30) | 36.40 (30/30) | 41.30 (30/30) |
| R1_B_new200_bitter200 | 55.90 (23/30) | none (0/30) | 72.50 (30/30) | 88.95 (30/30) |
| R1_C_bitter25 | none (0/30) | none (0/30) | none (0/30) | none (0/30) |
| R1_C_bitter50 | none (0/30) | none (0/30) | none (0/30) | none (0/30) |
| R1_C_bitter100 | none (0/30) | none (0/30) | none (0/30) | none (0/30) |
| R1_C_bitter200 | none (0/30) | none (0/30) | none (0/30) | none (0/30) |
| R1_Aprime_LB3c20_120 | 37.35 (30/30) | 49.70 (30/30) | 53.55 (30/30) | 58.90 (30/30) |

All 24,330 actually driven GRN-trials received Poisson events and produced neuronal spikes. Own-rate means for the curve sets and subset control are below; zero-dose rows monitor those same sets but do not drive them.

| Input Hz | Frozen23 own rate, Hz | Candidate33 own rate, Hz |
|---|---|---|
| 0 | 0 ± 0 (undriven) | 0 ± 0 (undriven) |
| 60 | 59.630 ± 1.743 | 59.665 ± 1.312 |
| 80 | 79.396 ± 1.692 | 79.187 ± 1.406 |
| 120 | 118.652 ± 2.085 | 118.792 ± 2.049 |
| 200 | 196.242 ± 3.229 | 196.512 ± 2.696 |

A-prime LB3c20 own rate: **118.873 ± 2.745 Hz**. Individual source rows retain their explicit input rate; overlapping group averages must not be added together. Full source-group rates, latencies and input events for all controls remain in the local raw artifacts.

## Provenance, verification and limits

| Experiment | Code commit at run start | Completed UTC | Runs / workers / elapsed |
|---|---|---|---|
| S1 | `e41c436ddeeee4f8fedfa5fddd100af26203a025` | 2026-09-14 01:47:40 | 60 / 6 / 65.5 s |
| R1 | `59ac2860f63f888bf1990aed6258024c873a5b23` | 2026-09-14 01:59:57 | 660 / 13 / 295.0 s |

Both used WSL2, Brian2 2.9.0 and Cython, the unchanged frozen model parameters, one-second trials and the grid seed formula with the new condition blocks specified above. They are not historical-grid spike replays: the fixed research layouts contain 197 and 165 physical input units respectively.

Definitions and source-bound IDs: [S1 protocol](../data/stim_protocol_salt.json), [S1 runner](../sim/run_salt_screen.py), [R1 protocol](../data/stim_protocol_refreeze_sugar.json), [R1 runner](../sim/run_refreeze_sugar.py). Local, gitignored outputs are `results/salt/s1/` and `results/refreeze/sugar_r1/`: per-condition NPZ spike/input events, JSON trial ledgers, individual/group CSVs, summaries, source hashes and run metadata. Both `--summarize-only` checks reconstructed complete metrics from raw spikes and verified current source hashes, without simulation.

Independent raw audits, without importing the experiment statistics helpers, verified S1's 4,500 individual rows / 590 grouped rows / 354 summary fields and R1's 60,720 / 7,200 / 1,440. Exact matched Poisson trains: S1 450 (220 LB3d22 and 230 sugar23); R1 2,400 (1,440 active shared12, 360 zero-drive shared12, 600 A-prime shared20). Node 67 tests, Python 309 tests, release validation and diff checks pass. No frozen data, site, scoring, encoder, copy or README honesty-table changes.

S1 is a ten-trial screen; R1 is a thirty-trial comparison, not a full re-freeze or validation of every input combination. Everything is inside Shiu's model and is not calibrated against behaviour. Cell-type associations do not make the designed 100 Hz drive a salt-concentration measurement. Membership, population size and wiring change together; neither the normalised curves nor A-prime isolate all of those effects.

The historical 19-versus-20 shared-ID wording in `docs/phase0_report.md` and
its generator was corrected to 20 in a separate post-run commit, `036a8ca`;
no gate or numeric result changed. R1's run metadata hashes the earlier
generator, so its strict current-source `--summarize-only` guard will reject
that later wording-only change; the successful reconstruction above preceded
the correction. Original artifacts and hashes are retained, not rewritten.

## Output-sign check — connectivity only

[Reproducible check](../scripts/salt_output_signs.py): all 54 XLSX-selected
cells have outgoing edges, and each has one consistent `Excitatory` value
across every output edge in `2025_Connectivity_783.parquet`; every
`Excitatory x Connectivity` value equals `Excitatory` times `Connectivity`.
These are the unchanged signs consumed by the model, not `consensusNt`.
Counts below are neurons, not edges or synapses.

| Set | Model positive outputs (+1) | Model negative outputs (-1) | Local annotation `top_nt` | Cells disagreeing with annotation-derived sign |
|---|---:|---:|---|---:|
| LB3d29 | 27 | 2 | 18 acetylcholine; 4 serotonin; 7 glutamate | 5 / 29 |
| LB3b25 | 25 | 0 | 21 acetylcholine; 4 serotonin | 0 / 25 |

Two distinct annotation comparisons must not be conflated. **Against
Tastekin's class-level glutamatergic LB3d label, 27/29 cells disagree:**
their model outputs are positive rather than negative. The local Schlegel
per-neuron annotation TSV instead labels only seven LB3d cells as glutamate;
five of those seven have positive model outputs, while the other two have
negative outputs. LB3b has no sign disagreements with its local annotations.
For this sign comparison, glutamate/GABA map to negative and acetylcholine/
serotonin to positive under the [documented Shiu convention](open_questions.md#v3-note-updated-2026-09-10-malecns-as-a-substrate);
agreement of signs does not mean agreement of transmitter identity.

The two negative-output LB3d IDs are `720575940609645124` and
`720575940623172843`. The five local-annotation sign mismatches are
`720575940612208406`, `720575940623138485`, `720575940630552151`,
`720575940609476562`, and `720575940620926234`.

Source hashes: connectivity parquet
`efeb23fb99098e9c390f6869969b2a121a2ee92c833cfc45ecb2c1d8e1af0347`;
`data/external/Supplemental_file1_neuron_annotations.tsv`
`9a4f8b2f843196074431ebd7cd883536afa1be86c8a4ce90970441e8be81d1be`.
The XLSX hash and row selection are recorded above. This check changes no
signs and offers no explanation for the simulated firing outcomes.
Its six synthetic tests pass; the post-decision checks pass all 315 Python
tests, 67 Node tests, release validation and 69 local documentation links.

## Checkpoint decisions — recorded, not executed

**Salt as a fifth axis: Closed.** LB3d29 at 100 Hz drives left MN9 to
61.5 Hz, or 18.7 Hz with the seven frozen-sugar-overlap cells removed;
adding the non-overlap 22 to frozen sugar at 120 Hz raises all four readouts
in 10/10 trials. The model does not express high-salt aversion under this
design, contrary to Tastekin's prediction for LB3d. No explanation is
assigned. Reopen only with reproducible high-salt-associated aversion under
a justified, versioned input/substrate design and an explicit product mapping.

**Cell-set policy:** v1 retains the frozen Shiu sets. Above 80 Hz the MN9
curve differences remain within the predeclared two-SD trial-spread rule;
the owner judges a full grid/replay rerun unjustified for prospective ranking
changes near noise. These are not measured mixed-taste ranking changes.
For v2's planned two-brain design, use Tastekin typing on both brains,
because the male sets must be defined through that typing in this design
and the typed sugar set passes all four Phase 0 gates on the female brain.
A-prime attributes about 10 Hz of left-MN9 drive to adding LB3b13 to LB3c20
at 120 Hz, so LB3b stays in the v2 sugar set. The comparison does not validate
the male substrate or other replacement axes. No re-freeze is executed.

[OQ-7 and OQ-10](open_questions.md) and the [v2 memo](v2_decision_memo.md)
record these decisions. This closes simulation work on the female brain;
MaleCNS feasibility awaits a separately specified task after this PR merges.
