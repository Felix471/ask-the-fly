# Sprite assets

All sprites are produced by `scripts/prep_assets.py` from raw PNGs in `assets/raw/` (raw files are not tracked; see `.gitignore`). Output goes to `site/assets/` and is tracked.

```
.venv\Scripts\python scripts/prep_assets.py            # dishes + fly
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

Eight batch-2 keys were skipped by the image generator as near-duplicates. `site/assets/dishes/fallbacks.json` maps them to the nearest existing sprite and the site draws that instead:

| key | renders with |
|---|---|
| soy-milk | milk |
| americano | black-coffee |
| cappuccino | latte |
| hot-chocolate | latte |
| oolong-tea | green-tea |
| sparkling-water | water |
| apple-juice | orange-juice |
| milk-chocolate | dark-chocolate-85 |

Adding a real `assets/raw/<key>.png` and re-running `prep_assets.py --only-new --palette-from site/assets/dishes` replaces the fallback automatically (the site prefers a sprite of its own when the file exists).

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
