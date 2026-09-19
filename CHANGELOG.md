# Changelog

What a visitor to askthefly.app would notice, newest first. One section per release; the heading is `## vX.Y.Z — YYYY-MM-DD` (the release tag on `main` and its date), and `scripts/validate_release.py` checks that `site/data/release.json` matches the top entry. Each entry ends with a line on whether the README honesty table changed.

## v1.2.1 — 2026-09-15

- Refreshed all 16 groups of Chinese and English fly speech with owner-supplied lines.
- Pixel-art happy, sweating and deadpan faces replace system emoji; speech bubbles and bilingual lettering now match the pixel style.
- No scores, state rules, speech conditions, tie handling or allocation changed. A final no_response pick still leaves without ownership speech.
- README honesty table: unchanged; speech remains a designed illustration.

## v1.2.0 — 2026-09-15

- Four designed response states now give each plate a distinct fly reaction, mouth inset, emotion bubble and bilingual speech. Results and share cards include MN11 readouts; baseline rasters include individual MN11D/V cells.
- No dish's MN9 score, ranking, tie or allocation rule changed. State labels use the owner's 5 Hz threshold on left MN9 and the two-cell MN11D mean; animation and speech are designed, not measured feeding.
- README honesty table: added state/readout row and revised animation row, owner-approved before release.

## v1.1.3 — 2026-09-13

- Long dish names under the plates no longer run together on narrow screens: they end in an ellipsis, with the full name available in the title tooltip. Plate rows keep the same height.
- No dish's score changed.
- README honesty table: unchanged.

## v1.1.2 — 2026-09-12

- The site footer now shows the latest release (version, date, one line) and links to this changelog.
- The README has a "What's new" section.
- The honesty table gains a row on tonic inhibition: a designed experiment on the model, not part of the product.
- No dish's score changed.
- README honesty table: changed, new tonic-inhibition row.

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
