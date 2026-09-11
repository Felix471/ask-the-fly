# Static site (Phase 3 scaffold)

The front end in `site/` is a dependency-free static page: one HTML file, one stylesheet, one ES module. It makes no LLM calls. It reads two JSON files from `site/data/`:

- `dishes.json` — the dish dictionary (copied from `data/dishes.json`); lookup is exact on the normalized key or a normalized alias, mirroring `encoder/normalize.py`.
- `lookup_table.json` — the `lookup_v1` table (`levels` → cells with `hz`, `mn9_mean`, `mn9_std`). Cells are indexed by their Hz vector, mirroring `sim/lookup.py`, so water `low` and `medium` (both 60 Hz) resolve to the same cell.

## Data

```
.venv\Scripts\python scripts/export_site_data.py --stub   # dictionary + STUB lookup table (placeholder numbers)
.venv\Scripts\python scripts/export_site_data.py          # dictionary + data/lookup_table.json (after build_lookup.py)
```

The stub table has the real schema and 400 cells but its MN9 values are a closed-form guess, flagged `"stub": true`. The page shows a yellow banner and stamps "STUB DATA" on the share card while it is loaded. Replace it with the real table once `scripts/build_lookup.py` has run on `results/grid/full`.

## Run locally

```
.venv\Scripts\python -m http.server 8000 -d site
```

then open http://localhost:8000/. `fetch()` needs an HTTP origin; opening `index.html` from disk will not load the data files.

## Tests

```
node --test site/test/app.test.mjs
```

Pure functions (`normalizeName`, `buildDictionary`, `buildLookup`, `scoreOptions`, `decide`, `issueUrl`, share-card strings) are exported from `site/app.js`; DOM wiring only runs in a browser.

## Behaviour

- Mobile-first, zh/en toggle (remembered per browser in `localStorage`).
- Options are added one at a time or pasted as a list (newline, comma, 、 or ; separated).
- "Ask the fly" picks the highest MN9; "Do the opposite" picks the lowest and says what the fly would have picked. Equal MN9 is reported as a tie.
- The result view lists every option with its sugar/bitter/water levels and MN9 mean ± std, in MN9 order.
- Unknown names take the miss path: "the fly hasn't tasted this yet" and a "Report it" button that opens a prefilled GitHub Issue (`REPO_URL` in `site/app.js`).
- The share card is a 3:4 canvas (900 × 1200) with the verdict, the option list, the four fixed lines and the honesty line on the front; "Save image" downloads a PNG.

## Placeholders to confirm

- `REPO_URL` in `site/app.js` points at https://github.com/Felix471/ask-the-fly (confirmed 2026-09-11).
- The four fixed lines (`STRINGS.*.fixedLines`) are drafted from the README product copy; replace them with the spec's wording if it differs.
