# M1j — bilateral typed sugar sets on both brains (v2 stimulus policy test)

Pre-declared 2026-09-19 (local 2026-09-18 evening, America/New_York).
Owner-signed declaration; no M1j results. This internal checkpoint contains
declaration files only. No substrate build, M0 recheck or simulation is performed.

## Policy and rationale

M1j tests a **v2 stimulus policy on both brains**: bilateral labellar sugar
LB3b ∪ LB3c from Tastekin Table S1, with no pharyngeal or tarsal GRNs.
The owner's rationale is that the one-sided 23-cell female set is Shiu's
benchmark convention, not a biological requirement; a fly tasting food uses
both labellar palps. This is a designed stimulus policy, not a male-only fix.
The [v2 memo](v2_decision_memo.md#cell-set-policy--decided-not-executed)
already records Tastekin typing on both brains. Bitter, water and Ir94e
(amino-acid aversion) sets stay unchanged for this test. No product, frozen
file, encoder dimension or README honesty-table change follows.

The [M1i checkpoint](malecns_phase0.md#m1i-results-checkpoint--2026-09-18)
matched all three fly-brain-minecraft replication criteria, but our 17-cell
labellar input passed A–D, S2 and S3 on L10331 and failed S1. The declared
input-size confound remains the recorded reading: 17 versus their 204 cells,
with the same graph and gain, about 37 versus 105 Hz at sugar 200.
S3 measures consistency **within sugar 200**, not absolute activity: M1i's
network spike count rose from about 3.9k per trial at sugar 100 to about 306k
at sugar 200; bitter alone drove about 300k while MN9 remained at zero.
These are historical context, not M1j outcomes.

## Substrates, source identities and layouts

The source workbook is local Table S1, SHA256
`7b28d5f3ae45d68c510b8a3616700f0df2a5a6f2e2d2dba490d172939f2b64c9`.
Both resolvers select GRNs by exact Connectome and Subtype, retaining both
Root_Side values. Female selection uses `FAFB – Flywire`; male uses `maleCNS`.
See the [source and hemisphere policy](salt_and_refreeze.md#source-identities-and-hemisphere-policy).

| Declaration | Male | Female |
|---|---|---|
| Substrate | Existing M1i whole-CNS ≥5, autapses removed | Frozen FlyWire v783, no cut |
| Connectivity | `data/malecns/derived/fbm/connectivity.parquet` | `vendor/fly-brain/data/2025_Connectivity_783.parquet` |
| w_syn | 0.65 × 0.275 = 0.17875 mV (stored full precision) | 0.275 mV |
| Sugar LB3b ∪ LB3c | 34: L17/R17 | 57: L33/R24 |
| LB3b | 11: L5/R6 | 25: L13/R12 |
| A′ LB3c-only subset | 23: L12/R11 | 32: L20/R12 |
| Unchanged bitter / water / Ir94e | 38 / 17 / 19 | 42 / 18 / 18 |
| Primary MN9 | L10331 | Frozen left 720575940660219265 |
| Recorded secondary MN9 | R16949 | Frozen right 720575940618238523 |
| Physical channel counts | 34 + 38 + 17 + 19 = 108 | 57 + 42 + 11 + 18 = 128 |

The male substrate is documented in the existing
[M1i substrate record](../data/malecns/substrate_record_fbm.json).
All model and trial fields remain unchanged from the respective parent
protocols, including 1,000 ms trials and dt 0.1 ms.

The female 57 include 12 frozen sugar cells and seven frozen water cells,
with zero bitter or Ir94e overlap. The exact overlap IDs are recorded in
the female cell file. Every physical root appears once; the seven shared
roots belong to the sugar channel. Water and Ir94e are 0 Hz in every
condition, so no conflicting drive arises. Male stimulus channels are
disjoint; A′ is a subset of the sugar channel, not extra physical units.
Channel order is sugar, bitter, water, Ir94e, with ascending numeric body ID
within each channel. Inactive units keep the ordinary refractory period;
driven units get refractory 0, exactly as in M1/M1i.

| Artifact | Source resolver / parent |
|---|---|
| [Male cells](../data/malecns/cells_m1j.json) | [Resolver](../sim/malecns/m1j_cells.py), [unchanged original cells](../data/malecns/cells.json) |
| [Female cells](../data/cells_m1j_female.json) | [Resolver](../scripts/build_m1j_female_cells.py), [frozen cells](../data/cells.json); every ID checked against v783 completeness |
| [Male protocol](../data/malecns/stim_protocol_malecns_m1j.json) | [M1i parent](../data/malecns/stim_protocol_malecns_fbm.json) |
| [Female protocol](../data/stim_protocol_m1j_female.json) | [Frozen parent](../data/stim_protocol.json); model and trial fields identical |

## Conditions and records

Both brains use this identical design, 30 trials per condition, seeds
`20260910 + trial` for trial 0–29 in every condition. These are M1 seeds;
R1 used the different grid formula `20260910+1000*(seed_index%40)+trial`.
The A′ union and subset conditions have paired seeds and the same physical
layout within each brain. Equal seed numbers across brains do not establish
identical input event trains across their different layouts.

| Group | Sugar Hz | Bitter Hz | Trials per brain |
|---|---|---|---:|
| A | 25 / 50 / 100 / 200 | 0 | 120 |
| B | 200 | 0 / 25 / 50 / 100 / 200 | 150 |
| C | 0 | 25 / 50 / 100 / 200 | 120 |
| D | 0 | 0 | 30 |
| A′ | Bilateral union and bilateral LB3c-only, each 120 | 0 | 60 |
| Total | | | 480 |

The two brains total 960 M1j trials. Per trial, retain both MN9 rates and
first-spike latencies, whole-network spike count, neurons fired, source
spike counts, Poisson event trains and worker peak RSS, as M1i did.

## Gates, adoption and stop rule

A–D use the unchanged historical predicates in
[`sim.malecns.phase0.evaluate_gates`](../sim/malecns/phase0.py), implementing
the female predicates in [`scripts/phase0_report.py`](../scripts/phase0_report.py).
Before any M1j trial, a test must assert the two agree on female summaries.
S uses [`sim.malecns.split.shape_gate`](../sim/malecns/split.py), on each
brain's primary MN9, with its existing definitions:

| Gate | Predicate |
|---|---|
| S1 | At least four of five mean rates at sugar 25/50/100/120/200 are >0 Hz |
| S2 | Each adjacent decrease ≤ sqrt((population SD before² + population SD after²)/2) |
| S3 | Sugar 200 whole-network spike count max/min <3; zero minimum fails |

A supplies 25/50/100/200; the A′ union supplies 120. No added S trials.
**Pass per brain requires A, B, C, D, S1, S2 and S3.** The secondary MN9 is
recorded, not deciding. **Adopt the policy for v2 only if both brains pass.**
If either fails, reject the policy and close the male line at nine variants.
The ledger becomes nine variants after M1j whatever the result. No further
variant, set, gain or threshold change after M1j is permitted under this
authorization. Historical rules and results are not rewritten.

## Retention declaration

Before trials, record male outgoing synapses of the 34 bilateral sugar cells
and the 23-cell A′ subset at ≥1 versus ≥5, in the same layout as M1i's table.
This is recorded, not deciding. The female frozen graph has no cut: its table
will give outgoing synapse totals of the 57 sugar cells only, **no retention
fraction**, explicitly labelled as such. These tables are not computed at
this declaration checkpoint.

## Mandatory M0 environment check

Before any M1j trial, rerun the M0 benchmark: baseline and sugar 200, five
trials each, seeds 20260910–20260914, whole-CNS all-edge male connectivity
`data/malecns/derived/connectivity.parquet`, w_syn 0.275 mV, original 91-unit
M0 layout. Use committed code and the same `SimNet.run_trial` routine as
[`sim/malecns/benchmark.py`](../sim/malecns/benchmark.py).
Write to the separate, write-once `data/malecns/runs/m0_recheck` directory.

Compare every neuron's spike-time array in each of all ten trials with the
stored `data/malecns/runs/m0` files: neuron keys must match and arrays must
be exactly equal. If identical, record that in the M1j section and proceed.
**Any difference: stop, run no M1j trial, report to the owner.** Stored M0
provenance names older source-file versions; this check determines whether
later edits changed the numbers. No M0 recheck is performed here.

## Owner follow-up and sequence

Owner addition, recorded rather than a gate: because the female bilateral
sugar set includes seven frozen water cells, a v2 re-typing must also
redefine water as LB3a, not only sugar. This follow-up is recorded in the
[v2 cell-set policy](v2_decision_memo.md#cell-set-policy--decided-not-executed);
water remains unchanged in M1j.

Declaration commit → cell files, protocols, retention tables and runners
with compile-only plans (internal checkpoint) → M0 recheck (stop if not
identical) → male run → female run → independent audit → results section
with both gate tables and both sugar curves side by side → memo and OQ
updates → PR into dev. One report to the owner at the end. Stop at the
current declaration-only internal checkpoint; subsequent work is not
performed here.
### M1j build checkpoint — 2026-09-19

Build-only checkpoint; no simulation trial or M0 recheck execution.

The [retention record](../data/malecns/m1j_retention.json) hashes both male graphs, the frozen female graph and their index/cell sources. Male legacy `outgoing_0_5` means baseline ≥1; `outgoing_c_star` means ≥5 without autapses. Flags are recorded, not a stop condition. Subset rows overlap the union and are not added to its totals.

| Male set | Cells | Outgoing ≥1 | Outgoing ≥5 | Retained | Below half |
|---|---:|---:|---:|---:|---|
| sugar_bilateral | 34 | 14950 | 11739 | 78.521739% | False |
| sugar_lb3c_bilateral | 23 | 11032 | 8864 | 80.348078% | False |

| Male body ID | Set / readout | Outgoing ≥1 | Outgoing ≥5 | Retained | Below half |
|---:|---|---:|---:|---:|---|
| 71254 | sugar_bilateral | 779 | 668 | 85.750963% | False |
| 72059 | sugar_bilateral | 1175 | 1099 | 93.531915% | False |
| 78240 | sugar_bilateral | 425 | 343 | 80.705882% | False |
| 85806 | sugar_bilateral | 791 | 674 | 85.208597% | False |
| 92440 | sugar_bilateral | 957 | 876 | 91.536050% | False |
| 101087 | sugar_bilateral | 603 | 479 | 79.436153% | False |
| 120303 | sugar_bilateral | 588 | 486 | 82.653061% | False |
| 140015 | sugar_bilateral | 508 | 401 | 78.937008% | False |
| 142827 | sugar_bilateral | 460 | 364 | 79.130435% | False |
| 159772 | sugar_bilateral | 422 | 344 | 81.516588% | False |
| 163597 | sugar_bilateral | 347 | 228 | 65.706052% | False |
| 180314 | sugar_bilateral | 178 | 88 | 49.438202% | True |
| 183084 | sugar_bilateral | 332 | 251 | 75.602410% | False |
| 187492 | sugar_bilateral | 334 | 226 | 67.664671% | False |
| 190769 | sugar_bilateral | 353 | 240 | 67.988669% | False |
| 202888 | sugar_bilateral | 511 | 405 | 79.256360% | False |
| 209155 | sugar_bilateral | 289 | 193 | 66.782007% | False |
| 215556 | sugar_bilateral | 609 | 499 | 81.937603% | False |
| 261450 | sugar_bilateral | 354 | 261 | 73.728814% | False |
| 262567 | sugar_bilateral | 266 | 134 | 50.375940% | False |
| 272263 | sugar_bilateral | 296 | 209 | 70.608108% | False |
| 512551 | sugar_bilateral | 876 | 799 | 91.210046% | False |
| 516217 | sugar_bilateral | 453 | 328 | 72.406181% | False |
| 531237 | sugar_bilateral | 414 | 316 | 76.328502% | False |
| 557646 | sugar_bilateral | 431 | 337 | 78.190255% | False |
| 933317 | sugar_bilateral | 1024 | 946 | 92.382812% | False |
| 942168 | sugar_bilateral | 106 | 36 | 33.962264% | True |
| 957530 | sugar_bilateral | 61 | 7 | 11.475410% | True |
| 158893964 | sugar_bilateral | 107 | 35 | 32.710280% | True |
| 174444965 | sugar_bilateral | 42 | 13 | 30.952381% | True |
| 213650853 | sugar_bilateral | 512 | 348 | 67.968750% | False |
| 349137284 | sugar_bilateral | 64 | 5 | 7.812500% | True |
| 475202322 | sugar_bilateral | 149 | 43 | 28.859060% | True |
| 766547228 | sugar_bilateral | 134 | 58 | 43.283582% | True |
| 72059 | sugar_lb3c_bilateral | 1175 | 1099 | 93.531915% | False |
| 78240 | sugar_lb3c_bilateral | 425 | 343 | 80.705882% | False |
| 85806 | sugar_lb3c_bilateral | 791 | 674 | 85.208597% | False |
| 92440 | sugar_lb3c_bilateral | 957 | 876 | 91.536050% | False |
| 101087 | sugar_lb3c_bilateral | 603 | 479 | 79.436153% | False |
| 120303 | sugar_lb3c_bilateral | 588 | 486 | 82.653061% | False |
| 140015 | sugar_lb3c_bilateral | 508 | 401 | 78.937008% | False |
| 142827 | sugar_lb3c_bilateral | 460 | 364 | 79.130435% | False |
| 180314 | sugar_lb3c_bilateral | 178 | 88 | 49.438202% | True |
| 190769 | sugar_lb3c_bilateral | 353 | 240 | 67.988669% | False |
| 202888 | sugar_lb3c_bilateral | 511 | 405 | 79.256360% | False |
| 215556 | sugar_lb3c_bilateral | 609 | 499 | 81.937603% | False |
| 261450 | sugar_lb3c_bilateral | 354 | 261 | 73.728814% | False |
| 262567 | sugar_lb3c_bilateral | 266 | 134 | 50.375940% | False |
| 512551 | sugar_lb3c_bilateral | 876 | 799 | 91.210046% | False |
| 516217 | sugar_lb3c_bilateral | 453 | 328 | 72.406181% | False |
| 531237 | sugar_lb3c_bilateral | 414 | 316 | 76.328502% | False |
| 933317 | sugar_lb3c_bilateral | 1024 | 946 | 92.382812% | False |
| 942168 | sugar_lb3c_bilateral | 106 | 36 | 33.962264% | True |
| 957530 | sugar_lb3c_bilateral | 61 | 7 | 11.475410% | True |
| 158893964 | sugar_lb3c_bilateral | 107 | 35 | 32.710280% | True |
| 349137284 | sugar_lb3c_bilateral | 64 | 5 | 7.812500% | True |
| 475202322 | sugar_lb3c_bilateral | 149 | 43 | 28.859060% | True |
| 10331 | MN9_L_primary | 280 | 51 | 18.214286% | True |
| 16949 | MN9_R_secondary | 445 | 203 | 45.617978% | True |

Female: frozen v783 graph has no cut; outgoing synapse totals only. Every `retention_fraction` is null.

| Female set | Cells | Outgoing synapses |
|---|---:|---:|
| sugar_bilateral | 57 | 11764 |
| sugar_lb3c_bilateral | 32 | 8070 |

| Female root ID | Set | Outgoing synapses |
|---:|---|---:|
| 720575940606002609 | sugar_bilateral | 197 |
| 720575940607347634 | sugar_bilateral | 151 |
| 720575940607737099 | sugar_bilateral | 121 |
| 720575940608305161 | sugar_bilateral | 226 |
| 720575940609919897 | sugar_bilateral | 185 |
| 720575940610296622 | sugar_bilateral | 103 |
| 720575940612010137 | sugar_bilateral | 169 |
| 720575940612445938 | sugar_bilateral | 69 |
| 720575940612579053 | sugar_bilateral | 290 |
| 720575940612612581 | sugar_bilateral | 82 |
| 720575940612670570 | sugar_bilateral | 451 |
| 720575940612950568 | sugar_bilateral | 297 |
| 720575940613601698 | sugar_bilateral | 170 |
| 720575940614302370 | sugar_bilateral | 67 |
| 720575940616742657 | sugar_bilateral | 239 |
| 720575940616851286 | sugar_bilateral | 37 |
| 720575940616885538 | sugar_bilateral | 261 |
| 720575940617000768 | sugar_bilateral | 302 |
| 720575940617181725 | sugar_bilateral | 134 |
| 720575940617801499 | sugar_bilateral | 63 |
| 720575940617937543 | sugar_bilateral | 416 |
| 720575940620296641 | sugar_bilateral | 93 |
| 720575940620589838 | sugar_bilateral | 346 |
| 720575940621502051 | sugar_bilateral | 240 |
| 720575940621508479 | sugar_bilateral | 17 |
| 720575940621754367 | sugar_bilateral | 171 |
| 720575940622200233 | sugar_bilateral | 68 |
| 720575940622413508 | sugar_bilateral | 133 |
| 720575940622486922 | sugar_bilateral | 294 |
| 720575940622731229 | sugar_bilateral | 234 |
| 720575940622825736 | sugar_bilateral | 233 |
| 720575940623629292 | sugar_bilateral | 181 |
| 720575940625861168 | sugar_bilateral | 219 |
| 720575940627490663 | sugar_bilateral | 170 |
| 720575940627907883 | sugar_bilateral | 77 |
| 720575940628853239 | sugar_bilateral | 495 |
| 720575940629025324 | sugar_bilateral | 128 |
| 720575940629176663 | sugar_bilateral | 240 |
| 720575940629388135 | sugar_bilateral | 452 |
| 720575940629510338 | sugar_bilateral | 154 |
| 720575940629852866 | sugar_bilateral | 172 |
| 720575940629884119 | sugar_bilateral | 154 |
| 720575940631147148 | sugar_bilateral | 169 |
| 720575940631393484 | sugar_bilateral | 158 |
| 720575940631656504 | sugar_bilateral | 9 |
| 720575940632510479 | sugar_bilateral | 241 |
| 720575940632627660 | sugar_bilateral | 14 |
| 720575940632880173 | sugar_bilateral | 54 |
| 720575940634023961 | sugar_bilateral | 57 |
| 720575940635172191 | sugar_bilateral | 301 |
| 720575940639043280 | sugar_bilateral | 549 |
| 720575940639198653 | sugar_bilateral | 719 |
| 720575940639259967 | sugar_bilateral | 557 |
| 720575940639332736 | sugar_bilateral | 206 |
| 720575940640649691 | sugar_bilateral | 188 |
| 720575940641339611 | sugar_bilateral | 52 |
| 720575940645332259 | sugar_bilateral | 189 |
| 720575940606002609 | sugar_lb3c_bilateral | 197 |
| 720575940608305161 | sugar_lb3c_bilateral | 226 |
| 720575940612010137 | sugar_lb3c_bilateral | 169 |
| 720575940612445938 | sugar_lb3c_bilateral | 69 |
| 720575940612579053 | sugar_lb3c_bilateral | 290 |
| 720575940612612581 | sugar_lb3c_bilateral | 82 |
| 720575940612670570 | sugar_lb3c_bilateral | 451 |
| 720575940612950568 | sugar_lb3c_bilateral | 297 |
| 720575940613601698 | sugar_lb3c_bilateral | 170 |
| 720575940616742657 | sugar_lb3c_bilateral | 239 |
| 720575940616885538 | sugar_lb3c_bilateral | 261 |
| 720575940617000768 | sugar_lb3c_bilateral | 302 |
| 720575940620296641 | sugar_lb3c_bilateral | 93 |
| 720575940620589838 | sugar_lb3c_bilateral | 346 |
| 720575940621502051 | sugar_lb3c_bilateral | 240 |
| 720575940621754367 | sugar_lb3c_bilateral | 171 |
| 720575940622486922 | sugar_lb3c_bilateral | 294 |
| 720575940622731229 | sugar_lb3c_bilateral | 234 |
| 720575940623629292 | sugar_lb3c_bilateral | 181 |
| 720575940625861168 | sugar_lb3c_bilateral | 219 |
| 720575940627907883 | sugar_lb3c_bilateral | 77 |
| 720575940628853239 | sugar_lb3c_bilateral | 495 |
| 720575940629388135 | sugar_lb3c_bilateral | 452 |
| 720575940629852866 | sugar_lb3c_bilateral | 172 |
| 720575940631147148 | sugar_lb3c_bilateral | 169 |
| 720575940632627660 | sugar_lb3c_bilateral | 14 |
| 720575940635172191 | sugar_lb3c_bilateral | 301 |
| 720575940639198653 | sugar_lb3c_bilateral | 719 |
| 720575940639259967 | sugar_lb3c_bilateral | 557 |
| 720575940639332736 | sugar_lb3c_bilateral | 206 |
| 720575940640649691 | sugar_lb3c_bilateral | 188 |
| 720575940645332259 | sugar_lb3c_bilateral | 189 |

Layouts: male 34 + 38 + 17 + 19 = **108** physical units; female 57 + 42 + 11 + 18 = **128**, with no duplicate targets. The seven female water-overlap roots occur only in sugar. A′ drives 23 of the 34 male sugar slots (11 at zero) and 32 of the 57 female sugar slots (25 at zero); physical layouts and slot ordering remain fixed. All inactive targets retain ordinary refractory; only positive-rate targets have refractory zero.

The [male runner](../sim/malecns/m1j_phase0.py), [shared adapter](../sim/malecns/m1j_adapter.py) and [female runner](../sim/m1j_female.py) validate protocols and cells against declaration commit `9d169c3`, reuse the historical M1 trial routine and A–D/S evaluators, and refuse retry/resume or existing output directories. Per-trial extended rows, including neurons fired, are stored in condition ledgers and the full results ledger; historical-format trial JSON and event archives are retained.

**Plans compiled in WSL (Brian2 2.9.0), one network each, zero simulated seconds, zero spikes:** [male plan](../data/malecns/m1j_male_plan.json) 8 workers from WSL 59.4 GiB available and host 88.4 GiB free, 5.4 GiB budget per worker over the recorded M1 peak 3.578 GiB; [female plan](../data/m1j_female_plan.json) 9 workers, 4.8 GiB budget over the recorded v1.2 lookup-run peak 3.164 GiB.

Female planning reads the recorded 3.1635169982910156 GiB peak from `data/lookup_v1_2_audit.json` (`run.peak_worker_rss_gib`) at plan time: the 400-cell × 30-trial v1.2 lookup run used 14 workers and the whole v783 network, also documented in `docs/grid_provenance.md`. The plan records this source path and value. Male planning uses the recorded M1 worker peak. Both call the unchanged `phase0.choose_workers` using fresh WSL and host available memory.

The [M0 recheck](../sim/malecns/m0_recheck.py) uses the original whole-CNS all-edge, 91-unit, 0.275 mV configuration and `SimNet.run_trial`: one fresh worker per baseline/sugar200 condition, zero-duration compile, five trials each with seeds 20260910–20260914. Separate write-once outputs are compared with stored M0 using identical key sets and exact `np.array_equal` for every neuron, plus per-trial MN9 rates/latencies and whole-network spike counts. The record reports compared neuron/spike counts and all six current versus historical source hashes. **Result: IDENTICAL** ([record](../data/malecns/m0_recheck.json)): all 10 trials, 88,346 neuron spike-time arrays and 5,792,465 spikes equal to the stored M0 files, MN9 rates and latencies equal; all six M0 provenance files carry their stored hashes. Both M1j runners require this verdict before trials.

Windows build checks include both layouts and A′ zeroing, protocol/cell tamper rejection, exact M0 array comparison, and female historical A–D predicate agreement. No numerical M1j result or policy adoption is claimed.

Verification: 20 new targeted tests pass; general Python discovery passes 353 tests. Male discovery passes all 109 tests after the reviewer-authorized report-scope correction: the exact generated M1i block must be a prefix, followed only by an empty suffix or a later top-level section beginning with `\n## `. Generated M1i text and the declaration prefix remain byte-identical. Female `--check`, M1i report regeneration and diff whitespace checks pass. Earlier build checks passed retention verification, both Windows `--check` commands and release validation; the earlier missing-directory M0 comparison failed cleanly as expected. The reviewer runs the M0 recheck separately.
