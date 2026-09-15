# MN11 animation material checkpoint

## Action revision v3 and emotion bubbles

The owner rejected v2 motion as insufficiently distinct and the forefeet as resembling feeding. V3 redraws action keyframes using built-in imagegen, keeping the approved rounded pixel style. Source is now ignored `assets/raw/mn11_preview/mn11-actions-v3.png`; prompts remain beside it. Earlier images and GIFs are retained, not used by the revised page.

- eats holds an extended proboscis while the red tip alternates open/closed three times.
- mouth_moves keeps a short mouthpart, alternates its opening and adds a small approach/retreat. Its tight inset excludes the grounded legs.
- proboscis_only extends once for an 80 ms contact, retracts and stays still for 1.6 seconds.
- no_response uses low forefoot rubbing separated from the mouth, then turns and exits left. Departure is a mirrored slide, not completed wingbeat animation. Its inset uses the dedicated closed-mouth reference, with no legs that could be mistaken for a proboscis.

At the owner's request, the review page adds optional emoji bubbles: eats ❤️, mouth_moves 🤔, proboscis_only ···, no_response 😒. These are designed character expression, not extra model readouts. Bubbles follow the enlarged body and disappear on departure. The local canvas preview uses staged PNGs, freezes on pause, starts static for reduced motion, and allows hiding bubbles to judge the action alone. V3 GIFs are separately saved without emoji. No product copy or site implementation changed.

V3 checks: seven processing tests, exhaustive existing suite, release validator, Chromium loading/pause/bubble toggle, 360px no overflow and reduced-motion static start. Eye detection excludes orange thorax pixels; it does not bypass clipping checks. Residual generated body differences remain a visual-review limitation.

## Original v2 checkpoint (superseded below where noted)

The owner approved the slightly rounder pixel-fly direction after PR42. This checkpoint stages motion previews only: no site assets, scoring, scientific data or speech copy changes.

## Reproducible local processing

Source: ignored `assets/raw/mn11_preview/mn11-pose-preview-v2.png`, the approved 1536×1024 imagegen pose board derived from the original `assets/raw/fly/fly.png`. Generation prompts and previous alternatives remain in that local folder. This uses the built-in generator, not a claim to reproduce the original unknown generator/model.

Run from the repository root:

```powershell
.venv\Scripts\python -m scripts.mn11_anim_preview
```

The script reuses `prep_assets.py` for tolerance-24 corner background removal, nearest-neighbour resizing, and the shared 32-colour palette reconstructed from existing fly sprites. It registers the red eye to a common (245,120) anchor on a 320×320 canvas instead of cropping each pose to its own content bounds. Original art and site assets are not overwritten.

Output is ignored `results/mn11_animation_preview/`: 16 transparent 48×48 body frames, 16 staging 64×64 mouth crops (including deliberately repeated static no-response crops), four GIF loops, a local HTML review page with pause and reduced-motion support, and a source-hash/timing manifest. Four frames per state follow the approved board; final deduplication and the production asset manifest remain pending. Insets are illustrative crops of the same source, not anatomical data.

| State | Review loop |
|---|---|
| eats | Rest → extend → hold → retract → rest. |
| mouth_moves | Small mouth movement and hesitant posture, two cycles, then rest. |
| proboscis_only | Partial extension 120 ms → full extension 80 ms → retract 160 ms; no repeated chewing. |
| no_response | Front-leg grooming sequence, mouth inset static. |

The longer final holds separate repetitions for review; they are not measured latencies. The stationary no-response loop does not yet include flight departure. The approved board's poses retain residual body/wing differences despite head registration; foreleg rubbing readability and native-size mouth distinctions still need visual approval. These are review assets, not a claim of production-ready smoothness. No new artwork was generated during this extraction/loop stage.
