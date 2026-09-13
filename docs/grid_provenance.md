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
