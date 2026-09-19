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
