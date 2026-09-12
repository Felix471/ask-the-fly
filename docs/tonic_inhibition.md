# Phase T: tonic inhibition of MN9 (designed condition, uncalibrated)

Generated 2026-09-12 by `scripts/tonic_report.py` from `results/tonic/full/summary_tonic.csv` (run 2026-09-12T21:48:30Z, git ea0657a, 60 conditions × 30 trials, 14 workers, 720 s). The frozen protocol, cell sets, grid levels and lookup table were read, not written.

## Method

Tastekin et al. 2026 (Fig S17) hold MN9 down by driving an inhibitory premotor neuron (GNG015) continuously, then test sugar with and without a disinhibition node silenced. GNG015 has no FlyWire v783 match (OQ-5), so three brakes were chosen from the connectome by synapse count onto left MN9 (`docs/tonic_candidates.md`): **buddy** = CB0806 (4 cells: 720575940626961241, 720575940618028125, 720575940647010356, 720575940627293540); **cb0862** = CB0862 (2 cells: 720575940620156209, 720575940611167842); **cb0465** = CB0465 (1 cell: 720575940636809646). Every choice here is ours and uncalibrated: the brake selection, the pairing with sugar only (bitter, water and ir94e at 0 Hz), and the drive level; 100 Hz is Tastekin's Fig S17 level for GNG015, their choice, and the 0 / 50 / 100 / 150 Hz sweep only shows sensitivity to it.

Protocol: `data/stim_protocol_tonic.json` on top of the frozen `data/stim_protocol.json` (same dt, w_syn, f_poi, 1 s trials, seed base, connectome, GRN sets, MN9 readout). The brake cells are driven with the same mechanism as the GRN channels (one Poisson input per cell, weight w_syn × f_poi, refractory zeroed while driven). Sugar takes the five grid levels; 30 trials per condition, seed scheme v2 over the (brake, drive, sugar) product order. Runner: `sim/run_tonic.py` (one batch per brake through `sim.runner.run_conditions`, with its ledgers). Readouts per trial: left and right MN9 rate, mean rate of the brake cells, latency to the first left-MN9 spike, rate of the frozen sugar GRN set. Results: `results/tonic/full/` (gitignored). Adding the brake units to the stimulus PoissonGroup changes the random stream, so the drive-0 row is compared with the frozen grid statistically, not spike for spike.

## Drive-0 row against the frozen grid (sugar-only column)

| sugar | frozen grid left MN9 (30 trials) | buddy drive 0 | cb0862 drive 0 | cb0465 drive 0 |
|---|---:|---:|---:|---:|
| none (0 Hz) | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| low (60 Hz) | 34.7 ± 6.1 | 34.3 ± 5.6 | 35.5 ± 6.4 | 35.6 ± 6.9 |
| medium (80 Hz) | 58.0 ± 5.4 | 57.0 ± 3.8 | 55.6 ± 5.0 | 56.1 ± 4.2 |
| high (120 Hz) | 74.6 ± 4.5 | 72.7 ± 4.3 | 73.2 ± 5.3 | 74.1 ± 4.0 |
| very_high (200 Hz) | 91.8 ± 5.0 | 93.1 ± 4.1 | 92.7 ± 4.3 | 92.9 ± 4.2 |

## buddy (CB0806)

### Left MN9 rate (Hz, mean ± sd over 30 trials), drive × sugar

| drive (Hz) | sugar none (0 Hz) | sugar low (60 Hz) | sugar medium (80 Hz) | sugar high (120 Hz) | sugar very_high (200 Hz) |
|---|---:|---:|---:|---:|---:|
| 0 | 0.0 ± 0.0 | 34.3 ± 5.6 | 57.0 ± 3.8 | 72.7 ± 4.3 | 93.1 ± 4.1 |
| 50 | 0.0 ± 0.0 | 0.1 ± 0.3 | 0.9 ± 1.7 | 5.0 ± 2.2 | 19.4 ± 6.5 |
| 100 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.1 ± 0.4 | 0.3 ± 0.8 |
| 150 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 |

### Right MN9 rate (Hz, mean)

| drive (Hz) | sugar none (0 Hz) | sugar low (60 Hz) | sugar medium (80 Hz) | sugar high (120 Hz) | sugar very_high (200 Hz) |
|---|---:|---:|---:|---:|---:|
| 0 | 0.0 | 27.1 | 42.6 | 52.4 | 62.5 |
| 50 | 0.0 | 0.0 | 0.4 | 1.5 | 5.6 |
| 100 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| 150 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |

### Brake cells' own rate (Hz, mean ± sd; mean over the brake's cells)

| drive (Hz) | sugar none (0 Hz) | sugar low (60 Hz) | sugar medium (80 Hz) | sugar high (120 Hz) | sugar very_high (200 Hz) |
|---|---:|---:|---:|---:|---:|
| 0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| 50 | 50.5 ± 3.5 | 49.8 ± 3.7 | 49.6 ± 3.2 | 49.4 ± 3.0 | 50.5 ± 3.7 |
| 100 | 99.8 ± 3.2 | 99.1 ± 5.2 | 98.2 ± 5.0 | 97.7 ± 4.5 | 99.4 ± 5.4 |
| 150 | 148.7 ± 6.0 | 148.0 ± 5.2 | 148.3 ± 6.6 | 147.0 ± 5.2 | 147.4 ± 7.3 |

### Latency to the first left-MN9 spike (ms, median over trials with a spike; silent trials in brackets)

| drive (Hz) | sugar none | sugar low | sugar medium | sugar high | sugar very_high |
|---|---:|---:|---:|---:|---:|
| 0 | – [30] | 73 [0] | 48 [0] | 36 [0] | 27 [0] |
| 50 | – [30] | 724 [27] | 371 [17] | 138 [1] | 49 [0] |
| 100 | – [30] | – [30] | – [30] | 49 [29] | 198 [25] |
| 150 | – [30] | – [30] | – [30] | – [30] | – [30] |

### Sugar GRN set rate (Hz, sanity: follows the sugar drive, not the brake)

| drive (Hz) | sugar none (0 Hz) | sugar low (60 Hz) | sugar medium (80 Hz) | sugar high (120 Hz) | sugar very_high (200 Hz) |
|---|---:|---:|---:|---:|---:|
| 0 | 0.0 | 59.5 | 79.8 | 118.8 | 196.4 |
| 50 | 0.0 | 59.7 | 79.9 | 117.9 | 195.5 |
| 100 | 0.0 | 60.0 | 79.1 | 118.7 | 196.7 |
| 150 | 0.0 | 59.3 | 79.3 | 119.4 | 196.9 |

## cb0862 (CB0862)

### Left MN9 rate (Hz, mean ± sd over 30 trials), drive × sugar

| drive (Hz) | sugar none (0 Hz) | sugar low (60 Hz) | sugar medium (80 Hz) | sugar high (120 Hz) | sugar very_high (200 Hz) |
|---|---:|---:|---:|---:|---:|
| 0 | 0.0 ± 0.0 | 35.5 ± 6.4 | 55.6 ± 5.0 | 73.2 ± 5.3 | 92.7 ± 4.3 |
| 50 | 0.0 ± 0.0 | 5.1 ± 3.6 | 12.1 ± 5.6 | 30.7 ± 6.0 | 55.1 ± 7.5 |
| 100 | 0.0 ± 0.0 | 0.1 ± 0.3 | 0.7 ± 1.0 | 3.1 ± 2.6 | 16.3 ± 5.4 |
| 150 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.1 ± 0.3 | 1.9 ± 2.2 |

### Right MN9 rate (Hz, mean)

| drive (Hz) | sugar none (0 Hz) | sugar low (60 Hz) | sugar medium (80 Hz) | sugar high (120 Hz) | sugar very_high (200 Hz) |
|---|---:|---:|---:|---:|---:|
| 0 | 0.0 | 26.4 | 41.8 | 52.1 | 63.5 |
| 50 | 0.0 | 2.9 | 6.2 | 13.4 | 22.8 |
| 100 | 0.0 | 0.0 | 0.1 | 0.9 | 2.5 |
| 150 | 0.0 | 0.0 | 0.0 | 0.0 | 0.1 |

### Brake cells' own rate (Hz, mean ± sd; mean over the brake's cells)

| drive (Hz) | sugar none (0 Hz) | sugar low (60 Hz) | sugar medium (80 Hz) | sugar high (120 Hz) | sugar very_high (200 Hz) |
|---|---:|---:|---:|---:|---:|
| 0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 |
| 50 | 51.8 ± 5.2 | 48.9 ± 5.8 | 50.0 ± 5.6 | 49.4 ± 5.5 | 47.8 ± 5.5 |
| 100 | 99.1 ± 8.3 | 98.2 ± 5.8 | 99.2 ± 7.1 | 100.2 ± 7.0 | 98.6 ± 6.6 |
| 150 | 146.9 ± 9.2 | 150.1 ± 7.8 | 147.5 ± 8.6 | 146.9 ± 9.8 | 145.5 ± 6.7 |

### Latency to the first left-MN9 spike (ms, median over trials with a spike; silent trials in brackets)

| drive (Hz) | sugar none | sugar low | sugar medium | sugar high | sugar very_high |
|---|---:|---:|---:|---:|---:|
| 0 | – [30] | 72 [0] | 49 [0] | 38 [0] | 28 [0] |
| 50 | – [30] | 396 [1] | 99 [0] | 47 [0] | 33 [0] |
| 100 | – [30] | 629 [26] | 515 [17] | 174 [6] | 53 [0] |
| 150 | – [30] | – [30] | – [30] | 463 [26] | 533 [7] |

### Sugar GRN set rate (Hz, sanity: follows the sugar drive, not the brake)

| drive (Hz) | sugar none (0 Hz) | sugar low (60 Hz) | sugar medium (80 Hz) | sugar high (120 Hz) | sugar very_high (200 Hz) |
|---|---:|---:|---:|---:|---:|
| 0 | 0.0 | 59.9 | 78.7 | 118.5 | 196.2 |
| 50 | 0.0 | 59.6 | 79.7 | 119.0 | 197.1 |
| 100 | 0.0 | 59.5 | 79.7 | 118.8 | 196.7 |
| 150 | 0.0 | 60.1 | 79.6 | 118.1 | 196.0 |

## cb0465 (CB0465)

### Left MN9 rate (Hz, mean ± sd over 30 trials), drive × sugar

| drive (Hz) | sugar none (0 Hz) | sugar low (60 Hz) | sugar medium (80 Hz) | sugar high (120 Hz) | sugar very_high (200 Hz) |
|---|---:|---:|---:|---:|---:|
| 0 | 0.0 ± 0.0 | 35.6 ± 6.9 | 56.1 ± 4.2 | 74.1 ± 4.0 | 92.9 ± 4.2 |
| 50 | 0.0 ± 0.0 | 22.6 ± 5.5 | 39.5 ± 5.4 | 53.3 ± 5.4 | 74.4 ± 6.8 |
| 100 | 0.0 ± 0.0 | 10.8 ± 3.4 | 23.6 ± 5.1 | 37.2 ± 5.2 | 54.6 ± 6.9 |
| 150 | 0.0 ± 0.0 | 5.3 ± 2.9 | 12.5 ± 3.5 | 22.9 ± 5.1 | 35.5 ± 6.9 |

### Right MN9 rate (Hz, mean)

| drive (Hz) | sugar none (0 Hz) | sugar low (60 Hz) | sugar medium (80 Hz) | sugar high (120 Hz) | sugar very_high (200 Hz) |
|---|---:|---:|---:|---:|---:|
| 0 | 0.0 | 27.6 | 41.5 | 52.4 | 64.1 |
| 50 | 0.0 | 25.8 | 39.4 | 50.6 | 59.4 |
| 100 | 0.0 | 21.1 | 36.2 | 48.1 | 60.5 |
| 150 | 0.0 | 18.9 | 33.5 | 46.8 | 56.7 |

### Brake cells' own rate (Hz, mean ± sd; mean over the brake's cells)

| drive (Hz) | sugar none (0 Hz) | sugar low (60 Hz) | sugar medium (80 Hz) | sugar high (120 Hz) | sugar very_high (200 Hz) |
|---|---:|---:|---:|---:|---:|
| 0 | 0.0 ± 0.0 | 6.3 ± 1.9 | 11.3 ± 1.8 | 16.5 ± 1.5 | 25.6 ± 2.0 |
| 50 | 49.6 ± 7.7 | 53.1 ± 6.9 | 54.6 ± 7.4 | 59.8 ± 6.2 | 64.4 ± 5.5 |
| 100 | 98.5 ± 10.6 | 104.2 ± 9.0 | 104.4 ± 10.9 | 107.0 ± 9.6 | 107.9 ± 9.8 |
| 150 | 151.0 ± 11.8 | 147.2 ± 10.4 | 149.1 ± 12.0 | 153.4 ± 8.6 | 152.8 ± 12.2 |

### Latency to the first left-MN9 spike (ms, median over trials with a spike; silent trials in brackets)

| drive (Hz) | sugar none | sugar low | sugar medium | sugar high | sugar very_high |
|---|---:|---:|---:|---:|---:|
| 0 | – [30] | 77 [0] | 51 [0] | 36 [0] | 27 [0] |
| 50 | – [30] | 96 [0] | 57 [0] | 43 [0] | 32 [0] |
| 100 | – [30] | 145 [0] | 75 [0] | 47 [0] | 37 [0] |
| 150 | – [30] | 259 [0] | 94 [0] | 62 [0] | 41 [0] |

### Sugar GRN set rate (Hz, sanity: follows the sugar drive, not the brake)

| drive (Hz) | sugar none (0 Hz) | sugar low (60 Hz) | sugar medium (80 Hz) | sugar high (120 Hz) | sugar very_high (200 Hz) |
|---|---:|---:|---:|---:|---:|
| 0 | 0.0 | 59.5 | 79.4 | 118.3 | 196.5 |
| 50 | 0.0 | 59.2 | 79.2 | 117.6 | 196.2 |
| 100 | 0.0 | 59.1 | 79.2 | 118.7 | 196.3 |
| 150 | 0.0 | 60.1 | 79.2 | 118.9 | 195.5 |

## Replays

One whole-network trial per condition, `results/tonic/replays/<cond_id>.npz` (grid replay layout; seed rule base_seed + 800000 + global_index); not packed, not shipped.

| cond_id | seed | spikes | left MN9 spikes |
|---|---:|---:|---:|
| T_buddy_d100_snone | 21060920 | 395 | 0 |
| T_buddy_d100_shigh | 21060923 | 8117 | 0 |
| T_cb0862_d100_snone | 21060940 | 218 | 0 |
| T_cb0862_d100_shigh | 21060943 | 9241 | 8 |
| T_cb0465_d100_snone | 21060960 | 116 | 0 |
| T_cb0465_d100_shigh | 21060963 | 11091 | 29 |

## Reading

Each question is answered against that brake's own drive-0 row, not against zero. "No brake" means the same brake at drive 0, which reproduces the frozen sugar-only column (table above; every cell within one standard deviation of the grid).

**buddy (CB0806, four cells).** With the brake at 100 Hz, sugar no longer raises left MN9 in any useful sense: 0.1 ± 0.4 Hz at sugar high and 0.3 ± 0.8 Hz at very_high against 72.7 and 93.1 Hz without the brake, a suppression of more than 99%; at 50 Hz drive sugar still gets through (5.0 Hz at high, 19.4 at very_high, 7% and 21% of no-brake), at 150 Hz nothing does. Sugar does not reduce the brake's own firing under drive: 99.8 Hz with no sugar, 97.7 Hz at sugar high, 99.4 at very_high, all within one standard deviation, and the drive-0 row is 0 Hz at every sugar level, so sugar neither recruits nor inhibits these cells. Right MN9 follows left MN9 (both CB0806 pairs project to both sides).

**cb0862 (CB0862, two cells).** With the brake at 100 Hz, sugar still raises left MN9 a little: 3.1 ± 2.6 Hz at high and 16.3 ± 5.4 at very_high, 4% and 18% of the no-brake rates (73.2, 92.7); at 50 Hz drive the brake only halves the response (30.7 and 55.1 Hz, 42% and 59%), at 150 Hz it removes it (0.1, 1.9). Sugar does not reduce the brake's own firing under drive (99.1 → 100.2 Hz at sugar high, 98.6 at very_high) and the drive-0 row is 0 Hz throughout. Onset latency grows with the drive: 38 ms at sugar high with no brake, 174 ms at 100 Hz (6 of 30 trials silent), 463 ms at 150 Hz (26 silent).

**cb0465 (CB0465, one cell, right side).** This brake does not hold MN9 down: at 100 Hz drive sugar still raises left MN9 to 37.2 ± 5.2 Hz at high and 54.6 ± 6.9 at very_high, 50% and 59% of the no-brake rates (74.1, 92.9), and even at 150 Hz to 22.9 and 35.5 Hz (31%, 38%); it delays onset (36 → 47 ms at sugar high, 100 Hz) but never silences a trial. Right MN9 is almost untouched (52.4 → 48.1 Hz at sugar high, 100 Hz), as its 10 synapses onto right MN9 predict. And sugar raises this brake's own firing rather than reducing it: with no drive the cell goes 0 → 6.3 → 11.3 → 16.5 → 25.6 Hz across the five sugar levels, and under drive the increment persists but shrinks (98.5 → 107.0 Hz at sugar high and 100 Hz drive, +8.5; 151.0 → 153.4 at 150 Hz), so the sugar-driven component adds sub-additively to the Poisson drive. That is **feed-forward inhibition, sugar → CB0465 → MN9**, the opposite direction from the disinhibition motif this condition was built to look for: in this model the sugar pathway recruits the strongest inhibitory input to left MN9 while it excites MN9, and that recruitment is already part of every sugar curve in the frozen grid (the drive-0 row here is the grid). Recorded as a separate finding under OQ-3.

**Across the three brakes.** None of them shows the signature the condition was designed to find: no brake's own rate falls when sugar arrives. The sugar GRN set fires at its drive rate under every condition (sanity rows), so the brakes act downstream of the GRNs, not on them. Tastekin et al.'s 100 Hz is their choice for GNG015; 100 Hz on CB0806 or CB0862 is a full brake and 100 Hz on CB0465 is a partial one, which says only that the three neurons differ in synapse count onto MN9, nothing about the fly. Nothing in this document is calibrated against behaviour.

## What is designed here

Brake selection (synapse count onto left MN9, `docs/tonic_candidates.md`), the drive levels (0 / 50 / 100 / 150 Hz; 100 Hz after Tastekin, uncalibrated), the pairing with sugar only (bitter, water and ir94e at 0 Hz), the trial count and seeds. Nothing under `data/` changed; the frozen grid and its replays are untouched. This condition is not part of the product.
