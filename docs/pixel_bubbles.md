# Pixel speech bubbles

Visual-only revision, 2026-09-15. The owner requested pixel-art emotions, a pixel
bubble and pixel text instead of system emoji and a rounded sans-serif capsule.
Copy, state thresholds, bucket conditions, scoring and action frames are unchanged.

## Asset and generation

`site/assets/response/emotions-v1.png` is one transparent, three-column atlas:
happy, nervous sweat, deadpan. Generated with the built-in image tool using
`assets/raw/fly/fly.png` as a style/palette reference, not an edit target. The
generated atlas is copied unchanged into the repository; CSS selects a column
and renders it with `image-rendering: pixelated`. No external image requests.
The three expressions are designed illustrations, not model measurements.

Final generation prompt:

> Use case: stylized-concept. Asset type: ONE pixel-art emotion sprite atlas for a retro fruit-fly game speech bubble. The reference is STYLE AND PALETTE ONLY, not a subject to copy. Create exactly THREE small round expressive face icons arranged left to right in three equal columns: HAPPY (closed delighted upward eyes, small smiling mouth), NERVOUS SWEAT (uncertain small mouth, one clearly visible pale-blue sweat drop at temple), DEADPAN / SPEECHLESS (flat horizontal eyes and straight small mouth). Restrained cute personality, warm ochre/orange face, dark brown outlines, cream highlights, the same chunky hand-placed square pixel aesthetic as the reference fly. Each face designed on a strict 24 by 24 logical pixel grid, enlarged with nearest-neighbour squares. Each icon entirely inside its own column, same size and baseline, generous clear padding, equal spacing. Transparent background with real alpha, no backdrop, no shadows outside the sprite, no gradients, no antialiasing, no glossy Apple/system emoji look, no smooth vector curves, no text, no letters, no labels, no extra icons, no fly body. This is a sprite sheet asset, not a screenshot or UI mockup. The three faces must remain immediately distinct when reduced to 24 pixels.

Mapping: eats → happy; mouth_moves → sweat; proboscis_only/no_response →
deadpan; a tie uses deadpan. This changes only the decorative emotion, not the
response state or which line is selected. Final no_response departure still
hides the entire bubble.

## Bubble and type

The local CSS bubble has a dark stepped outline, cream interior and stepped
tail, without rounded corners. The atlas sits beside a separate text node;
the emoji is decorative and hidden from accessibility announcements. Existing
self-hosted Pixelify Sans supplies English at 18 px; Fusion Pixel 12px supplies
Chinese at 24 px (2×). The bubble width is included in viewport clamping.

`scripts/prep_fonts.py` now includes `copy/fly_lines.json` when building the
Chinese subset. Previously 43 distinct speech characters were missing; every
character in the current Chinese speech is now covered by the pixel font.
Other interface glyph fallback reporting remains intact.

## Verification

`tests/test_pixel_bubbles.py` first reproduced both defects: system emoji and
missing speech glyphs. `scripts/check_pixel_bubbles.py` verifies live bilingual
text/fonts and all 96 strings at three widths (288 cases), saving local images
under `results/pixel-bubbles/`. Full state flows remain covered by
`scripts/check_mn11_site.py`; no_response still leaves without an ownership line.

Atlas SHA256: `316af6999c5451f570b20420bc2d3614ef6ede7ffe1ff970b59a8ab8ecfeb51c`.
