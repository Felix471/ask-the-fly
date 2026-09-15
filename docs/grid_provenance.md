# Lookup grid provenance

The 400-cell lookup grid (`results/grid/full`, gitignored) that produced `data/lookup_table.json` recorded the commit it ran from in `run_meta.json`. That hash predates a history rewrite on 2026-09-11 that stripped commit-message trailers and changed every hash after the initial commit. Commit contents are identical.

| what | value |
|---|---|
| run started / finished (UTC) | 2026-09-11 00:19:48 / 01:38:17 (78 min, 14 workers, Brian2 2.9.0 cython) |
| cells × trials | 400 × 30 (5 sugar × 5 bitter × 4 water × 4 ir94e unique Hz vectors) |
| `git_commit` recorded by the run (pre-rewrite) | `4d66cfcc6d080da46e316bf57dabe30132e0d5eb` |
| same commit after the rewrite | `01a798e042a412edcb44f482ec6c9706c585d767` ("Grid levels v1.1: water medium shares the low cell; grid deduplicated to 400 cells; verdict YES") |
| `data/lookup_table.json` cells_sha256 | `2e08e5f6b3738ce7eb5150b117a0671f561ab8543568e012332ef6c2dc4df15c` |
| grid levels | `data/grid_levels.json` v1.1 (water low = medium = 60 Hz) |
| protocol / cells | `data/stim_protocol.json`, `data/cells.json` (SHA-256 in the table's `protocol_sha256` / `source_cells_sha256`) |

`git_commit` inside `data/lookup_table.json` and inside the site's copy still carries the pre-rewrite hash; it is left as recorded so the table's `cells_sha256` stays valid. Use this file to resolve it.

## Seed scheme and resume ledger (D01, D02)

Trial seeds are `base_seed + trial + 1000 × index`. Until 2026-09-11 the index was the
position within the list handed to `run_conditions` (**scheme v1**), so a batched run
seeded each cell by its position inside its batch. Every published table was produced
under v1:

| product | run | batch size | consequence |
|---|---|---|---|
| `data/lookup_table.json` (cells_sha256 `2e08e5f6b3738ce7eb5150b117a0671f561ab8543568e012332ef6c2dc4df15c`), `results/grid/full` | `scripts/run_grid.py --stage full`, 400 cells | 40 (10 batches) | cell *k* used index *k mod 40*: cells 40 apart shared seeds |
| Phase 0 / Phase 1 / fixed-path recheck | `run_conditions` on the whole condition list | single batch | index = global position (identical to v2) |
| replay pack (`site/data/replay`) | `scripts/run_replay.py` | n/a | `base_seed + 700000 + global condition index`: unaffected |

Since 2026-09-11 conditions carry a `global_index` (their position in canonical grid
order) and the seed uses it (**scheme v2**), so batch size, worker count, filtering and
resume no longer change a condition's seed. `run_meta.json` and `summary.csv` record
the scheme. Nothing has been regenerated: a v2 recompute of the grid is a different
but equivalent random stream, to be run only with an explicit decision and a
migration note.

Every condition now also writes `<cond_id>.meta.json` next to its parquet: n_trials,
duration, rates, channels, protocol and cells hashes, seed scheme, seeds, and the list
of completed trials. A resume (`run_conditions(..., force=False)`) reuses a stored
result only when that ledger matches the requested run exactly and lists every
trial; a trial with no MN9 spike leaves no spike row, so without the ledger a missing
trial would be counted as zero firing. Results without a ledger (all runs before this
date) cannot be resumed; rerun them with `--force`.

## The ir94e ≠ none slice is in use (2026-09-12)

Until 2026-09-12 the product read only the 100 cells with ir94e = 0 Hz (the site hardcoded `ir94e: "none"`). Encoder v2.3 assigns every dish an ir94e level and the site now looks each dish up in its own slice, so all 400 cells (and their recorded replays in `site/data/replay/`) are consumed. No new simulation runs: the grid, `data/lookup_table.json` (cells sha256 unchanged since v1.0.0) and the replay pack are exactly the ones recorded above.

## v1.2 re-recording with extra MN readouts (2026-09-15 UTC)

Step 1 is complete and staged, **not used by the site**. The original
`data/lookup_table.json`, all files under `site/`, the protocol, cell sets,
grid levels, encoder outputs and original replay index remain untouched.
The new [lookup table](../data/lookup_table_v1_2.json) adds MN11D/MN11V
two-cell means and population SDs, right-MN9 mean/SD aliases, and the
[predeclared state rule](site.md#v12-data-preparation-not-yet-used-by-the-site).
The six recorded neuron IDs and literal target-muscle labels come from the
existing [Tastekin Table S1 extract](../data/mn_readout_ids.json).

| Record | Value |
|---|---|
| Run source commit, declared before simulation | `5d3275c8a1d9b2ddb18ae212813060210d626799` |
| Recording specification | [lookup_v1_2_recording.json](../data/lookup_v1_2_recording.json) |
| Run completed (UTC) | 2026-09-15T01:12:52.852047+00:00 |
| Runs | 400 cells × 30 trials = 12,000; six individual MNs per trial |
| Seeds | `20260910 + 1000 * (canonical_grid_index % 40) + trial`, trial 0–29 |
| Model | Unchanged frozen protocol and `sim/network.py`; Brian2 2.9.0, WSL2, cython |
| Runtime | 4788.2 s (79.8 min), 14 workers; peak worker RSS 3.164 GiB |
| Raw trial records (local/gitignored) | `results/grid/v1_2/<cell>.json` and `<cell>.npz`; `run_meta.json` |
| Unchanged protocol SHA-256 | `9f9495033281bfcd6f3b373551817987deb2cc083ae94ab61fece9065102d82a` |
| Unchanged original lookup file SHA-256 | `bd7c6f61656dbb0ec3943d267bd24ed9c2e06d0f00075671b17094b7cfd7c51c` |
| Original cell projection SHA-256 | `2e08e5f6b3738ce7eb5150b117a0671f561ab8543568e012332ef6c2dc4df15c` |
| New lookup file SHA-256 | `2659a18e4cd759364983f2f46a801aa275fd46ccaf92c9757c845bcd64fcbe0d` |
| New lookup cells SHA-256 | `e71c2bf519f98ed7e11bfe55b9f30948f9c0b35a61a854a55787aa75b0ab8829` |
| Audit and per-cell artifact hashes | [lookup_v1_2_audit.json](../data/lookup_v1_2_audit.json) |

This deliberately uses the published **batch-40 seed scheme**, not the current
generic runner's v2 scheme. It is a re-recording with extra readouts, not 30
additional independent samples: the estimate remains **n = 30**, not n = 60.
Each trial records MN9 left/right and both individual cells of MN11D and MN11V;
the latter groups are averaged within each trial before calculating their
30-trial mean and population SD (`ddof=0`). Added summary fields are rounded
to three decimals. State assignment uses unrounded means; rounding changes
none of the 400 states. The six existing MN9 fields are retained verbatim.

The 14-worker plan reserved 15 GiB from 60.47 GiB initially available in WSL,
using a nominal 3 GiB per worker. Observed peak worker RSS was 3.164 GiB;
the midpoint memory check still showed 21.23 GiB available. No run failed or
needed a retry.

### Identity and completeness checks

- All **24,000 bilateral MN9 neuron-trial spike trains** match the original
  `results/grid/full/<cell>.parquet` arrays exactly, before any new summary is saved.
- Recomputed left/right means and population SDs, rounded as in the original
  builder, match all six legacy fields in all 400 cells.
- All **2,400 complete serialized MN9 field lines**, including indentation,
  numeric formatting, delimiters and original CRLF endings, are byte-identical.
  Projecting every new cell onto all its original keys also reproduces the
  original canonical cells hash above.
- The post-run audit independently reconstructs **72,000 individual neuron-trials**
  and **48,000 grouped readout-trials** from the saved spike arrays, matching the
  ledgers' rates, counts and latencies. All 400 ledgers contain exactly 30 trials
  and the expected seeds; all recorded source hashes remain unchanged.
- Legacy source-file hashes refer to their recorded Windows CRLF bytes (Git
  stores those legacy text files with LF). New generated artifacts have narrowly
  scoped `.gitattributes` rules preserving their literal bytes across checkouts.
  Runtime source checks are not relaxed; static checkout tests allow only exact
  LF/CRLF reconstruction to the recorded legacy hash.

The new table retains the frozen table's historical `level_notes`, including
its old Ir94e rollout note; the current four-axis product usage is described in
the preceding section. No historical frozen metadata was silently rewritten.

### State counts and dictionary mapping

These are owner-designed categories of model rates, not calibrated behaviour.
Active means a 30-trial mean **≥ 5 Hz**, and silent means **< 5 Hz**, not
necessarily zero spikes. State uses left MN9 `720575940660219265` and the
MN11D two-cell mean only; right MN9 and MN11V do not decide it. Ties remain
the existing MN9 tie handling, not a fifth state. English/Chinese display
wording and honesty-table changes are deferred to Step 2.

| Internal state | Grid cells | Dishes |
|---|---:|---:|
| `eats` | 185 | 96 |
| `mouth_moves` | 52 | 26 |
| `proboscis_only` | 4 | 2 |
| `no_response` | 159 | 50 |
| **Total** | **400** | **174** |

Dish counts use all 174 unique dictionary keys, not aliases, resolving their
unchanged four encoded levels by Hz. Water `low` and `medium` both map to
60 Hz and therefore the same grid cell. The audit JSON includes every
dish-to-state assignment.

### All 52 `mouth_moves` cells

Levels below are in canonical grid order; water `low` also represents
the aliased `medium` level. Rates are 30-trial means in Hz.

| Sugar | Bitter | Water | Ir94e | MN9 left | MN11D |
|---|---|---|---|---:|---:|
| low | none | none | medium | 0.433 | 5.417 |
| low | none | none | high | 0.100 | 10.450 |
| low | none | low | medium | 1.567 | 16.233 |
| low | none | low | high | 0.467 | 16.367 |
| low | low | low | medium | 0.667 | 9.633 |
| low | medium | none | none | 0.500 | 15.633 |
| low | medium | low | low | 1.100 | 10.250 |
| medium | none | none | medium | 3.633 | 26.817 |
| medium | none | none | high | 0.867 | 27.100 |
| medium | none | low | high | 3.067 | 40.567 |
| medium | low | none | medium | 0.800 | 15.233 |
| medium | low | none | high | 0.033 | 8.067 |
| medium | low | low | high | 1.000 | 13.567 |
| medium | medium | none | none | 3.933 | 56.617 |
| medium | medium | none | low | 0.067 | 8.600 |
| medium | medium | low | low | 4.167 | 37.667 |
| medium | medium | low | medium | 0.200 | 9.117 |
| medium | medium | high | high | 3.233 | 7.233 |
| medium | high | low | none | 1.067 | 31.950 |
| medium | high | high | low | 2.400 | 12.767 |
| high | low | none | high | 2.700 | 38.167 |
| high | medium | none | low | 3.833 | 68.667 |
| high | medium | none | medium | 0.467 | 24.583 |
| high | medium | none | high | 0.033 | 7.767 |
| high | medium | low | high | 1.433 | 15.400 |
| high | high | none | none | 1.700 | 61.383 |
| high | high | none | low | 0.067 | 13.267 |
| high | high | low | low | 0.733 | 29.167 |
| high | high | high | medium | 1.767 | 23.317 |
| high | high | high | high | 0.400 | 5.150 |
| high | high | very_high | medium | 3.133 | 21.783 |
| high | high | very_high | high | 0.967 | 7.033 |
| high | very_high | high | none | 1.567 | 17.600 |
| high | very_high | very_high | none | 3.633 | 19.400 |
| very_high | high | none | medium | 0.767 | 63.267 |
| very_high | high | none | high | 0.233 | 29.250 |
| very_high | high | low | medium | 3.400 | 79.050 |
| very_high | high | low | high | 0.633 | 42.650 |
| very_high | high | high | high | 3.267 | 68.617 |
| very_high | high | very_high | high | 3.533 | 67.850 |
| very_high | very_high | none | none | 3.400 | 73.167 |
| very_high | very_high | none | low | 0.067 | 26.383 |
| very_high | very_high | none | medium | 0.000 | 10.167 |
| very_high | very_high | low | low | 0.467 | 51.450 |
| very_high | very_high | low | medium | 0.133 | 21.433 |
| very_high | very_high | low | high | 0.000 | 5.300 |
| very_high | very_high | high | low | 1.633 | 67.800 |
| very_high | very_high | high | medium | 0.633 | 36.800 |
| very_high | very_high | high | high | 0.033 | 19.783 |
| very_high | very_high | very_high | low | 1.633 | 67.533 |
| very_high | very_high | very_high | medium | 0.700 | 46.383 |
| very_high | very_high | very_high | high | 0.200 | 23.000 |

### Staged baseline replay pack

[The new manifest](../data/replay_v1_2/manifest.json) is
`replay_manifest_v2`, with `replay_v3` headers and the existing AFR1
binary container. It stages exactly **400 baseline files** in
`data/replay_v1_2/`, outside `site/`. No replay simulation was needed:
the original whole-network `results/replay/<cell>.npz` records already
contain MN11D and MN11V.

Each header adds four explicit individual MN11 rows (both cells of each
type, including empty rows for silence), with times, counts, first spike,
and per-type two-cell mean rate. All **800 packed MN9 rows** and every
existing MN9 header field are byte-identical; more strongly, **all 400
entire binary spike payloads are unchanged**, verified against the raw
recordings. The original neuron-index file is copied without changing
its IDs, order, flags or bytes.

The manifest SHA-256 is
`d3efcfb6c5ad193377bf5b6c24cce42609647c83b5b5f0a7ce048e326d209486`.
It records old/new file hashes and raw replay hashes for every cell.
Each replay remains its original **one extra trial**, not a lookup trial
or the 30-trial mean used for state. Existing silencing variants are not
repacked by this baseline-only step and remain untouched in the live bundle.

The table/pack builders are [build_lookup_v1_2.py](../scripts/build_lookup_v1_2.py)
and [pack_replay_v1_2.py](../scripts/pack_replay_v1_2.py); the recording runner is
[sim/lookup_v1_2.py](../sim/lookup_v1_2.py). No site, copy, README honesty-table
or artwork change is included. The existing art pipeline and source locations
are recorded in [docs/site.md](site.md#v12-data-preparation-not-yet-used-by-the-site).
