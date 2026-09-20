# Sprite assets

All sprites are produced by `scripts/prep_assets.py` from raw PNGs in `assets/raw/` (raw files are not tracked; see `.gitignore`). Output goes to `site/assets/` and is tracked.

```
.venv\Scripts\python scripts/prep_assets.py --only-new --palette-from site/assets/dishes
.venv\Scripts\python scripts/prep_assets.py --only fly
```

Pipeline per image: background removal (existing alpha is kept; otherwise a flood fill from the four corners on near-background colour, `--tolerance 24`), crop to content and pad to a square, nearest-neighbour downsample, quantize to one 32-colour palette shared by the whole batch, write RGBA PNG.

## Dishes

| input | output |
|---|---|
| `assets/raw/<slug>.png`, 1024 × 1024, dish on a flat background or transparent | `site/assets/dishes/<slug>.png`, 96 × 96 |

`<slug>` is the suggested asset filename printed by `scripts/export_dish_list.py` (the dictionary key, lowercase, non-alphanumerics collapsed to hyphens, e.g. `mapo-tofu.png`, `sweet-red-bean-soup.png`). The site looks a dish up by that slug; a missing file falls back to the placeholder plate.

## Fly

Frames go in `assets/raw/fly/` as individual PNGs, or as one horizontal sheet per state named `<state>_sheet.png` (frames of equal width, left to right), which the script splits first.

A single 3 × 3 grid sheet named `fly.png` is also accepted (the form the first asset batch used): row-major `idle_1, idle_2, fly_1, fly_2, fly_3, fly_4, land_1, proboscis_1, proboscis_2`; `proboscis_3` (retract) is copied from `land_1`. Cells are cropped to content after background removal.

| state | frames | files |
|---|---:|---|
| idle | 2 | `idle_1.png`, `idle_2.png` |
| fly | 4 | `fly_1.png` … `fly_4.png` |
| land | 1 | `land_1.png` |
| proboscis | 3 | `proboscis_1.png`, `proboscis_2.png`, `proboscis_3.png` (extension, out, retract) |

Output: `site/assets/fly/<state>_<n>.png`, 48 × 48, facing right; the site mirrors for leftward flight. The `fly` frames are the wing-beat cycle; `proboscis` is played on the winning plate.

## Sprite fallbacks

The eight batch-2 keys formerly borrowed sibling sprites; batch 3 replaces all eight with their own sprites, leaving `site/assets/dishes/fallbacks.json` with an empty map.

| key | renders with |
|---|---|
| None | All 174 dishes have their own sprite |

`scripts/audit_sprites.py` prints every dictionary key, its expected and resolved sprite,
borrows, missing files, sharing and orphans; `--check` also invokes the release validator's
`check_sprites`. Both reject borrows, missing sprites and shared resolved files. The
validator also rejects malformed fallback maps and missing targets, even unused ones.

## Generation record

Batch-3 replacements use the **built-in image generator of the coding agent,
reference-image edit**, one call per dish with the corresponding sibling raw PNG as
the style reference. Verbatim prompts and reference paths are recorded in
`assets/raw/prompts/batch3_replacements.md` (local, gitignored).

Style rules: chunky pixel-art look; a single dish or glass centred; dark brown
outline; warm limited palette; plain white or transparent background; no text;
no plate unless the dish sits on one in real life; the same scale as siblings.
Soy milk has a youtiao stick, americano a tall paper cup, cappuccino cocoa-dusted
foam, hot chocolate marshmallows, oolong amber tea, sparkling water bubbles and a
lime wedge, apple juice an apple slice, and milk chocolate a lighter bar in a wrapper.

The eight native generator outputs were 1254 × 1254, retained unchanged in
`assets/raw/batch3_generated/`; nearest-neighbour normalization produces the requested
1024 × 1024 `assets/raw/<slug>.png` inputs, preserving generated alpha. Cropping uses
the same alpha > 127 visibility threshold as final quantization, so faint peripheral
alpha noise cannot shrink the sprite. Processing uses
only `prep_assets.py --only-new --palette-from site/assets/dishes`: dictionary dishes
only, existing sprites skipped, no implicit fly processing. This also excludes raw
contact sheets from future additive runs. Never regenerate shipped sprites.

All 166 previous dish sprites are checked byte-for-byte using SHA256 before and
after processing. Local records: `assets/raw/batch3_sprites_before_sha256.json` and
`assets/raw/batch3_sprites_hash_proof.json`. The owner's decision-point-2 comparison
is `assets/raw/batch3_replacements_sheet.png`: eight borrowed/own pairs, each sprite
at 4× nearest-neighbour with labels. Future dictionary additions use this same
recorded pipeline after the owner fixes their list; the replacement stage generated
only the eight replacements.

### Batch-3 dictionary additions

The approved 106-entry list is `encoder/foods_batch3.json`. New raw art uses the
same built-in generator and reference style as the replacements, one call per
slug. Exact prompts and sibling reference paths are in
`assets/raw/prompts/batch3_new.md`; completed generation sources are recorded in
`assets/raw/batch3_new_sources.jsonl`. Native outputs are retained under
`assets/raw/batch3_new_generated/`, with nearest-neighbour normalization to
1024 × 1024 for `assets/raw/<slug>.png` when necessary. Existing raw files are
skipped on resumption.

The 23 not-food items remain tasteful pixel art, never photorealistic or gross:
feces is a small brown mound with two tiny flies; swill is a bucket of scraps;
rotting fruit has brown spots and a tiny fly; rotten egg is cracked with a green
wisp; sour milk has a curdled surface. Lees and risen dough use bowls; kimchi
brine uses a jar, beer dregs the last inch of a glass, and coffee grounds a paper
filter. Nectar is a flower with a droplet; honeydew a leaf with aphids and
droplets; sap is bark with an amber drip; pollen is yellow dust on a flower.
Sweat is a droplet on a towel without skin, and tears a teardrop without a face.
Toothpaste uses a squeezed tube, dish soap a bottle with bubbles, soap a bar
with bubbles, candle a lit candle, and mosquito repellent a plug-in bottle.

Only `prep_assets.py --only-new --palette-from site/assets/dishes` processes
additions. Its explicit allowlist includes the approved batch-3 keys before
dictionary merge; contact sheets remain excluded and existing sprites are
never overwritten. The 174 existing sprites have a SHA256 baseline in
`assets/raw/batch3_new_before_sha256.json`; before/after proof is recorded in
`assets/raw/batch3_new_hash_proof.json`. New sprites are expected audit orphans
until their dictionary entries land; this does not relax the release gate.
Owner review contact sheets are saved under `assets/raw/batch3_sheets/`.

The addition stage completed 106 raw images and 106 distinct 96 × 96 RGBA sprites,
with zero refusals and zero skipped slugs. All 174 baseline sprites remain
byte-identical. The final sprite audit passed: 279 dictionary entries, no missing,
borrowed or shared sprites, and one orphan (`umeboshi.png`). The dictionary changed
concurrently during generation, so the anticipated 106-orphan pre-merge state
was no longer present at final verification. No sprite gate was changed.

The 12 section sheets use 4× nearest-neighbour sprites and three columns (two
for Drinks), keeping their width at 1248 px or less. The requested five-column
layout conflicts with the 1400 px limit: five 96 px sprites at 4× already occupy
1920 px before margins. The phone-width limit and exact 4× scale were retained;
five columns remains unmet. `all_new.png` uses 3× sprites in four columns, at
1272 × 10620 px. Sheet paths, dimensions and file sizes are recorded in
`assets/raw/batch3_sheets/manifest.json` and `assets/raw/batch3_new_report.md`.

## Placeholders

Dish sprites are drawn with their own plate, so the scene adds only a shadow under them; without a sprite it draws a plate and a coloured circle (hue from the key), and without fly frames a simple drawn fly. Sprites are picked up automatically when the files exist.

## Backgrounds

`assets/raw/bg/tablecloth.png` and `assets/raw/bg/paper.png` (512 px, gitignored) become
`site/assets/bg/*.png` through `scripts/prep_bg.py`: 256 × 256 nearest-neighbour, one
palette shared by both tiles (32 colours max; the tablecloth uses 13, the paper 3),
no dithering. The script checks seamless tiling (mean wrap-edge difference / mean
interior neighbour difference; ≤ 1.5 passes: tablecloth 0.73, paper 0.11) and measures
WCAG contrast of the text colours against the darkest and lightest tile pixel:

| tile | ink `#1f1a17` | muted `#6b625b` | used for |
|---|---:|---:|---|
| tablecloth | 14.2:1 | 4.9:1 | the stage, at 2× (`.scene-canvas`), thin darker rim; plate shadows drawn by the scene; no overlay needed |
| paper | 15.4:1 | 5.3:1 | the page body, at 2×, light scheme only |

23.6 KB in total. The brain view stays black; chips, buttons, the result surface and the
modal stay solid. On the share card the tablecloth appears only behind the winner
sprite (a rounded patch with the same rim); every line of text stays on solid cream.
Reduced motion: the idle fly shows one frame instead of animating, and scrolling is not
smoothed; the textures themselves never move.

## Fonts

Two tiers. Display tier, pixel fonts, only at 16 px and above: the h1, section
headings, buttons (not the small 14 px ones), chips, dish names on tiles, the result
title, the share card's title and dish name. Body tier: the system sans stack for
everything else (intro, captions, honesty lines, table, details, footer, plate labels).

`scripts/prep_fonts.py` builds `site/assets/fonts/`: Pixelify Sans (variable weight,
Basic Latin + Latin-1 + the punctuation the copy uses) and Fusion Pixel 12px
proportional zh_hans, subset to `glyphs-zh.txt` (all zh dictionary display names and
aliases, section names, every zh string in `copy/site_strings.json`, digits, ASCII and
CJK punctuation); `coverage.json` records what the CJK subset covers and which
characters fall back to the system CJK sans. Both are woff2 with `font-display: swap`,
preloaded from `index.html`, served same-origin (CSP `font-src 'self'`); no external
font requests. The share card draws its title and dish name with the display fonts and
waits for `document.fonts` before drawing. Licenses: `LICENSE-PixelifySans.txt`,
`LICENSE-FusionPixel.txt` (OFL 1.1, with the component fonts' licenses).
