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

Nine batch-2 keys were skipped by the image generator as near-duplicates. `site/assets/dishes/fallbacks.json` maps them to the nearest existing sprite and the site draws that instead:

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
| tomato | apple — **needs its own sprite** (a tomato drawn as an apple is the one fallback that misleads) |

Adding a real `assets/raw/<key>.png` and re-running `prep_assets.py --only-new --palette-from site/assets/dishes` replaces the fallback automatically (the site prefers a sprite of its own when the file exists).

## Placeholders

Dish sprites are drawn with their own plate, so the scene adds only a shadow under them; without a sprite it draws a plate and a coloured circle (hue from the key), and without fly frames a simple drawn fly. Sprites are picked up automatically when the files exist.
