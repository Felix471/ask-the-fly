# Phase 0 report — full

## Run metadata

| Field | Value |
|---|---|
| Stage | full |
| Run date | 2026-09-10T21:24:01.815995+00:00 |
| Git commit | 46d13d6e8ecadd8f739039d225d2fd0f122840ca |
| brian2 version | 2.9.0 |
| Codegen target | cython |
| n_proc | 14 |
| Protocol sha256 | 9f9495033281bfcd6f3b373551817987deb2cc083ae94ab61fece9065102d82a |
| Cells sha256 | f78f5071af3bf0984e2e71326f715777c567794e03c0e6369846a147015b395a |
| Total simulated trials | 540 |
| Parallel walltime | 218.0 s |

The paper calibrated w_syn on FlyWire v630; all runs here use v783 only. Absolute Hz may therefore differ from the paper; directions are the acceptance criteria.

MN9 aggregation = left_only (contralateral to the right-hemisphere sugar GRNs), frozen in data/stim_protocol.json.

## Results

| Gate | Stimulus | Aggregated mean ± std (Hz) | Left mean ± std (Hz) | Right mean ± std (Hz) | Right/left | n trials |
|---|---|---:|---:|---:|---:|---:|
| A | 25 Hz sugar | 0.1 ± 0.3 | 0.1 ± 0.3 | 0.1 ± 0.4 | 0.7 | 30 |
| A | 50 Hz sugar | 17.6 ± 4.9 | 17.6 ± 4.9 | 13.3 ± 3.9 | 0.8 | 30 |
| A | 100 Hz sugar | 67.2 ± 4.7 | 67.2 ± 4.7 | 49.5 ± 4.1 | 0.7 | 30 |
| A | 200 Hz sugar | 93.3 ± 5.8 | 93.3 ± 5.8 | 62.1 ± 4.6 | 0.7 | 30 |
| B | 0 Hz bitter (sugar 200 Hz) | 93.0 ± 4.5 | 93.0 ± 4.5 | 62.2 ± 3.9 | 0.7 | 30 |
| B | 25 Hz bitter (sugar 200 Hz) | 79.4 ± 4.0 | 79.4 ± 4.0 | 48.9 ± 4.7 | 0.6 | 30 |
| B | 50 Hz bitter (sugar 200 Hz) | 69.6 ± 4.2 | 69.6 ± 4.2 | 39.7 ± 3.7 | 0.6 | 30 |
| B | 100 Hz bitter (sugar 200 Hz) | 28.3 ± 5.0 | 28.3 ± 5.0 | 13.2 ± 3.1 | 0.5 | 30 |
| B | 200 Hz bitter (sugar 200 Hz) | 0.7 ± 0.6 | 0.7 ± 0.6 | 0.1 ± 0.2 | 0.1 | 30 |
| C | 25 Hz bitter alone | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | N/A | 30 |
| C | 50 Hz bitter alone | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | N/A | 30 |
| C | 100 Hz bitter alone | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | N/A | 30 |
| C | 200 Hz bitter alone | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | N/A | 30 |
| D | 0 Hz | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | N/A | 30 |
| A' | 25 Hz sugar (benchmark 21 IDs) | 0.0 ± 0.2 | 0.0 ± 0.2 | 0.0 ± 0.2 | 1.0 | 30 |
| A' | 50 Hz sugar (benchmark 21 IDs) | 18.1 ± 5.5 | 18.1 ± 5.5 | 14.8 ± 4.6 | 0.8 | 30 |
| A' | 100 Hz sugar (benchmark 21 IDs) | 67.6 ± 3.7 | 67.6 ± 3.7 | 51.2 ± 3.4 | 0.8 | 30 |
| A' | 200 Hz sugar (benchmark 21 IDs) | 92.8 ± 4.8 | 92.8 ± 4.8 | 63.0 ± 4.4 | 0.7 | 30 |

## Hard gates

- **Gate A: PASS.** Sugar sequence: 25 Hz: 0.1 Hz, 50 Hz: 17.6 Hz, 100 Hz: 67.2 Hz, 200 Hz: 93.3 Hz. The 200 Hz response must be far above baseline (> D + 5×sd_D + 5 Hz).
- **Gate B: PASS.** Bitter sequence: 0 Hz: 93.0 Hz, 25 Hz: 79.4 Hz, 50 Hz: 69.6 Hz, 100 Hz: 28.3 Hz, 200 Hz: 0.7 Hz. Percent suppression: 0 Hz: 0.0%, 25 Hz: 14.7%, 50 Hz: 25.1%, 100 Hz: 69.6%, 200 Hz: 99.2%.
- **Gate C: PASS.** Bitter-alone sequence: 25 Hz: 0.0 Hz, 50 Hz: 0.0 Hz, 100 Hz: 0.0 Hz, 200 Hz: 0.0 Hz. Limit: 1.0 Hz.
- **Gate D: PASS.** Baseline aggregated MN9: 0.0 ± 0.0 Hz; required trials: 30. The model has no intrinsic activity, so 0 Hz is expected.

**Overall: PASS** (A–D must all pass).

## Soft indicators

- Sugar@100 / sugar@200 = 0.7 (72.1%), compared with the paper's calibration statement: "W_syn chosen so that sugar GRN activation at 100 Hz gives roughly 80% of maximal MN9 firing" (Shiu et al. 2024 Methods). The paper does not define "maximal"; we use the 200 Hz value as the denominator, so this comparison is provisional.
- Bitter suppression at 200/200 Hz = 99.2%, versus the ≥70% target. This is provisional because the paper gives no number in text (Fig. 3b heatmap only).
- Right/left ratios are shown per condition in the Results table. The paper reports contralateral (left) MN9 responding more strongly to right-hemisphere sugar GRNs.

## Appendix A'

A' uses benchmark.py's 21 sugar IDs instead of the notebook's 23 (19 IDs in common). It does not affect gates.

| Sugar frequency | A aggregated mean ± std (Hz) | A' aggregated mean ± std (Hz) | Absolute difference (Hz) | Percent difference vs A |
|---:|---:|---:|---:|---:|
| 25 Hz | 0.1 ± 0.3 | 0.0 ± 0.2 | 0.1 | 66.7% |
| 50 Hz | 17.6 ± 4.9 | 18.1 ± 5.5 | 0.4 | 2.5% |
| 100 Hz | 67.2 ± 4.7 | 67.6 ± 3.7 | 0.4 | 0.5% |
| 200 Hz | 93.3 ± 5.8 | 92.8 ± 4.8 | 0.5 | 0.5% |

## Equivalence

| Implementation | Aggregated mean ± std (Hz) | Left mean ± std (Hz) | Right mean ± std (Hz) | Walltime (s) |
|---|---:|---:|---:|---:|
| Reusable | 71.2 ± 2.8 | 71.2 ± 2.8 | 52.4 ± 2.2 | 33.6 |
| Legacy | 64.2 ± 5.0 | 64.2 ± 5.0 | 51.2 ± 6.3 | 315.9 |

The ±1 std intervals overlap.

## Backend cross-check (PyTorch CUDA, conditions A and D)

Device: NVIDIA GeForce RTX 4080 SUPER; torch 2.14.0+cu126; float32; batched trials.

| Condition | Brian2 aggregated (Hz) | PyTorch aggregated (Hz) | PyTorch / Brian2 |
|---|---:|---:|---:|
| 25 Hz sugar | 0.1 ± 0.3 | 0.0 ± 0.2 | 0.3 |
| 50 Hz sugar | 17.6 ± 4.9 | 19.7 ± 7.0 | 1.1 |
| 100 Hz sugar | 67.2 ± 4.7 | 78.3 ± 5.0 | 1.2 |
| 200 Hz sugar | 93.3 ± 5.8 | 120.7 ± 4.1 | 1.3 |
| baseline | 0.0 ± 0.0 | 0.0 ± 0.0 | N/A |

- **Hard gate (same monotonic direction and same order of magnitude at 200 Hz): PASS.**
- Soft reference (within ±15% at 200 Hz): not met (PyTorch/Brian2 = 1.3).
- The soft reference is informational only, not a veto. Brian2 CPU remains ground truth.

## Files

- `results/phase0/full/A_sugar_dose_sugar25Hz_bitter0Hz.parquet`
- `results/phase0/full/A_sugar_dose_sugar50Hz_bitter0Hz.parquet`
- `results/phase0/full/A_sugar_dose_sugar100Hz_bitter0Hz.parquet`
- `results/phase0/full/A_sugar_dose_sugar200Hz_bitter0Hz.parquet`
- `results/phase0/full/B_bitter_suppression_sugar200Hz_bitter0Hz.parquet`
- `results/phase0/full/B_bitter_suppression_sugar200Hz_bitter25Hz.parquet`
- `results/phase0/full/B_bitter_suppression_sugar200Hz_bitter50Hz.parquet`
- `results/phase0/full/B_bitter_suppression_sugar200Hz_bitter100Hz.parquet`
- `results/phase0/full/B_bitter_suppression_sugar200Hz_bitter200Hz.parquet`
- `results/phase0/full/C_bitter_alone_sugar0Hz_bitter25Hz.parquet`
- `results/phase0/full/C_bitter_alone_sugar0Hz_bitter50Hz.parquet`
- `results/phase0/full/C_bitter_alone_sugar0Hz_bitter100Hz.parquet`
- `results/phase0/full/C_bitter_alone_sugar0Hz_bitter200Hz.parquet`
- `results/phase0/full/D_baseline.parquet`
- `results/phase0/full/A_prime_sugar_bench21_sugar25Hz.parquet`
- `results/phase0/full/A_prime_sugar_bench21_sugar50Hz.parquet`
- `results/phase0/full/A_prime_sugar_bench21_sugar100Hz.parquet`
- `results/phase0/full/A_prime_sugar_bench21_sugar200Hz.parquet`
- `results/phase0/equiv/reusable_sugar100Hz.parquet`
- `results/phase0/equiv/legacy_sugar100Hz.parquet`
- `results/phase0_torch/full/A_sugar_dose_sugar25Hz_bitter0Hz.parquet`
- `results/phase0_torch/full/A_sugar_dose_sugar50Hz_bitter0Hz.parquet`
- `results/phase0_torch/full/A_sugar_dose_sugar100Hz_bitter0Hz.parquet`
- `results/phase0_torch/full/A_sugar_dose_sugar200Hz_bitter0Hz.parquet`
- `results/phase0_torch/full/D_baseline.parquet`
