# Changelog

What a visitor to askthefly.app would notice, newest first. One section per release; the heading is `## vX.Y.Z — YYYY-MM-DD` (the release tag on `main` and its date), and `scripts/validate_release.py` checks that `site/data/release.json` matches the top entry. Each entry ends with a line on whether the README honesty table changed.

## v1.1.1 — 2026-09-12

- The brain view now follows the fly all the way: when it lands on the dish it picks, the brain replay, caption and spike raster switch to that dish instead of staying on the last one tasted.
- The empty "Brain response:" line under "How each dish was scored" is gone.
- README honesty table: unchanged.

## v1.1.0 — 2026-09-12

- The fly can now tell savory dishes apart. A fourth taste dimension, amino acids (the fly's Ir94e channel), is scored for every dish, so soy-, stock- and meat-heavy dishes no longer land in the same cell as plain bread or rice. Kung pao chicken versus tomato and egg is no longer a tie.
- Meat- and soy-seasoned dishes now score very low, because in this brain model amino acids strongly suppress the "eat" neuron. That is the model's property, shown as is.
- When the fly's pick scores under 5 Hz, the result says so: "The fly didn't care much for any of these."
- The score table has an "Amino acids" column with a one-line explanation; the share card's second line no longer says "after bitter" for dishes with no bitter.
- README honesty table: changed, new row on the amino-acid channel (mapping ours, suppression the model's, uncalibrated).

## v1.0.0 — 2026-09-11

- Launch: pick a few dishes and a published fruit-fly brain model (Shiu 2024, FlyWire v783) tastes each one and picks the one that makes its "eat" neuron fire most. Chinese and English.
- Watch the recorded brain activity for each dish, silence named neurons, and share a card with a QR code that replays the same comparison.
- README honesty table: first version.
