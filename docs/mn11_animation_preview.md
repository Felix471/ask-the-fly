# MN11 animation material checkpoint

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
