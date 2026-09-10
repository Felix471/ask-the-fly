# Phase 1 characterization

## Run metadata

| Field | Value |
|---|---|
| Stage | characterize |
| Run date | 2026-09-10T22:12:54.598577+00:00 |
| Git commit | 035567f3f332b31756d0b97c1cf7c8ad355b540a |
| brian2 version | 2.9.0 |
| Codegen target | cython |
| n_proc | 14 |
| Conditions (deduplicated/raw) | 374/443 |
| Protocol sha256 | 9f9495033281bfcd6f3b373551817987deb2cc083ae94ab61fece9065102d82a |
| Cells sha256 | f78f5071af3bf0984e2e71326f715777c567794e03c0e6369846a147015b395a |
| Total simulated trials | 11220 |
| Parallel walltime | 3870.8 s |

## Provenance note (2026-09-10)

This report was produced with the reusable Brian2 path BEFORE the refractory fix of 2026-09-10: every stimulable GRN (sugar, bitter, water, ir94e) had its refractory period set to 0 at build time, whereas the paper's model.py sets rfc = 0 only for neurons that receive Poisson input. The equivalence study (docs/equivalence_study.md) measured the pure effect of this rule with the random stream held fixed: zero (10/10 seeds spike-for-spike identical at sugar 100 Hz, bitter 0 Hz), i.e. the undriven GRNs never fired in that condition. The rule was corrected for fidelity to model.py, not because it changes results. Any difference between pre-fix and fixed runs is sampling noise from different random streams (the stimulus group size changed the draws). The lookup grid uses the corrected per-channel rule. Measured delta at sugar 100 Hz, fixed minus pre-fix (condition A, 30 trials each): +0.1 Hz (pre-fix 67.2, fixed 67.3). See docs/fixed_path_recheck.md.

The paper calibrated w_syn on FlyWire v630; this run uses flywire_v783 only. Absolute Hz may therefore differ from the paper.

MN9 aggregation = left_only (contralateral to the right-hemisphere sugar GRNs), frozen in `data/stim_protocol.json`. Right MN9 is recorded and reported but is not the aggregated readout.

## Single-channel dose curves

### sugar

| Hz | MN9 aggregated mean ± std | Left mean ± std | Right mean ± std |
|---:|---:|---:|---:|
| 0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| 20 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| 40 | 4.2 ± 3.2 | 4.2 ± 3.2 | 3.6 ± 2.7 |
| 60 | 31.1 ± 6.8 | 31.1 ± 6.8 | 24.2 ± 5.7 |
| 80 | 56.1 ± 5.7 | 56.1 ± 5.7 | 43.0 ± 4.3 |
| 100 | 65.3 ± 4.8 | 65.3 ± 4.8 | 47.4 ± 3.9 |
| 120 | 75.2 ± 5.6 | 75.2 ± 5.6 | 52.7 ± 4.1 |
| 140 | 81.1 ± 5.5 | 81.1 ± 5.5 | 56.5 ± 4.2 |
| 160 | 86.8 ± 4.7 | 86.8 ± 4.7 | 59.9 ± 4.8 |
| 180 | 89.3 ± 5.3 | 89.3 ± 5.3 | 60.0 ± 5.4 |
| 200 | 93.5 ± 4.8 | 93.5 ± 4.8 | 62.2 ± 4.3 |

Monotonic non-decreasing: **yes**; monotonic non-increasing: **no**. Maximum adjacent |Δ| = 26.9 Hz versus pooled std = 4.7 Hz; range = 93.5 Hz. Classification: **excitatory**.

### bitter

| Hz | MN9 aggregated mean ± std | Left mean ± std | Right mean ± std |
|---:|---:|---:|---:|
| 0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| 20 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| 40 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| 60 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| 80 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| 100 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| 120 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| 140 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| 160 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| 180 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| 200 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 |

Monotonic non-decreasing: **yes**; monotonic non-increasing: **yes**. Maximum adjacent |Δ| = 0.0 Hz versus pooled std = 0.0 Hz; range = 0.0 Hz. Classification: **no effect**.

Approximately zero response to bitter alone is expected and is not a failure.

### water

| Hz | MN9 aggregated mean ± std | Left mean ± std | Right mean ± std |
|---:|---:|---:|---:|
| 0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| 20 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| 40 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| 60 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| 80 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| 100 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| 120 | 0.2 ± 0.5 | 0.2 ± 0.5 | 0.0 ± 0.0 |
| 140 | 2.7 ± 2.3 | 2.7 ± 2.3 | 0.4 ± 0.8 |
| 160 | 10.4 ± 3.2 | 10.4 ± 3.2 | 3.0 ± 2.4 |
| 180 | 20.6 ± 4.3 | 20.6 ± 4.3 | 7.6 ± 3.4 |
| 200 | 29.3 ± 5.3 | 29.3 ± 5.3 | 12.0 ± 4.4 |
| 220 | 38.2 ± 4.7 | 38.2 ± 4.7 | 16.3 ± 3.9 |
| 240 | 46.3 ± 4.9 | 46.3 ± 4.9 | 21.9 ± 4.5 |
| 260 | 50.8 ± 5.1 | 50.8 ± 5.1 | 25.0 ± 5.1 |

Monotonic non-decreasing: **yes**; monotonic non-increasing: **no**. Maximum adjacent |Δ| = 10.2 Hz versus pooled std = 3.1 Hz; range = 50.8 Hz. Classification: **excitatory**.

### ir94e

| Hz | MN9 aggregated mean ± std | Left mean ± std | Right mean ± std |
|---:|---:|---:|---:|
| 0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| 20 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| 40 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| 60 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| 80 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| 100 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| 120 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| 140 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| 160 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| 180 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| 200 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 |

Monotonic non-decreasing: **yes**; monotonic non-increasing: **yes**. Maximum adjacent |Δ| = 0.0 Hz versus pooled std = 0.0 Hz; range = 0.0 Hz. Classification: **no effect**.

Approximately zero response to ir94e alone is expected and is not a failure.

## Pairwise

### sugar × bitter

| Sugar Hz \ bitter Hz | 0 | 20 | 40 | 60 | 80 | 100 | 120 | 140 | 160 | 180 | 200 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| 20 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| 40 | 4.2 | 1.4 | 0.1 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| 60 | 31.1 | 20.1 | 2.7 | 0.3 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| 80 | 56.1 | 40.3 | 15.8 | 3.6 | 0.3 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| 100 | 65.3 | 51.8 | 32.6 | 12.2 | 2.8 | 0.4 | 0.1 | 0.0 | 0.0 | 0.0 | 0.0 |
| 120 | 75.2 | 63.0 | 47.9 | 23.1 | 7.0 | 1.4 | 0.4 | 0.3 | 0.0 | 0.0 | 0.1 |
| 140 | 81.1 | 69.2 | 58.1 | 34.5 | 17.1 | 6.0 | 1.5 | 0.6 | 0.3 | 0.1 | 0.1 |
| 160 | 86.8 | 73.9 | 66.7 | 45.8 | 25.5 | 11.8 | 4.7 | 1.0 | 0.7 | 0.3 | 0.2 |
| 180 | 89.3 | 76.8 | 71.2 | 54.7 | 35.5 | 19.4 | 9.5 | 2.8 | 1.0 | 0.9 | 0.4 |
| 200 | 93.5 | 82.3 | 76.9 | 60.6 | 41.6 | 29.6 | 16.6 | 7.8 | 3.1 | 1.2 | 0.7 |

Percent change from bitter=0 to bitter=max:

- Sugar 60 Hz: -100.0%
- Sugar 80 Hz: -100.0%
- Sugar 100 Hz: -100.0%
- Sugar 120 Hz: -99.9%
- Sugar 140 Hz: -99.9%
- Sugar 160 Hz: -99.7%
- Sugar 180 Hz: -99.6%
- Sugar 200 Hz: -99.3%

At sugar=200 Hz, MN9 is **non-increasing** along the bitter axis. Modifier classification: **suppressive**.

### sugar × water

| Sugar Hz \ water Hz | 0 | 20 | 40 | 60 | 80 | 100 | 120 | 140 | 160 | 180 | 200 | 220 | 240 | 260 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.2 | 2.7 | 10.4 | 20.6 | 29.3 | 38.2 | 46.3 | 50.8 |
| 20 | 0.0 | 0.1 | 1.0 | 1.6 | 1.8 | 5.0 | 12.6 | 22.4 | 31.3 | 38.3 | 46.2 | 48.6 | 55.8 | 59.5 |
| 40 | 4.2 | 9.7 | 24.3 | 33.7 | 39.5 | 45.6 | 46.4 | 54.9 | 58.9 | 58.9 | 62.6 | 62.2 | 64.3 | 65.7 |
| 60 | 31.1 | 44.2 | 53.9 | 60.4 | 64.7 | 63.0 | 67.1 | 68.1 | 69.8 | 68.6 | 70.2 | 71.8 | 73.1 | 71.4 |
| 80 | 56.1 | 61.8 | 67.4 | 70.7 | 75.7 | 78.4 | 77.2 | 79.0 | 78.8 | 79.1 | 77.5 | 77.4 | 80.0 | 78.5 |
| 100 | 65.3 | 71.0 | 73.9 | 80.1 | 83.1 | 84.8 | 85.9 | 86.8 | 84.9 | 83.8 | 84.0 | 84.5 | 85.1 | 84.2 |
| 120 | 75.2 | 76.3 | 80.5 | 86.4 | 87.6 | 89.9 | 88.8 | 92.5 | 90.8 | 88.9 | 89.1 | 89.3 | 88.7 | 87.9 |
| 140 | 81.1 | 82.8 | 85.3 | 90.2 | 90.7 | 94.1 | 92.3 | 92.6 | 95.1 | 97.5 | 94.0 | 94.0 | 92.6 | 92.3 |
| 160 | 86.8 | 87.8 | 91.0 | 92.2 | 95.0 | 96.5 | 98.0 | 96.1 | 96.9 | 95.4 | 95.5 | 96.0 | 95.1 | 94.5 |
| 180 | 89.3 | 91.8 | 93.4 | 94.6 | 96.9 | 100.1 | 98.9 | 100.9 | 99.5 | 100.3 | 99.6 | 99.5 | 97.5 | 99.2 |
| 200 | 93.5 | 94.6 | 94.0 | 98.6 | 99.4 | 100.5 | 101.3 | 101.9 | 100.8 | 103.0 | 101.1 | 100.8 | 99.9 | 99.9 |

Percent change from water=0 to water=max:

- Sugar 60 Hz: 129.2%
- Sugar 80 Hz: 40.0%
- Sugar 100 Hz: 28.8%
- Sugar 120 Hz: 17.0%
- Sugar 140 Hz: 13.7%
- Sugar 160 Hz: 8.8%
- Sugar 180 Hz: 11.1%
- Sugar 200 Hz: 6.9%

At sugar=200 Hz, MN9 is **non-monotonic** along the water axis. Modifier classification: **facilitating**.

### sugar × ir94e

| Sugar Hz \ ir94e Hz | 0 | 20 | 40 | 60 | 80 | 100 | 120 | 140 | 160 | 180 | 200 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| 20 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| 40 | 4.2 | 0.8 | 0.0 | 0.0 | 0.0 | 0.0 | 0.1 | 0.0 | 0.0 | 0.0 | 0.0 |
| 60 | 31.1 | 24.7 | 6.6 | 1.7 | 0.5 | 0.4 | 0.2 | 0.2 | 0.1 | 0.2 | 0.2 |
| 80 | 56.1 | 48.1 | 30.8 | 16.7 | 7.3 | 5.1 | 3.8 | 1.5 | 2.0 | 1.3 | 0.5 |
| 100 | 65.3 | 62.7 | 52.7 | 40.1 | 24.0 | 16.5 | 10.0 | 7.5 | 6.0 | 4.2 | 3.1 |
| 120 | 75.2 | 72.3 | 65.0 | 56.4 | 46.4 | 35.7 | 25.5 | 19.1 | 16.0 | 11.6 | 8.7 |
| 140 | 81.1 | 77.3 | 73.5 | 67.0 | 58.8 | 55.2 | 44.0 | 37.7 | 30.1 | 26.7 | 21.5 |
| 160 | 86.8 | 85.8 | 78.9 | 75.1 | 67.6 | 63.4 | 58.0 | 52.9 | 46.2 | 45.5 | 39.4 |
| 180 | 89.3 | 85.5 | 83.3 | 79.4 | 75.8 | 70.1 | 64.4 | 61.7 | 60.0 | 56.8 | 50.6 |
| 200 | 93.5 | 91.7 | 87.0 | 85.1 | 79.2 | 78.3 | 70.8 | 68.4 | 66.1 | 63.7 | 62.5 |

Percent change from ir94e=0 to ir94e=max:

- Sugar 60 Hz: -99.4%
- Sugar 80 Hz: -99.0%
- Sugar 100 Hz: -95.3%
- Sugar 120 Hz: -88.4%
- Sugar 140 Hz: -73.5%
- Sugar 160 Hz: -54.6%
- Sugar 180 Hz: -43.3%
- Sugar 200 Hz: -33.1%

At sugar=200 Hz, MN9 is **non-increasing** along the ir94e axis. Modifier classification: **suppressive**.

## Channel summary

| Channel | Alone effect | Effect as modifier of sugar | Verdict |
|---|---|---|---|
| sugar | excitatory | not assessed | stable & interpretable |
| bitter | no effect | suppressive | stable & interpretable |
| water | excitatory | facilitating | stable & interpretable |
| ir94e | no effect | suppressive | stable & interpretable |

## Proposed level → Hz mapping (provisional, for user confirmation)

A level is distinguishable when adjacent MN9 outcomes differ by at least max(3 Hz, 1.5 × pooled std). All selections are measured points; no interpolation is used.

### Bitter modifier context

| Bitter Hz | MN9 at sugar=100 Hz (mean ± std) | MN9 at sugar=200 Hz (mean ± std) |
|---:|---:|---:|
| 0 | 65.3 ± 4.8 | 93.5 ± 4.8 |
| 20 | 51.8 ± 5.8 | 82.3 ± 5.1 |
| 40 | 32.6 ± 5.8 | 76.9 ± 4.6 |
| 60 | 12.2 ± 3.0 | 60.6 ± 5.8 |
| 80 | 2.8 ± 2.2 | 41.6 ± 5.0 |
| 100 | 0.4 ± 0.5 | 29.6 ± 3.7 |
| 120 | 0.1 ± 0.3 | 16.6 ± 4.0 |
| 140 | 0.0 ± 0.0 | 7.8 ± 3.3 |
| 160 | 0.0 ± 0.0 | 3.1 ± 1.9 |
| 180 | 0.0 ± 0.0 | 1.2 ± 0.9 |
| 200 | 0.0 ± 0.0 | 0.7 ± 0.6 |

### sugar

The single-channel sugar curve is used.
Measured response direction: **increasing** (observed trend: **non-decreasing**).

| Level | proposed Hz | MN9 at that Hz (mean ± std) | Δ vs previous level | distinguishable? |
|---|---:|---:|---:|---|
| none | 0 | 0.0 ± 0.0 | — | — |
| low | 60 | 31.1 ± 6.8 | +31.1 Hz | yes |
| medium | 80 | 56.1 ± 5.7 | +24.9 Hz | yes |
| high | 100 | 65.3 ± 4.8 | +9.3 Hz | yes |
| very_high | 160 | 86.8 ± 4.7 | +21.5 Hz | yes |

Current provisional mapping comparison: none=0 Hz -> 0.0 ± 0.0 Hz; low=25 Hz -> not measured; medium=50 Hz -> not measured; high=100 Hz -> 65.3 ± 4.8 Hz; very_high=200 Hz -> 93.5 ± 4.8 Hz.
Noise floor: pooled std = 4.7 Hz; distinguishability threshold = 7.1 Hz.

### bitter

The proposal uses the modifier curve at sugar=200 Hz.
Measured response direction: **decreasing** (observed trend: **non-increasing**).

| Level | proposed Hz | MN9 at that Hz (mean ± std) | Δ vs previous level | distinguishable? |
|---|---:|---:|---:|---|
| none | 0 | 93.5 ± 4.8 | — | — |
| low | 40 | 76.9 ± 4.6 | -16.6 Hz | yes |
| medium | 80 | 41.6 ± 5.0 | -35.2 Hz | yes |
| high | 100 | 29.6 ± 3.7 | -12.0 Hz | yes |
| very_high | 160 | 3.1 ± 1.9 | -26.5 Hz | yes |

Current provisional mapping comparison: none=0 Hz -> 93.5 ± 4.8 Hz; low=25 Hz -> not measured; medium=50 Hz -> not measured; high=100 Hz -> 29.6 ± 3.7 Hz; very_high=200 Hz -> 0.7 ± 0.6 Hz.
Noise floor: pooled std = 4.0 Hz; distinguishability threshold = 6.0 Hz.

### water

The single-channel curve is used because its 50.8 Hz range exceeds max(2 Hz, 2 × pooled std) = 6.2 Hz.
Measured response direction: **increasing** (observed trend: **non-decreasing**).

| Level | proposed Hz | MN9 at that Hz (mean ± std) | Δ vs previous level | distinguishable? |
|---|---:|---:|---:|---|
| none | 0 | 0.0 ± 0.0 | — | — |
| low | 160 | 10.4 ± 3.2 | +10.4 Hz | yes |
| medium | 200 | 29.3 ± 5.3 | +18.9 Hz | yes |
| high | 220 | 38.2 ± 4.7 | +8.9 Hz | yes |
| very_high | 240 | 46.3 ± 4.9 | +8.1 Hz | yes |

Current provisional mapping comparison: none=0 Hz -> 0.0 ± 0.0 Hz; low=25 Hz -> not measured; medium=50 Hz -> not measured; high=100 Hz -> 0.0 ± 0.0 Hz; very_high=200 Hz -> 29.3 ± 5.3 Hz.
Noise floor: pooled std = 3.1 Hz; distinguishability threshold = 4.6 Hz.

### ir94e

The modifier curve at sugar=200 Hz is used because the single-channel range is 0.0 Hz, which does not exceed max(2 Hz, 2 × pooled std) = 2.0 Hz. Measured for completeness; v1 does not encode ir94e.
Measured response direction: **decreasing** (observed trend: **non-increasing**).

| Level | proposed Hz | MN9 at that Hz (mean ± std) | Δ vs previous level | distinguishable? |
|---|---:|---:|---:|---|
| none | 0 | 93.5 ± 4.8 | — | — |
| low | 60 | 85.1 ± 3.8 | -8.4 Hz | yes |
| medium | 120 | 70.8 ± 5.2 | -14.3 Hz | yes |
| high | 140 | 68.4 ± 7.7 | -2.4 Hz | no — not distinguishable from medium |
| very_high | 200 | 62.5 ± 5.8 | -5.9 Hz | no — not distinguishable from high |

Current provisional mapping comparison: none=0 Hz -> 93.5 ± 4.8 Hz; low=25 Hz -> not measured; medium=50 Hz -> not measured; high=100 Hz -> 78.3 ± 4.7 Hz; very_high=200 Hz -> 62.5 ± 5.8 Hz.
Noise floor: pooled std = 5.5 Hz; distinguishability threshold = 8.3 Hz.

### Proposal summary

| Dimension | none | low | medium | high | very_high | curve used |
|---|---:|---:|---:|---:|---:|---|
| sugar | 0 | 60 | 80 | 100 | 160 | single-channel sugar |
| bitter | 0 | 40 | 80 | 100 | 160 | modifier at sugar=200 Hz |
| water | 0 | 160 | 200 | 220 | 240 | single-channel water |
| ir94e | 0 | 60 | 120 | 140 | 200 | modifier at sugar=200 Hz |

These values are proposals from measured points; the frozen protocol covers mechanics only. Level→Hz is confirmed by the user before any grid is generated.

## Dimensionality options

- **3D sugar×bitter×water.** The observed alone effects are sugar=excitatory, bitter=no effect, and water=excitatory; bitter is suppressive and water is facilitating as a sugar modifier. The characterization does not measure bitter×water or three-way interactions.
- **2D sugar×bitter with water as a modifier.** This directly represents the measured sugar×bitter plane (suppressive) while treating the measured water effect (facilitating) outside the two primary axes.
- **4 channels.** This retains sugar, bitter, water, and ir94e; their verdicts are sugar=stable & interpretable, bitter=stable & interpretable, water=stable & interpretable, ir94e=stable & interpretable. Current evidence covers each channel alone and each non-sugar channel paired with sugar, but not other pairings or higher-order interactions.

Decision pending user confirmation on both dimensionality and level→Hz mapping; no grid generated. Grid cells will use 30 trials.
