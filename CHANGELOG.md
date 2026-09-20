# Changelog

What a visitor to askthefly.app would notice, newest first. One section per release; the heading is `## vX.Y.Z — YYYY-MM-DD` (the release tag on `main` and its date), and `scripts/validate_release.py` checks that `site/data/release.json` matches the top entry. Each entry ends with a line on whether the README honesty table changed.

## v2.1.0 — 2026-09-19

- Adds 105 entries, including 23 not-food items, for a 279-entry menu organized into 14 bilingual sections. Not-food entries carry a badge and an explanatory note.
- Eight existing dishes now have their own sprites; all 105 new entries have dedicated art.
- Existing dishes' scores and choices are unchanged, fixture-tested on all 174 reference keys for both flies. No lookup table or scientific protocol changed.
- README honesty table: added the owner-approved bilingual not-food row, distinguishing the model response from our names, classification and encoder estimates.

## v2.0.1 — 2026-09-19

- Chinese wording of the male brain-view caption revised to the owner's text; no data, scores, states, allocations or English text changed.
- README honesty table: unchanged.

## v2.0.0 — 2026-09-19

- Adds a second, independently computed male fly using MaleCNS v1.0, connections with at least 5 synapses, 0.17875 mV synaptic weight and bilateral Tastekin-typed taste-cell sets. Select female, male or both; results and share cards keep their choices separate and show the disagreement sentence whenever they disagree.
- Adds male brain views and recorded replays from grid trial 0 for the 55 cells occupied by the menu. Replays illustrate one trial; scores and designed response states use 30-trial means. Proboscis-only speech now has sweet, savoury, watery and remainder groups.
- Female scores, states, ties and allocations are unchanged and fixed by a v1.2.1 regression fixture covering all 174 dishes and all 15,051 pairs in both modes, plus the legacy female share query.
- README honesty table: changed, with the four commitments on independent calibration, different stimulus protocols, the missed bitter-alone gate and inseparable causes of disagreement; the Phase 2 comparison and male readout/replay provenance are recorded. Phase 2 pair agreement is 71.2%; male dish states are 12 eats / 0 mouth_moves / 90 proboscis_only / 72 no_response, with 72 dishes below our designed 5 Hz MN9 threshold.

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
