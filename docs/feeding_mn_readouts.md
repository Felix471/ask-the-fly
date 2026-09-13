# Feeding motor-neuron readouts beyond MN9

## Status and scope

2026-09-13, checkpoint C1: screen of existing replays complete; no new simulation.
C2 (30-trial selected-cell reruns) awaits the owner's choice and go.
This is research only: frozen inputs, lookup scores, replay files, `site/`, encoder
values and README honesty tables are unchanged. No checkpoint-chain score has been built.

MN11D and MN11V usually covary with left MN9, but substantial on/silent
disagreements and different bitter/Ir94e responses make them worth replicating.
All six CEM neurons were monitored and remained silent in all 400 trials.
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

## Reproduction and measurement choices

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
This is not an isolated LB2 experiment. Tastekin's Results (printed pp.
5541–5542, Figures 6I–K and S13–S15) link LB2 to pumping/crop-entry MNs by
effective connectivity and propose ingestion suppression as well as
disinhibitory and mixed-sign CEM pathways; they do not simply predict that
our mixed frozen set must excite CEM in this zero-basal-activity design.
CEM silence here neither tests all those motifs nor rules out CEM activity
with other stimuli/backgrounds. No connectivity remapping, tonic background,
pharyngeal stimulation or mechanistic follow-up was performed.
[Primary source: Tastekin et al.](https://doi.org/10.1016/j.cell.2026.08.016)

A checkpoint-chain candidate is therefore worth testing at the **MN9 versus
MN11** distinction: overall correlations are high but individual readouts
can separate. MN4a/MN6/MN8 track left MN9 closely in this screen (rho
0.912/0.964/0.933), making them less urgent than pumping MNs for a first
replication. A CEM checkpoint is not supported by an observable response
under the current design. Adding one now would be our unvalidated decision,
not something established by the model.

## C1 recommendation for a possible C2

These are proposed cells, **not rerun or approved**. Coordinates are
(sugar, bitter, water, Ir94e) input Hz, uniquely identifying frozen cells.
Primary set: ten cells / 300 trials if the owner selects all ten.

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

If authorised, C2 must use the selected cells' **published grid trial
seeds**, not the extra replay seeds or today's corrected default seed rule,
to support a matched MN9 check. It will use a new, referencing protocol,
not edit the frozen protocol or feed results into the lookup table.
No C2 protocol, simulation or mean±sd result exists yet.

## Verification

The extraction was independently cross-checked against a second raw-replay
calculation: all 400 left-MN9 rates, 9,600 type rates/latencies, 18,800
type/side rates/latencies and 26,400 individual count/rate/latency triples
match exactly; all 24 correlations agree to floating-point precision.
All displayed axis values and the 93 saved top-disagreement rows also match.
Synthetic tests exercise exact 64-bit IDs, silence, latency, grouping, tied
ranks, malformed inputs and same-trial MN9 mismatch detection.
