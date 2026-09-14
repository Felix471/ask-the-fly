# MaleCNS Phase 0 report — M1 full

## Run metadata

| Field | Value |
|---|---|
| Run date | 2026-09-14T06:55:53.483002+00:00 |
| Simulation commit | `a781697ce1d9d959186673a265e24889e82d4ba7` |
| Brian2 / codegen | 2.9.0 / cython |
| Workers | 9, selected from available RAM |
| Trials | A–D: 420; A′: 60; total 480; 30 per condition |
| Seeds | 20260910–20260939, reused across all conditions |
| Parallel walltime | 1104.4 s |
| Maximum observed worker peak RSS | 3.578 GiB |
| Substrate | 166,700 neurons; 25,582,938 edges; 124,177,617 synapses |

The plan measured WSL available RAM 60.58 GiB and host free RAM 85.02 GiB. It reserved 15.15 GiB (25% of the smaller figure; minimum 8 GiB), budgeted 4.6 GiB per worker (over 1.5× M0 peak), and chose **9 workers**, not the female run’s 14. Available WSL RAM was checked again at launch (60.62 GiB). RSS is the Linux Python-worker lifetime high-water mark, not summed simultaneous RSS or a guarantee of future workloads.

Sources: [plan](../data/malecns/phase0_plan.json), [frozen substrate](../data/malecns/substrate_record.json), [model protocol](../data/malecns/stim_protocol_malecns.json), [result/seed ledger](../data/malecns/phase0_results.json).

## Provenance and side convention

Both sides are recorded and gated separately in every condition. **R16949 is contralateral to XLSX-L sugar; L10331 is ipsilateral.** R remains the M0 reporting reference, not a settled primary choice; the owner deferred that decision until after M1. No readout was switched because it fired more.

Female comparison columns use the same relative/XLSX-side convention: contralateral is Shiu’s historical `left` (720575940660219265), ipsilateral is historical `right` (720575940618238523). A–D values are the original [female Phase 0 report](phase0_report.md): frozen23 sugar, n=30, **before the refractory correction**, not a fresh female rerun. Male uses typed17 and the corrected shared implementation. Sets, layouts and substrate differ; these columns are not paired trials or a controlled sex comparison.

The [adapter](../sim/malecns/adapter.py) calls the unchanged Shiu network builder and model parameters. M1 retains all 91 physical input slots from M0; inactive cells keep the ordinary refractory period. A′ zeros only the five LB3b input slots, preserving the twelve shared LB3c slots and random-stream layout. All results below are mean ± population SD, Hz, n=30 unless indicated.

## Results

| Gate; sugar/bitter Hz | Male contra R16949 | Male ipsi L10331 | Female contra (Shiu L) | Female ipsi (Shiu R) |
|---|---:|---:|---:|---:|
| A; 25/0 | 10.400 ± 12.727 | 43.033 ± 45.558 | 0.100 ± 0.300 | 0.067 ± 0.359 |
| A; 50/0 | 8.867 ± 7.719 | 42.333 ± 28.293 | 17.633 ± 4.854 | 13.267 ± 3.872 |
| A; 100/0 | 8.067 ± 3.245 | 58.567 ± 19.164 | 67.233 ± 4.724 | 49.500 ± 4.105 |
| A; 200/0 | 34.367 ± 3.082 | 129.800 ± 5.243 | 93.300 ± 5.780 | 62.067 ± 4.633 |
| B; 200/0 | 34.367 ± 3.082 | 129.800 ± 5.243 | 93.000 ± 4.539 | 62.167 ± 3.933 |
| B; 200/25 | 0.000 ± 0.000 | 9.700 ± 29.703 | 79.367 ± 3.996 | 48.933 ± 4.739 |
| B; 200/50 | 0.000 ± 0.000 | 1.300 ± 1.320 | 69.633 ± 4.167 | 39.733 ± 3.696 |
| B; 200/100 | 0.000 ± 0.000 | 3.033 ± 1.622 | 28.267 ± 5.033 | 13.200 ± 3.081 |
| B; 200/200 | 0.000 ± 0.000 | 6.567 ± 2.305 | 0.733 ± 0.573 | 0.067 ± 0.249 |
| C; 0/25 | 0.000 ± 0.000 | 19.000 ± 42.782 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| C; 0/50 | 0.000 ± 0.000 | 10.733 ± 31.228 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| C; 0/100 | 0.000 ± 0.000 | 6.200 ± 22.275 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| C; 0/200 | 0.000 ± 0.000 | 6.767 ± 23.308 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| D; 0/0 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 |

## Hard gates

The original [female gate predicates](../scripts/phase0_report.py) are applied independently to both sides; none is relaxed. Female ipsilateral verdicts below are recalculated from the original reported means/SDs using those same predicates, not an original frozen primary-readout decision.

| Check | Male contra R | Male ipsi L | Female contra | Female ipsi |
|---|---|---|---|---|
| A: sugar rises | FAIL | FAIL | PASS | PASS |
| B: bitter suppresses | PASS | FAIL | PASS | PASS |
| C: bitter-alone limit | PASS | FAIL | PASS | PASS |
| D: historical completeness | PASS | PASS | PASS | PASS |
| D: literal zero (additional) | PASS | PASS | PASS | PASS |
| C: literal zero (additional) | PASS | FAIL | PASS | PASS |
| Overall historical A–D | FAIL | FAIL | PASS | PASS |

A requires strictly rising successive sugar means (adjacent zeros allowed), and sugar200 > baseline + 5×baseline SD + 5 Hz. B requires every successive bitter mean to be non-increasing and bitter200 < 0.5×bitter0. C requires each bitter-alone mean ≤ baseline + 2×baseline SD + 1 Hz. **Historical D checks a baseline condition with at least 30 trials, not zero firing**; therefore literal zero mean and SD are reported separately rather than silently changing that gate. All conditions here also require exactly 30 complete trials.

## Soft indicators

| Indicator | Male contra R | Male ipsi L | Female contra | Female ipsi |
|---|---:|---:|---:|---:|
| Sugar100 / sugar200 | 0.235 | 0.451 | 0.721 | 0.798 |
| Bitter200 suppression vs bitter0 | 100.00% | 94.94% | 99.21% | 99.89% |

The original approximately-80%-of-maximum sugar comparison and ≥70% suppression reference remain soft indicators, not substitutes for monotonicity or the hard gates.

## Appendix A′ — 120 Hz

Male compares sugar17 (LB3b5 ∪ LB3c12, XLSX L) against LB3c12 alone, 30 fresh trials each. Female columns here switch explicitly to the [R1 typed-set comparison](salt_and_refreeze.md#adapted-a-prime-lb3c-only-l-subset-20-cells): sugar33 versus LB3c20, n=30, same 120 Hz level. This is the class-matched reference, not frozen23 and not the original 21-versus-23 A′, which did not test 120 Hz.

| Set / comparison | Male contra R | Male ipsi L | Female contra (Shiu L) | Female ipsi (Shiu R) |
|---|---:|---:|---:|---:|
| Typed sugar: male17 / female33 | 13.433 ± 5.590 | 80.333 ± 21.229 | 80.233 ± 4.492 | 51.700 ± 3.761 |
| LB3c-only: male12 / female20 | 10.667 ± 3.486 | 63.600 ± 20.318 | 69.567 ± 3.547 | 43.767 ± 4.039 |
| Paired subset-minus-union difference | -2.767 ± 6.731 | -16.733 ± 32.179 | -10.667 ± 6.529 | -7.933 ± 5.790 |

Differences are trial-wise paired differences, not differences of independent SDs. The historical female 21-versus-23 mean difference was <0.5 Hz for its primary MN9 across 25/50/100/200 Hz; it is not the same experiment as either typed-set A′.

## Laterality and decision boundary

At sugar200, male contra/ipsi means are 34.367/129.800 Hz; the female frozen23 reference is 93.300/62.067 Hz. The direction of the dominant response is compared under the same side convention; possible causes are Root_Side convention, reconstruction or a real difference, unresolved. [OQ-11](open_questions.md#oq-11-malecns-substrate-and-reversed-sugar-to-mn9-laterality-2026-09-14).

The primary male readout remains deferred to the owner. M1 is inside Shiu’s model and is not calibrated against behaviour. No female rerun, parameter tuning, product changes or M2 replication was performed.

## Equivalence and verification

The M1 audit checks saved full-network and Poisson events, all condition/trial/seed counts, rates, latencies, summary statistics and bilateral gate decisions. The first five A200/B0 and baseline trials are compared against the existing M0 recordings, not simulated again as an extra equivalence experiment. M0 overlaps the M1 seeds and is not pooled as n=35. A200 and B0 intentionally share identical drives/layout/seeds; their duplicate observations are not n=60.

Verification passed for 480 raw trials / 960 MN9-neuron trials, 1,395 M0 neuron-train comparisons, 2,910 shared Poisson-train comparisons and 30 identical A200/B0 whole-network pairs. [Audit record](../data/malecns/phase0_audit.json). Software checks: 25 male-only tests, 315 existing Python tests, 67 Node tests and release validation passed; this does not turn failed scientific gates into passes.

Brian2 emitted a `rates` namespace-name warning and explicitly used its internal Poisson rates variable. No warning was suppressed or source edited during the run; recorded input events are checked by the audit.

## Backend cross-check

No male PyTorch/CUDA cross-check was authorised or run; Brian2 is the simulation backend.

## Files

- [Male result and provenance ledger](../data/malecns/phase0_results.json)
- [Frozen M0 substrate](../data/malecns/substrate_record.json)
- [M1 plan](../data/malecns/phase0_plan.json)
- [Runner](../sim/malecns/phase0.py)
- [Report generator](../sim/malecns/report_phase0.py)
- Raw, gitignored spikes and input events: `data/malecns/runs/m1/`.
- Female A–D source: `results/phase0/full/summary.csv`.
- [Frozen female comparison values and source hashes](../data/malecns/phase0_female_reference.json).
- Female typed A′ sources: `results/refreeze/sugar_r1/readout_summary.csv` and `group_trials.csv`.

## M1b / M1c decision boundary (declared before rescaled runs)

M1b diagnoses saved M1 spikes and unsigned synaptic in-degree only; no new simulations.
See the [M1b tables, diagnosis and density-definition checkpoint](malecns_m1b.md).
The owner has pre-declared exactly two M1c candidates: original `w_syn / r_all`
and original `w_syn / r_mn9`, with every other protocol parameter unchanged.
M1b must be reported and the derivations confirmed before either candidate runs.
No search over `w_syn` is authorised.

**Stop rule:** a candidate counts as passing only if all four historical A–D gates
pass on at least one MN9 side, evaluated separately with the unchanged criteria above.
If neither candidate passes, the male line stops and this report will say so;
no third value will be tried in this task. The primary readout is not switched in advance.

Each candidate will retain 30 trials per condition with M1's seeds: 420 A–D trials
plus both 120-Hz A′ arms (sugar17 and LB3c12, 30 each), i.e. 480 per candidate,
960 including A′ across the two candidates. No M1c trial has run.

The exact requested 200-partner `r_mn9` is presently undefined: male contralateral
R16949 has only 137 retained presynaptic partners. An explicitly labeled
available-partner alternative may be reported at M1b but requires owner confirmation;
missing partners will not be fabricated or silently padded with zeros.

**Owner confirmation, before M1c:** means are used for both ratios; the
137-partner exception is accepted with the two sides' mean degrees equally
weighted. `r_all=1.8951912499349262` gives `w_syn=0.14510408910416958 mV`;
`r_mn9=1.985509366815815` gives `w_syn=0.13850350171906808 mV`.
These are the full-precision versions of the approved 0.145104 / 0.138504 mV
candidates, not additional candidates. The external Poisson kick remains
`w_syn*f_poi`; all other model/trial parameters remain unchanged. The
[preflight additions](malecns_m1b.md) were recorded before rescaled runs.
