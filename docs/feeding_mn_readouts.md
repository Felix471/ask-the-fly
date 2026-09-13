# Feeding motor-neuron readouts beyond MN9

## Status and scope

2026-09-13: C1 screen, C2 thirteen-cell / 30-trial rerun, and C2b
connectivity-only audit complete. C2 records twelve MNs in 390 completed trials.
This is research only: frozen inputs, lookup scores, replay files, `site/`, encoder
values and README honesty tables are unchanged. No checkpoint-chain score has been built.

MN11D and MN11V usually covary with left MN9, but C2 confirms markedly
different responses at intermediate bitter drive. All six CEM neurons remained
silent in all 400 C1 trials and all 390 C2 trials; pharyngeal inputs have more
two-hop structural input to CEM than the frozen labellar sets (C2b).
This does not establish a serial, causal feeding-checkpoint chain.

## Sources, inventory and coverage gate

The ID source is the local workbook
`docs/papers/Tastekin_2025_bioRxiv_v2_SupplTable2_GRN_MN_body_IDs.xlsx`,
sheet `MNs`, exactly the `Connectome = FAFB – Flywire` rows.
This is bioRxiv v2 Supplemental table 2, corresponding to Table S1 of
[Tastekin et al., Cell (2026)](https://doi.org/10.1016/j.cell.2026.08.016);
see the existing [cell-set cross-check](cell_set_crosscheck.md).
The source workbook stays local/gitignored.

[The new ID inventory](../data/mn_readout_ids.json) preserves every selected
row's `Body_ID`, `Root_Side`, `Type` and `Target_Muscle` and adds
`in_v783`. IDs are decimal strings, never converted through floating point.
The source's literal `Unknown` target muscles remain `Unknown`.
There are 66 distinct neurons, 24 types and 47 observed type/side groups; all
66 IDs are in the model's 138,639-neuron v783 completeness index.
Uneven source counts are preserved (for example MNx01 has three R rows and no
L row); an absent source group is not fabricated as a silent neuron.

| Source | SHA-256 |
|---|---|
| XLSX | `7b28d5f3ae45d68c510b8a3616700f0df2a5a6f2e2d2dba490d172939f2b64c9` |
| `vendor/fly-brain/data/2025_Completeness_783.csv` | `52b0ac6094cd32c546f8d4c341e094376f48f4e791f8db9b166de5dff8199ea4` |

The 400 baseline raw spike tables are
`results/replay/G_s{sugar}_b{bitter}_w{water}_i{ir94e}.npz`, with
`results/replay/run_meta.json`; see [the replay producer](../scripts/run_replay.py)
and [grid provenance](grid_provenance.md).
They are not the compact site's neuron subset and not the separate silencing
replays. The recorded run commit is
`e27e528e62905989aaa62171f37b569d3fcaf4c4`, run on 2026-09-11.
Inspection of `sim/network.py` at that commit confirms
`SpikeMonitor(neurons)` without a subset filter. `run_trial` exports all
nonempty spike trains; the NPZ is therefore sparse because silent neurons
have no rows, not because only selected neurons were monitored.

All 400 expected baseline files passed condition-index, input-Hz, seed,
finite-time/window and v783-membership checks. Their 7,460,121 spike rows
match the run metadata total. Of the 66 monitored MNs, 40 spike in at least
one cell and 26 never spike (including all six CEMs).
**Missing monitored MNs: none.** Zero-spike MNs must not be called missing
or judged by membership in the compact site's replay index.

### Source target-muscle labels

Throughout this report, MN type names refer only to the literal `Target_Muscle`
values below; no functional descriptions are inferred from another source.
These values are copied from the XLSX `MNs` sheet / FlyWire rows, with the
source filename, sheet and SHA-256 cited in [the extracted inventory](../data/mn_readout_ids.json).
`Unknown` is the source value, not an omitted annotation.

| MN type | XLSX `Target_Muscle` |
|---|---|
| CEM | `Crop Entry` |
| MN1 | `1` |
| MN10 | `10` |
| MN11D | `11D` |
| MN11V | `11V` |
| MN12D | `12D` |
| MN13 | `13` |
| MN2Da | `2D` |
| MN2Db | `Unknown` |
| MN2V | `2V` |
| MN3L | `3L` |
| MN3M | `3M` |
| MN4a | `4` |
| MN4b | `Unknown` |
| MN5 | `5` |
| MN6 | `6` |
| MN7 | `7` |
| MN8 | `8` |
| MN9 | `9` |
| MNx01 | `Unknown` |
| MNx02 | `Unknown` |
| MNx03 | `Unknown` |
| MNx04 | `Unknown` |
| MNx05 | `Unknown` |

MN9 L/R in C2 retain the frozen protocol's side convention, not the XLSX
`Root_Side` convention described below. Both MN9s have target `9`; MN11D
has `11D`, MN11V has `11V`, and all six CEMs have `Crop Entry`.

### MN9 sanity: an important seed distinction

Frozen left MN9 is `720575940660219265`; frozen right MN9 is
`720575940618238523`. The spreadsheet labels these `Root_Side = R`
and `L`, respectively. Side exports retain the spreadsheet convention;
the reference always uses the frozen left ID, not the spreadsheet's L row.

The replay is an extra trial, with seed
`20260910 + 700000 + global_index` (20960910 through 20961309).
It was **not one of the lookup table's 30 trials**. The published grid used
the historical batch-40 rule
`20260910 + (global_index % 40) * 1000 + trial_index`, for trial indices
0–29; see [the documented seed history](grid_provenance.md).
There is no matching lookup-trial seed, and the lookup table stores means
and standard deviations, not individual trial observations.

Consequently, equality to a lookup-table trial value cannot be tested.
The exact same-trial sanity that can be tested passed in every cell:
raw left and right MN9 spike counts, first-spike latencies and entire
spike-time lists agree with the frozen AFR1 replay headers (at the pack's
0.1 ms precision); the raw left count also agrees with the replay manifest.
Raw timestamps are retained for the analysis. Lookup means/std are exported
alongside the replay reference for context, never substituted for it.
For example, sugar-high alone has raw left MN9 68 Hz versus the lookup
30-trial mean 74.633 Hz; these are different trial samples, not a sanity failure.

The lookup cells hash remains
`2e08e5f6b3738ce7eb5150b117a0671f561ab8543568e012332ef6c2dc4df15c`.
Raw-run protocol/cell-set/grid hashes also match the frozen files.

## C1 reproduction and measurement choices

With the local source workbook, vendor completeness CSV and existing raw
replays present, run these separate PowerShell commands:

```powershell
.\.venv\Scripts\python.exe -B scripts/build_mn_readout_ids.py
.\.venv\Scripts\python.exe -B scripts/mn_readouts_from_replays.py
.\.venv\Scripts\python.exe -B -m unittest tests.test_mn_readout_ids tests.test_mn_readouts
```

Neither script imports or starts Brian2. Analysis artifacts stay under
gitignored `results/mn-readouts/c1/`; no source replay is rewritten.

| Artifact | Content |
|---|---|
| `neuron_readouts.csv` | 26,400 neuron/cell rows with source identity, count, Hz and first-spike ms |
| `type_side_readouts.csv` | 18,800 type/side/cell rows, using source sides |
| `type_readouts.csv` | 9,600 type/cell rows |
| `correlations.csv` | All 24 type correlations and active-cell counts |
| `discordant_cells.csv` | Every exact on/silent disagreement |
| `disagreements.json` | Up to three strongest cells per type and direction |
| `summary.json` | All 400 cell summaries, axes, coverage/sanity and input hashes/seeds |
| `screen_tables.md` | Computed tables reproduced below |

Our analysis choices, not extra model outputs:

- Rate is spike count divided by the full 1 s trial, with no burn-in removed.
  For a type or type/side group, the displayed rate is the **mean per member
  neuron, including silent members**; summed rate and spike count are also
  exported. Unequal type sizes therefore do not inflate displayed rates.
- First-spike latency is measured from trial start in the interval
  `[0, 1000)` ms. For groups it is the earliest spike of any member,
  not the mean latency of the firing members. All-silent groups have
  `null` in JSON and an empty latency field in CSV (not zero milliseconds).
- MN9 in a type row means the two-neuron mean; the separately labelled
  frozen-left reference is one neuron. MN11D/MN11V each contain two neurons
  and CEM contains six.
- Spearman uses average ranks for ties across **400 unique physical grid
  cells**, including zero-rate cells. An all-constant type has undefined
  correlation (em dash), not zero correlation. No p-values are inferred.
- Water `low` and `medium` both mean 60 Hz in the frozen grid. They appear
  twice in the five-level water display, but are the same replay and count
  only once in the 400-cell analysis.
- Disagreement means exactly one readout is silent and the other fires.
  We rank the positive readout's rate to find the strongest examples;
  ties are ordered by cell ID. This ranking is not a behavioral threshold.

## C1 screen

All table entries are output Hz (not stimulus Hz), rounded to at most three
decimals. Column headers give the designed GRN input level/rate.
Unmentioned inputs are none/0 Hz. These are single recorded trials, not
30-trial means.

<!-- BEGIN COMPUTED C1 TABLES -->
### Sugar only

| MN type (mean Hz per neuron) | none (0 Hz) | low (60 Hz) | medium (80 Hz) | high (120 Hz) | very_high (200 Hz) |
|---|---:|---:|---:|---:|---:|
| Frozen left MN9 (reference) | 0 | 24 | 58 | 68 | 93 |
| CEM | 0 | 0 | 0 | 0 | 0 |
| MN1 | 0 | 0 | 0 | 0 | 0 |
| MN10 | 0 | 2 | 40 | 36.333 | 54.667 |
| MN11D | 0 | 5.5 | 93.5 | 87.5 | 122 |
| MN11V | 0 | 2 | 36.5 | 34.5 | 51.5 |
| MN12D | 0 | 0 | 0 | 0 | 0 |
| MN13 | 0 | 0 | 0.5 | 1.5 | 5.5 |
| MN2Da | 0 | 0 | 2.5 | 4.5 | 11 |
| MN2Db | 0 | 0 | 0 | 0 | 0 |
| MN2V | 0 | 0 | 0 | 0 | 0 |
| MN3L | 0 | 0.25 | 0.5 | 0 | 0 |
| MN3M | 0 | 0 | 0 | 0 | 0 |
| MN4a | 0 | 3.5 | 10.5 | 12.5 | 16.75 |
| MN4b | 0 | 12.5 | 39 | 46 | 68.5 |
| MN5 | 0 | 0 | 0 | 0 | 0 |
| MN6 | 0 | 9.5 | 25 | 28.5 | 34.5 |
| MN7 | 0 | 18.75 | 29.5 | 38 | 38.5 |
| MN8 | 0 | 15.5 | 34 | 48.5 | 64.5 |
| MN9 | 0 | 20.5 | 50 | 59 | 79 |
| MNx01 | 0 | 2.333 | 41 | 40.667 | 60.333 |
| MNx02 | 0 | 0 | 0 | 0 | 0 |
| MNx03 | 0 | 0 | 0 | 0 | 0 |
| MNx04 | 0 | 0 | 0 | 0 | 0 |
| MNx05 | 0 | 0 | 0 | 0 | 0 |

### Bitter at sugar high (120 Hz)

| MN type (mean Hz per neuron) | none (0 Hz) | low (30 Hz) | medium (60 Hz) | high (100 Hz) | very_high (160 Hz) |
|---|---:|---:|---:|---:|---:|
| Frozen left MN9 (reference) | 68 | 57 | 21 | 4 | 1 |
| CEM | 0 | 0 | 0 | 0 | 0 |
| MN1 | 0 | 0 | 0 | 0 | 0 |
| MN10 | 36.333 | 31 | 36.667 | 24.667 | 0 |
| MN11D | 87.5 | 79.5 | 87.5 | 64.5 | 0 |
| MN11V | 34.5 | 33 | 40.5 | 26.5 | 0 |
| MN12D | 0 | 0 | 0 | 0.5 | 0 |
| MN13 | 1.5 | 4 | 0 | 0 | 0 |
| MN2Da | 4.5 | 4 | 0 | 0 | 0 |
| MN2Db | 0 | 0 | 0 | 0 | 0 |
| MN2V | 0 | 0 | 0 | 0 | 0 |
| MN3L | 0 | 0 | 0.5 | 0 | 0 |
| MN3M | 0 | 0 | 0 | 0 | 0 |
| MN4a | 12.5 | 9.25 | 1.5 | 0 | 0 |
| MN4b | 46 | 34 | 7 | 1 | 0 |
| MN5 | 0 | 0 | 0 | 0 | 0 |
| MN6 | 28.5 | 21 | 6 | 1.5 | 0 |
| MN7 | 38 | 20.25 | 2 | 0 | 0 |
| MN8 | 48.5 | 34 | 10 | 0.5 | 0 |
| MN9 | 59 | 48 | 18 | 3 | 0.5 |
| MNx01 | 40.667 | 34 | 36.667 | 26.667 | 0 |
| MNx02 | 0 | 0 | 0 | 0 | 0 |
| MNx03 | 0 | 0 | 0 | 0 | 0 |
| MNx04 | 0 | 0 | 0 | 0 | 0 |
| MNx05 | 0 | 0 | 0 | 0 | 0 |

### Water at sugar none

| MN type (mean Hz per neuron) | none (0 Hz) | low (60 Hz) | medium (60 Hz) | high (180 Hz) | very_high (240 Hz) |
|---|---:|---:|---:|---:|---:|
| Frozen left MN9 (reference) | 0 | 0 | 0 | 21 | 48 |
| CEM | 0 | 0 | 0 | 0 | 0 |
| MN1 | 0 | 0 | 0 | 0 | 0 |
| MN10 | 0 | 0 | 0 | 0 | 1.333 |
| MN11D | 0 | 0 | 0 | 5.5 | 19 |
| MN11V | 0 | 0 | 0 | 0 | 2 |
| MN12D | 0 | 0 | 0 | 0 | 1 |
| MN13 | 0 | 0 | 0 | 0 | 0 |
| MN2Da | 0 | 0 | 0 | 2.5 | 5.5 |
| MN2Db | 0 | 0 | 0 | 0 | 0 |
| MN2V | 0 | 0 | 0 | 0 | 0 |
| MN3L | 0 | 0 | 0 | 0.75 | 0.25 |
| MN3M | 0 | 0 | 0 | 0.5 | 0 |
| MN4a | 0 | 0 | 0 | 0.25 | 4.5 |
| MN4b | 0 | 0 | 0 | 4 | 20 |
| MN5 | 0 | 0 | 0 | 0 | 0 |
| MN6 | 0 | 0 | 0 | 8.5 | 22.5 |
| MN7 | 0 | 0 | 0 | 1 | 10 |
| MN8 | 0 | 0 | 0 | 3 | 18 |
| MN9 | 0 | 0 | 0 | 13 | 35.5 |
| MNx01 | 0 | 0 | 0 | 0 | 1.667 |
| MNx02 | 0 | 0 | 0 | 0 | 0 |
| MNx03 | 0 | 0 | 0 | 0 | 0 |
| MNx04 | 0 | 0 | 0 | 0 | 0 |
| MNx05 | 0 | 0 | 0 | 0 | 0 |

### Ir94e at sugar high (120 Hz)

| MN type (mean Hz per neuron) | none (0 Hz) | low (60 Hz) | medium (120 Hz) | high (200 Hz) |
|---|---:|---:|---:|---:|
| Frozen left MN9 (reference) | 68 | 40 | 14 | 9 |
| CEM | 0 | 0 | 0 | 0 |
| MN1 | 0 | 0 | 0 | 0 |
| MN10 | 36.333 | 32.333 | 28.333 | 34.667 |
| MN11D | 87.5 | 83 | 76.5 | 90.5 |
| MN11V | 34.5 | 31.5 | 27 | 33 |
| MN12D | 0 | 0 | 0 | 0.25 |
| MN13 | 1.5 | 1 | 0 | 0.5 |
| MN2Da | 4.5 | 3.5 | 1 | 1 |
| MN2Db | 0 | 0 | 0 | 0 |
| MN2V | 0 | 0 | 0 | 0 |
| MN3L | 0 | 0 | 0 | 0 |
| MN3M | 0 | 0 | 0 | 0 |
| MN4a | 12.5 | 8.25 | 3.25 | 2.75 |
| MN4b | 46 | 32.5 | 11.5 | 10 |
| MN5 | 0 | 0 | 0 | 0 |
| MN6 | 28.5 | 17.5 | 5 | 3 |
| MN7 | 38 | 10.75 | 1.25 | 0 |
| MN8 | 48.5 | 19.5 | 3 | 1 |
| MN9 | 59 | 35.5 | 11 | 8 |
| MNx01 | 40.667 | 33.667 | 31.667 | 35.667 |
| MNx02 | 0 | 0 | 0 | 0 |
| MNx03 | 0 | 0 | 0 | 0 |
| MNx04 | 0 | 0 | 0 | 0 |
| MNx05 | 0 | 0 | 0 | 0 |

### Ir94e alone (sugar, bitter and water none)

| MN type (mean Hz per neuron) | none (0 Hz) | low (60 Hz) | medium (120 Hz) | high (200 Hz) |
|---|---:|---:|---:|---:|
| Frozen left MN9 (reference) | 0 | 0 | 0 | 0 |
| CEM | 0 | 0 | 0 | 0 |
| MN1 | 0 | 0 | 0 | 0 |
| MN10 | 0 | 0 | 0 | 1 |
| MN11D | 0 | 0 | 0 | 3 |
| MN11V | 0 | 0 | 0 | 1 |
| MN12D | 0 | 0 | 0 | 0 |
| MN13 | 0 | 0 | 0 | 0 |
| MN2Da | 0 | 0 | 0 | 0 |
| MN2Db | 0 | 0 | 0 | 0 |
| MN2V | 0 | 0 | 0 | 0 |
| MN3L | 0 | 0 | 0 | 0 |
| MN3M | 0 | 0 | 0 | 0 |
| MN4a | 0 | 0 | 0 | 0 |
| MN4b | 0 | 0 | 0 | 0 |
| MN5 | 0 | 0 | 0 | 0 |
| MN6 | 0 | 0 | 0 | 0 |
| MN7 | 0 | 0 | 0 | 0 |
| MN8 | 0 | 0 | 0 | 0 |
| MN9 | 0 | 0 | 0 | 0 |
| MNx01 | 0 | 0 | 0 | 1 |
| MNx02 | 0 | 0 | 0 | 0 |
| MNx03 | 0 | 0 | 0 | 0 |
| MNx04 | 0 | 0 | 0 | 0 |
| MNx05 | 0 | 0 | 0 | 0 |

### Across all 400 unique cells

| MN type | Neurons | Active cells | Spearman vs frozen left MN9 |
|---|---:|---:|---:|
| CEM | 6 | 0 | — |
| MN1 | 4 | 0 | — |
| MN10 | 3 | 264 | 0.873 |
| MN11D | 2 | 261 | 0.91 |
| MN11V | 2 | 240 | 0.892 |
| MN12D | 4 | 71 | 0.375 |
| MN13 | 2 | 30 | 0.29 |
| MN2Da | 2 | 267 | 0.797 |
| MN2Db | 2 | 26 | -0.202 |
| MN2V | 2 | 0 | — |
| MN3L | 4 | 11 | 0.081 |
| MN3M | 2 | 1 | 0.03 |
| MN4a | 4 | 168 | 0.912 |
| MN4b | 2 | 194 | 0.948 |
| MN5 | 2 | 0 | — |
| MN6 | 2 | 205 | 0.964 |
| MN7 | 4 | 150 | 0.876 |
| MN8 | 2 | 194 | 0.933 |
| MN9 | 2 | 240 | 0.999 |
| MNx01 | 3 | 247 | 0.886 |
| MNx02 | 2 | 0 | — |
| MNx03 | 4 | 0 | — |
| MNx04 | 2 | 0 | — |
| MNx05 | 2 | 0 | — |

### Strongest on/silent disagreements

Silence means exactly zero spikes in this trial; 'strongest' ranks the active readout's Hz, without a behavioral threshold. Up to three cells per direction/type are in `disagreements.json`; all discordant cells are in the CSV. Cell IDs below omit the common `G_` prefix.

| MN type | Highest left MN9 while type silent (Hz; cell) | Highest type mean while left MN9 silent (Hz; cell) |
|---|---|---|
| CEM | 110; `svery_high_bnone_wvery_high_inone` | none |
| MN1 | 110; `svery_high_bnone_wvery_high_inone` | none |
| MN10 | 58; `snone_blow_wvery_high_inone` | 21.333; `svery_high_bhigh_wlow_ihigh` |
| MN11D | 7; `snone_bhigh_wvery_high_inone` | 52; `svery_high_bhigh_wlow_ihigh` |
| MN11V | 58; `snone_blow_wvery_high_inone` | 18; `svery_high_bhigh_wlow_ihigh` |
| MN12D | 110; `svery_high_bnone_wvery_high_inone` | 0.5; `slow_bnone_wnone_ihigh` |
| MN13 | 110; `svery_high_bnone_wvery_high_inone` | none |
| MN2Da | 24; `slow_bnone_wnone_inone` | 11.5; `svery_high_bvery_high_wvery_high_ihigh` |
| MN2Db | 110; `svery_high_bnone_wvery_high_inone` | 3; `snone_bmedium_wvery_high_ihigh` |
| MN2V | 110; `svery_high_bnone_wvery_high_inone` | none |
| MN3L | 110; `svery_high_bnone_wvery_high_inone` | none |
| MN3M | 110; `svery_high_bnone_wvery_high_inone` | none |
| MN4a | 24; `snone_bmedium_wvery_high_inone` | none |
| MN4b | 11; `smedium_bmedium_wvery_high_ihigh` | none |
| MN5 | 110; `svery_high_bnone_wvery_high_inone` | none |
| MN6 | 6; `snone_bmedium_wvery_high_ilow` | none |
| MN7 | 32; `svery_high_bhigh_wvery_high_ilow` | none |
| MN8 | 16; `slow_bhigh_wvery_high_inone` | 3.5; `snone_bnone_wvery_high_ihigh` |
| MN9 | none | none |
| MNx01 | 58; `snone_blow_wvery_high_inone` | 20.667; `svery_high_bhigh_wlow_ihigh` |
| MNx02 | 110; `svery_high_bnone_wvery_high_inone` | none |
| MNx03 | 110; `svery_high_bnone_wvery_high_inone` | none |
| MNx04 | 110; `svery_high_bnone_wvery_high_inone` | none |
| MNx05 | 110; `svery_high_bnone_wvery_high_inone` | none |

<!-- END COMPUTED C1 TABLES -->

### Latency examples

Earliest group spike, ms from trial start; `none` means no spike during the
1 s window. Full individual and type/side latencies are in the CSVs.

| Inputs (sugar, bitter, water, Ir94e), Hz | Frozen left MN9 | MN11D | MN11V | CEM |
|---|---:|---:|---:|---|
| (60, 0, 0, 0) | 137.8 | 758.5 | 762.8 | none |
| (80, 0, 0, 0) | 70.4 | 90.3 | 97.2 | none |
| (120, 0, 0, 0) | 43.5 | 45.3 | 49 | none |
| (120, 100, 0, 0) | 146 | 48.2 | 52.1 | none |
| (200, 100, 60, 200) | none | 42.1 | 47.9 | none |
| (0, 0, 0, 200) | none | 328.3 | 330.3 | none |

The bitter-high example has the earliest MN11 spikes before the first
left-MN9 spike. That is a screen observation, not proof of muscle movement,
a causal ordering, or a validated behavioral checkpoint.

### Two questions, one sentence each

**Does bitter suppress MN11 and CEM the way it suppresses MN9?** Not uniformly:
at sugar 120 Hz and bitter 100 Hz, left MN9 falls from 68 to 4 Hz while
MN11D/MN11V remain at 64.5/26.5 Hz (versus 87.5/34.5 without bitter), both
MN11 types are silent at bitter 160 Hz, and CEM suppression cannot be
assessed because CEM is already silent without bitter.

**Does the Ir94e set drive CEM when sugar is none?** No CEM spikes were
observed under this design at any Ir94e-only level (0/60/120/200 Hz), or
indeed anywhere in the 400-cell screen, despite all six CEMs being monitored.

### Interpretation and caveats

**n = 1 trial per cell: this is a screen, not a characterisation.** Different
grid cells use different extra replay seeds; apparent dose steps, reversals
and first-spike differences may reflect trial variability. Silence means no
spike in this 1 s sample, not an estimated zero firing probability. The 400
conditions are a designed stimulus grid, not 400 independent biological
replicates. Correlation across that grid does not establish causation,
a serial chain, muscle contraction, intake, or behavior.

The frozen Ir94e set includes seven LB2 cells alongside eleven LB1e cells
([OQ-7](open_questions.md#oq-7-25-of-101-frozen-v1-grns-fall-outside-the-mapped-tastekin-subtypes-2026-09-12)).
This is not an isolated LB2 experiment. CEM silence in C1 does not rule out
activity with other stimuli or backgrounds. The zero-basal-activity design
and unchanged mixed input set limit that conclusion; neither connectivity
remapping nor tonic background nor pharyngeal stimulation was performed.
C2b below audits structural input without adding stimulation or predicting firing.

A checkpoint-chain candidate is therefore worth testing at the **MN9 versus
MN11** distinction: overall correlations are high but individual readouts
can separate. MN4a/MN6/MN8 track left MN9 closely in this screen (rho
0.912/0.964/0.933), making them less urgent than MN11D/V for a first
replication. A CEM checkpoint is not supported by an observable response
under the current design. Adding one now would be our unvalidated decision,
not something established by the model.

## C1 selection rationale (historical; all thirteen approved for C2)

The C1 proposal below contained ten primary and three optional cells; the
owner subsequently approved all thirteen for C2 (390 trials). Coordinates
are (sugar, bitter, water, Ir94e) input Hz, uniquely identifying frozen cells.
Numbers in the rationale are the historical one-trial C1 observations.

| Priority | Proposed cells (Hz) | What to check |
|---|---|---|
| Primary | (0,0,0,0), (0,0,0,200) | Negative control and weak Ir94e-only MN11 firing; CEM null |
| Primary | (120,0,0,0), (120,60,0,0), (120,100,0,0), (120,160,0,0) | MN9/MN11 bitter-response separation and maximal-drive suppression |
| Primary | (120,0,0,200) | Ir94e lowers left MN9 to 9 Hz while MN11D/V remain 90.5/33 Hz |
| Primary | (0,0,240,0), (0,30,240,0) | Left MN9 active with weak/silent MN11V (48/58 versus 2/0 Hz) |
| Primary | (200,100,60,200) | Strongest MN11D/V firing with silent left MN9 (52/18 versus 0 Hz) |
| Optional | (200,100,0,200) | Paired water-none comparison for that disagreement |
| Optional | (60,0,0,0), (80,0,0,0) | Steep sugar response and long low-sugar MN11 onset |

Readouts: both MN9 neurons, both MN11D, both MN11V, and all six CEM
neurons (12 individual neurons). Preserve individual/source-side rates and
latencies, including censored/no-spike trials, before type aggregation.
MN4a/MN6/MN8 are optional later additions only if requested, not an expansion
of C2 here.

The authorised C2 uses the selected cells' **published grid trial
seeds**, not the extra replay seeds or today's corrected default seed rule,
to support a matched MN9 check. It uses a new, referencing protocol;
it does not edit the frozen protocol or feed results into the lookup table.

## C1 verification

The extraction was independently cross-checked against a second raw-replay
calculation: all 400 left-MN9 rates, 9,600 type rates/latencies, 18,800
type/side rates/latencies and 26,400 individual count/rate/latency triples
match exactly; all 24 correlations agree to floating-point precision.
All displayed axis values and the 93 saved top-disagreement rows also match.
Synthetic tests exercise exact 64-bit IDs, silence, latency, grouping, tied
ranks, malformed inputs and same-trial MN9 mismatch detection.

## C2: thirteen-cell 30-trial rerun

All thirteen owner-selected cells were rerun for 30 trials each, recording
the twelve source neurons in [the new referencing protocol](../data/stim_protocol_mn.json):
MN9 L/R (`Target_Muscle = 9`), MN11D (`11D`, two neurons), MN11V
(`11V`, two), and CEM (`Crop Entry`, six), from the
[XLSX MNs/FlyWire/Target_Muscle extract](../data/mn_readout_ids.json).
These target labels are source values, not functional descriptions supplied by us.

[The C2 runner](../sim/run_mn_readouts.py) reads the frozen base protocol
unchanged; its network, four-channel order (sugar, bitter, water, ir94e),
101 Poisson entries, GRN sets, 1000 ms duration and 0.1 ms step are unchanged.
No added stimulus, silencing or tonic background is introduced.
The historical published seed is `20260910 + 1000 * (global_index % 40) + trial`,
with the original canonical grid index and trial 0–29, not the thirteen-cell
selection index or today's v2 default.

Execution: WSL2 `flybrain`, Brian2 2.9.0 / existing cython network,
13 workers, 390 completed trials, 250.8 s; completed 2026-09-13.
Every bilateral MN9 spike train matched its original
`results/grid/full/<cell_id>.parquet` trial exactly. Those original
parquets have no seed column or completion ledger; their seed identity is
reconstructed from the historical run's batch-40 provenance. The new C2
ledgers explicitly record all completed trials and seeds, including silent trials.

The original grid parquets also contain the other MNs: an independent
comparison found all 4,680 twelve-neuron/trial spike trains and all 57,823
saved MN spikes identical in the fresh rerun. This reproduces the published
grid's original trial series; it does **not** create a second independent
set of 30 samples or increase n to 60.

### C2 statistics and censoring

MN9 L/R are individual rates; MN11D/V and CEM are per-trial means over their
2/2/6 neurons, including silent members, followed by the mean and SD across
30 trials. SD uses `ddof=0`, matching the frozen grid, rather than an
unlabelled switch to sample SD. CEM is zero in every neuron/trial.

Latencies are from trial start; each group uses the earliest member spike
in each trial. The displayed median is conditional on that group firing,
always accompanied by the number of active trials out of 30. Silent trials
are right-censored at the 1 s recording window, not given a latency of zero
or treated as known 1000 ms spike times. These medians are not unconditional
population medians and should not be compared without their active counts.

Bitter ratios divide the mean rate at each bitter level by the no-bitter
mean at sugar 120 Hz, water/Ir94e zero; they are **not** averages of
trial-wise ratios. The four bitter cells have different seed blocks and
are not shared-seed paired contrasts. Only bitter 0/60/100/160 Hz were
selected for C2; the unselected 30 Hz level remains C1-only.

<!-- BEGIN COMPUTED C2 TABLES -->
### C2 rates (mean ± population SD, Hz; 30 trials)

| Inputs (sugar,bitter,water,Ir94e), Hz | MN9 L | MN9 R | MN11D | MN11V | CEM |
|---|---:|---:|---:|---:|---:|
| (0, 0, 0, 0) | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| (0, 0, 0, 200) | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.200 ± 0.542 | 0.083 ± 0.227 | 0.000 ± 0.000 |
| (120, 0, 0, 0) | 74.633 ± 4.476 | 54.700 ± 4.713 | 92.733 ± 8.514 | 37.383 ± 3.991 | 0.000 ± 0.000 |
| (120, 60, 0, 0) | 23.700 ± 5.843 | 16.367 ± 3.167 | 84.767 ± 8.925 | 35.000 ± 4.109 | 0.000 ± 0.000 |
| (120, 100, 0, 0) | 1.700 ± 1.509 | 1.667 ± 1.193 | 61.383 ± 13.992 | 24.950 ± 5.508 | 0.000 ± 0.000 |
| (120, 160, 0, 0) | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.917 ± 3.099 | 0.317 ± 1.228 | 0.000 ± 0.000 |
| (120, 0, 0, 200) | 8.600 ± 4.302 | 4.267 ± 3.245 | 73.633 ± 10.182 | 28.083 ± 5.545 | 0.000 ± 0.000 |
| (0, 0, 240, 0) | 45.800 ± 5.338 | 20.400 ± 4.055 | 21.483 ± 3.736 | 1.800 ± 1.646 | 0.000 ± 0.000 |
| (0, 30, 240, 0) | 46.533 ± 5.506 | 19.567 ± 4.047 | 20.467 ± 2.607 | 1.467 ± 1.354 | 0.000 ± 0.000 |
| (200, 100, 60, 200) | 0.633 ± 0.875 | 0.067 ± 0.359 | 42.650 ± 13.038 | 14.000 ± 5.465 | 0.000 ± 0.000 |
| (200, 100, 0, 200) | 0.233 ± 0.496 | 0.000 ± 0.000 | 29.250 ± 12.472 | 9.050 ± 5.037 | 0.000 ± 0.000 |
| (60, 0, 0, 0) | 34.667 ± 6.052 | 27.467 ± 4.478 | 35.167 ± 14.244 | 11.783 ± 5.307 | 0.000 ± 0.000 |
| (80, 0, 0, 0) | 58.033 ± 5.376 | 43.800 ± 5.147 | 70.650 ± 8.020 | 25.083 ± 3.645 | 0.000 ± 0.000 |

### C2 first-spike latency medians (ms; active trials / 30)

| Inputs (sugar,bitter,water,Ir94e), Hz | MN9 L | MN9 R | MN11D | MN11V | CEM |
|---|---:|---:|---:|---:|---:|
| (0, 0, 0, 0) | none (0/30) | none (0/30) | none (0/30) | none (0/30) | none (0/30) |
| (0, 0, 0, 200) | none (0/30) | none (0/30) | 339.25 (4/30) | 343.80 (4/30) | none (0/30) |
| (120, 0, 0, 0) | 35.80 (30/30) | 41.85 (30/30) | 44.40 (30/30) | 48.75 (30/30) | none (0/30) |
| (120, 60, 0, 0) | 40.95 (30/30) | 63.10 (30/30) | 47.45 (30/30) | 51.80 (30/30) | none (0/30) |
| (120, 100, 0, 0) | 47.70 (22/30) | 292.50 (25/30) | 63.05 (30/30) | 66.85 (30/30) | none (0/30) |
| (120, 160, 0, 0) | none (0/30) | none (0/30) | 607.00 (5/30) | 689.75 (2/30) | none (0/30) |
| (120, 0, 0, 200) | 134.85 (30/30) | 354.00 (29/30) | 74.50 (30/30) | 80.00 (30/30) | none (0/30) |
| (0, 0, 240, 0) | 54.50 (30/30) | 76.80 (30/30) | 57.20 (30/30) | 76.75 (22/30) | none (0/30) |
| (0, 30, 240, 0) | 51.40 (30/30) | 78.35 (30/30) | 63.25 (30/30) | 75.30 (23/30) | none (0/30) |
| (200, 100, 60, 200) | 416.50 (14/30) | 743.60 (1/30) | 57.20 (30/30) | 69.90 (30/30) | none (0/30) |
| (200, 100, 0, 200) | 460.50 (6/30) | none (0/30) | 66.90 (30/30) | 131.90 (29/30) | none (0/30) |
| (60, 0, 0, 0) | 94.75 (30/30) | 92.55 (30/30) | 126.75 (30/30) | 156.40 (30/30) | none (0/30) |
| (80, 0, 0, 0) | 49.35 (30/30) | 53.80 (30/30) | 68.20 (30/30) | 71.80 (30/30) | none (0/30) |

### Bitter / no-bitter mean-rate ratios (sugar 120 Hz; water/Ir94e 0)

| Bitter input Hz | MN9 L | MN9 R | MN11D | MN11V |
|---:|---:|---:|---:|---:|
| 0 | 1.000000 | 1.000000 | 1.000000 | 1.000000 |
| 60 | 0.317552 | 0.299208 | 0.914091 | 0.936246 |
| 100 | 0.022778 | 0.030469 | 0.661934 | 0.667410 |
| 160 | 0.000000 | 0.000000 | 0.009885 | 0.008471 |
<!-- END COMPUTED C2 TABLES -->

### C2 finding and limits

The bitter veto acts on MN9 before it acts comparably on MN11D/V **along
the increasing bitter-drive axis**, not as a demonstrated temporal or
causal sequence: at bitter 60 Hz, MN9 L/R retain 31.8%/29.9% of baseline
while MN11D/V retain 91.4%/93.6%; at 100 Hz the values are 2.28%/3.05%
versus 66.19%/66.74%. At 160 Hz both MN9s are silent in all 30 trials,
whereas MN11D/V retain 0.989%/0.847% of baseline, firing in 5/30 and 2/30
trials respectively.

C2 also qualifies the C1 on/silent examples: at (200,100,60,200) Hz,
left MN9 averages 0.633 Hz and fires in 14/30 trials, versus MN11D/V means
42.650/14.000 Hz with both active in 30/30; at (0,30,240,0), MN11V is
weak (1.467 Hz) rather than invariably silent (23/30 active trials).
Ir94e alone at 200 Hz gives MN11D/V means 0.200/0.083 Hz, each active
in 4/30 trials, and no CEM spikes. The single C1 samples must not be
substituted for these 30-trial estimates.

Distinct MN9 and MN11 readouts are supported under this design; a serial
checkpoint chain, muscle movement or a product score is not established.
CEM activation was not observed in any of the 390 C2 trials; this does not
rule out other inputs/backgrounds. The new pharyngeal comparison below is
structural only, not a pharyngeal stimulation experiment.

### C2 reproduction, artifacts and provenance

```powershell
.\.venv\Scripts\python.exe -B -m sim.run_mn_readouts --check-design
wsl.exe --cd /mnt/d/WhatDoesTheFlyEat -e bash -lc 'exec ~/miniforge3/bin/conda run -n flybrain --no-capture-output python -B -m sim.run_mn_readouts --n-proc 13'
.\.venv\Scripts\python.exe -B -m unittest tests.test_mn_c2
```

Outputs are local/gitignored `results/mn-readouts/c2/`: one NPZ and
completion/identity JSON per cell, 4,680 individual trial rows in
`individual_trials.csv`, 1,950 grouped trial rows in `group_trials.csv`,
`summary.json`, `bitter_ratios.csv`, `tables.md` and `run_meta.json`.
The NPZs save only these twelve MNs after full-network simulation; silent
neurons/trials remain explicit in the CSVs and ledgers. A repeat invocation
reuses only complete outputs with matching identity/source/spike hashes;
it refuses to overwrite incomplete or mismatched outputs.

The run recorded HEAD `f9f8928aa50aaf96c4135f0e9955358b412410d2`, before
the new C2 files were committed; that HEAD alone is not the executed-source
identity. `run_meta.json` captures the actual source bytes, including:

| Executed source | SHA-256 |
|---|---|
| `data/stim_protocol_mn.json` | `c68f3a8019fedd7e681ff76c0013da7204f01431410adb56e146aa784350f1cf` |
| `sim/run_mn_readouts.py` | `3fa47a1dcc950a5440a2b942e6f4c1b862e5009710474df95717a644d699b307` |
| Unchanged `sim/network.py` | `eee33ef855203a47e03920b56b4aba98551cc400ab22107ebb91edc385475ae7` |

The same metadata records frozen protocol/cell/grid/inventory/connectome
hashes; each cell records its original grid-parquet hash and thirty seeds.
Independent verification matched all 4,680 individual and 1,950 grouped
rates/latencies, all 65 mean/SD/median/active-count summaries, all sixteen
ratio values, all 390 seeds, and every source identity/target-muscle field.

## C2b: CEM input connectivity (no simulation)

CEM's source `Target_Muscle` is `Crop Entry` for all six cells
([XLSX MN-row extract](../data/mn_readout_ids.json), `MNs` sheet /
FlyWire / `Target_Muscle`). L/R in the table are XLSX `Root_Side`.
Pharyngeal sources are exactly the 50 `GRNs`-sheet FlyWire rows typed
PhG1–16; all 50 and all six CEM IDs are in v783. The four labellar sets
are unchanged from `data/cells.json`.

Source graph: `vendor/fly-brain/data/2025_Connectivity_783.parquet`,
named by the frozen protocol, 15,091,983 directed-pair rows, SHA-256
`efeb23fb99098e9c390f6869969b2a121a2ee92c833cfc45ecb2c1d8e1af0347`.
Counts use the unsigned `Connectivity` column, including both signs of
`Excitatory`. They are structural counts, not rates or effective weights.

For a source set S, any intermediate M and selected CEM target(s) T,
two-hop means exactly S→M→T. We count actual synapses on each leg
separately, once per directed edge: A counts S→M synapses and B counts
M→T synapses reachable from S. We do not multiply the two edge weights or
count a shared M→T edge repeatedly for every source reaching M.
Pooled source and target unions are recomputed; source-group rows are not
additive, and pooled first-leg counts are not sums of the six columns.

<!-- BEGIN COMPUTED CEM INPUT TABLE -->
D / A / B = direct source->CEM synapses / unique source->intermediate synapses on two-edge paths / unique intermediate->CEM synapses on those paths. The totals row instead gives unique presynaptic partners / total input synapses.

| Source (n) | 720575940620008112 (L) | 720575940625799513 (L) | 720575940640681680 (L) | 720575940621126384 (R) | 720575940621169690 (R) | 720575940628781333 (R) | All six (union) |
|---|---:|---:|---:|---:|---:|---:|---:|
| All presynaptic input: partners / synapses | 70 / 660 | 55 / 510 | 47 / 445 | 64 / 555 | 66 / 494 | 73 / 634 | 143 / 3298 |
| sugar (23) | 0 / 5 / 17 | 0 / 10 / 16 | 0 / 5 / 20 | 0 / 0 / 0 | 0 / 3 / 2 | 0 / 4 / 4 | 0 / 13 / 59 |
| bitter (42) | 0 / 15 / 5 | 0 / 119 / 5 | 0 / 1 / 2 | 0 / 1 / 2 | 0 / 0 / 0 | 0 / 70 / 14 | 0 / 189 / 28 |
| water (18) | 0 / 4 / 17 | 0 / 16 / 16 | 0 / 4 / 20 | 0 / 0 / 0 | 0 / 2 / 2 | 0 / 3 / 3 | 0 / 18 / 58 |
| ir94e (18) | 0 / 31 / 19 | 0 / 155 / 19 | 0 / 24 / 10 | 0 / 4 / 2 | 0 / 1 / 1 | 0 / 8 / 7 | 0 / 162 / 58 |
| Labellar union (101) | 0 / 55 / 31 | 0 / 300 / 26 | 0 / 34 / 29 | 0 / 5 / 2 | 0 / 6 / 3 | 0 / 85 / 24 | 0 / 382 / 115 |
| PhG1 (8) | 0 / 673 / 309 | 0 / 829 / 262 | 0 / 1044 / 241 | 0 / 820 / 276 | 0 / 1008 / 252 | 0 / 978 / 343 | 0 / 1553 / 1683 |
| PhG2 (5) | 0 / 8 / 24 | 0 / 19 / 14 | 0 / 9 / 17 | 0 / 18 / 60 | 0 / 16 / 56 | 0 / 20 / 47 | 0 / 39 / 218 |
| PhG3 (2) | 0 / 81 / 16 | 0 / 85 / 15 | 0 / 77 / 20 | 0 / 124 / 81 | 0 / 96 / 44 | 0 / 252 / 66 | 0 / 358 / 242 |
| PhG4 (4) | 0 / 23 / 48 | 0 / 27 / 67 | 0 / 25 / 42 | 0 / 26 / 45 | 0 / 34 / 30 | 0 / 68 / 51 | 0 / 99 / 283 |
| PhG5 (2) | 0 / 15 / 12 | 0 / 48 / 13 | 0 / 6 / 13 | 0 / 11 / 17 | 0 / 14 / 19 | 0 / 49 / 49 | 0 / 95 / 123 |
| PhG6 (2) | 0 / 112 / 39 | 0 / 266 / 49 | 0 / 111 / 30 | 0 / 52 / 26 | 0 / 52 / 15 | 0 / 185 / 44 | 0 / 440 / 203 |
| PhG7 (5) | 0 / 51 / 20 | 0 / 119 / 24 | 0 / 54 / 21 | 0 / 28 / 28 | 0 / 13 / 30 | 0 / 108 / 56 | 0 / 238 / 179 |
| PhG8 (4) | 0 / 7 / 13 | 0 / 24 / 14 | 0 / 26 / 25 | 0 / 33 / 44 | 0 / 47 / 46 | 0 / 79 / 67 | 0 / 112 / 209 |
| PhG9 (4) | 0 / 20 / 19 | 0 / 157 / 17 | 0 / 168 / 19 | 0 / 191 / 19 | 0 / 208 / 20 | 0 / 330 / 30 | 0 / 596 / 124 |
| PhG10 (2) | 0 / 45 / 22 | 0 / 15 / 23 | 0 / 6 / 20 | 0 / 23 / 14 | 0 / 4 / 21 | 0 / 152 / 35 | 0 / 168 / 135 |
| PhG11 (2) | 0 / 43 / 23 | 0 / 51 / 27 | 0 / 46 / 31 | 0 / 42 / 35 | 0 / 32 / 40 | 0 / 164 / 65 | 0 / 218 / 221 |
| PhG12 (2) | 0 / 0 / 0 | 0 / 28 / 2 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 1 / 9 | 0 / 29 / 11 |
| PhG13 (2) | 0 / 2 / 4 | 0 / 3 / 3 | 0 / 2 / 2 | 0 / 3 / 3 | 0 / 1 / 2 | 0 / 1 / 2 | 0 / 4 / 16 |
| PhG14 (2) | 0 / 0 / 0 | 0 / 2 / 7 | 0 / 1 / 5 | 0 / 2 / 2 | 0 / 1 / 2 | 0 / 11 / 5 | 0 / 14 / 21 |
| PhG15 (2) | 0 / 77 / 30 | 0 / 68 / 20 | 0 / 51 / 13 | 0 / 35 / 46 | 0 / 31 / 55 | 0 / 36 / 61 | 0 / 101 / 225 |
| PhG16 (2) | 0 / 149 / 26 | 0 / 126 / 21 | 0 / 94 / 11 | 0 / 64 / 43 | 0 / 63 / 45 | 0 / 90 / 48 | 0 / 212 / 194 |
| Pharyngeal union (50) | 0 / 1306 / 313 | 0 / 1867 / 263 | 0 / 1720 / 247 | 0 / 1472 / 325 | 0 / 1620 / 283 | 0 / 2524 / 376 | 0 / 4276 / 1807 |
<!-- END COMPUTED CEM INPUT TABLE -->

Pharyngeal input is structurally stronger than frozen labellar input at
two hops—1,807 versus 115 unique final-leg synapses onto the six CEMs
(15.7×), with no direct synapses from either group.

The pharyngeal-union final leg contains 488 positive and 1,319 negative
synapses under the model's signs; larger unsigned input does not establish
net excitation, active intermediates, or CEM firing. No pharyngeal
stimulation or simulation was performed for C2b.

Reproduce the structural audit without Brian2:

```powershell
.\.venv\Scripts\python.exe -B scripts/cem_inputs.py
.\.venv\Scripts\python.exe -B -m unittest tests.test_cem_inputs
```

The complete source IDs, hashes, individual/pool counts and sign splits are
in local/gitignored `results/mn-readouts/c2b/cem_inputs.json`;
`cem_inputs.csv` and `relevant_edges.csv` retain the numeric/edge audit.
A separate streaming calculation over all parquet rows exactly matched
all 154 source-group/target combinations, including both legs and signs.
