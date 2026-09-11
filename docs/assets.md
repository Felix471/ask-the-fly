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

| state | frames | files |
|---|---:|---|
| idle | 2 | `idle_1.png`, `idle_2.png` |
| fly | 4 | `fly_1.png` … `fly_4.png` |
| land | 1 | `land_1.png` |
| proboscis | 3 | `proboscis_1.png`, `proboscis_2.png`, `proboscis_3.png` (extension, out, retract) |

Output: `site/assets/fly/<state>_<n>.png`, 48 × 48, facing right; the site mirrors for leftward flight. The `fly` frames are the wing-beat cycle; `proboscis` is played on the winning plate.

## Placeholders

Until assets land the site draws a coloured circle per dish (hue from the key) and a simple two-ellipse fly, so the sequence can be tested. Both are swapped for sprites automatically when the files exist.
