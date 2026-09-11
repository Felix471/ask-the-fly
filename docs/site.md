# Static site (Phase 3 scaffold)

The front end in `site/` is a dependency-free static page: one HTML file, one stylesheet, one ES module. It makes no LLM calls. It reads two JSON files from `site/data/`:

- `dishes.json` — the dish dictionary (copied from `data/dishes.json`); lookup is exact on the normalized key or a normalized alias, mirroring `encoder/normalize.py`.
- `lookup_table.json` — the `lookup_v1` table (`levels` → cells with `hz`, `mn9_mean`, `mn9_std`). Cells are indexed by their Hz vector, mirroring `sim/lookup.py`, so water `low` and `medium` (both 60 Hz) resolve to the same cell.

## Replay pack and brain view

The result view is a fly with a brain tasting the options. Every visual of neural activity is a **replay of recorded simulation output**, labelled as such on the page.

- `scripts/run_replay.py run` (WSL, Brian2) records ONE extra 1 s trial per grid cell on the fixed path with the SpikeMonitor on the whole network, seed = protocol base seed + 700000 + grid index, into `results/replay/<cell>.npz` (gitignored). 400 trials take about 2.5 minutes on 14 workers.
- `scripts/run_replay.py pack` writes `site/data/replay/<cell>.bin` (magic `AFR1`, JSON header with provenance: cell id, levels, Hz, seed, git commit, protocol sha, MN9 left/right spike times; then uint16 neuron indices and uint16 spike times in 0.1 ms) plus `site/data/replay/manifest.json` and `data/replay_neurons.json` (root ids + flags in index order). Median file 68 KB; the site fetches only the cells it shows.
- `scripts/export_neurons.py` writes `site/data/neurons.json` (base64 Uint16 x/y + Uint8 flags). `--annotations <flywire annotations tsv>` uses FlyWire soma positions (anterior view) and adds a background subsample up to the 300 KB budget; `--placeholder` writes a deterministic pseudo-layout flagged `"layout": "placeholder"`, which the page labels as such. The shipped file uses the real positions: `python scripts/export_neurons.py --annotations data/external/Supplemental_file1_neuron_annotations.tsv` (Schlegel et al. 2024, CC BY 4.0; download from github.com/flyconnectome/flywire_annotations into the gitignored `data/external/`). 9,326 replay neurons plus 20,000 background neurons for the silhouette, aspect preserved, 191 KB.
- `site/brain.js` draws the dots once and replays a cell's spikes over 1 s at 0.5×/1×/2×: GRN inputs and MN9 have their own colours, the MN9 counter ticks with each left-MN9 spike and ends at the trial's count. Caption: "Replay of recorded simulation: {cell} · 1 s · ~{n} spikes" / "仿真记录回放：{cell} · 1 秒 · 约 {n} 个 spike".
- `site/fly.js` lays the options out as plates (row, grid on narrow screens) and runs the sequence: idle → fly to plate → land → replay that plate's cell → next plate → winner + proboscis frames. "Do the opposite" approaches the fly's pick, turns away and lands on the loser. Ties hover between the tied plates. Skip jumps to the result. The level/MN9 table stays below, collapsed.

Sprites come from `site/assets/` when present (see `docs/assets.md`); otherwise a coloured circle per dish and a drawn fly stand in.

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

## Deploy (GitHub Pages)

`.github/workflows/pages.yml` runs the unit tests and deploys `site/` with the official Pages actions (configure-pages, upload-pages-artifact, deploy-pages) on every push to `main` that touches `site/`, and on manual dispatch. It only works once the repository setting **Settings → Pages → Build and deployment → Source** is set to **GitHub Actions**; until then the workflow's deploy job fails with a "Pages not enabled" error and nothing is published.

## Tests

```
node --test site/test/app.test.mjs
```

Pure functions (`normalizeName`, `buildDictionary`, `buildLookup`, `scoreOptions`, `decide`, `issueUrl`, share-card strings) are exported from `site/app.js`; the replay parser, neuron decoder, plate layout and cancel token from `site/brain.js` / `site/fly.js`. The tests parse every dictionary entry's replay file against the manifest. DOM wiring only runs in a browser.

## Behaviour

- Mobile-first, zh/en toggle (remembered per browser in `localStorage`).
- Options are added one at a time or pasted as a list (newline, comma, 、 or ; separated).
- Autocomplete: typing shows up to 6 matches on key, both display names and aliases, ranked prefix → substring → edit distance (tolerance grows with query length: Latin none under 3 chars, 1 up to 5, then 2; CJK 1 from 2 chars). Arrow keys move, Enter or tap selects, Escape closes. With no match the dropdown says "Not tasted yet; closest: …" (edit distance ≤ 3, tappable) or "Press Enter to add it anyway", and Enter adds the raw text, which then takes the miss path.
- "The fly has tasted these": every dictionary entry as a chip in the current language, tap to add; collapsed by default under 560 px.
- "Ask the fly" picks the highest MN9; "Do the opposite" picks the lowest and says what the fly would have picked. Equal MN9 is reported as a tie.
- The result view lists every option with its sugar/bitter/water levels and MN9 mean ± std, in MN9 order.
- Unknown names take the miss path: "the fly hasn't tasted this yet" and a "Report it" button that opens a prefilled GitHub Issue (`REPO_URL` in `site/app.js`).
- The share card is a 3:4 canvas (900 × 1200) with the verdict, the option list, the four fixed lines and the front-bottom line; "Save image" downloads a PNG. The water honesty line stays in the page footer.

## Placeholders to confirm

- `REPO_URL` in `site/app.js` points at https://github.com/Felix471/ask-the-fly (confirmed 2026-09-11).
- The four fixed lines (`STRINGS.*.fixedLines`) and the front-bottom line (`cardBottom`) are the product owner's exact wording (2026-09-11). `{hz_sugar_only}` is the same dish looked up with bitter = none; it equals `{hz}` when the dish has no bitter and is shown anyway. Options that land in the same grid cell tie exactly (no jitter in v1) and the card says "the fly can't tell these apart".
