# Static site

The front end in `site/` is a static page with no build step or LLM calls: `index.html`, `style.css`, the `app.js`, `brain.js` and `fly.js` ES modules, generated `strings.js`, and the vendored QR-code module. Its two scoring inputs in `site/data/` are:

- `dishes.json` — the dish dictionary (copied from `data/dishes.json`); lookup is exact on the normalized key or a normalized alias, mirroring `encoder/normalize.py`.
- `lookup_table_v1_2.json` — the additive table with unchanged MN9 fields plus MN9 right, MN11D/V means and SDs, and a designed state. Cells are indexed by their Hz vector, mirroring `sim/lookup.py`, so water `low` and `medium` (both 60 Hz) resolve to the same cell. The old table remains untouched.

The page also reads dish sections, release metadata, neuron positions, named neurons, neuropil outlines, and the replay manifest and binary files from `site/data/`. The canonical URL comes from `site/config.json`; sprites, fonts, backgrounds and sprite-fallback mappings come from `site/assets/`.

## v1.2 readouts and presentation

Step 1 staged `data/lookup_table_v1_2.json` and the expanded baseline replay pack in
`data/replay_v1_2/`. Step 2 copies them to additive paths under `site/data/` using
`scripts/export_mn11_site.py`; baseline replay loading now uses `replay_v1_2/`.
The original table and replay files remain unchanged. The state rule,
also recorded in the new table header, is an owner-designed interpretation of model
rates, not a new model output or a behavioural calibration:

| Left MN9 mean | MN11D mean | Internal state |
|---|---|---|
| Active | Active | `eats` |
| Silent | Active | `mouth_moves` |
| Active | Silent | `proboscis_only` |
| Silent | Silent | `no_response` |

Active means **mean ≥ 5.0 Hz**; silent means **mean < 5.0 Hz**, using the existing
low-interest threshold for both readouts. MN9 is the 30-trial mean of the frozen
left readout, `720575940660219265`. MN11D is the 30-trial mean of each trial's
two-cell mean rate. MN9 right and both MN11V cells are recorded, but do not decide
the state; the result table displays them. Ties are not a state: existing MN9 tie
handling remains unchanged. Raster rows show each MN11D/V cell from the single
recorded replay, not the 30-trial mean used for state classification. Legacy
silencing replays retain their original path and lack these added rows; the UI
says they are unavailable, not zero, and does not classify a silencing trial.

Animation uses the existing art pipeline: original fly sheet
`assets/raw/fly/fly.png` and dish inputs `assets/raw/<slug>.png`, processed by
[`scripts/prep_assets.py`](../scripts/prep_assets.py) as documented in
[`docs/assets.md`](assets.md). The approved action board is
`assets/raw/mn11_preview/mn11-actions-v3.png`; `scripts/mn11_anim_preview.py`
uses the `prep_assets.py` palette/background/nearest-neighbour helpers to prepare
four body frames and four mouth insets per state. `scripts/export_mn11_site.py`
copies these 32 approved frames into `site/assets/response/`.

Actions, emoji bubbles and mouth insets are illustrations, not measured behaviour.
The final `no_response` fly leaves without ownership speech, including in
`opposite` mode; ranking, ties and human allocation are unchanged. Speech comes
from `copy/fly_lines.json`, emitted as `site/fly_lines.js` by the copy importer.
Rules use the four input levels, first matching bucket wins, and the line index
is `seed % 3`. A fresh run draws a random presentation seed; share URLs include
`&seed=N`, and older links without it use 0. It is not a visitor identifier, is
not persisted, and never affects scoring. No third-party requests, analytics or
tracking are added. The README state/animation honesty rows require owner review
before release.

Integration checks (2026-09-15): 74 Node tests, 345 Python tests, release
validation, F02/F03/F04/F05/F06/F08/F15 browser regressions, all four full
state flows in both languages, and the six 360/390/430 px plate-caption cases
pass. All 400 baseline replay MN9 header fields and event bodies retain their
original bytes; every dish-pair decision in both modes matches the old table.
Three-, four- and five-dish share-card checks cover QR decoding and text bounds.
`scripts/check_mn11_site.py` stores local screenshots under `results/mn11-site/`.

## Replay pack and brain view

The result view is a fly with a brain tasting the options. Every visual of neural activity is a **replay of recorded simulation output**, labelled as such on the page.

- `scripts/run_replay.py run` (WSL, Brian2) records ONE extra 1 s trial per grid cell on the fixed path with the SpikeMonitor on the whole network, seed = protocol base seed + 700000 + grid index, into `results/replay/<cell>.npz` (gitignored). 400 trials take about 2.5 minutes on 14 workers.
- `scripts/run_replay.py pack` writes `site/data/replay/<cell>.bin` (magic `AFR1`, JSON header with provenance: cell id, levels, Hz, seed, git commit, protocol sha, MN9 left/right spike times; then uint16 neuron indices and uint16 spike times in 0.1 ms) plus `site/data/replay/manifest.json` and `data/replay_neurons.json` (root ids + flags in index order). Median file 68 KB; the site fetches only the cells it shows.
- `scripts/export_neurons.py` writes `site/data/neurons.json` (base64 Uint16 x/y + Uint8 flags). `--annotations <flywire annotations tsv>` uses FlyWire soma positions (anterior view) and adds a background subsample up to the 300 KB budget; `--placeholder` writes a deterministic pseudo-layout flagged `"layout": "placeholder"`, which the page labels as such. The shipped file uses the real positions: `python scripts/export_neurons.py --annotations data/external/Supplemental_file1_neuron_annotations.tsv` (Schlegel et al. 2024, CC BY 4.0; download from github.com/flyconnectome/flywire_annotations into the gitignored `data/external/`). 9,326 replay neurons plus 20,000 background neurons for the silhouette, aspect preserved, 191 KB.
- `site/brain.js` draws the dots once and replays a cell's spikes over 1 s at 0.5×/1×/2×: GRN inputs and MN9 have their own colours, the MN9 counter ticks with each left-MN9 spike and ends at the trial's count. Caption: "Replay of recorded simulation: {cell} · 1 s · ~{n} spikes" / "仿真记录回放：{cell} · 1 秒 · 约 {n} 个 spike".
- `site/fly.js` lays the options out as plates (row, grid on narrow screens) and runs the sequence: idle → fly to plate → land → replay that plate's cell → next plate → winner + proboscis frames. The fly's behaviour is the same in both modes: it lands on its own pick (the highest MN9); "Let the fly eat first" changes only who gets what in the verdict and on the card. The final landing replays the run of the plate the fly lands on (its own pick, in every mode), so caption, HUD and raster show that plate; when the pick was the last plate tasted its run is already on screen and nothing restarts. Ties hover between the tied plates and the brain keeps the last tasted run. Skip jumps to the result. The level/MN9 table stays below, collapsed.

- **Neuroscience layers (details toggle).** `site/data/neuropils.json` (`scripts/export_neuropils.py`): 2D convex outlines of SEZ, antennal lobes, mushroom bodies, central complex and optic lobes from the JFRC2NP surfaces in FlyWire space, drawn under the dots with small bilingual labels. `data/named_neurons.json` (`scripts/build_named_neurons.py`): Clavicle, Bract I/II, Roundup, Sink and Synch, Fdg, DNg103 and Bluebell resolved to v783 IDs, drawn as larger labelled dots and given their own raster rows; Quasimodo, Scapula, GNG016 and GNG510 have no v783 match and are skipped. The raster strip (sugar / bitter / water GRNs, named neurons, MN9 L/R, 0–1000 ms) and the HUD (neurons in the model, neurons that fired, MN9 counts, latency to the first MN9 spike, input rates) are built only from the replay file. Silencing: `scripts/run_replay.py run --silence clavicle` records every cell with Clavicle's incoming and outgoing synapses set to zero (as in Tastekin 2026); the files ship as `<cell>_silence_clavicle.bin`, and the "Silence …" buttons replay them with the MN9 delta in the caption. Every named neuron with v783 IDs has a recorded silencing run; the manifest carries per-neuron statistics over the cells where baseline MN9 fired (median change, share of cells that dropped / stayed / rose), and the site shows Clavicle plus the two neurons with the largest and most consistent effect as buttons, the rest behind "More neurons". A neuron whose silencing leaves MN9 unchanged in the current cell and has a zero median across cells gets a caption that says so: that is a result, not a missing one. A per-MN9-spike click is available, off by default.

The raster currently groups only sugar, bitter and water GRNs; it has no separate Ir94e row (`rasterRows` in `site/brain.js`). Ir94e is included in the four-axis score lookup, brain-dot colouring, caption and HUD input rates. The raster's three GRN rows do not describe the full set of taste inputs.

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

## Copy (all user-facing text)

Every string the page shows lives in `copy/site_strings.json` (key, context, en, zh, optional max_length). `scripts/import_copy.py` generates `site/strings.js` from it (the page imports that module; never edit it by hand) and writes the `<title>` and the description / Open Graph / Twitter meta tags into `site/index.html` from the `meta.*` entries. Keys are stable; edit only `en` and `zh`. The importer warns about keys that were removed (previous value kept unless explicitly retired with `--remove-key KEY`, after removal from the copy source), unknown keys (ignored) and values over `max_length` (still applied); `--check` reports without writing. The README prose is exported per section with `scripts/export_copy.py --readme` into `copy/readme_sections.md` and rebuilt with `scripts/import_copy.py --readme`.

## Deploy (Cloudflare Workers, GitHub Pages as backup)

The canonical site is https://askthefly.app/, served as static assets by a Cloudflare Worker: `wrangler.jsonc` at the repo root (name `ask-the-fly`, `assets.directory` = `site`, observability on) is the file Cloudflare generated; Cloudflare Workers Builds is connected to the GitHub repository (production branch `main`, deploy command `npx wrangler deploy`): merging into `main` deploys production automatically, and every push to another branch produces a non-production preview build (a preview can also be uploaded by hand with `npx wrangler versions upload`). Running `npx wrangler deploy` yourself is only the manual fallback when the automatic build fails; it publishes `site/` as is (no build step). Before a merge, CI (`.github/workflows/ci.yml`) runs the test job, unit tests plus `scripts/validate_release.py`, on pull requests into `dev` as well as `main`, so release validation happens before the automatic deploy, not after it. `.wrangler/` and `.dev.vars*` are gitignored. The canonical URL lives in `site/config.json` (`site_url`) and nowhere else by hand: the page reads it at load for share links and the QR code (`SITE_URL` in `site/app.js` is only the fallback), `scripts/import_copy.py` writes it into the canonical link, `og:url`, `og:image` and `twitter:image`, and `scripts/export_share_card.py` checks the QR against it. The READMEs' "Try it" line is copy (`copy/readme_sections.md`); the import script warns when it disagrees with the config.

Security headers: `site/_headers` sets a Content-Security-Policy (same-origin scripts, styles, images and fetches; `data:` images for the favicon and the placeholder plate; no objects, no framing), `nosniff`, `Referrer-Policy` and a `Permissions-Policy` on the Cloudflare deploy; `index.html` carries the same CSP in a `<meta>` tag so GitHub Pages, which cannot set headers, enforces it too. The page has no inline scripts or style attributes, no third-party requests, no cookies, and stores only the language preference in `localStorage`.

### GitHub Pages (backup)

`.github/workflows/pages.yml` runs a **stdlib-only** Python preflight (no Pillow, numpy or pandas are installed there: any test collected by `tests.test_merge_validation` or `tests.test_validate_release` must import third-party packages lazily and skip with `unittest.skipUnless` when they are missing, as the sprite tests do) and then deploys `site/` with the official Pages actions (configure-pages, upload-pages-artifact, deploy-pages) on every push to `main` that touches `site/`, and on manual dispatch. It only works once the repository setting **Settings → Pages → Build and deployment → Source** is set to **GitHub Actions**; until then the workflow's deploy job fails with a "Pages not enabled" error and nothing is published.

## Releases

Annotated tags on `main`; every update ships under a version (feature branch off `dev`, PR into `dev`, PR `dev` → `main`, tag after the automatic deploy is verified on askthefly.app).

| tag | commit | note |
|---|---|---|
| v1.0.0 | 019fe5d | launch |
| v1.1.0 | 41f8b72 | Ir94e (amino-acid aversion) axis enabled in the encoder and the site; no simulation changes. |
| v1.1.1 | 31021cb | Brain view follows the fly's final landing (caption, HUD, raster switch to the plate it lands on); the empty "Brain response:" page line dropped. |
| v1.1.2 | 65fa510 | Footer "what's new" line and CHANGELOG.md; README "What's new"; tonic-inhibition honesty row (designed experiment, not in the product); no dish score changed. |
| v1.1.3 | c58c735 | Long plate names no longer overlap on narrow screens: ellipsis with full-name titles; row heights unchanged; no dish score changed. |
| v1.2.0 | 1ff70c1 | Four designed response states (eats / mouth_moves / proboscis_only / no_response) with a per-plate fly reaction, emotion bubble and bilingual speech; MN11 readouts on results, share cards and baseline rasters; no MN9 score, ranking, tie or allocation changed. Honesty table: state/readout row added, animation row revised, owner-approved before release. |
| v1.2.1 | 5789e3b | Owner-supplied bilingual fly speech refreshed; pixel-art emotion faces, speech bubbles and lettering; no scores, state rules or allocation changed. Honesty table unchanged. |
| v2.0.0 | 641f29b | Second, independently computed male fly (MaleCNS v1.0, >=5-synapse connections, 0.17875 mV, bilateral Tastekin-typed sets) with a female/male/both selector, the fixed disagreement sentence, male brain view (soma or synapse-centroid positions, MaleCNS ROI outlines), trial-0 replays for the 55 dish cells and proboscis-only speech split into four groups; female scores, states, ties and allocations unchanged (v1.2.1 fixture). Honesty table: MaleCNS row rewritten; four commitment rows, Phase 2 comparison, male readout/state and replay/layout rows added, owner-approved. |
| v2.0.1 | 54837ca | Chinese wording of the male brain-view caption revised to the owner's text; no data, scores, states, allocations or English text changed. Honesty table unchanged. |
| v2.1.0 | 5f28a72 | 105 new entries (23 Not food), 14 bilingual sections, not-food badges and notes, eight replacement sprites and 105 new sprites; existing scores unchanged for both flies. Owner-approved not-food honesty row added. See [batch report](dictionary_batch3.md). |

### Changelog and the footer "what's new" line

`CHANGELOG.md` at the repo root is the single source for what changed: one `## vX.Y.Z — YYYY-MM-DD` section per release, newest first, two or three plain-language lines on what a visitor notices, and one line on whether the README honesty table changed. Three things follow from it. The README "What's new" block (the three latest entries, en and zh) lives in `copy/readme_sections.md` and is rebuilt with `scripts/import_copy.py --readme`. The site footer shows the latest release only, `vX.Y.Z · YYYY-MM-DD · summary`, with the version and a "what's new" link pointing at `CHANGELOG.md` on GitHub: version, date, summary key and changelog URL come from `site/data/release.json`; the zh/en summary is the `releaseSummary` string in `copy/site_strings.json` (`releaseLink` is the link text), regenerated by the importer; nothing is hard-coded in `index.html` (`releaseLine` / `renderReleaseLine` in `site/app.js`). `scripts/validate_release.py` refuses a release whose `release.json` version or date differs from the top `CHANGELOG.md` entry or whose summary key is missing from `site/strings.js` (`tests/test_validate_release.py`).

Release checklist: add the `CHANGELOG.md` entry → update `site/data/release.json` (version, date) and the `releaseSummary` en/zh strings → refresh the README "What's new" block in `copy/readme_sections.md` → `python scripts/import_copy.py --readme` → `python scripts/validate_release.py` → PR into `dev`, PR `dev` → `main`, tag after the automatic deploy is verified, then add the row to the Releases table above.

For dictionary batches, also:

- Validate complete, exclusive section membership and bilingual labels with the sections validator in `scripts/validate_release.py`.
- Run `scripts/audit_sprites.py --check`: every dictionary key must own an existing sprite, with no borrowed/shared sprite; report unused orphans separately.
- Run the unchanged 174-key female and male fixtures, the full-menu lookup/replay Node test, and `scripts/report_batch3.py --check` for batch 3.
- Run live browser F23 (all 14 section labels plus All reachable at 390 px) and F24 (not-food badges/notes in both languages, both flies and both modes); F24 must pass, not skip.
- Run `scripts/check_plate_labels.py`, including `--dishes hainanese-chicken-rice,mosquito-coil-liquid,food-waste-swill`, and export a Chinese `nectar,steak` share card with a decoded QR.
- Set the actual release date in CHANGELOG, release metadata and both README What's new lines at merge; 2026-09-19 is the v2.1.0 preparation placeholder. The Releases row remains pending merge until the owner releases and tags.

v2.0.0 shipped on 2026-09-19 (tag on 641f29b) with the owner-approved wording and the `tip` sprite promoted. Before any later PR that touches the male bundle:

- Run `scripts/export_male_site.py --check` and `scripts/validate_release.py`: the male lookup must match its frozen source byte-for-byte, and the shipping manifest must cover exactly the current dish-occupied trial-0 replays (70 for batch 3; 55 at v2.0.0) with matching hashes and no orphans.
- Check `site/data/neurons_male.json` with the male data/export tests: replay index order and counts, named readouts, anterior soma projection, explicitly non-anatomical placeholders and the size limit must hold.
- Run the female v1.2.1 fixture test (174 dishes, 15,051 pairs × both modes, fixed share query), male UI tests, browser checks and narrow plate-label checks.
- Export both-mode share cards in English and Chinese, including a disagreeing pair and opposite mode; decode each QR and check the full disagreement sentence and card bounds. Example: `.venv\Scripts\python scripts/export_share_card.py --url http://127.0.0.1:8765/ --dishes brownie,steak --fly both --lang en --out results/p4/card-both-en.png`.
- Male art: the `tip` variant was promoted for v2.0.0 with `scripts/prep_male_sprites.py --promote tip` (42 PNGs in `site/assets/fly_male/` and `site/assets/response_male/`, `male_sprite_variant` in `site/config.json`). A different variant needs those folders removed first; the command refuses to overwrite.
- Require both CI `test` and Workers Builds to pass. The owner merges, deploys and tags.

## Tests

```
node --test site/test/app.test.mjs site/test/regress.test.mjs
```

Pure functions (`normalizeName`, `buildDictionary`, `buildLookup`, `scoreOptions`, `decide`, `issueUrl`, share-card strings) are exported from `site/app.js`; the replay parser, neuron decoder, plate layout and cancel token from `site/brain.js` / `site/fly.js`. The tests parse every dictionary entry's replay file against the manifest. DOM wiring only runs in a browser.

With a local server serving `site/` on port 8765, run `python scripts/browser_checks.py` for browser regressions and `python scripts/check_plate_labels.py` for the longest dictionary names in en/zh at 360, 390 and 430 px. The latter saves six screenshots and a JSON report under `results/plate-labels/after/`, and checks full names/titles, non-overlap, stable scene height, language switching, resize, skip and reset. `--baseline --out results/plate-labels/before` records the original canvas-label overlap before applying the fix; `--compare results/plate-labels/before/report.json` also checks heights against that baseline.

## Behaviour

- Mobile-first, zh/en toggle (remembered per browser in `localStorage`).
- Plate names use fixed-height, single-line HTML captions over the canvas; long names end in a CSS ellipsis, with the unchanged full name in the caption's text and `title`. The plate layout and scene height do not change with name length or language.
- Options are added one at a time or pasted as a list (newline, comma, 、 or ; separated).
- Autocomplete: typing shows up to 6 matches on key, both display names and aliases, ranked prefix → substring → edit distance (tolerance grows with query length: Latin none under 3 chars, 1 up to 5, then 2; CJK 1 from 2 chars). Arrow keys move, Enter or tap selects, Escape closes. With no match the dropdown says "Not tasted yet; closest: …" (edit distance ≤ 3, tappable) or "Press Enter to add it anyway", and Enter adds the raw text, which then takes the miss path.
- Page order: one-line intro, input with autocomplete, the selected dishes ("On the table": removable chips with a 26 px sprite thumbnail; the idle fly sprite rests on the table's edge; a one-line hint while empty), "Ask the fly" / "Let the fly eat first", then "Browse dishes": a horizontal row of 12 popular dishes as picture tiles (`popular` in `data/dish_sections.json`, copied to `site/data/sections.json`), and "View all" for search, section tabs (中餐/日韩/东南亚/西餐/饮料/水果蔬菜) and a tile grid (4 per row from 560 px, 2 on phones). Tiles toggle the selection and show a check when selected. Selections are stored as dish keys (typed unknown text as typed), so the language toggle relabels everything in place without rerunning or changing a number. Dishes without a sprite (typed, unknown) use one neutral placeholder plate; sprites without their own file use `site/assets/dishes/fallbacks.json`.
- "Ask the fly" gives the human the fly's pick (highest MN9). "Let the fly eat first" (`mode: "opposite"`) gives the human what the fly leaves: with two dishes the other one (the lowest), with three or more every dish except the fly's pick (`humanSet`); the fly itself still goes to its own pick, and the verdict, stage caption and share card state both sides. Equal MN9 is reported as a tie.
- Each dish is looked up in its own grid cell on all four axes: sugar, bitter, water and ir94e (`ir94eLevel(entry)`, `none` for an entry without the field). Since 2026-09-12 (encoder v2.3) every entry carries `ir94e`, so soy-, stock- and meat-heavy dishes land in the ir94e low / medium slices and score far lower than plain starches; that ordering is the model's (README honesty table, OQ-6). The level table shows an "Amino acids" column with a one-line explanation under it (`colIr94e`, `ir94eExplain`); the brain caption and HUD input rates include the ir94e level / Hz.
- Low-interest caption: when the fly's own pick (`decision.flyPick`, the winner in "Ask the fly", the fly's dish in "Let the fly eat first") has MN9 mean below 5 Hz, the result adds one line under the pick (`lowInterest`, `LOW_INTEREST_HZ` in `site/app.js`): "The fly didn't care much for any of these. This one was just the least uninteresting." The 5 Hz threshold is ours; the caption changes no decision or tie. Separately, v1.2 uses the same threshold for its designed state animation, as specified above.
- The result view leads with the chosen dish sprite and the fly's designed state frame (no fly for `no_response`), the other dishes small, greyscale and struck beside it (`drawResultHero`); the level / MN9 L/R / MN11D/V table (mean ± SD, MN9 order), with a designed-state column and the card's fixed lines sit collapsed under "How each dish was scored". "Ask again" is primary, "Share" secondary. During the run, plates show no Hz until the fly has tasted them ("loading…" while a replay is fetched); replays are prefetched at run start.
- Unknown names take the miss path: "the fly hasn't tasted this yet" and a "Report it" button that opens the "New dish request" issue form (`.github/ISSUE_TEMPLATE/dish-request.yml`, `REPO_URL` in `site/app.js`) with the typed name and page language prefilled; the form asks for the Chinese name, the English name and a one-line description.
- The share card is a 3:4 canvas (900 × 1200) opened in a modal (`<dialog>`, near full-screen on phones, a centred sheet from 560 px). Content, top to bottom: title, headline, the chosen name; the chosen dish sprite with the fly on it (state frame, absent for `no_response`; ties show every tied sprite with the fly hovering above; in "Let the fly eat first" no fly on the chosen (human's) dish); the MN9 bar comparison with state and MN11D/V means (shared MN9 scale, at most four rows, then "+N"); the MN9 line (`fixedLines[1]`); one honesty sentence (`cardHonesty`: taste levels are LLM estimates, the response comes from precomputed runs of a published fly-connectome model); then the brain snapshot, grown into the remaining height, with its caption, and the QR code (error correction M, 4-module quiet zone) with the short URL in monospace. The taste-levels line and the rest of the fixed lines are shown on the page instead, under "How each dish was scored". "Save image" downloads the PNG.
- Share links: `?d=slug,slug,…&lang=zh|en[&m=opposite][&seed=N]` (`shareUrl` / `parseShareParams` / `resolveShared` in `site/app.js`). Known dishes travel as their sprite slug (`slugFor(key)`: ASCII, hyphens), unknown names as typed, URL-encoded. On load the site resolves each slug back through the dictionary (a slug is looked up as is, then with hyphens as spaces), fills the options, applies `lang` for that view only (the saved preference is untouched) and runs the sequence; unresolved names take the miss path as usual. `scripts/export_share_card.py` renders a card from such a link with Playwright and decodes the QR with OpenCV to check it.
- QR codes come from `site/vendor/qrcode-generator/qrcode.mjs` (qrcode-generator 2.0.4 by Kazuhiko Arase, MIT; license and provenance next to it). No other third-party code ships with the site.
- Footer provenance: the lookup table records the git commit of the grid run as it was when the run happened. The repository history was rewritten on 2026-09-11 (commit trailers stripped), so `COMMIT_REWRITE` in `site/app.js` maps the recorded hash to the same commit's current hash and the footer shows the latter; the data file keeps the original. Mapping: `4d66cfcc6d080da46e316bf57dabe30132e0d5eb` → `01a798e042a412edcb44f482ec6c9706c585d767` (see docs/grid_provenance.md).

## Placeholders to confirm

- `REPO_URL` in `site/app.js` points at https://github.com/Felix471/ask-the-fly (confirmed 2026-09-11).
- The four fixed lines (`STRINGS.*.fixedLines`) and the front-bottom line (`cardHonesty`) are the product owner's exact wording (2026-09-11). `{hz_sugar_only}` is the same dish looked up with bitter = none and ir94e = none; it equals `{hz}` when the dish has neither and is shown anyway. Line 2 reads "with bitter and amino acids {hz}" since 2026-09-12 (it said "after bitter", which was wrong for a dish whose drop comes from ir94e alone); line 3 lists the four levels. Options that land in the same grid cell tie exactly (no jitter in v1) and the card says "the fly can't tell these apart".
