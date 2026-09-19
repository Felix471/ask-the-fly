# MaleCNS Phase 0 report — M1, M1c, M1d and M1f

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

## M1 parameter audit — 2026-09-14 (no simulation)

Scope: the **unscaled M1** runs, not the later M1c candidates. Source: Tastekin et al. (2026), [STAR Methods, “Connectome-based integrate-and-fire model”, p. e5](https://doi.org/10.1016/j.cell.2026.08.016) (local PDF page 31), and the vendored Shiu `model.py`, `default_params` and `poi` functions. The [male protocol](../data/malecns/stim_protocol_malecns.json) and [frozen female protocol](../data/stim_protocol.json) have exactly equal `model` and `trial` objects; the [adapter](../sim/malecns/adapter.py#L10) enforces that equality. “Identical” below compares our male and female implementations, not equality to every Tastekin experimental condition.

| Parameter / source rule | Tastekin STAR Methods or Shiu reference code | M1 male value / rule | Frozen female value / rule | Male/female identical? | Where set in our code |
|---|---|---|---|---|---|
| `t_run` | 1 s | 1000 ms | 1000 ms | Yes | Protocol `trial.duration_ms`; [M1 run](../sim/malecns/phase0.py#L146), [shared run](../sim/network.py#L102) |
| `n_run` | 30 | 30 per condition | 30 per condition | Yes (not the 5-trial sanity stage) | Protocol `trial.n_trials`; [M1 conditions](../sim/malecns/phase0.py#L28) |
| `v_0` | −52 mV | −52 mV | −52 mV | Yes | Protocol `model.v_0_mV`; [shared parameter conversion / initialisation](../sim/network.py#L139) |
| `v_rst` | −52 mV | −52 mV | −52 mV | Yes | Protocol `model.v_rst_mV`; [shared builder](../sim/network.py#L139) |
| `v_th` | −45 mV | −45 mV | −45 mV | Yes | Protocol `model.v_th_mV`; [shared builder](../sim/network.py#L139) |
| `t_mbr` | 20 ms | 20 ms | 20 ms | Yes | Protocol `model.t_mbr_ms`; [shared builder](../sim/network.py#L139) |
| `tau` | 5 ms | 5 ms | 5 ms | Yes | Protocol `model.tau_ms`; [shared builder](../sim/network.py#L139) |
| `t_rfc` | 2.2 ms | 2.2 ms except driven cells below | Same | Yes, corrected implementation; historical exception below | Protocol `model.t_rfc_ms`; [initial refractory](../sim/network.py#L175) |
| `t_dly` | 1.8 ms | 1.8 ms | 1.8 ms | Yes | Protocol `model.t_dly_ms`; [synaptic delay](../sim/network.py#L182) |
| `w_syn` | Printed **275 μs**; Shiu code `.275 * mV` | **0.275 mV** | **0.275 mV** | Yes; not a literal time-unit match to the printed text | Protocol `model.w_syn_mV`; [conversion](../sim/network.py#L147), [signed weights](../sim/network.py#L189) |
| `r_poi` | 200 Hz | Sugar 0/25/50/100/200 Hz in A–D; A′ 120 Hz | Same A–D schedule; historical A′ 25/50/100/200 Hz | A–D yes; **A′ no**; neither uses a universal 200 Hz | Protocol `phase0_conditions`; [M1 conditions](../sim/malecns/phase0.py#L28), [rate assignment](../sim/malecns/phase0.py#L140) |
| `r_poi2` | 100 Hz | Bitter 0/25/50/100/200 Hz; no GNG015 drive | Same A–D bitter schedule; no GNG015 drive | Yes for A–D; **not Tastekin’s fixed 100 Hz second-drive condition** | Protocol `phase0_conditions`; [M1 conditions](../sim/malecns/phase0.py#L28), [shared set_rates](../sim/network.py#L80) |
| `f_poi` | 250 | 250 | 250 | Yes | Protocol `model.f_poi`; [external weight](../sim/network.py#L221) |
| Synapse signs | Glu/GABA inhibitory; everything else excitatory | `consensus_nt` GABA/glutamate → −1, all others → +1, including unclear/missing | Inherited Shiu frozen `Excitatory x Connectivity`; not re-signed from Tastekin labels | **Not identical sign data**; nominal Glu/GABA convention agrees, assignments/source differ | [Male sign assignment](../sim/malecns/substrate.py#L68); [shared signed-edge loading](../sim/network.py#L158) and [weight application](../sim/network.py#L189) |
| Poisson-drive rule (Shiu code) | Per selected cell, `PoissonInput(N=1)`, direct voltage kick `w_syn*f_poi` | One PoissonGroup unit per input cell; one-to-one `v += w_stim`; **68.75 mV/event** | Same shared implementation and kick | Yes in rule; **not identical layouts/random streams** (male 91 slots, female frozen grid 101) | Protocol `stimulus`; [PoissonGroup / one-to-one Synapses](../sim/network.py#L212), [weight](../sim/network.py#L221) |
| Driven-cell refractory rule (Shiu code) | `poi()` sets `rfc=0` for cells in its passed stimulation lists | Per trial: positive-rate cells 0 ms; inactive cells 2.2 ms, including five excluded LB3b cells in A′ | Corrected path: positive-rate channels 0 ms; inactive channels 2.2 ms | **Yes on corrected path; no versus pre-correction historical female runs** | [Shared correction](../sim/network.py#L80); [M1 per-cell reset / override](../sim/malecns/phase0.py#L143) |

The reference `poi()` zeros refractory for every cell in a passed list even if that list's rate is zero; our reusable implementation represents “driven” by a positive rate, retaining inactive input slots without zeroing their refractory. Both substrates use this corrected rule. Shiu's vendored `default_params` has `r_poi=150 Hz` and `r_poi2=0 Hz`, not Tastekin's printed 200/100; those rates are condition settings, not immutable model constants. Our channel names do not imply that bitter GRNs are the interneurons stimulated in Tastekin's experiment. The PoissonGroup implementation is not literally the reference PoissonInput object; its validation and differing random streams are documented in the [equivalence study](equivalence_study.md#acceptance-criteria).

**Female refractory correction.** The original female Phase 0 comparison values in this report predate the correction: every built stimulus channel had `rfc=0`, even when inactive. The frozen grid uses the corrected per-trial rule, and the male adapter calls that same builder; M1 additionally applies it per physical cell for the A′ subset. At sugar 100 Hz, the [10 matched-seed diagnostic](equivalence_study.md#refractory-quirk-10-matched-seeds) found zero pure refractory effect and exact all-neuron spike agreement in 10/10 trials. That is a tested-condition result, not proof of zero effect everywhere; see the [female report provenance](phase0_report.md#provenance-note-2026-09-10).

**Weight-unit interpretation and reproduction evidence.** Our operational reading is settled as **0.275 mV = 275 μV**, not 275 μs: Shiu's executable reference explicitly uses `.275*mV`, and that value was retained in the female reproduction/validation ([Phase 0](phase0_report.md#hard-gates), [reference-code equivalence](equivalence_study.md#acceptance-criteria)). However, these reports do **not** establish exact reproduction of Shiu's published absolute rates: the [published-calibration comparison](phase0_report.md#soft-indicators) is explicitly provisional (72.1% versus approximately 80%, with an assumed maximum). Thus the code and female validation settle what **we implemented**, not what Tastekin's unpublished executable build actually used. No parameter, protocol, saved result or simulation code was changed for this audit.

## Further-variant rule and M1d authorisation — 2026-09-14

From M1d onward, each further variant must rest on a **distinct structural rationale written before running**, must re-run **all gates including shape gate S**, and must be reported whether it passes or fails. There will be **no sweep over `w_syn` values, no fixing one failed gate in isolation, and no removing failed variants from the record**. This replaces a blanket “this line stops regardless of outcome” framing for future work; it does not alter the completed M1/M1c protocols, criteria or results.

The owner authorises M1d to separate external stimulation from recurrent connectivity: keep the stimulus kick at the frozen female value (`0.275 mV * 250 = 68.75 mV/event`) while scaling recurrent weights by the already measured `r_all` (`0.275 / 1.895191250 = 0.145104089 mV` per signed synapse). The structural rationale is that the measured synaptic in-degree difference concerns recurrent connectivity, not the strength of the externally imposed Poisson drive; M1c scaled both together. This is a distinct design, not another searched weight. Evaluate A–D and S on primary MN9 L10331, retain R16949 as secondary, and include the A′ analogue.

**Gate S confirmed before M1d:** sugar 25/50/100/120/200 Hz, all other inputs zero, 30 trials per level with M1 seeds 20260910–20260939. Reuse A's four levels and the A′ sugar17 120-Hz arm; no extra S trials. S1: positive MN9 mean at at least four levels. S2: each adjacent mean decrease is no greater than one pooled population SD, `sqrt((SD_before² + SD_after²)/2)`. S3: sugar200 whole-network spike count max/min is strictly less than 3; a zero minimum is undefined/infinite and fails. S requires S1–S3; the M1d pass rule requires historical A–D **and S on L10331**. R16949 is recorded but does not decide. Exactly 420 A–D plus 60 A′ trials; report all outcomes and stop at the checkpoint. [Split protocol and derivation](../data/malecns/stim_protocol_malecns_split.json); [isolated male adapter](../sim/malecns/split.py). The original model, M1/M1c protocols and their recorded criteria remain unchanged.

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
960 including A′ across the two candidates. At this declaration no M1c trial had run.

At M1b the exact requested 200-partner `r_mn9` was undefined: male contralateral
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

## M1c — two pre-declared rescalings

Only `w_syn` changes; the external Poisson kick remains tied as `w_syn*f_poi`. The full-precision definitions and stop rule above were frozen before any candidate result. Both candidates reuse the unchanged M1 trial runner, physical 91-cell input layout, seeds 20260910–20260939, one-second duration, and historical gate predicates. No readout was substituted and no third weight or M2 was run.

The [pre-run plan](../data/malecns/rescale_plan.json) chose 8 workers: WSL available 60.58 GiB, host free 85.34 GiB, reserve 15.15 GiB, budget 5.4 GiB/worker (over 1.5× measured M1 peak). Candidate pools ran sequentially. Each candidate has 420 A–D plus 60 A′ trials, **960 total**, not 840 including A′. Means ± population SD use n=30. Network counts are median [minimum–maximum]; Poisson-source events are excluded.

### Candidate `all` — 0.145104089 mV

[Protocol and derivation](../data/malecns/stim_protocol_malecns_all.json); [results and raw-ledger hash](../data/malecns/rescale_all_results.json). Simulation commit `92d8be5b56c5fdaab6336dea82344a57d0c12031`; Brian2 2.9.0 / cython; parallel walltime 393.0 s, peak worker RSS 3.340 GiB. Completed 2026-09-14T08:39:18.136968+00:00.

| Condition | M1 R Hz | M1 L Hz | Rescaled R Hz | Rescaled L Hz | M1 network spikes | Rescaled network spikes |
|---|---:|---:|---:|---:|---:|---:|
| A_s25_b0 | 10.400 ± 12.727 | 43.033 ± 45.558 | 0.000 ± 0.000 | 0.000 ± 0.000 | 315,526 [101,199–987,904] | 468.5 [433–520] |
| A_s50_b0 | 8.867 ± 7.719 | 42.333 ± 28.293 | 0.000 ± 0.000 | 0.000 ± 0.000 | 935,017 [144,175–1,048,059] | 1,098.5 [1,047–1,293] |
| A_s100_b0 | 8.067 ± 3.245 | 58.567 ± 19.164 | 0.000 ± 0.000 | 0.000 ± 0.000 | 1,107,911 [994,456–1,141,791] | 2,774.5 [2,539–2,903] |
| A_s200_b0 | 34.367 ± 3.082 | 129.800 ± 5.243 | 0.000 ± 0.000 | 8.667 ± 2.948 | 1,156,672.5 [1,132,192–1,166,319] | 299,441.5 [232,765–333,567] |
| B_s200_b0 | 34.367 ± 3.082 | 129.800 ± 5.243 | 0.000 ± 0.000 | 8.667 ± 2.948 | 1,156,672.5 [1,132,192–1,166,319] | 299,441.5 [232,765–333,567] |
| B_s200_b25 | 0.000 ± 0.000 | 9.700 ± 29.703 | 0.000 ± 0.000 | 0.000 ± 0.000 | 1,146,230.5 [1,100,800–1,156,474] | 28,357.5 [12,073–335,725] |
| B_s200_b50 | 0.000 ± 0.000 | 1.300 ± 1.320 | 0.000 ± 0.000 | 0.000 ± 0.000 | 1,148,973.5 [1,097,898–1,158,387] | 15,373.5 [14,479–285,358] |
| B_s200_b100 | 0.000 ± 0.000 | 3.033 ± 1.622 | 0.000 ± 0.000 | 0.000 ± 0.000 | 1,152,283.5 [1,114,405–1,157,934] | 22,875 [21,400–351,962] |
| B_s200_b200 | 0.000 ± 0.000 | 6.567 ± 2.305 | 0.000 ± 0.000 | 0.000 ± 0.000 | 1,164,084 [1,129,965–1,170,541] | 32,900 [32,055–354,517] |
| C_s0_b25 | 0.000 ± 0.000 | 19.000 ± 42.782 | 0.000 ± 0.000 | 0.000 ± 0.000 | 1,062,197 [224,387–1,091,812] | 6,911.5 [6,516–7,249] |
| C_s0_b50 | 0.000 ± 0.000 | 10.733 ± 31.228 | 0.000 ± 0.000 | 0.000 ± 0.000 | 1,096,009 [1,064,489–1,121,085] | 10,007.5 [9,501–10,318] |
| C_s0_b100 | 0.000 ± 0.000 | 6.200 ± 22.275 | 0.000 ± 0.000 | 0.000 ± 0.000 | 1,097,902 [237,110–1,112,628] | 17,853.5 [16,641–18,882] |
| C_s0_b200 | 0.000 ± 0.000 | 6.767 ± 23.308 | 0.000 ± 0.000 | 0.000 ± 0.000 | 1,113,387.5 [1,092,999–1,134,876] | 28,299.5 [27,332–29,162] |
| D_s0_b0 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0 [0–0] | 0 [0–0] |

| Gate | M1 R | M1 L | Rescaled R16949 (contra) | Rescaled L10331 (ipsi) |
|---|---|---|---|---|
| A: sugar rises | FAIL | FAIL | FAIL | PASS |
| B: bitter suppresses | PASS | FAIL | FAIL | PASS |
| C: bitter-alone limit | PASS | FAIL | PASS | PASS |
| D: completeness | PASS | PASS | PASS | PASS |
| Baseline literal zero (additional) | PASS | PASS | PASS | PASS |
| Bitter-alone literal zero (additional) | PASS | FAIL | PASS | PASS |
| Overall A–D | FAIL | FAIL | FAIL | PASS |

R sugar means at 25/50/100/200 Hz: **0.000/0.000/0.000/0.000 Hz**. A does not pass.

L sugar means at 25/50/100/200 Hz: **0.000/0.000/0.000/8.667 Hz**. A passes the historical adjacent-zero exception and >5 Hz endpoint; this is not evidence of a graded response over the lower levels.

R is silent in every B condition: B fails its strict endpoint test (`0 < 0` is false), not a measured reversal of bitter suppression.

| Soft indicator (not a gate) | Rescaled R | Rescaled L |
|---|---:|---:|
| Sugar100 / sugar200 | undefined (0/0) | 0.000 |
| Bitter200 suppression vs bitter0 | undefined (0/0) | 100.00% |

**A′ at 120 Hz:** same seeds and fixed layout; difference = LB3c12 minus sugar17.

| Set / comparison | M1 R Hz | M1 L Hz | Rescaled R Hz | Rescaled L Hz | Network spikes |
|---|---:|---:|---:|---:|---:|
| AP_sugar_120 | 13.433 ± 5.590 | 80.333 ± 21.229 | 0.000 ± 0.000 | 0.000 ± 0.000 | 3,422 [3,211–3,577] |
| AP_sugar_lb3c_120 | 10.667 ± 3.486 | 63.600 ± 20.318 | 0.000 ± 0.000 | 0.000 ± 0.000 | 2,680 [2,480–2,940] |
| Paired difference | -2.767 ± 6.731 | -16.733 ± 32.179 | 0.000 ± 0.000 | 0.000 ± 0.000 | — |

Paired lower/equal/higher trial counts: R 0/30/0, L 0/30/0.

| Condition | Neurons fired: median [min–max] | R latency median, ms (firing trials/30) | L latency median, ms (firing trials/30) |
|---|---:|---:|---:|
| A_s25_b0 | 23 [22–27] | none (0/30) | none (0/30) |
| A_s50_b0 | 46 [37–52] | none (0/30) | none (0/30) |
| A_s100_b0 | 73 [64–86] | none (0/30) | none (0/30) |
| A_s200_b0 | 7,081.5 [6,959–7,550] | none (0/30) | 213.50 (30/30) |
| B_s200_b0 | 7,081.5 [6,959–7,550] | none (0/30) | 213.50 (30/30) |
| B_s200_b25 | 3,410.5 [392–7,850] | none (0/30) | none (0/30) |
| B_s200_b50 | 468.5 [434–7,518] | none (0/30) | none (0/30) |
| B_s200_b100 | 675.5 [629–7,988] | none (0/30) | none (0/30) |
| B_s200_b200 | 817 [771–7,353] | none (0/30) | none (0/30) |
| C_s0_b25 | 303.5 [289–316] | none (0/30) | none (0/30) |
| C_s0_b50 | 353 [332–370] | none (0/30) | none (0/30) |
| C_s0_b100 | 570 [538–595] | none (0/30) | none (0/30) |
| C_s0_b200 | 718 [685–748] | none (0/30) | none (0/30) |
| D_s0_b0 | 0 [0–0] | none (0/30) | none (0/30) |
| AP_sugar_120 | 84.5 [74–109] | none (0/30) | none (0/30) |
| AP_sugar_lb3c_120 | 77 [61–97] | none (0/30) | none (0/30) |

Latency medians include firing trials only; silence is none, not zero latency.

### Candidate `mn9` — 0.138503502 mV

[Protocol and derivation](../data/malecns/stim_protocol_malecns_mn9.json); [results and raw-ledger hash](../data/malecns/rescale_mn9_results.json). Simulation commit `92d8be5b56c5fdaab6336dea82344a57d0c12031`; Brian2 2.9.0 / cython; parallel walltime 345.0 s, peak worker RSS 3.339 GiB. Completed 2026-09-14T08:45:03.263267+00:00.

| Condition | M1 R Hz | M1 L Hz | Rescaled R Hz | Rescaled L Hz | M1 network spikes | Rescaled network spikes |
|---|---:|---:|---:|---:|---:|---:|
| A_s25_b0 | 10.400 ± 12.727 | 43.033 ± 45.558 | 0.000 ± 0.000 | 0.000 ± 0.000 | 315,526 [101,199–987,904] | 462 [426–515] |
| A_s50_b0 | 8.867 ± 7.719 | 42.333 ± 28.293 | 0.000 ± 0.000 | 0.000 ± 0.000 | 935,017 [144,175–1,048,059] | 1,059.5 [1,005–1,225] |
| A_s100_b0 | 8.067 ± 3.245 | 58.567 ± 19.164 | 0.000 ± 0.000 | 0.000 ± 0.000 | 1,107,911 [994,456–1,141,791] | 2,640 [2,397–2,808] |
| A_s200_b0 | 34.367 ± 3.082 | 129.800 ± 5.243 | 0.000 ± 0.000 | 7.400 ± 2.703 | 1,156,672.5 [1,132,192–1,166,319] | 246,019 [20,982–292,980] |
| B_s200_b0 | 34.367 ± 3.082 | 129.800 ± 5.243 | 0.000 ± 0.000 | 7.400 ± 2.703 | 1,156,672.5 [1,132,192–1,166,319] | 246,019 [20,982–292,980] |
| B_s200_b25 | 0.000 ± 0.000 | 9.700 ± 29.703 | 0.000 ± 0.000 | 0.033 ± 0.180 | 1,146,230.5 [1,100,800–1,156,474] | 85,972.5 [10,039–296,751] |
| B_s200_b50 | 0.000 ± 0.000 | 1.300 ± 1.320 | 0.000 ± 0.000 | 0.000 ± 0.000 | 1,148,973.5 [1,097,898–1,158,387] | 13,286 [12,825–298,101] |
| B_s200_b100 | 0.000 ± 0.000 | 3.033 ± 1.622 | 0.000 ± 0.000 | 0.000 ± 0.000 | 1,152,283.5 [1,114,405–1,157,934] | 18,957.5 [17,803–302,837] |
| B_s200_b200 | 0.000 ± 0.000 | 6.567 ± 2.305 | 0.000 ± 0.000 | 0.000 ± 0.000 | 1,164,084 [1,129,965–1,170,541] | 130,049.5 [28,699–315,481] |
| C_s0_b25 | 0.000 ± 0.000 | 19.000 ± 42.782 | 0.000 ± 0.000 | 0.000 ± 0.000 | 1,062,197 [224,387–1,091,812] | 5,119 [4,738–5,459] |
| C_s0_b50 | 0.000 ± 0.000 | 10.733 ± 31.228 | 0.000 ± 0.000 | 0.000 ± 0.000 | 1,096,009 [1,064,489–1,121,085] | 8,184 [7,691–8,604] |
| C_s0_b100 | 0.000 ± 0.000 | 6.200 ± 22.275 | 0.000 ± 0.000 | 0.000 ± 0.000 | 1,097,902 [237,110–1,112,628] | 13,642.5 [12,951–15,124] |
| C_s0_b200 | 0.000 ± 0.000 | 6.767 ± 23.308 | 0.000 ± 0.000 | 0.000 ± 0.000 | 1,113,387.5 [1,092,999–1,134,876] | 24,799 [23,943–25,887] |
| D_s0_b0 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0 [0–0] | 0 [0–0] |

| Gate | M1 R | M1 L | Rescaled R16949 (contra) | Rescaled L10331 (ipsi) |
|---|---|---|---|---|
| A: sugar rises | FAIL | FAIL | FAIL | PASS |
| B: bitter suppresses | PASS | FAIL | FAIL | PASS |
| C: bitter-alone limit | PASS | FAIL | PASS | PASS |
| D: completeness | PASS | PASS | PASS | PASS |
| Baseline literal zero (additional) | PASS | PASS | PASS | PASS |
| Bitter-alone literal zero (additional) | PASS | FAIL | PASS | PASS |
| Overall A–D | FAIL | FAIL | FAIL | PASS |

R sugar means at 25/50/100/200 Hz: **0.000/0.000/0.000/0.000 Hz**. A does not pass.

L sugar means at 25/50/100/200 Hz: **0.000/0.000/0.000/7.400 Hz**. A passes the historical adjacent-zero exception and >5 Hz endpoint; this is not evidence of a graded response over the lower levels.

R is silent in every B condition: B fails its strict endpoint test (`0 < 0` is false), not a measured reversal of bitter suppression.

| Soft indicator (not a gate) | Rescaled R | Rescaled L |
|---|---:|---:|
| Sugar100 / sugar200 | undefined (0/0) | 0.000 |
| Bitter200 suppression vs bitter0 | undefined (0/0) | 100.00% |

**A′ at 120 Hz:** same seeds and fixed layout; difference = LB3c12 minus sugar17.

| Set / comparison | M1 R Hz | M1 L Hz | Rescaled R Hz | Rescaled L Hz | Network spikes |
|---|---:|---:|---:|---:|---:|
| AP_sugar_120 | 13.433 ± 5.590 | 80.333 ± 21.229 | 0.000 ± 0.000 | 0.000 ± 0.000 | 3,276 [3,037–3,457] |
| AP_sugar_lb3c_120 | 10.667 ± 3.486 | 63.600 ± 20.318 | 0.000 ± 0.000 | 0.000 ± 0.000 | 2,485 [2,287–2,679] |
| Paired difference | -2.767 ± 6.731 | -16.733 ± 32.179 | 0.000 ± 0.000 | 0.000 ± 0.000 | — |

Paired lower/equal/higher trial counts: R 0/30/0, L 0/30/0.

| Condition | Neurons fired: median [min–max] | R latency median, ms (firing trials/30) | L latency median, ms (firing trials/30) |
|---|---:|---:|---:|
| A_s25_b0 | 23 [22–25] | none (0/30) | none (0/30) |
| A_s50_b0 | 41.5 [30–50] | none (0/30) | none (0/30) |
| A_s100_b0 | 64 [58–81] | none (0/30) | none (0/30) |
| A_s200_b0 | 6,399.5 [4,684–6,524] | none (0/30) | 325.60 (29/30) |
| B_s200_b0 | 6,399.5 [4,684–6,524] | none (0/30) | 325.60 (29/30) |
| B_s200_b25 | 6,283.5 [323–6,620] | none (0/30) | 966.40 (1/30) |
| B_s200_b50 | 400 [361–6,545] | none (0/30) | none (0/30) |
| B_s200_b100 | 554.5 [478–6,631] | none (0/30) | none (0/30) |
| B_s200_b200 | 6,521.5 [656–6,823] | none (0/30) | none (0/30) |
| C_s0_b25 | 245.5 [221–266] | none (0/30) | none (0/30) |
| C_s0_b50 | 296.5 [264–313] | none (0/30) | none (0/30) |
| C_s0_b100 | 437.5 [377–488] | none (0/30) | none (0/30) |
| C_s0_b200 | 598 [544–624] | none (0/30) | none (0/30) |
| D_s0_b0 | 0 [0–0] | none (0/30) | none (0/30) |
| AP_sugar_120 | 70 [64–89] | none (0/30) | none (0/30) |
| AP_sugar_lb3c_120 | 67 [51–85] | none (0/30) | none (0/30) |

Latency medians include firing trials only; silence is none, not zero latency.

### M1c checkpoint and stop rule

Passing candidate/side combinations: **all/L, mn9/L**. These satisfy the pre-declared gate rule, not behavioural calibration or a primary-readout decision.

The tracing-status evidence and 556-versus-6,012 input asymmetry remain a likely reconstruction explanation, not a causal demonstration: rescaling does not repair or control tracing completeness. Both sides are reported; the primary readout remains an owner decision. [Tracing preflight and female replay comparison](malecns_m1b.md).

[Raw-event audit](../data/malecns/rescale_audit.json): 960 trials / 1920 MN9-neuron trials reconstructed; all network counts, rates, latencies, summaries, A′ paired differences and bilateral gates agree. All 960 complete Poisson event arrays match their M1 counterparts; 43,680 physical-slot trains match between candidates. Each candidate has 30 identical A200/B0 whole-network pairs and 360 identical shared A′ LB3c input trains. Duplicate A200/B0 observations are not n=60; the two weights and M1 are paired by seed, not pooled replicates.

Brian2 retained the historical `rates` namespace warning and used its internal variable; input-event equality was checked rather than suppressing the warning. Raw spikes, source rates and ledgers remain ignored under `data/malecns/runs/m1c/`. Female frozen data, pipeline, site, scoring and README honesty table are unchanged. Stop here; no M2.

Software verification: 40 male-only unit tests, 315 existing Python tests, 67 Node tests and release validation pass. These checks do not establish behavioural validity.

### Post-M1c decision — 2026-09-14

**Post-M1c owner decision — 2026-09-14:** the primary male readout is **L10331**, chosen on reconstruction-completeness grounds; **R16949 remains recorded as secondary**. R16949 has 556 retained incoming synapses versus 6,012 for L10331, with neuPrint status labels `RT Hard to trace` versus `Roughly traced`. GNG postsynaptic capture is approximately 35% (35.3665%), an **ROI-wide figure, not either neuron's completeness estimate**. The owner records reconstruction completeness as the most likely explanation for the laterality reversal, not a demonstrated causal result. The cross-brain mapping places both bodies with the female MN9s in CB0701; it does not indicate that Table S1 identified the wrong bodies.

This decision was made **after M1c completed and its results were reported**. The completed runs, candidate protocols and original pre-declared stop rule remain unchanged: all four gates must pass on at least one side. **Both candidates passed under that original rule, on L10331.** This is not a retrospective amendment to the run design. Candidate selection is still pending; no rerun is performed or authorised by this record. [Mapping, tracing and ROI-capture evidence](malecns_m1b.md#additional-mapping-and-roi-capture-check); [OQ-11](open_questions.md#oq-11-malecns-substrate-and-reversed-sugar-to-mn9-laterality-2026-09-14).
## M1f pre-declaration — brain-only substrate, 2026-09-14

Structural rationale: the female FlyWire model contains no VNC and Shiu's parameters were calibrated on a brain-only network, so a male brain-only comparison removes a substrate-scope mismatch rather than tuning one failed gate. Hypnagogia reports approximately80 Hz male MN9 at sugar200 with brain-only scope and recurrent count scaling0.581; this motivates testing scope, **not** adopting its scale or treating its different setup as a matched result. [Their cut](https://github.com/ankthba/hypnagogia/blob/86da5f93e25a2f1ac78c2fa810f34a4a57992b66/src/hypnagogia/connectome.py#L342-L371); [their result](https://github.com/ankthba/hypnagogia/blob/86da5f93e25a2f1ac78c2fa810f34a4a57992b66/results.md#L45-L60).

The original superclass-nonnull male roster is retained as the starting point. Drop `vnc_*` and ENS (enteric, not brain) bodies; retain brain and ascending/descending/crossing bodies. The aggregate weights file has only `body_pre`, `body_post`, `weight`, **no synapse locations**. No6.8-GB partner-file download: remove all edges incident on a removed body, not only VNC-to-VNC edges. This is an **endpoint-based approximation**, not a precise spatial dissection: VNC-local contacts between retained crossing bodies remain, and brain-local contacts on removed bodies are lost. Hypnagogia additionally filters `status == Traced`; we do not add that second roster change, and retain Tastekin signs rather than their histamine/DPM/graded-APL changes.

[Brain substrate freeze](../data/malecns/substrate_record_brain.json): **146,221 neurons,21,884,935 edges,101,220,515 synapses**. Removed20,479 neurons,3,698,003 edges,22,957,102 synapses. All91 input slots and both MN9s retained. Mean unsigned in-degree692.243351 male versus393.056225 female, including isolated neurons: **r_brain=1.761181496**, alongside whole-CNS **r_all=1.895191250**. Synapse weights/signs are otherwise unchanged.

Two and only two pre-declared candidates: recurrent **0.275 mV** (unscaled) and **0.275/r_brain=0.156145179 mV** (full measured precision). External stimulus stays **68.75 mV/event** for both. Each runs420 A–D plus60 A′ trials,30 per condition, M1 seeds20260910–20260939, fixed91-slot layout. S reuses A and A′ sugar17 points. **Pass requires historical A–D and S1–S3 on L10331**; R16949 is recorded but not deciding. All outcomes retained. No third candidate, other change or automatic follow-up at this checkpoint. Protocols: [unscaled](../data/malecns/stim_protocol_malecns_brain_unscaled.json), [density](../data/malecns/stim_protocol_malecns_brain_density.json).

### M1d weight and event verification before M1f

The [post-run verification](../data/malecns/split_weight_verification.json) checks M1d's source hashes and reconstructs its exact builder with zero-duration compilation only (no extra trial). Both after construction and after restoring `m1_init`, the observed external weights are **68.75 mV/event** and recurrent weights divided by signed synapse counts are **0.14510408910416955–0.14510408910416960 mV**. M1c `all` used the same recurrent weight but **36.276022276 mV/event** externally. This is a post-run reconstruction, not a runtime dump recorded during M1d; M1f will record live per-worker weight checks before running.

All **480 whole-network spike arrays and Poisson arrays are exactly identical** between M1d and M1c `all`; every condition summary, gate and A′ statistic matches. The68.75-mV kick is9.82 times the resting7-mV threshold gap; even36.276 mV is5.18 times it. Thus varying between these two suprathreshold kicks was **inert in this tested design**: it did not change the trajectories, including recurrent high-activity episodes. However, the saved driven-cell output is not universally one spike for every input event: only4,109/14,580 driven-neuron trials have equal input/output counts, and3,800 have the exact one-timestep-shifted input train. A universal “every event regardless of stimulus weight” or “runaway is entirely recurrent” conclusion is not established by this comparison alone; external input can trigger recurrent dynamics. This qualification does not change the owner's design decision: **no future variant will vary stimulus weight**. No parameter or old result was rewritten.

## M1d checkpoint — split stimulus and recurrent weights

**Overall primary L10331: FAIL.** A–D pass, but shape gate S fails coverage S1: only 1 of five levels has a positive mean. S2 and S3 pass. This failed variant remains in the record; no automatic follow-up variant is run.

[Pre-run protocol](../data/malecns/stim_protocol_malecns_split.json); [plan](../data/malecns/split_plan.json); [results](../data/malecns/split_results.json); [raw-event audit](../data/malecns/split_audit.json).

Protocol/source declaration `dc633d7`; run commit `48b54ab95541f88e5403bbed6c17537e890ff063`. Exactly 480 trials, seeds20260910–20260939, 30 per condition, duration1 s. Eight workers; WSL free 60.65 GiB, host free 80.16 GiB, reserve 15.16 GiB, budget5.4 GiB/worker (>1.5× M1 peak). Brian2 2.9.0 cython; wall 380.7 s, peak worker 3.346 GiB. Completed 2026-09-14T18:13:28.205122+00:00.

| Gate | L10331 primary | R16949 secondary (not deciding) |
|---|---|---|
| A | PASS | FAIL |
| B | PASS | FAIL |
| C | PASS | PASS |
| D | PASS | PASS |
| S1: coverage ≥4/5 | FAIL: 1/5 | Not evaluated |
| S2: adjacent decrease ≤ pooled SD | PASS | Not evaluated |
| S3: network max/min <3 at200 | PASS: 1.433063 | Not evaluated |
| S overall | FAIL | Not evaluated |
| A–D plus S | FAIL | Not deciding |

Historical D checks completeness; additionally, baseline and bitter-alone MN9 rates are literally zero on both sides. A retains its historical adjacent-zero exception, which is why A can pass while S1 fails. S3 is the owner-defined count-ratio criterion, not a general statistical test proving unimodality.

### Five-level sugar curve

Mean ± population SD, Hz. Female is frozen23 throughout: historical pre-correction Phase0 at25/50/100/200; **120 uses the corrected frozen grid**, not the typed33 A′ arm. Different layouts/seed schemes and historical refractory handling make this a contextual comparison, not one matched female curve or a controlled sex comparison. Female Shiu L is contralateral; Shiu R is ipsilateral. [Female Phase0 source](../data/malecns/phase0_female_reference.json); [grid source](../data/lookup_table.json).

| Sugar Hz | Male L10331 ipsi | Male R16949 contra | Female Shiu L contra | Female Shiu R ipsi | Male network spikes: median [min–max] |
|---|---:|---:|---:|---:|---:|
| 25 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.100 ± 0.300 | 0.067 ± 0.359 | 468.5 [433–520] |
| 50 | 0.000 ± 0.000 | 0.000 ± 0.000 | 17.633 ± 4.854 | 13.267 ± 3.872 | 1,098.5 [1,047–1,293] |
| 100 | 0.000 ± 0.000 | 0.000 ± 0.000 | 67.233 ± 4.724 | 49.500 ± 4.105 | 2,774.5 [2,539–2,903] |
| 120 | 0.000 ± 0.000 | 0.000 ± 0.000 | 74.633 ± 4.476 | 54.700 ± 4.713 | 3,422.0 [3,211–3,577] |
| 200 | 8.667 ± 2.948 | 0.000 ± 0.000 | 93.300 ± 5.780 | 62.067 ± 4.633 | 299,441.5 [232,765–333,567] |

### Every condition and A′

| Condition (sugar/bitter Hz) | L10331 Hz | R16949 Hz | Network spikes: median [min–max] | Neurons fired: median [min–max] |
|---|---:|---:|---:|---:|
| A_s25_b0 | 0.000 ± 0.000 | 0.000 ± 0.000 | 468.5 [433–520] | 23.0 [22–27] |
| A_s50_b0 | 0.000 ± 0.000 | 0.000 ± 0.000 | 1,098.5 [1,047–1,293] | 46.0 [37–52] |
| A_s100_b0 | 0.000 ± 0.000 | 0.000 ± 0.000 | 2,774.5 [2,539–2,903] | 73.0 [64–86] |
| A_s200_b0 | 8.667 ± 2.948 | 0.000 ± 0.000 | 299,441.5 [232,765–333,567] | 7,081.5 [6,959–7,550] |
| B_s200_b0 | 8.667 ± 2.948 | 0.000 ± 0.000 | 299,441.5 [232,765–333,567] | 7,081.5 [6,959–7,550] |
| B_s200_b25 | 0.000 ± 0.000 | 0.000 ± 0.000 | 28,357.5 [12,073–335,725] | 3,410.5 [392–7,850] |
| B_s200_b50 | 0.000 ± 0.000 | 0.000 ± 0.000 | 15,373.5 [14,479–285,358] | 468.5 [434–7,518] |
| B_s200_b100 | 0.000 ± 0.000 | 0.000 ± 0.000 | 22,875.0 [21,400–351,962] | 675.5 [629–7,988] |
| B_s200_b200 | 0.000 ± 0.000 | 0.000 ± 0.000 | 32,900.0 [32,055–354,517] | 817.0 [771–7,353] |
| C_s0_b25 | 0.000 ± 0.000 | 0.000 ± 0.000 | 6,911.5 [6,516–7,249] | 303.5 [289–316] |
| C_s0_b50 | 0.000 ± 0.000 | 0.000 ± 0.000 | 10,007.5 [9,501–10,318] | 353.0 [332–370] |
| C_s0_b100 | 0.000 ± 0.000 | 0.000 ± 0.000 | 17,853.5 [16,641–18,882] | 570.0 [538–595] |
| C_s0_b200 | 0.000 ± 0.000 | 0.000 ± 0.000 | 28,299.5 [27,332–29,162] | 718.0 [685–748] |
| D_s0_b0 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.0 [0–0] | 0.0 [0–0] |
| AP_sugar_120 | 0.000 ± 0.000 | 0.000 ± 0.000 | 3,422.0 [3,211–3,577] | 84.5 [74–109] |
| AP_sugar_lb3c_120 | 0.000 ± 0.000 | 0.000 ± 0.000 | 2,680.0 [2,480–2,940] | 77.0 [61–97] |

A′: sugar17 versus LB3c12 at120 Hz, same layout/seeds. Both are **0 ±0 Hz on both MN9s**; paired subset-minus-union is **0 ±0 Hz**, equal in30/30 trials on each side. Duplicate A200/B0 runs are not pooled as n=60.

Saved-event audit: 480 trials / 960 MN9-neuron trials; all rates, latencies, source-cell counts, network counts, summaries, gates and paired differences verified. All480 Poisson event arrays match M1; all360 shared A′ LB3c trains match; all30 A200/B0 whole-network pairs match. No female simulation or product/frozen-data change. 49 male tests,315 existing Python tests,67 Node tests and release validation pass.

M1e is the separate [community survey](malecns_community_survey.md). Stop at this checkpoint; no further variant is selected or run.

## M1f edge-threshold check — 2026-09-14

Direct histograms of the unsigned `Connectivity` column, before simulation filtering or scaling, are recorded with source sizes and SHA256 in [the audit record](../data/malecns/edge_threshold_audit.json); [audit code](../sim/malecns/edge_threshold_audit.py). Each row of these tables is a directed edge, not an individual synapse.

| Synapses per edge | Female frozen v783 | Male whole CNS | Male brain-only endpoint cut |
|---|---:|---:|---:|
| 1 | 7,496,016 | 10,299,701 | 8,861,233 |
| 2 | 2,679,736 | 4,762,806 | 4,128,470 |
| 3 | 1,379,004 | 2,621,228 | 2,270,061 |
| 4 | 836,714 | 1,657,085 | 1,429,353 |
| >=5 | 2,700,513 | 6,242,118 | 5,195,818 |
| Total edges | 15,091,983 | 25,582,938 | 21,884,935 |
| Minimum | 1 | 1 | 1 |

[Shiu et al. 2024, Methods, Computational model](https://pmc.ncbi.nlm.nih.gov/articles/PMC11446845/) defines connection strength as FlyWire connectivity times presynaptic sign times `W_syn`. It specifies a cleft-score cutoff of 50 in the neurotransmitter-prediction procedure, **not** a five-synapse-per-edge cutoff; no >=5 edge threshold is stated there. The paper describes v630, whereas the directly audited frozen female file is `2025_Connectivity_783.parquet`. The male graph uses the `minconf-0.5` release with endpoint-roster filtering and no additional edge-count threshold; synapse confidence and aggregate edge count are different filters.

**Decision:** the female graph is not effectively >=5. The owner's conditional third M1f candidate is therefore not triggered; the two pre-declared candidates and their substrates remain unchanged. `r_all = 1.895191250` and `r_brain = 1.761181496` do not measure a female >=5 versus male all-edge discrepancy. This does not establish equivalence of upstream synapse detection, confidence filtering, reconstruction, or roster policies. No new simulation was used for this audit.

## Accepted reading — 2026-09-14

The owner accepts both failures as bracketing the desired behaviour: unscaled brain-only has a graded sugar curve and passes S, but bitter alone activates MN9 and the network runs hot; density scaling reduces activity and passes A–D and sugar-200 S3, but loses the required sugar coverage. Here “stable” is limited to that S3 result, not established network-wide stability: the saved network ranges below still include large high-activity excursions in other conditions. **No intermediate `w_syn` will be tried.** The next authorised work is [M1g confidence feasibility](malecns_synapse_confidence.md), research only; no M1g simulation is pre-declared or authorised.

## M1f checkpoint — brain-only endpoint approximation

Results: **unscaled: FAIL**, **density: FAIL**. No candidate is selected automatically; no additional variant is run.

Structural rationale, cut limitations, two weights and S criteria were declared above before results. Source declaration `4d1bb58`; preflight `b2dbc51`. Unscaled started at `b2dbc51`, density at `7140e47` after the separate edge-threshold audit commit; all frozen simulation-source and protocol hashes stayed identical. Same91 physical input slots and M1 seeds20260910–20260939,30 trials per condition;480 per candidate,960 total. Pools sequential,8 workers; reserve15.13 GiB from60.51 GiB WSL available (host80.45 GiB),5.4 GiB/worker budget.

| Substrate | Neurons | Edges | Synapses | Mean unsigned in-degree | Male/female ratio |
|---|---:|---:|---:|---:|---:|
| Male brain endpoint cut | 146,221 | 21,884,935 | 101,220,515 | 692.243351 | 1.761181496 |
| Male whole CNS (M0) | 166,700 | 25,582,938 | 124,177,617 | 744.916719 | 1.895191250 |
| Female frozen | 138,639 | 15,091,983 | 54,492,922 | 393.056225 | 1 |

[Brain record and SHA256 hashes](../data/malecns/substrate_record_brain.json); [edge-for-edge audit](../data/malecns/brain_substrate_audit.json). This is not an exact anatomical brain cut: crossing-body VNC synapses cannot be removed from aggregate endpoint counts. No sign rule, female substrate, product or scoring changes.

| Gate, L10331 only | Unscaled0.275 | Density-scaled0.156145179 |
|---|---|---|
| A | PASS | PASS |
| B | FAIL | PASS |
| C | FAIL | PASS |
| D | PASS | PASS |
| S1 | PASS (5/5 positive) | FAIL (2/5 positive) |
| S2 | PASS | PASS |
| S3 | PASS (max/min 1.013630) | PASS (max/min 1.306577) |
| S | PASS | FAIL |
| Overall A–D + S | FAIL | FAIL |

| Secondary R16949 gate | Unscaled | Density-scaled |
|---|---|---|
| A | FAIL | FAIL |
| B | PASS | FAIL |
| C | PASS | PASS |
| D | PASS | PASS |

R16949 is recorded but not used for acceptance; S is evaluated on L10331 only, as pre-declared. Historical D is the completeness predicate; literal baseline-zero passes on both sides for both candidates. S3 is the specified sugar200 max/min bound, not a general statistical test of unimodality.

### Five-level sugar curve

Mean ± population SD, Hz, n=30. Female frozen23 reference is historical pre-correction Phase0 at25/50/100/200 and the corrected frozen-grid120 point; not a matched five-level female rerun. Shiu L is female contralateral, Shiu R ipsilateral; male L is ipsilateral. Hypnagogia reports **80.4 Hz at200**, with brain-only144,209 neurons,0.581 scaling, different roster/sign and mapped-input definitions; no matched bilateral values or lower-dose curve are supplied by that reported comparison. It is contextual evidence, not a gate or target fit. [Female references](../data/malecns/phase0_female_reference.json); [grid120](../data/lookup_table.json); [hypnagogia source](https://github.com/ankthba/hypnagogia/blob/86da5f93e25a2f1ac78c2fa810f34a4a57992b66/results.md#L45-L60).

| Sugar Hz | Unscaled L | Unscaled R | Density L | Density R | Female Shiu L | Female Shiu R | Hypnagogia MN9 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 25 | 28.800 ± 34.783 | 5.967 ± 8.890 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.100 ± 0.300 | 0.067 ± 0.359 | Not reported |
| 50 | 33.267 ± 20.898 | 5.867 ± 4.193 | 0.000 ± 0.000 | 0.000 ± 0.000 | 17.633 ± 4.854 | 13.267 ± 3.872 | Not reported |
| 100 | 76.100 ± 16.232 | 11.733 ± 4.033 | 0.000 ± 0.000 | 0.000 ± 0.000 | 67.233 ± 4.724 | 49.500 ± 4.105 | Not reported |
| 120 | 88.267 ± 11.673 | 14.600 ± 3.738 | 0.833 ± 3.257 | 0.000 ± 0.000 | 74.633 ± 4.476 | 54.700 ± 4.713 | Not reported |
| 200 | 126.200 ± 4.996 | 30.967 ± 2.316 | 19.733 ± 3.596 | 0.000 ± 0.000 | 93.300 ± 5.780 | 62.067 ± 4.633 | 80.4 (reported mean) |

### All conditions: network activity and both MN9s

| Condition | Unscaled L Hz | Unscaled R Hz | Unscaled network spikes median [min–max] | Density L Hz | Density R Hz | Density network spikes median [min–max] |
|---|---:|---:|---:|---:|---:|---:|
| A_s25_b0 | 28.800 ± 34.783 | 5.967 ± 8.890 | 787,162.0 [107,784–951,255] | 0.000 ± 0.000 | 0.000 ± 0.000 | 482.5 [438–537] |
| A_s50_b0 | 33.267 ± 20.898 | 5.867 ± 4.193 | 929,500.5 [143,673–992,204] | 0.000 ± 0.000 | 0.000 ± 0.000 | 1,211.5 [1,116–1,432] |
| A_s100_b0 | 76.100 ± 16.232 | 11.733 ± 4.033 | 1,054,082.5 [956,940–1,081,850] | 0.000 ± 0.000 | 0.000 ± 0.000 | 3,011.0 [2,665–3,304] |
| A_s200_b0 | 126.200 ± 4.996 | 30.967 ± 2.316 | 1,102,476.5 [1,093,286–1,108,188] | 19.733 ± 3.596 | 0.000 ± 0.000 | 391,462.0 [315,748–412,549] |
| B_s200_b0 | 126.200 ± 4.996 | 30.967 ± 2.316 | 1,102,476.5 [1,093,286–1,108,188] | 19.733 ± 3.596 | 0.000 ± 0.000 | 391,462.0 [315,748–412,549] |
| B_s200_b25 | 13.133 ± 33.389 | 0.000 ± 0.000 | 1,104,273.5 [1,060,696–1,114,221] | 0.067 ± 0.249 | 0.000 ± 0.000 | 342,943.5 [15,254–419,762] |
| B_s200_b50 | 0.000 ± 0.000 | 0.000 ± 0.000 | 1,105,089.5 [1,056,398–1,113,666] | 0.000 ± 0.000 | 0.000 ± 0.000 | 315,401.5 [17,806–421,184] |
| B_s200_b100 | 0.000 ± 0.000 | 0.000 ± 0.000 | 1,107,289.5 [1,068,213–1,117,447] | 0.000 ± 0.000 | 0.000 ± 0.000 | 373,675.0 [24,584–430,175] |
| B_s200_b200 | 0.033 ± 0.180 | 0.000 ± 0.000 | 1,119,421.0 [1,084,981–1,123,868] | 0.000 ± 0.000 | 0.000 ± 0.000 | 296,485.0 [32,727–438,182] |
| C_s0_b25 | 25.067 ± 45.483 | 0.000 ± 0.000 | 1,023,031.5 [192,577–1,060,388] | 0.000 ± 0.000 | 0.000 ± 0.000 | 9,992.0 [9,329–369,109] |
| C_s0_b50 | 28.767 ± 47.645 | 0.000 ± 0.000 | 1,055,591.0 [1,025,867–1,076,162] | 0.000 ± 0.000 | 0.000 ± 0.000 | 115,099.5 [12,512–345,689] |
| C_s0_b100 | 76.600 ± 50.215 | 0.000 ± 0.000 | 1,058,075.5 [1,001,729–1,073,774] | 0.000 ± 0.000 | 0.000 ± 0.000 | 206,150.0 [18,170–380,748] |
| C_s0_b200 | 35.433 ± 54.136 | 0.000 ± 0.000 | 1,075,743.0 [1,051,980–1,092,783] | 0.000 ± 0.000 | 0.000 ± 0.000 | 27,721.0 [26,776–382,835] |
| D_s0_b0 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.0 [0–0] | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.0 [0–0] |
| AP_sugar_120 | 88.267 ± 11.673 | 14.600 ± 3.738 | 1,075,834.0 [1,051,247–1,089,050] | 0.833 ± 3.257 | 0.000 ± 0.000 | 3,745.0 [3,435–336,581] |
| AP_sugar_lb3c_120 | 82.467 ± 17.517 | 13.367 ± 4.658 | 1,044,834.0 [932,651–1,081,932] | 0.033 ± 0.180 | 0.000 ± 0.000 | 3,000.0 [2,626–3,250] |

### A′ at120 Hz

Both sets are newly run with paired seeds and identical91-slot layout; subset=LB3c12, union=sugar17.

| Candidate | L subset−union Hz | R subset−union Hz | L lower/equal/higher trials | R lower/equal/higher trials |
|---|---:|---:|---:|---:|
| unscaled | -5.800 ± 21.394 | -1.233 ± 6.184 | 19/1/10 | 18/2/10 |
| density | -0.800 ± 3.270 | 0.000 ± 0.000 | 3/26/1 | 0/30/0 |

### Execution and verification

| Candidate | Parallel wall seconds | Peak worker GiB | Completion UTC |
|---|---:|---:|---|
| unscaled | 812.1 | 3.089 | 2026-09-14T18:45:57.391006+00:00 |
| density | 368.4 | 3.101 | 2026-09-14T18:52:05.996071+00:00 |

Live per-worker weights were checked after construction and restore before positive-duration runs: stimulus68.75 mV/event for both; recurrence0.275 or0.1561451789913389 mV per signed synapse. All worker logs are hashed in the result manifests. [Unscaled result](../data/malecns/brain_unscaled_results.json); [density result](../data/malecns/brain_density_results.json).

[Saved-event audit](../data/malecns/brain_runs_audit.json): 960 trials /1920 MN9-neuron trials reconstructed; rates, latencies, driven-cell counts, network counts, gates and A′ statistics pass. Every input array matches M1; 43,680 cross-candidate input trains match; each candidate has360 identical shared A′ trains and30 identical A200/B0 network pairs. Repeated A200/B0 or seeds across variants are not independent extra replicates. Raw spikes remain ignored under data/malecns/runs/m1f/.

Interpretation under the unchanged gates: the unscaled brain cut has a five-level rising mean sugar curve, but fails B because the mean rises from0 at bitter100 to0.033 Hz at bitter200, and fails C because bitter-alone L means25.067–76.600 Hz exceed1 Hz. The density-scaled cut passes A–D but has positive L means only at120 and200 Hz, so fails S1. Large network counts can persist when MN9 is silent; passing S3 at200 does not establish network stability at other conditions. Neither candidate passes the complete pre-declared rule.

Verification:55 male tests,315 existing Python tests,67 Node tests, release validation,82 local report links, generated-report comparison and diff whitespace checks pass.

Checkpoint only: no further variant is selected or run.

## M1h pre-declaration — 2026-09-14

Owner-authorised final structural candidate, declared before substrate selection or simulation. Rationale: Shiu's female-calibrated `w_syn = 0.275 mV` is tested on a male graph matched to the female's mean unsigned synaptic in-degree. This is a density-matching construction, not precision matching or gate optimisation; matching density does not establish biological equivalence. M1g did not identify a precision-matched cutoff, rather than proving that none exists.

Use the full v1.0 `minconf-0.5` partner export, the exact M1f 146,221-neuron roster and endpoint cut (including crossing cells), and the unchanged male sign rule. Keep isolated neurons in the density denominator. Retain contacts only when both pre- and postsynaptic confidence meet `c*`. Choose among stored confidence breakpoints the cutoff minimising absolute distance of the male/female mean unsigned in-degree ratio from 1.00; ties choose the lower cutoff. Require ratio 1.00 ± 0.02. Target is the frozen female 54,492,922 synapses / 138,639 neurons. No model activity or gate data enter this choice. No intermediate `w_syn` is tested.

Before simulation, report full-file URL/size/SHA256, `c*`, graph counts, exact synapses-per-edge histogram, and incoming synapse counts for all 91 input cells and both MN9s versus the same brain cut at 0.5. Flag every loss strictly greater than 50%; a zero baseline is reported separately. Recall at `c*` requires published threshold-calibrated validation, not retained-contact fraction; report unavailable if that calibration cannot be established. **Stop at this substrate checkpoint and await the owner's go.**

After that checkpoint only: one candidate, recurrent0.275 mV, stimulus68.75 mV/event unchanged, remaining protocol unchanged. Gates A–D plus S decide on L10331; R16949 is recorded, not deciding. Same M1 seeds20260910–20260939,420 A–D trials plus60 A′ trials (sugar17 and LB3c12 at120 Hz),480 total. Pass requires A, B, C, D and all S components on10331. No isolated gate repair or additional candidate follows. Whatever the result, append a dated ledger of M1, M1c all/mn9, M1d, M1f unscaled/density and M1h, preserving original rules/results, and close the male line pending replies from Tastekin and the fly-brain-minecraft author; update the memo then. No M1h trials have run.

## M1h substrate checkpoint — 2026-09-14

**STOP before simulation:** 79 of 91 input cells lose more than half their incoming synapses. Neither MN9 crosses that threshold. No M1h trial has run.

Density-only declaration `a8234d3`; builder `5187492`. Full-file contacts reproduce every M1f brain edge count at0.5 exactly. Same roster, endpoint cut and signs; VNC-local contacts between retained crossing neurons remain. The cutoff is selected without reading any trial activity.

| Measure | Value |
|---|---:|
| `c*` (display) | 0.869 |
| `c*` (exact stored float32 value) | 0.8690000176429749 |
| Neurons, including isolated | 146,221 |
| Edges | 15,569,773 |
| Synapses | 57,499,865 |
| Male mean unsigned in-degree | 393.239445770 |
| Female mean unsigned in-degree | 393.056225160 |
| Ratio | 1.000466144 |
| M1f ratio at0.5 | 1.761181496 |
| Contacts retained versus brain0.5 | 56.8065% |

Full [partner file](https://storage.googleapis.com/flyem-male-cns/v1.0/connectome-data/flat-connectome/syn-partners-male-cns-v1.0-minconf-0.5.feather): **6,777,179,098 bytes**; SHA256 `959d8ef4173b35382a3e6acfaf5167c795b6d10b877572d146af04e1b487bc07`. [Substrate record, exact histogram, per-cell degrees and artifact hashes](../data/malecns/substrate_record_density_matched.json). Build/count/audit wall time 39.0s, excluding download. No Brian2 run.

The selected breakpoint is the closest density match among all486,079 distinct stored brain confidence values. Neighbouring achievable choices establish the discontinuity; no contacts tied at the cutoff are selectively removed:

| Cutoff | Retained synapses | Density ratio |
|---|---:|---:|
| 0.8689990043640137 | 57,499,950 | 1.000467622 |
| 0.8690000176429749 | 57,499,865 | 1.000466144 |
| 0.8690009713172913 | 57,356,709 | 0.997975308 |

### Synapses per edge

| Synapses per edge | Number of edges |
|---|---:|
| 1 | 7,248,536 |
| 2 | 2,908,892 |
| 3 | 1,533,547 |
| 4 | 935,401 |
| ≥5 | 2,943,397 |
| Total | 15,569,773 |

The record contains every integer-weight bin, not just the grouped ≥5 bin.

### Recall cost and source limitation

The newly retrieved [Berg supplement, Fig. S8E](https://ars.els-cdn.com/content/image/1-s2.0-S0092867426009426-mmc1.pdf) explicitly reports precision0.82 and recall0.81 at released cutoff0.5. The rest of its precision–recall curve has no confidence labels. The published ROI connection/T-bar tables likewise contain no cutoff column. Therefore **recall at0.869 is unavailable from these sources**, not0.81 and not56.8%. Contact retention is a graph-size measurement, not ground-truth recall; neither multiplication by0.81 nor interpolation along an unlabeled curve establishes it. This missing calibration is a cost uncertainty at the checkpoint. Supplement SHA256 `a7bd4e6e572a658635f082ae7e812b096ef0f7c9b964bb7adf35d207191572fb`,10,650,236 bytes; whole S8 page and caption visually inspected. See the [M1g source follow-up](malecns_synapse_confidence.md#m1h-source-follow-up--2026-09-14).

### Incoming synapse loss before any run

Comparison is within the same M1f brain roster at0.5, not the whole-CNS degree. Loss means incoming synapse count, not unique partners; strictly greater than50% is flagged. All91 inputs have nonzero baseline degree. The flag does not measure loss of the external Poisson drive, which remains unchanged.

| Class | Cells flagged / total |
|---|---:|
| sugar | 13/17 |
| bitter | 35/38 |
| water | 15/17 |
| ir94e | 16/19 |

| Cell / class | Body ID | Incoming at0.5 | Incoming at `c*` | Retained | Loss >50% |
|---|---:|---:|---:|---:|---|
| MN9 L primary | 10331 | 6,012 | 3,814 | 63.44% | No |
| MN9 R secondary | 16949 | 556 | 282 | 50.72% | No |
| ir94e | 44816 | 352 | 175 | 49.72% | FLAG |
| bitter | 54104 | 157 | 66 | 42.04% | FLAG |
| sugar | 71254 | 341 | 210 | 61.58% | No |
| sugar | 78240 | 326 | 160 | 49.08% | FLAG |
| bitter | 81741 | 177 | 83 | 46.89% | FLAG |
| sugar | 85806 | 337 | 154 | 45.70% | FLAG |
| bitter | 107241 | 180 | 83 | 46.11% | FLAG |
| ir94e | 111660 | 209 | 113 | 54.07% | No |
| bitter | 115666 | 118 | 44 | 37.29% | FLAG |
| bitter | 125111 | 197 | 89 | 45.18% | FLAG |
| water | 136183 | 175 | 89 | 50.86% | No |
| ir94e | 137497 | 246 | 119 | 48.37% | FLAG |
| bitter | 139178 | 158 | 66 | 41.77% | FLAG |
| water | 140619 | 120 | 59 | 49.17% | FLAG |
| water | 141663 | 125 | 50 | 40.00% | FLAG |
| bitter | 144334 | 132 | 56 | 42.42% | FLAG |
| ir94e | 154359 | 208 | 81 | 38.94% | FLAG |
| bitter | 154544 | 129 | 37 | 28.68% | FLAG |
| sugar | 159772 | 228 | 100 | 43.86% | FLAG |
| water | 160435 | 227 | 95 | 41.85% | FLAG |
| bitter | 163395 | 108 | 48 | 44.44% | FLAG |
| water | 166190 | 104 | 39 | 37.50% | FLAG |
| water | 167663 | 118 | 57 | 48.31% | FLAG |
| bitter | 168492 | 142 | 59 | 41.55% | FLAG |
| bitter | 173462 | 164 | 72 | 43.90% | FLAG |
| ir94e | 175572 | 226 | 99 | 43.81% | FLAG |
| water | 178913 | 62 | 31 | 50.00% | No |
| sugar | 180314 | 105 | 40 | 38.10% | FLAG |
| water | 183061 | 52 | 20 | 38.46% | FLAG |
| water | 187776 | 129 | 59 | 45.74% | FLAG |
| sugar | 190769 | 88 | 46 | 52.27% | No |
| water | 199308 | 83 | 37 | 44.58% | FLAG |
| ir94e | 200001 | 203 | 95 | 46.80% | FLAG |
| water | 203234 | 57 | 27 | 47.37% | FLAG |
| bitter | 208885 | 65 | 19 | 29.23% | FLAG |
| ir94e | 209688 | 259 | 116 | 44.79% | FLAG |
| ir94e | 232730 | 44 | 20 | 45.45% | FLAG |
| bitter | 256844 | 152 | 67 | 44.08% | FLAG |
| sugar | 261450 | 94 | 44 | 46.81% | FLAG |
| sugar | 262567 | 28 | 12 | 42.86% | FLAG |
| sugar | 272263 | 108 | 47 | 43.52% | FLAG |
| water | 374701 | 86 | 39 | 45.35% | FLAG |
| bitter | 375038 | 75 | 25 | 33.33% | FLAG |
| bitter | 511882 | 229 | 95 | 41.48% | FLAG |
| sugar | 512551 | 395 | 206 | 52.15% | No |
| bitter | 514546 | 214 | 82 | 38.32% | FLAG |
| bitter | 514547 | 237 | 93 | 39.24% | FLAG |
| bitter | 517255 | 228 | 106 | 46.49% | FLAG |
| bitter | 518112 | 219 | 97 | 44.29% | FLAG |
| water | 518542 | 129 | 52 | 40.31% | FLAG |
| bitter | 522746 | 260 | 131 | 50.38% | No |
| bitter | 522752 | 173 | 59 | 34.10% | FLAG |
| bitter | 522753 | 236 | 121 | 51.27% | No |
| bitter | 522754 | 189 | 83 | 43.92% | FLAG |
| bitter | 522761 | 220 | 93 | 42.27% | FLAG |
| bitter | 522762 | 235 | 94 | 40.00% | FLAG |
| bitter | 522841 | 278 | 143 | 51.44% | No |
| sugar | 531237 | 213 | 97 | 45.54% | FLAG |
| bitter | 533618 | 143 | 67 | 46.85% | FLAG |
| ir94e | 534361 | 298 | 157 | 52.68% | No |
| bitter | 549024 | 135 | 54 | 40.00% | FLAG |
| bitter | 556797 | 135 | 56 | 41.48% | FLAG |
| bitter | 557937 | 117 | 45 | 38.46% | FLAG |
| ir94e | 908747 | 256 | 120 | 46.88% | FLAG |
| bitter | 912379 | 164 | 56 | 34.15% | FLAG |
| ir94e | 919429 | 46 | 20 | 43.48% | FLAG |
| sugar | 933317 | 457 | 231 | 50.55% | No |
| bitter | 140334446 | 146 | 63 | 43.15% | FLAG |
| bitter | 144295263 | 21 | 4 | 19.05% | FLAG |
| sugar | 158893964 | 74 | 29 | 39.19% | FLAG |
| sugar | 174444965 | 10 | 2 | 20.00% | FLAG |
| ir94e | 214700177 | 98 | 53 | 54.08% | No |
| bitter | 304136793 | 69 | 23 | 33.33% | FLAG |
| bitter | 324178811 | 168 | 70 | 41.67% | FLAG |
| sugar | 349137284 | 12 | 1 | 8.33% | FLAG |
| water | 388541892 | 66 | 26 | 39.39% | FLAG |
| ir94e | 418840426 | 95 | 32 | 33.68% | FLAG |
| water | 456838775 | 19 | 7 | 36.84% | FLAG |
| sugar | 475202322 | 21 | 9 | 42.86% | FLAG |
| ir94e | 491986845 | 45 | 16 | 35.56% | FLAG |
| ir94e | 551057545 | 46 | 15 | 32.61% | FLAG |
| water | 553738738 | 17 | 7 | 41.18% | FLAG |
| bitter | 602736959 | 38 | 12 | 31.58% | FLAG |
| ir94e | 633272971 | 15 | 3 | 20.00% | FLAG |
| sugar | 766547228 | 22 | 6 | 27.27% | FLAG |
| bitter | 772366874 | 87 | 26 | 29.89% | FLAG |
| water | 786482749 | 12 | 4 | 33.33% | FLAG |
| ir94e | 792429427 | 48 | 22 | 45.83% | FLAG |
| bitter | 911389008 | 45 | 18 | 40.00% | FLAG |
| ir94e | 912111327 | 82 | 29 | 35.37% | FLAG |
| ir94e | 947005552 | 36 | 17 | 47.22% | FLAG |

The 480-trial experiment, final variant ledger/closing section and corresponding memo closure remain pending this checkpoint. No gate result or pass/fail is assigned to M1h yet.

## M1h outgoing-retention checkpoint — 2026-09-14

**STOP: all four input sets retain less than half their outgoing synapses. The owner’s conditional run criterion fails. No M1h trials are run; no A–D/S result is assigned.**

At `c* = 0.869` the graph keeps **56.8% of brain contacts**; recall at that cutoff is unknown (**0.81 at0.5 per Berg S8E**). This is a **heavily pruned graph, density-matched by construction**. The previous incoming-loss flags are not the run criterion for these Poisson-driven inputs; the owner instead requires each input set to retain at least half its outputs.

[Hashed outgoing audit and all values](../data/malecns/m1h_output_retention.json). Counts are unsigned synapse totals within the same M1f brain endpoint cut, not unique partners or signed net drive. Set retention is a ratio of totals, not the average of per-cell fractions.

| Set | Cells | Outgoing at0.5 | Outgoing at `c*` | Retained | Below half |
|---|---:|---:|---:|---:|---|
| sugar | 17 | 6,674 | 3,111 | 46.61% | FLAG |
| bitter | 38 | 23,430 | 10,640 | 45.41% | FLAG |
| water | 17 | 4,633 | 1,994 | 43.04% | FLAG |
| ir94e | 19 | 7,052 | 3,375 | 47.86% | FLAG |

### Both MN9s and all91 input cells

| Cell / set | Body ID | Outgoing at0.5 | Outgoing at `c*` | Retained |
|---|---:|---:|---:|---:|
| MN9 L primary | 10331 | 280 | 27 | 9.64% |
| MN9 R secondary | 16949 | 445 | 87 | 19.55% |
| sugar | 71254 | 779 | 358 | 45.96% |
| sugar | 78240 | 425 | 130 | 30.59% |
| sugar | 85806 | 791 | 410 | 51.83% |
| sugar | 159772 | 422 | 185 | 43.84% |
| sugar | 180314 | 178 | 37 | 20.79% |
| sugar | 190769 | 353 | 203 | 57.51% |
| sugar | 261450 | 354 | 174 | 49.15% |
| sugar | 262567 | 266 | 128 | 48.12% |
| sugar | 272263 | 296 | 135 | 45.61% |
| sugar | 512551 | 876 | 432 | 49.32% |
| sugar | 531237 | 414 | 181 | 43.72% |
| sugar | 933317 | 1,024 | 515 | 50.29% |
| sugar | 158893964 | 107 | 30 | 28.04% |
| sugar | 174444965 | 42 | 18 | 42.86% |
| sugar | 349137284 | 64 | 33 | 51.56% |
| sugar | 475202322 | 149 | 75 | 50.34% |
| sugar | 766547228 | 134 | 67 | 50.00% |
| bitter | 54104 | 416 | 193 | 46.39% |
| bitter | 81741 | 738 | 363 | 49.19% |
| bitter | 107241 | 1,127 | 546 | 48.45% |
| bitter | 115666 | 367 | 180 | 49.05% |
| bitter | 125111 | 807 | 380 | 47.09% |
| bitter | 139178 | 420 | 218 | 51.90% |
| bitter | 144334 | 372 | 167 | 44.89% |
| bitter | 154544 | 400 | 195 | 48.75% |
| bitter | 163395 | 327 | 151 | 46.18% |
| bitter | 168492 | 380 | 183 | 48.16% |
| bitter | 173462 | 381 | 201 | 52.76% |
| bitter | 208885 | 340 | 145 | 42.65% |
| bitter | 256844 | 976 | 445 | 45.59% |
| bitter | 375038 | 102 | 28 | 27.45% |
| bitter | 511882 | 997 | 474 | 47.54% |
| bitter | 514546 | 911 | 419 | 45.99% |
| bitter | 514547 | 835 | 382 | 45.75% |
| bitter | 517255 | 572 | 203 | 35.49% |
| bitter | 518112 | 827 | 386 | 46.67% |
| bitter | 522746 | 913 | 417 | 45.67% |
| bitter | 522752 | 991 | 440 | 44.40% |
| bitter | 522753 | 996 | 467 | 46.89% |
| bitter | 522754 | 1,007 | 477 | 47.37% |
| bitter | 522761 | 985 | 380 | 38.58% |
| bitter | 522762 | 889 | 394 | 44.32% |
| bitter | 522841 | 1,190 | 525 | 44.12% |
| bitter | 533618 | 786 | 344 | 43.77% |
| bitter | 549024 | 302 | 149 | 49.34% |
| bitter | 556797 | 437 | 205 | 46.91% |
| bitter | 557937 | 279 | 108 | 38.71% |
| bitter | 912379 | 825 | 342 | 41.45% |
| bitter | 140334446 | 334 | 163 | 48.80% |
| bitter | 144295263 | 75 | 38 | 50.67% |
| bitter | 304136793 | 625 | 300 | 48.00% |
| bitter | 324178811 | 740 | 315 | 42.57% |
| bitter | 602736959 | 98 | 38 | 38.78% |
| bitter | 772366874 | 436 | 184 | 42.20% |
| bitter | 911389008 | 227 | 95 | 41.85% |
| water | 136183 | 392 | 191 | 48.72% |
| water | 140619 | 295 | 118 | 40.00% |
| water | 141663 | 324 | 119 | 36.73% |
| water | 160435 | 485 | 205 | 42.27% |
| water | 166190 | 401 | 171 | 42.64% |
| water | 167663 | 334 | 144 | 43.11% |
| water | 178913 | 306 | 127 | 41.50% |
| water | 183061 | 369 | 183 | 49.59% |
| water | 187776 | 357 | 147 | 41.18% |
| water | 199308 | 227 | 95 | 41.85% |
| water | 203234 | 266 | 127 | 47.74% |
| water | 374701 | 97 | 34 | 35.05% |
| water | 518542 | 290 | 130 | 44.83% |
| water | 388541892 | 239 | 101 | 42.26% |
| water | 456838775 | 78 | 28 | 35.90% |
| water | 553738738 | 65 | 30 | 46.15% |
| water | 786482749 | 108 | 44 | 40.74% |
| ir94e | 44816 | 1,097 | 579 | 52.78% |
| ir94e | 111660 | 487 | 238 | 48.87% |
| ir94e | 137497 | 635 | 321 | 50.55% |
| ir94e | 154359 | 465 | 230 | 49.46% |
| ir94e | 175572 | 390 | 175 | 44.87% |
| ir94e | 200001 | 365 | 166 | 45.48% |
| ir94e | 209688 | 560 | 262 | 46.79% |
| ir94e | 232730 | 131 | 53 | 40.46% |
| ir94e | 534361 | 594 | 293 | 49.33% |
| ir94e | 908747 | 536 | 260 | 48.51% |
| ir94e | 919429 | 110 | 54 | 49.09% |
| ir94e | 214700177 | 446 | 220 | 49.33% |
| ir94e | 418840426 | 163 | 45 | 27.61% |
| ir94e | 491986845 | 233 | 105 | 45.06% |
| ir94e | 551057545 | 163 | 79 | 48.47% |
| ir94e | 633272971 | 149 | 53 | 35.57% |
| ir94e | 792429427 | 160 | 82 | 51.25% |
| ir94e | 912111327 | 262 | 133 | 50.76% |
| ir94e | 947005552 | 106 | 27 | 25.47% |

### L10331 top20 direct presynaptic partners

Rank fixed using the0.5 graph: strongest direct synapse count into L10331, ties by ascending body ID. Total outgoing retention alone does not establish last-hop retention, so both are shown; zero surviving direct contacts would be explicit. These rows do not select or adjust `c*`.

| Rank | Partner body | All outputs0.5 | All outputs `c*` | Retained | Into L10331 at0.5 | Into L10331 at `c*` | Last-hop retained |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 10833 | 2,427 | 1,261 | 51.96% | 464 | 250 | 53.88% |
| 2 | 10881 | 2,087 | 1,252 | 59.99% | 359 | 247 | 68.80% |
| 3 | 13754 | 1,442 | 941 | 65.26% | 357 | 275 | 77.03% |
| 4 | 12851 | 2,850 | 1,649 | 57.86% | 351 | 199 | 56.70% |
| 5 | 26764 | 3,970 | 2,806 | 70.68% | 348 | 273 | 78.45% |
| 6 | 523590 | 2,548 | 1,600 | 62.79% | 266 | 219 | 82.33% |
| 7 | 10849 | 6,418 | 3,155 | 49.16% | 241 | 130 | 53.94% |
| 8 | 513655 | 2,040 | 1,225 | 60.05% | 214 | 141 | 65.89% |
| 9 | 14891 | 2,278 | 1,318 | 57.86% | 198 | 119 | 60.10% |
| 10 | 17782 | 1,877 | 1,063 | 56.63% | 187 | 130 | 69.52% |
| 11 | 28181 | 1,865 | 1,296 | 69.49% | 177 | 148 | 83.62% |
| 12 | 11755 | 6,124 | 2,958 | 48.30% | 160 | 91 | 56.88% |
| 13 | 523679 | 2,243 | 1,445 | 64.42% | 142 | 103 | 72.54% |
| 14 | 16142 | 2,098 | 1,233 | 58.77% | 136 | 98 | 72.06% |
| 15 | 12752 | 3,699 | 1,974 | 53.37% | 101 | 60 | 59.41% |
| 16 | 12364 | 3,623 | 1,987 | 54.84% | 96 | 59 | 61.46% |
| 17 | 10673 | 5,602 | 2,513 | 44.86% | 92 | 54 | 58.70% |
| 18 | 238142 | 1,116 | 598 | 53.58% | 92 | 60 | 65.22% |
| 19 | 13402 | 2,156 | 1,139 | 52.83% | 78 | 54 | 69.23% |
| 20 | 522702 | 2,490 | 1,579 | 63.41% | 76 | 50 | 65.79% |

These fixed20 partners retain 2,760/4,135 direct synapses into L10331 (66.75%). This does not override the input-set stop condition. The experiment remains stopped before simulation, awaiting the owner’s decision.

## M1h owner decision to proceed — 2026-09-14

After seeing the outgoing audit and before any M1h trial, the owner chose to proceed despite the pre-declared50% outgoing-synapse threshold being crossed by all four input sets (43–48% retained). **The flag remains crossed in the record; this is a post-audit waiver, not a pass or a retroactive threshold change.** The owner's stated reasons: the round50% threshold had no derivation; the input sets retain slightly less than the graph average56.8%; stimulus entry remains intact in absolute-count terms (sugar3,111 and bitter10,640 outgoing synapses); the last hop into L10331 retains66.8%, with all top20 partners still connected. These are the owner's reasons to test, not evidence that function survived pruning or that recall is known.

Run the single declared candidate at recurrent0.275 mV and unchanged stimulus68.75 mV/event, all historical A–D plus S criteria onL10331, R16949 recorded, A′ included, M1 seeds,480 trials. The density cutoff and graph remain frozen; no further candidate is selected. After this result the male line closes pending replies from Tastekin and the fly-brain-minecraft author, regardless of the gate result.

## M1h results checkpoint — 2026-09-14

**Overall on primary L10331: FAIL.** All480 trials completed once; no extra candidate or rerun. The crossed outgoing-retention flag and dated owner waiver above remain intact.

| Gate | L10331 primary | R16949 secondary |
|---|---|---|
| A | PASS | FAIL |
| B | FAIL | FAIL |
| C | FAIL | PASS |
| D | PASS | PASS |
| S1 | FAIL (1/5 positive levels) | Not evaluated; non-deciding |
| S2 | PASS | Not evaluated; non-deciding |
| S3 | FAIL (network max/min=53.756254) | Not evaluated; non-deciding |
| S | FAIL | Not evaluated; non-deciding |
| Overall A–D + S | FAIL | Non-deciding |

Historical D is the completeness predicate; baseline-zero is separately reported. S3 is the declared sugar200 spike-count max/min bound, not proof of general network stability. S and acceptance apply only to L10331.

B fails because bitter25→50 raises the L mean from2.367 to4.700 Hz, despite98.7% endpoint suppression at bitter200. C fails because bitter-alone25/50/100 means2.300/3.167/1.400 Hz exceed the unchanged1 Hz limit. D literal baseline-zero passes on both sides. Sugar200 ranges5,317–285,822 network spikes, failing S3; no new mechanism is assigned.

### Five-level sugar curve

Mean ± population SD, Hz, n=30. Female Shiu L/R are historical aliases (contralateral/ipsilateral); male L10331 is ipsilateral. Female25/50/100/200 come from historical pre-correction Phase0,120 from the corrected frozen grid, so this is not a matched five-level female rerun. M1f unscaled is the previously recorded brain endpoint graph at confidence0.5 and recurrent0.275. [Female reference](../data/malecns/phase0_female_reference.json), [female120](../data/lookup_table.json), [M1f unscaled](../data/malecns/brain_unscaled_results.json).

| Sugar Hz | M1h L | M1h R | Female Shiu L | Female Shiu R | M1f unscaled L | M1f unscaled R |
|---|---:|---:|---:|---:|---:|---:|
| 25 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.100 ± 0.300 | 0.067 ± 0.359 | 28.800 ± 34.783 | 5.967 ± 8.890 |
| 50 | 0.000 ± 0.000 | 0.000 ± 0.000 | 17.633 ± 4.854 | 13.267 ± 3.872 | 33.267 ± 20.898 | 5.867 ± 4.193 |
| 100 | 0.000 ± 0.000 | 0.000 ± 0.000 | 67.233 ± 4.724 | 49.500 ± 4.105 | 76.100 ± 16.232 | 11.733 ± 4.033 |
| 120 | 0.000 ± 0.000 | 0.000 ± 0.000 | 74.633 ± 4.476 | 54.700 ± 4.713 | 88.267 ± 11.673 | 14.600 ± 3.738 |
| 200 | 5.267 ± 9.370 | 0.000 ± 0.000 | 93.300 ± 5.780 | 62.067 ± 4.633 | 126.200 ± 4.996 | 30.967 ± 2.316 |

### Every condition: both MN9s and network counts

| Condition | L Hz | R Hz | Network spikes median [min–max] | Neurons fired median [min–max] |
|---|---:|---:|---:|---:|
| A_s25_b0 | 0.000 ± 0.000 | 0.000 ± 0.000 | 470.5 [433–527] | 23.5 [23–28] |
| A_s50_b0 | 0.000 ± 0.000 | 0.000 ± 0.000 | 1,085.5 [1,042–1,257] | 37.0 [33–71] |
| A_s100_b0 | 0.000 ± 0.000 | 0.000 ± 0.000 | 2,560.5 [2,365–2,707] | 84.0 [54–95] |
| A_s200_b0 | 5.267 ± 9.370 | 0.000 ± 0.000 | 5,565.5 [5,317–285,822] | 139.0 [100–5,996] |
| B_s200_b0 | 5.267 ± 9.370 | 0.000 ± 0.000 | 5,565.5 [5,317–285,822] | 139.0 [100–5,996] |
| B_s200_b25 | 2.367 ± 6.529 | 0.000 ± 0.000 | 12,484.0 [11,982–270,125] | 398.5 [376–6,117] |
| B_s200_b50 | 4.700 ± 7.568 | 0.000 ± 0.000 | 14,902.0 [14,324–278,048] | 484.0 [397–6,150] |
| B_s200_b100 | 2.900 ± 3.496 | 0.000 ± 0.000 | 72,177.5 [18,907–281,922] | 5,909.0 [457–6,347] |
| B_s200_b200 | 0.067 ± 0.249 | 0.000 ± 0.000 | 99,399.5 [27,051–306,870] | 6,083.0 [573–6,426] |
| C_s0_b25 | 2.300 ± 6.111 | 0.000 ± 0.000 | 7,837.0 [7,207–252,327] | 440.5 [298–6,091] |
| C_s0_b50 | 3.167 ± 5.693 | 0.000 ± 0.000 | 10,195.5 [9,471–259,474] | 503.5 [336–6,152] |
| C_s0_b100 | 1.400 ± 1.855 | 0.000 ± 0.000 | 82,430.5 [14,082–256,806] | 5,904.0 [387–6,364] |
| C_s0_b200 | 0.000 ± 0.000 | 0.000 ± 0.000 | 89,159.5 [22,338–286,399] | 6,024.5 [523–6,413] |
| D_s0_b0 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.0 [0–0] | 0.0 [0–0] |
| AP_sugar_120 | 0.000 ± 0.000 | 0.000 ± 0.000 | 3,124.5 [2,970–3,276] | 68.0 [61–97] |
| AP_sugar_lb3c_120 | 0.000 ± 0.000 | 0.000 ± 0.000 | 2,327.0 [2,128–2,473] | 54.0 [49–58] |

### A′ sugar17 versus LB3c12 at120 Hz

| Side | Sugar17 Hz | LB3c12 Hz | Paired subset−union Hz | Lower/equal/higher trials |
|---|---:|---:|---:|---:|
| L | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0/30/0 |
| R | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0/30/0 |

### Execution and verification

Protocol/source freeze `e163c6e`, execution-plan commit `02db48f`; run HEAD `02db48f3801f6a66c311c0d8192d5390ebcd023d`. Same91 physical slots and M1 seeds20260910–20260939,420 A–D plus60 A′ trials. 8 workers, reserve15.13GiB, budget5.4GiB/worker. Wall254.7s; peak worker2.176GiB; completed2026-09-14T21:12:04.007412+00:00.

Actual weights checked after construction and restore: recurrent0.275 mV per signed synapse and stimulus68.75 mV/event. [Results](../data/malecns/m1h_results.json), [protocol](../data/malecns/stim_protocol_malecns_density_matched.json), [saved-event audit](../data/malecns/m1h_runs_audit.json). Raw spikes, per-trial ledgers and live weight logs are retained locally. The audit reconstructs480 trials/960 MN9-neuron trials, all network counts, gates, A′, and verifies identical Poisson input arrays against M1. Repeated seeds and A200/B0 are not independent extra replicates.

Cost: confidence0.869 retains56.8% of brain contacts; recall there is unknown (Berg S8E gives0.81 at0.5). This is a heavily pruned graph, density-matched by construction. Gate results do not establish behavioural calibration or compensate for reconstruction differences.

## Male line closing decision — 2026-09-14

Per the owner’s instruction before M1h results, **the male line is closed pending replies from Tastekin and the fly-brain-minecraft author**. Every attempted variant remains in the record. No intermediate weight, additional candidate, M2, or product change follows this checkpoint.

| Variant | Structural rationale / design | Recorded result under its declared rule |
|---|---|---|
| [M1](#hard-gates) | Whole CNS, original Shiu weights, typed male inputs | Neither side passes A–D. L fails A/B/C; R fails A. S not yet declared. |
| [M1c all](../data/malecns/rescale_all_results.json) | Scale recurrent and tied external weights by whole-network mean density ratio | Passes original A–D-on-at-least-one-side rule on L; R fails A/B. Only200 Hz activates L among A levels; S not yet declared. |
| [M1c mn9](../data/malecns/rescale_mn9_results.json) | Scale by equal-side mean density of strongest MN9 input partners, with the declared137-partner exception | Passes original A–D rule on L; R fails A/B. Only200 Hz activates L among A levels; S not yet declared. |
| [M1d](../data/malecns/split_results.json) | Keep female external kick; scale recurrent weights by whole-network density | FAIL: A–D pass on L, S1 fails (1/5). Saved activity identical to M1c all. |
| [M1f unscaled](../data/malecns/brain_unscaled_results.json) | Brain endpoint cut, original recurrent weight, female kick | FAIL: L B/C fail; graded sugar and S pass. |
| [M1f density](../data/malecns/brain_density_results.json) | Same brain cut; recurrent weight scaled by its density | FAIL: L A–D pass; S1 fails (2/5). |
| [M1h](#m1h-results-checkpoint--2026-09-14) | Confidence-pruned brain graph matched to female density; original weight/kick; outgoing flag explicitly waived | FAIL under A–D + S on L10331; full gate breakdown above. |

This closure is an owner decision about further work pending external information, not a claim that every possible male model fails. Historical M1c passes retain their original rule; the later S gate is not applied retroactively. Female pipeline, frozen scores, site and README honesty table remain unchanged.


## M1i pre-declaration — 2026-09-18

The owner reopened the male line for exactly one variant, M1i, on 2026-09-18.
This is the signed-off declaration only; no substrate build or simulation has run.
The historical closing decision and seven-variant ledger above remain unchanged;
the eight-variant closing ledger and decision memo follow the results checkpoint.

Configuration sources: [fly-brain-minecraft VALIDATION.md §2, §3, §9](https://github.com/blendi-remade/fly-brain-minecraft/blob/main/docs/VALIDATION.md)
and [PROVENANCE.md](https://github.com/blendi-remade/fly-brain-minecraft/blob/main/PROVENANCE.md).
The source facts were verified against that repository before this declaration.

1. Rationale: replication of an externally calibrated configuration; the >= 5 threshold and gain 0.65 are
   theirs, cited as such, not values we chose. Their gain was selected by their own sweep on this feeding
   stimulus, so run (b) is partly circular as a test of their gain; run (a) with our sugar17 is the
   independent test. External contacts (Tastekin email 2026-09-14; fly-brain-minecraft GitHub issue) had no
   reply; the replication proceeds without them.
2. Substrate `male-cns-v1.0-fbm-ge5-1`: whole CNS; our proofread roster (superclass non-null, 166,700,
   the existing data/malecns/derived/neuron_index.csv and indices reused); edges with >= 5 synapses from the
   same minconf-0.5 weight file; autapses dropped as they do; Tastekin signs unchanged (consensusNt only;
   GABA/glutamate negative; everything else, including histamine, unclear and missing, positive). Every
   difference from their roster/graph is recorded in data/malecns/substrate_record_fbm.json with counts
   against their 176,422 neurons / 6,287,749 connections / 90,296,905 synapses: roster rule and count
   difference, raw >= 5 edges touching non-roster endpoints, autapses dropped, sign-rule differences with
   affected neuron counts (histamine sign, predictedNt fallback not used), dt 0.1 ms versus their 0.5 ms,
   readout definition.
3. Model: w_syn = 0.65 x 0.275 = 0.17875 mV; every other Shiu parameter unchanged; external kick stays
   w_syn x f_poi = 44.6875 mV per event (every event still spikes, as in M1c). KC check uses a second
   connectivity file with `Excitatory x Connectivity` multiplied by 0.25 on every edge whose postsynaptic
   neuron is class Kenyon_Cell; sim/network.py is not modified (it multiplies that column by w_syn as float).
4. Run (b), replication, 95 trials, seeds 20260910 + trial, 1,000 ms each, dt 0.1 ms, Poisson layout of
   242 physical cells: their sugar 204 (LB3b+LB3c both sides 120 Hz; PhG1a-c 100 Hz; LgLG3 80 Hz) and
   bitter 38 (LB1a-d 120 Hz):
   - fbm_sugar (30), fbm_bitter (30), fbm_both (30);
   - fbm_sugar_kc: sugar condition on the KC-scaled file, 5 trials, seeds 20260910-20260914, paired with
     the first five fbm_sugar trials; paired difference reported, no criterion.
   Readouts: per-cell 1 s rates of L10331 and R16949, the 2-cell mean, and the 2-cell mean per 50 ms bin
   (20 bins per trial; report min/median/max across bins and trials), next to their 30-90 / 0 / 0.
   Replication criteria: fbm_sugar: 2-cell 1 s mean within [30, 90] Hz over 30 trials and > 0 Hz in 30/30;
   fbm_bitter: both MN9 cells 0 spikes in 30/30; fbm_both: both MN9 cells 0 spikes in 30/30.
   Run (a) proceeds whatever (b) shows; (b) is an internal checkpoint only for implementation defects,
   which are fixed before (a) without touching any rule.
5. Run (a), our gates, 480 trials, M1 seeds 20260910-20260939, same 91-cell layout as M1 (sugar17 XLSX-L
   LB3b u LB3c, bitter38, water17, ir94e19): A sugar 25/50/100/200; B sugar 200 with bitter 0/25/50/100/200;
   C bitter 25/50/100/200; D baseline; 30 each = 420; A' sugar17 versus sugar_lb3c12 at 120 Hz, 30 each = 60.
   Gates A-D and S1-S3 exactly as M1d-M1h (reuse sim.malecns.phase0.evaluate_gates and the split shape_gate
   definition), decided on L10331; R16949 recorded, not deciding. Pass rule: A, B, C, D, S1, S2, S3 all pass
   on L10331. Confound to be stated in the report: their sugar drive is 204 cells including pharyngeal and
   tarsal GRNs, ours 17 labellar cells; (b) versus (a) separates the configuration from the input size.
6. Owner additions (2026-09-18, no rule change): (i) report whole-network spike count median and range for
   every condition in (b) and (a), as in earlier male reports; (ii) before running, record outgoing-synapse
   retention on the >= 5 substrate for the 91 input cells by set and for both MN9s, in the same table form
   as M1h (data/malecns/m1h_output_retention.json, including the fixed top-20 direct L10331 presynaptic
   partners last-hop block); recorded, not a stop condition.
7. Stop rule: after (a), stop whatever the result. No second gain, no threshold change, no isolated gate
   repair, no M2. If (a) passes, report and stop; product work is a separate decision. Whatever the outcome:
   M1i section in docs/malecns_phase0.md, the closing ledger becomes eight variants, docs/v2_decision_memo.md
   updated to match. No honesty-table row.
8. Sequence: declaration commit -> substrate build, KC file, retention table, runners, tests
   (internal checkpoint) -> run (b) (internal checkpoint) -> run (a) -> audits, reports, memo, PR
   into dev. Results under data/malecns/runs/m1i (ignored); versioned JSON summaries under data/malecns/.

### Declaration artifacts

| Artifact | Declared scope |
|---|---|
| [Run (b) protocol](../data/malecns/stim_protocol_malecns_fbm_replication.json) | 90 replication trials plus 5 paired KC trials; 242 physical inputs |
| [Run (a) protocol](../data/malecns/stim_protocol_malecns_fbm.json) | 420 A–D plus 60 A′ trials; original 91 physical inputs |
| [Stimulus cells](../data/malecns/cells_fbm.json) and [resolver](../sim/malecns/fbm_cells.py) | Local annotation-derived sets; bitter IDs and historical readout keys preserved |

The protocols record `0.65 * 0.275` as Python float `0.17875000000000002`;
its tied external kick is `44.68750000000001` mV/event. These are the float
representations of the declared 0.17875 and 44.6875 values, not another gain.
All other model and trial fields retain their original values. Run (a) copies
the existing split shape-gate declaration and reuses the historical gate functions.
Run (b)'s KC condition uses five trials while the common trial defaults remain unchanged.

| Input set | Count | rootSide L | rootSide R |
|---|---:|---:|---:|
| Labellar LB3b + LB3c | 34 | 17 | 17 |
| Pharyngeal PhG1a + PhG1b + PhG1c | 8 | 4 | 4 |
| Tarsal LgLG3 | 162 | 78 | 84 |
| Bitter LB1a–d | 38 | 19 | 19 |

The four sets are disjoint: 242 physical inputs, including 204 sugar-drive cells.
The bitter IDs equal the existing 38-cell set. The copied readout dictionary retains
its historical key names; both M1i protocols explicitly declare L10331 primary and
R16949 secondary. Substrate differences and retention counts follow at the substrate checkpoint,
including autapse removal; the existing roster's 6,242,118 ≥5 edges is a prior
audit count, not a newly built M1i graph count.

### M1i substrate checkpoint — 2026-09-18

Built against declaration commit `db7ae6e`; the two protocols, `cells_fbm.json`, and the preceding pre-declaration remain unchanged. No simulation trial has run. The substrate and retention artifacts are complete; Windows checks pass. Both compile-only plans were then built in WSL (Brian2 2.9.0): one network each, zero simulated seconds, zero spikes. The plans are recorded in [fbm_replication_plan.json](../data/malecns/fbm_replication_plan.json) and [fbm_phase0_plan.json](../data/malecns/fbm_phase0_plan.json): 8 workers from WSL 60.0 / 59.6 GiB available and 95.1 GiB host free, 5.4 GiB budget per worker (over 1.5x the M1 peak).

[Substrate record](../data/malecns/substrate_record_fbm.json) and [outgoing retention](../data/malecns/m1i_output_retention.json) contain file hashes, source records, and per-cell values. Large derived graphs stay ignored. Both builders refuse to overwrite existing outputs; their `--verify` modes re-hash the recorded files without rebuilding the graphs.

#### Counts and configuration comparison

| Quantity | This substrate | Their reported configuration |
|---|---:|---:|
| Neurons | 166,700 | 176,422 |
| Directed edges | 6,242,085 | 6,287,749 |
| Synapses | 89,859,938 | 90,296,905 |
| Integration dt (ms) | 0.1 | 0.5 |

The roster and indices are the unchanged M0 superclass-non-null whole-CNS roster. The roster difference (theirs minus ours) is 9,722 bodies. Our final edge/synapse differences (theirs minus ours) are 45,664 / 436,967. No explanation is assigned to the neuPrint-fetch versus GCS-flat-file residual.

| Raw GCS reconciliation at >=5 | Edges |
|---|---:|
| All raw rows at >=5 | 7,622,864 |
| At least one endpoint outside our roster | 1,380,746 |
| On-roster before autapse removal | 6,242,118 |
| On-roster autapses removed | 33 |
| On-roster non-autapses retained | 6,242,085 |
| Autapses across all raw >=5 rows (includes 7 outside roster) | 40 |

Raw >=5 rows contain 97,991,093 synapses before autapse removal. Relative to all raw >=5 non-autapse rows, their reported counts minus the flat-file counts are -1,335,075 edges and -7,693,794 synapses. The retained raw endpoints, order and weights reconcile exactly to every row in the new graph.

| Superclass-null annotation status | Bodies |
|---|---:|
| Orphan | 15,893 |
| Glia | 11,864 |
| Unimportant | 10,751 |
| (missing) | 3,470 |
| Assign | 1,832 |
| Anchor | 551 |
| Traced | 516 |

The source synapse-per-edge histogram is recorded in full in the substrate record; threshold actions below precede the separate autapse removal.

| Synapses per edge | Edges | Action |
|---|---:|---|
| 1 | 10,299,701 | Removed |
| 2 | 4,762,806 | Removed |
| 3 | 2,621,228 | Removed |
| 4 | 1,657,085 | Removed |
| >=5 | 6,242,118 | Kept before removing 33 autapses |

The recurrent weight is `0.65 * 0.275` mV (Python representation `0.17875000000000002`); the external event kick remains that value times 250 (`44.68750000000001` mV). All other frozen Shiu parameters remain unchanged. Run (b) records each MN9 over 1 s, their two-cell mean, and 20 x 50 ms two-cell mean bins; their reported readout is the two-cell mean per 50 ms tick in one 600 ms run (30-90 / 0 / 0 Hz). Run (a) evaluates the frozen gates on L10331, with R16949 recorded.

#### Sign-rule differences and KC file

Their sign rule would change 8,278 roster-neuron signs: 7,891 consensus-histamine neurons plus 387 unresolved-consensus neurons receiving negative fallback labels. Our consensus-only signs are unchanged. Of 3,177 unclear/missing consensus labels, the counterfactual fallback assignments are:

| Resulting label | predictedNt confidence >=0.5 fallback | Subsequent celltypePredictedNt fallback |
|---|---:|---:|
| acetylcholine | 329 | 0 |
| dopamine | 3 | 0 |
| gaba | 53 | 0 |
| glutamate | 320 | 0 |
| histamine | 14 | 0 |
| octopamine | 31 | 8 |
| serotonin | 327 | 22 |

The KC file preserves every edge, `Connectivity`, and `Excitatory` value. Only `Excitatory x Connectivity` becomes float64, with a 0.25 multiplier on the 70,931 edges / 906,584 synapses targeting the 4,064 roster bodies annotated `class == Kenyon_Cell`. Both completeness copies are byte-identical to M0; the shared neuron index is reused.

#### Outgoing retention

**Recorded, not a stop condition; no flag stops anything.** Counts are unsigned synapse totals on the same whole-CNS roster. Fractions are ratios of totals. The JSON retains the M1h field names: `*_0_5` means the >=1 baseline and `*_c_star` means >=5 without autapses here; no synapse-confidence threshold has changed.

| Set | Cells | Outgoing >=1 | Outgoing >=5 | Retained | Below half |
|---|---:|---:|---:|---:|---|
| sugar | 17 | 6,674 | 5,176 | 77.55% | No |
| bitter | 38 | 23,430 | 17,900 | 76.40% | No |
| water | 17 | 4,633 | 3,434 | 74.12% | No |
| ir94e | 19 | 7,052 | 5,597 | 79.37% | No |
| fbm_sugar_labellar | 34 | 14,950 | 11,739 | 78.52% | No |
| fbm_sugar_pharyngeal | 8 | 19,661 | 17,792 | 90.49% | No |
| fbm_sugar_tarsal | 162 | 58,464 | 43,556 | 74.50% | No |
| bitter | 38 | 23,430 | 17,900 | 76.40% | No |

Both MN9s and all 91 M1 input cells:

| Cell / set | Body ID | Outgoing >=1 | Outgoing >=5 | Retained |
|---|---:|---:|---:|---:|
| MN9_L_primary | 10331 | 280 | 51 | 18.21% |
| MN9_R_secondary | 16949 | 445 | 203 | 45.62% |
| sugar | 71254 | 779 | 668 | 85.75% |
| sugar | 78240 | 425 | 343 | 80.71% |
| sugar | 85806 | 791 | 674 | 85.21% |
| sugar | 159772 | 422 | 344 | 81.52% |
| sugar | 180314 | 178 | 88 | 49.44% |
| sugar | 190769 | 353 | 240 | 67.99% |
| sugar | 261450 | 354 | 261 | 73.73% |
| sugar | 262567 | 266 | 134 | 50.38% |
| sugar | 272263 | 296 | 209 | 70.61% |
| sugar | 512551 | 876 | 799 | 91.21% |
| sugar | 531237 | 414 | 316 | 76.33% |
| sugar | 933317 | 1,024 | 946 | 92.38% |
| sugar | 158893964 | 107 | 35 | 32.71% |
| sugar | 174444965 | 42 | 13 | 30.95% |
| sugar | 349137284 | 64 | 5 | 7.81% |
| sugar | 475202322 | 149 | 43 | 28.86% |
| sugar | 766547228 | 134 | 58 | 43.28% |
| bitter | 54104 | 416 | 231 | 55.53% |
| bitter | 81741 | 738 | 573 | 77.64% |
| bitter | 107241 | 1,127 | 980 | 86.96% |
| bitter | 115666 | 367 | 221 | 60.22% |
| bitter | 125111 | 807 | 652 | 80.79% |
| bitter | 139178 | 420 | 259 | 61.67% |
| bitter | 144334 | 372 | 239 | 64.25% |
| bitter | 154544 | 400 | 244 | 61.00% |
| bitter | 163395 | 327 | 178 | 54.43% |
| bitter | 168492 | 380 | 203 | 53.42% |
| bitter | 173462 | 381 | 246 | 64.57% |
| bitter | 208885 | 340 | 180 | 52.94% |
| bitter | 256844 | 976 | 814 | 83.40% |
| bitter | 375038 | 102 | 14 | 13.73% |
| bitter | 511882 | 997 | 882 | 88.47% |
| bitter | 514546 | 911 | 797 | 87.49% |
| bitter | 514547 | 835 | 709 | 84.91% |
| bitter | 517255 | 572 | 429 | 75.00% |
| bitter | 518112 | 827 | 678 | 81.98% |
| bitter | 522746 | 913 | 772 | 84.56% |
| bitter | 522752 | 991 | 853 | 86.07% |
| bitter | 522753 | 996 | 837 | 84.04% |
| bitter | 522754 | 1,007 | 850 | 84.41% |
| bitter | 522761 | 985 | 797 | 80.91% |
| bitter | 522762 | 889 | 780 | 87.74% |
| bitter | 522841 | 1,190 | 1,009 | 84.79% |
| bitter | 533618 | 786 | 630 | 80.15% |
| bitter | 549024 | 302 | 136 | 45.03% |
| bitter | 556797 | 437 | 309 | 70.71% |
| bitter | 557937 | 279 | 166 | 59.50% |
| bitter | 912379 | 825 | 647 | 78.42% |
| bitter | 140334446 | 334 | 200 | 59.88% |
| bitter | 144295263 | 75 | 23 | 30.67% |
| bitter | 304136793 | 625 | 484 | 77.44% |
| bitter | 324178811 | 740 | 533 | 72.03% |
| bitter | 602736959 | 98 | 15 | 15.31% |
| bitter | 772366874 | 436 | 246 | 56.42% |
| bitter | 911389008 | 227 | 84 | 37.00% |
| water | 136183 | 392 | 329 | 83.93% |
| water | 140619 | 295 | 214 | 72.54% |
| water | 141663 | 324 | 254 | 78.40% |
| water | 160435 | 485 | 389 | 80.21% |
| water | 166190 | 401 | 319 | 79.55% |
| water | 167663 | 334 | 258 | 77.25% |
| water | 178913 | 306 | 230 | 75.16% |
| water | 183061 | 369 | 296 | 80.22% |
| water | 187776 | 357 | 271 | 75.91% |
| water | 199308 | 227 | 141 | 62.11% |
| water | 203234 | 266 | 206 | 77.44% |
| water | 374701 | 97 | 31 | 31.96% |
| water | 518542 | 290 | 235 | 81.03% |
| water | 388541892 | 239 | 162 | 67.78% |
| water | 456838775 | 78 | 21 | 26.92% |
| water | 553738738 | 65 | 35 | 53.85% |
| water | 786482749 | 108 | 43 | 39.81% |
| ir94e | 44816 | 1,097 | 922 | 84.05% |
| ir94e | 111660 | 487 | 401 | 82.34% |
| ir94e | 137497 | 635 | 549 | 86.46% |
| ir94e | 154359 | 465 | 396 | 85.16% |
| ir94e | 175572 | 390 | 321 | 82.31% |
| ir94e | 200001 | 365 | 299 | 81.92% |
| ir94e | 209688 | 560 | 464 | 82.86% |
| ir94e | 232730 | 131 | 82 | 62.60% |
| ir94e | 534361 | 594 | 503 | 84.68% |
| ir94e | 908747 | 536 | 468 | 87.31% |
| ir94e | 919429 | 110 | 57 | 51.82% |
| ir94e | 214700177 | 446 | 346 | 77.58% |
| ir94e | 418840426 | 163 | 119 | 73.01% |
| ir94e | 491986845 | 233 | 167 | 71.67% |
| ir94e | 551057545 | 163 | 105 | 64.42% |
| ir94e | 633272971 | 149 | 76 | 51.01% |
| ir94e | 792429427 | 160 | 95 | 59.38% |
| ir94e | 912111327 | 262 | 177 | 67.56% |
| ir94e | 947005552 | 106 | 50 | 47.17% |

The JSON additionally records all 242 replication input cells individually. The following 20 partners are fixed by largest direct input into L10331 in the >=1 graph, ties by ascending body ID; there is no reranking after filtering.

| Rank | Partner body | All outputs >=1 | All outputs >=5 | Retained | Into L10331 >=1 | Into L10331 >=5 | Last-hop retained |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 10833 | 3,054 | 2,691 | 88.11% | 464 | 464 | 100.00% |
| 2 | 10881 | 2,087 | 1,854 | 88.84% | 359 | 359 | 100.00% |
| 3 | 13754 | 1,442 | 1,290 | 89.46% | 357 | 357 | 100.00% |
| 4 | 12851 | 2,850 | 2,655 | 93.16% | 351 | 351 | 100.00% |
| 5 | 26764 | 3,970 | 3,688 | 92.90% | 348 | 348 | 100.00% |
| 6 | 523590 | 2,548 | 2,193 | 86.07% | 266 | 266 | 100.00% |
| 7 | 10849 | 6,418 | 5,969 | 93.00% | 241 | 241 | 100.00% |
| 8 | 513655 | 2,040 | 1,905 | 93.38% | 214 | 214 | 100.00% |
| 9 | 14891 | 2,278 | 2,123 | 93.20% | 198 | 198 | 100.00% |
| 10 | 17782 | 1,877 | 1,718 | 91.53% | 187 | 187 | 100.00% |
| 11 | 28181 | 1,865 | 1,639 | 87.88% | 177 | 177 | 100.00% |
| 12 | 11755 | 6,124 | 5,719 | 93.39% | 160 | 160 | 100.00% |
| 13 | 523679 | 2,450 | 2,127 | 86.82% | 142 | 142 | 100.00% |
| 14 | 16142 | 2,098 | 1,932 | 92.09% | 136 | 136 | 100.00% |
| 15 | 12752 | 4,754 | 4,308 | 90.62% | 101 | 101 | 100.00% |
| 16 | 12364 | 5,088 | 4,615 | 90.70% | 96 | 96 | 100.00% |
| 17 | 10673 | 5,602 | 4,442 | 79.29% | 92 | 92 | 100.00% |
| 18 | 238142 | 1,116 | 996 | 89.25% | 92 | 92 | 100.00% |
| 19 | 13402 | 2,156 | 1,972 | 91.47% | 78 | 78 | 100.00% |
| 20 | 522702 | 2,490 | 2,257 | 90.64% | 76 | 76 | 100.00% |

These fixed partners retain 4,135/4,135 last-hop synapses (100.00%). This remains recorded, not a stop condition.

#### Runner plans and verification

Both `--check` modes validate the entire protocol against the frozen declaration commit, cells/layouts, seeds, condition lists and substrate/retention hashes without importing Brian2. Both `--plan` modes are implemented to build exactly one network, call only `net.run(0*second)`, assert zero elapsed simulated time and zero spikes, then write a source-hashed plan with live host/WSL RAM and `phase0.choose_workers` output. The launch path chooses workers again from live RAM and refuses existing run directories. Both plans compiled in WSL with a Windows-measured `--host-free-kib` value; each plan records the source-file hashes that the launch re-checks, and the launch measures memory again.

| Run | Poisson units | Conditions | Planned trials | Seeds | Windows check | WSL compile |
|---|---:|---:|---:|---|---|---|
| b | 242 | 4 | 95 | 20260910-20260939; KC first five only | PASS | PASS (compiled, 8 workers) |
| a | 91 | 16 | 480 | 20260910-20260939 | PASS | PASS (compiled, 8 workers) |

Run (b) channel order is labellar, pharyngeal, tarsal, bitter, with ascending body IDs in each channel. Run (a) preserves sugar, bitter, water, ir94e order. The replication runner stores per-cell rates/latencies, bilateral 1 s and 50 ms rates, whole-network counts, source spike counts, raw network/Poisson events and peak RSS. The run-a runner imports the existing trial routine and A-D/S evaluators; both summaries include whole-network median/range by condition.

| Run b condition | Labellar Hz | Pharyngeal Hz | Tarsal Hz | Bitter Hz | Trials | Graph |
|---|---:|---:|---:|---:|---:|---|
| fbm_sugar | 120 | 100 | 80 | 0 | 30 | >=5 |
| fbm_bitter | 0 | 0 | 0 | 120 | 30 | >=5 |
| fbm_both | 120 | 100 | 80 | 120 | 30 | >=5 |
| fbm_sugar_kc | 120 | 100 | 80 | 0 | 5 | KC gain 0.25 |

| Run a condition | Sugar set | Sugar Hz | Bitter Hz | Trials |
|---|---|---:|---:|---:|
| A_s25_b0 | sugar | 25 | 0 | 30 |
| A_s50_b0 | sugar | 50 | 0 | 30 |
| A_s100_b0 | sugar | 100 | 0 | 30 |
| A_s200_b0 | sugar | 200 | 0 | 30 |
| B_s200_b0 | sugar | 200 | 0 | 30 |
| B_s200_b25 | sugar | 200 | 25 | 30 |
| B_s200_b50 | sugar | 200 | 50 | 30 |
| B_s200_b100 | sugar | 200 | 100 | 30 |
| B_s200_b200 | sugar | 200 | 200 | 30 |
| C_s0_b25 | sugar | 0 | 25 | 30 |
| C_s0_b50 | sugar | 0 | 50 | 30 |
| C_s0_b100 | sugar | 0 | 100 | 30 |
| C_s0_b200 | sugar | 0 | 200 | 30 |
| D_s0_b0 | sugar | 0 | 0 | 30 |
| AP_sugar_120 | sugar | 120 | 0 | 30 |
| AP_sugar_lb3c_120 | sugar_lb3c | 120 | 0 | 30 |

Verification: 15 new M1i tests and all 83 male tests pass; all 348 main Python tests pass; release validation passes. The substrate/retention hash verification and both Windows dry checks pass. No result claim or gate outcome is assigned. Stop at the substrate checkpoint before trial execution.
## M1i results checkpoint — 2026-09-18

**Run (a): FAIL on primary L10331; failing gates: S1.** PASS requires A, B, C, D, S1, S2 and S3 all to pass on L10331. R16949 is recorded, not deciding.

### Run metadata

| Run | Completed UTC | Simulation commit in run_meta | Brian2 / backend | Workers used (budget) | Trials | Seeds | Wall seconds | Peak worker RSS GiB |
|---|---|---|---|---:|---:|---|---:|---:|
| b | 2026-09-19T00:55:44.057942+00:00 | Not recorded | 2.9.0 / cython | 4 (8) | 95 | 20260910–20260939; KC first five | 135.793 | 0.980125 |
| a | 2026-09-19T01:03:24.753353+00:00 | Not recorded | 2.9.0 / cython | 8 (8) | 480 | 20260910–20260939 | 405.418 | 0.981274 |

The launch was reported at `18698a39a7a3c6faa13a19e153c054b26f2ede62`. The run_meta files omit a git commit; the audit verifies every executed source-file hash exactly against metadata and compares its text to that commit with only LF/CRLF normalization. Workers used are the distinct PIDs in the condition ledgers; the replication pool caps the memory budget at four workers. The checkpoint date is 2026-09-18 local; completion timestamps above are 2026-09-19 UTC.

Whole CNS: **166,700 neurons / 6,242,085 edges / 89,859,938 synapses**, edges >=5 after autapse removal; w_syn 0.17875 mV per signed synapse. KC input gain 0.25 changes the declared KC-target signed weights only. [Outgoing retention and fixed top-20 last-hop table](#m1i-substrate-checkpoint--2026-09-18) remain recorded, not stop conditions.

### Run (b): replication

Rates are mean ± population SD across n=30 trials per main condition and n=5 for KC. Bin min/median/max pool all 20 two-cell 50 ms bins per trial; positive trials refer to the two-cell mean.

| Condition | L10331 Hz | R16949 Hz | Two-cell mean Hz | Bin min / median / max Hz | Positive trials | Network spikes median [min–max] | Their reported Hz | Criterion |
|---|---:|---:|---:|---:|---:|---:|---|---|
| fbm_sugar | 104.733 ± 4.449 | 0.000 ± 0.000 | 52.367 ± 2.225 | 10 / 50 / 90 | 30/30 | 296,472.0 [127,140–342,083] | 30–90 | MATCH |
| fbm_bitter | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0 / 0 / 0 | 0/30 | 314,397.0 [297,157–322,332] | 0 | MATCH |
| fbm_both | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0 / 0 / 0 | 0/30 | 335,922.5 [312,456–346,537] | 0 | MATCH |
| fbm_sugar_kc | 96.400 ± 3.072 | 0.000 ± 0.000 | 48.200 ± 1.536 | 10 / 50 / 80 | 5/5 | 228,439.0 [197,059–236,252] | not reported | KC−base -3.800 ± 1.691 Hz; no criterion |

Their number is a per-tick two-cell mean from one 600 ms run at dt 0.5 ms; ours is thirty 1 s trials at dt 0.1 ms on a 166,700-neuron roster (the KC check has five trials). MATCH denotes only the declared replication criteria.

Declared confound: their sugar drive is 204 cells including pharyngeal and tarsal GRNs, ours 17 labellar cells; (b) versus (a) separates the configuration from the input size.

KC−base paired differences use the first five fbm_sugar trials with identical Poisson events, not the thirty-trial sugar mean. L10331: -7.600 ± 3.382 Hz; R16949: 0.000 ± 0.000 Hz; two-cell mean: -3.800 ± 1.691 Hz. No criterion.

### Run (a): declared gates

| Gate | L10331 primary | R16949 secondary |
|---|---|---|
| A | PASS | FAIL |
| B | PASS | FAIL |
| C | PASS | PASS |
| D | PASS | PASS |
| C_literal_zero | FAIL | PASS |
| D_literal_zero | PASS | PASS |
| S1 | FAIL (3/5 positive levels; requires >=4) | Not evaluated; non-deciding |
| S2 | PASS | Not evaluated; non-deciding |
| S3 | PASS (network max/min=1.232990; requires <3) | Not evaluated; non-deciding |
| S | FAIL | Not evaluated; non-deciding |
| Overall A–D + S | FAIL | Non-deciding |

Historical D is completeness, not literal baseline zero. C allows the declared baseline mean + 2 SD + 1 Hz; its literal-zero addition is reported separately and does not change acceptance. S3 applies only to sugar200 network counts. R16949 is silent throughout run (a).

### Run (a): five-level sugar curve

Mean ± population SD in Hz, n=30 at every level.

| Sugar Hz | L10331 | R16949 |
|---|---:|---:|
| 25 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| 50 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| 100 | 0.800 ± 1.013 | 0.000 ± 0.000 |
| 120 | 6.300 ± 3.874 | 0.000 ± 0.000 |
| 200 | 37.067 ± 4.494 | 0.000 ± 0.000 |

### Run (a): every condition

Mean ± population SD, Hz; n=30 per condition.

| Condition | L10331 Hz | R16949 Hz | Network spikes median [min–max] | Neurons fired median [min–max] |
|---|---:|---:|---:|---:|
| A_s25_b0 | 0.000 ± 0.000 | 0.000 ± 0.000 | 510.5 [469–587] | 28.5 [23–53] |
| A_s50_b0 | 0.000 ± 0.000 | 0.000 ± 0.000 | 1,536.0 [1,272–1,812] | 147.5 [56–250] |
| A_s100_b0 | 0.800 ± 1.013 | 0.000 ± 0.000 | 3,890.0 [3,041–5,484] | 197.0 [119–747] |
| A_s200_b0 | 37.067 ± 4.494 | 0.000 ± 0.000 | 305,694.0 [259,827–320,364] | 7,976.5 [7,700–8,200] |
| B_s200_b0 | 37.067 ± 4.494 | 0.000 ± 0.000 | 305,694.0 [259,827–320,364] | 7,976.5 [7,700–8,200] |
| B_s200_b25 | 0.033 ± 0.180 | 0.000 ± 0.000 | 300,033.0 [281,918–328,744] | 7,936.5 [7,588–8,226] |
| B_s200_b50 | 0.000 ± 0.000 | 0.000 ± 0.000 | 307,669.5 [286,481–317,577] | 8,052.5 [7,721–8,372] |
| B_s200_b100 | 0.000 ± 0.000 | 0.000 ± 0.000 | 314,773.5 [293,074–324,729] | 8,184.0 [7,476–8,351] |
| B_s200_b200 | 0.000 ± 0.000 | 0.000 ± 0.000 | 321,222.5 [294,262–332,164] | 8,148.5 [7,949–8,445] |
| C_s0_b25 | 0.800 ± 0.833 | 0.000 ± 0.000 | 295,348.0 [275,168–306,627] | 7,886.5 [7,224–8,084] |
| C_s0_b50 | 0.067 ± 0.359 | 0.000 ± 0.000 | 304,356.0 [288,559–313,766] | 8,034.5 [7,251–8,319] |
| C_s0_b100 | 0.000 ± 0.000 | 0.000 ± 0.000 | 312,298.5 [297,194–320,395] | 8,148.0 [7,972–8,259] |
| C_s0_b200 | 0.000 ± 0.000 | 0.000 ± 0.000 | 316,152.0 [277,504–328,558] | 8,099.5 [7,375–8,222] |
| D_s0_b0 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.0 [0–0] | 0.0 [0–0] |
| AP_sugar_120 | 6.300 ± 3.874 | 0.000 ± 0.000 | 6,360.0 [4,044–305,941] | 598.5 [167–7,941] |
| AP_sugar_lb3c_120 | 1.833 ± 1.827 | 0.000 ± 0.000 | 4,555.0 [3,745–7,013] | 287.0 [156–644] |

### Run (a): A′ sugar17 versus LB3c12 at 120 Hz

Mean ± population SD, n=30 paired seeds; difference is LB3c12 minus sugar17.

| Side | Sugar17 Hz | LB3c12 Hz | Paired subset−union Hz | Lower/equal/higher trials |
|---|---:|---:|---:|---:|
| L | 6.300 ± 3.874 | 1.833 ± 1.827 | -4.467 ± 3.931 | 25/4/1 |
| R | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0/30/0 |

### Execution and verification

The [independent raw audit](../data/malecns/m1i_runs_audit.json) passes 575 raw trial JSON/NPZ pairs (95 b + 480 a), 1150 MN9-neuron trials, 1900 bilateral bin rows and 66,670 Poisson-unit trials. It reconstructs counts, rates, first-spike latencies, network counts and every scientific summary field, including the unchanged A–D/S predicates and both paired comparisons. Every Poisson event index/time is reproduced from the declared seed, rates, dt and physical layout without running a network. The 5 KC pairs (1210 unit trains), 360 A′ shared trains and 30 A200/B0 whole-network pairs match exactly. Repeated seeds are not independent extra replicates.

[Run b summary](../data/malecns/m1i_b_results.json), [run a summary](../data/malecns/m1i_a_results.json), [audit implementation](../sim/malecns/audit_fbm.py), [report and corruption tests](../sim/malecns/test_fbm_report.py). Verification covers audit structure, deliberately corrupted trial data, input reconstruction, report regeneration, the male and main Python suites, and release validation. No new simulation, rerun, M2, alternative gain/threshold, product or frozen-data change is part of this results checkpoint.

## Male line closing ledger — eight variants (2026-09-18)

| Variant | Structural rationale / design | Recorded result under its declared rule |
|---|---|---|
| [M1](#hard-gates) | Whole CNS, original Shiu weights, typed male inputs | Neither side passes A–D. L fails A/B/C; R fails A. S not yet declared. |
| [M1c all](../data/malecns/rescale_all_results.json) | Scale recurrent and tied external weights by whole-network mean density ratio | Passes original A–D-on-at-least-one-side rule on L; R fails A/B. Only200 Hz activates L among A levels; S not yet declared. |
| [M1c mn9](../data/malecns/rescale_mn9_results.json) | Scale by equal-side mean density of strongest MN9 input partners, with the declared137-partner exception | Passes original A–D rule on L; R fails A/B. Only200 Hz activates L among A levels; S not yet declared. |
| [M1d](../data/malecns/split_results.json) | Keep female external kick; scale recurrent weights by whole-network density | FAIL: A–D pass on L, S1 fails (1/5). Saved activity identical to M1c all. |
| [M1f unscaled](../data/malecns/brain_unscaled_results.json) | Brain endpoint cut, original recurrent weight, female kick | FAIL: L B/C fail; graded sugar and S pass. |
| [M1f density](../data/malecns/brain_density_results.json) | Same brain cut; recurrent weight scaled by its density | FAIL: L A–D pass; S1 fails (2/5). |
| [M1h](#m1h-results-checkpoint--2026-09-14) | Confidence-pruned brain graph matched to female density; original weight/kick; outgoing flag explicitly waived | FAIL under A–D + S on L10331; full gate breakdown above. |
| [M1i](#m1i-results-checkpoint--2026-09-18) | Whole CNS, edges >=5, gain 0.65; replication inputs and sugar17 gates declared separately | b fbm_sugar: MATCH; b fbm_bitter: MATCH; b fbm_both: MATCH. a: FAIL under A–D + S on L10331; failing gates: S1. |

Per the declared stop rule, the male line stops after M1i whatever the result. Run (a) fails; the male line is Closed after eight variants. No further variant, gain, threshold change or M2 follows. Historical M1c passes retain their original rules; S is not applied retroactively. No product, frozen-data, copy or honesty-table changes.

## M1j pre-declaration — 2026-09-19

The owner declares [M1j bilateral typed sugar on both brains](bilateral_sugar_policy.md)
(local 2026-09-18 evening) as a v2 stimulus policy test. The male half uses
M1i's whole-CNS ≥5 substrate without autapses, w_syn 0.17875 mV, bilateral
LB3b ∪ LB3c sugar34 (L17/R17), and bilateral LB3c-only A′23 (L12/R11).
Bitter38, water17 and Ir94e19 remain unchanged; 108 physical units, primary
L10331 and recorded R16949. The same A–D plus A′ design totals 480 trials,
seeds 20260910+trial, n=30, 1,000 ms, dt 0.1 ms. Before any M1j trial,
the declared ten-trial M0 recheck must reproduce every stored neuron
spike-time array exactly; any difference stops the task.

Each brain must pass historical A–D and S1–S3 on its primary MN9; adoption
requires both brains to pass. If either fails, reject the policy and close
the male line at nine variants. The ledger becomes nine variants after
M1j whatever the result; no further variant, set, gain or threshold change
is authorized. The linked declaration fixes the female design, overlap
handling, retention reporting, M0 comparison and sequence. This is a
declaration-only internal checkpoint: no substrate build, M0 recheck or
simulation, and no product, frozen-data or honesty-table change.
