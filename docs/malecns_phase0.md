# MaleCNS Phase 0 report — M1, M1c and M1d

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
