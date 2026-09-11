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
