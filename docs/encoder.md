# Dish encoder v2.3
The default prompt is `encode_v2.3`; select `encode_v1`, `encode_v2`, `encode_v2.1` or `encode_v2.2` with `--prompt-version VERSION`.
V2.3 (2026-09-12) adds a fourth dimension, `ir94e`: sources of free glutamate or free amino acids in the dish as normally eaten (the amino-acid-aversion channel, Tastekin et al. 2026, LB1e; never defined as salt or umami). Exactly four levels: `none` (no such ingredient), `low` (a small amount used as seasoning: a little soy sauce, fish sauce, cheese, tomato, oyster sauce), `medium` (a fermented, aged or stock-based flavour is a main component: miso soup, ramen broth, parmesan-heavy dishes, red-braised dishes with heavy dark soy), `high` (nearly pure glutamate: MSG, soy sauce itself, dashi concentrate, Marmite). There is no `very_high` for ir94e; `encoder/levels.py` `IR94E_LEVELS` / `IR94E_HZ` (0 / 60 / 120 / 200 Hz, matching `data/grid_levels.json`). The sugar, bitter and water definitions are byte-identical to v2.2. Prompts before v2.3 still validate three dimensions (`encode.dimensions_for`); the Gemini response schema is chosen per prompt (`schema_v1` three dimensions, `schema_v2` four). Stability: `docs/encoder_stability_v2_3.md` (41 foods, ir94e 39/41 cross-language, 100% within-language) and `docs/encoder_stability_v2_3_batch2.md` (133 batch2 dishes, ir94e 121/133, 100%).
**Water-anchor check.** `python scripts/check_water_anchors.py RAW.jsonl` compares each anchor food named in the water definition (water, clear tea, clear broth = very_high; milk = high; cola, juice, bubble tea, miso soup, watermelon, orange, grapes = medium; honey, cake, apple, banana, steamed rice = low) with its modal water level per language in a stability run; exit 0 when every anchor holds, exit 1 listing each drifted (food, language), exit 2 when the run contains no anchor food. It reports and corrects nothing. **Under the default v2.3 prompt this check is currently red**: miso soup encodes to water `high` in both languages (6/6 runs each, on the 41-food and the 174-dish runs) against its listed anchor `medium`, with the water wording unchanged from v2.2, where the same check is green on all 13 anchors. This is a known, accepted drift (Checkpoint 2 of the Ir94e work, 2026-09-12), not a broken check; water levels were not merged from v2.3 (see the one-version rule below), so the dictionary is unaffected. A future prompt revision is green again only when every anchor food present in its stability run sits at its anchor level in both languages, miso soup at `medium` included; adding dish examples to force that is not a fix (the rule from the Ir94e task: adjust level definitions only).
Encode Chinese: `.venv\Scripts\python -m encoder.encode "红烧肉" --lang zh [--prompt-version encode_v2.2]`.
Encode English: `.venv\Scripts\python -m encoder.encode "black coffee" --lang en`.
V2.1 retains v2's osmolarity-based water definition and adds bilingual anchor examples.
V2.2 moves the water anchors so juicy fruit that releases juice when bitten (watermelon, orange, grapes) is `medium`, while firm or starchy fruit (apple, banana) stays `low`. Labels only: water `low` and `medium` share one grid cell (60 Hz), so MN9 results are unchanged.
**One-version rule (2026-09-11, amended 2026-09-12).** `data/dishes.json` is encoded at exactly one prompt version per dimension: the top-level `encoder_version` is the run that produced sugar, bitter and water, and a dimension encoded by a different run is listed in `encoder_version_by_dimension` (today `{"ir94e": "gemini-3.1-flash-lite@encode_v2.3"}` on every entry, next to the v2.2 top-level version). Within a dimension a new prompt version is applied as a full re-encode of the whole dictionary, never as a partial relabel; a new dimension is added with `--only-dimension` (below) so the existing levels stay byte-identical. Product-owner decisions are recorded as `human_checked` entries that override individual levels (the `reason` field says what the encoder proposed); they keep the `encoder_version` of the run they were reviewed against and survive later merges. Current version: `gemini-3.1-flash-lite@encode_v2.2` (stability: `docs/encoder_stability_v2_2.md`, water agreement 37/41). Human-checked overrides at v2.2: endive and gai lan water = low; curry, espresso and sweet red bean soup water = medium; grapefruit bitter = high; tonic water sugar = high, bitter = very_high, water = medium.
Plain water, clear tea, and clear broth are `very_high`; dilute milk and most soups are `high`; sweet/salty drinks and sauces are `medium`; moist solids and syrups are `low`; dry solids are `none`.
Sugar and bitter definitions are unchanged from `encode_v1`.

Run stability: `.venv\Scripts\python -m encoder.stability --repeats 6 --langs zh,en`.
Use `--prompt-version VERSION`; the default is `encode_v2.2`.
Use `--dimensions water` (or a comma list) to restrict report tables; raw JSONL entries still contain all dimensions.
Use `--raw PATH` and `--report PATH` to choose outputs; defaults are `results/encoder/stability_raw.jsonl` and `docs/encoder_stability.md`.
Limit a new run with `--limit N`; exercise it without Gemini with `--dry-run`.
Retry failed rows with `--retry-errors`; regenerate only the report with `--report-only`.
Resume an interrupted run with `--resume`: error-free rows already in `--raw` for the same prompt version are reused and only the missing (food, lang, repeat) cells are called.
Each raw row records `prompt_version`; `encoder_version` is `model_id@prompt_version`.

Merge raw results with `.venv\Scripts\python -m encoder.merge PATH [--replace-llm] [--arbitration-report] [--only-dimension ir94e]`.
`--only-dimension ir94e` writes only that dimension into entries that already exist: the level, `reason.ir94e`, `confidence.ir94e`, `arbitration.ir94e` (when the languages disagreed) and `encoder_version_by_dimension.ir94e`; key, aliases, display, the other levels, reasons, confidences, `review` and `encoder_version` are left byte-identical (test: `tests/test_merge_validation.py`). Every incoming dish must already be in the dictionary, else nothing is written. `human_checked` entries are filled too (their review covered sugar, bitter and water only) and each is printed for the owner to check; the label is kept. The needs_review rule applies to ir94e on its four-level scale: modes two steps apart (none vs medium, low vs high) make the entry `needs_review`. Full merges are unchanged for existing entries; a full re-encode at a prompt without ir94e prints `dropped ir94e from KEY` per entry and `scripts/validate_release.py` then refuses to publish. Used 2026-09-12: `python -m encoder.merge results/encoder/stability_raw_v2_3_all.jsonl --foods encoder/foods_dictionary.json --only-dimension ir94e --arbitration-report` (174 dishes, 6 repeats, zh/en; `encoder/foods_dictionary.json` lists the 133 batch2 dishes first, then the 41 stability foods).
Per dimension, merge compares the zh and en modal levels. Agreement needs no arbitration record.
For adjacent modes, the language with higher mean confidence wins; if the confidences differ by less than 0.1, the lower level is taken (`lower_level`). English is never a tie-break default.
For modes at least two steps apart, English is provisional and the entry becomes `needs_review`.
Arbitrated dimensions store zh/en/chosen levels and the `confidence`, `lower_level`, or `needs_review` rule.
`--arbitration-report` prints `dish | dimension | zh | en | chosen | rule` after merging.
`--replace-llm` replaces matching `llm_v1` and `needs_review` entries, including across encoder versions.
Merge never overwrites `human_checked` entries and reports every changed level as `key | dimension | old -> new`.
Use `--into data/another.json` to select another dictionary; JSON arrays of complete entries are also accepted.
Ambiguous names never become keys or aliases; `data/ambiguous_names.json` defines their separate dishes.
List splits with `--split-list`; paired `zh_entry`/`en_entry` inputs must agree on levels.
Sample review candidates with `--sample N --seed S`; `needs_review` entries are shown first and marked.
`--mark-checked KEY [KEY ...]` changes either `llm_v1` or `needs_review` to `human_checked`.

Dimensions are exactly sugar, bitter, water and ir94e; sugar, bitter and water take none, low, medium, high, very_high; ir94e takes none, low, medium, high.
The fixed Hz map in `encoder/levels.py` (`LEVEL_HZ`: none=0, low=25, medium=50, high=100, very_high=200) is the legacy v1 map; the grid Hz per level are in `data/grid_levels.json` (ir94e: 0 / 60 / 120 / 200).
The model assigns levels; application code owns Hz conversion.
Review values are `llm_v1`, `needs_review`, `human_checked`, and `proxy`; distant cross-language modes create `needs_review` entries.
Names are NFKC-normalized, lowercased, trimmed, and internal whitespace is collapsed.
Lookup is exact on the normalized key or a normalized alias.

## Environment

The encoder reads two variables from a gitignored `.env` at the repo root (or the environment): `GEMINI_API_KEY`, and `ENCODER_MODEL` = the exact model id, which is also written into every entry's `encoder_version`. Nothing in the site needs them; the site makes no LLM calls.

## Adding a batch of dishes

1. List the dishes in a batch file (`data/batch2_dishes.json`: key = dictionary key = sprite slug, en/zh display names, section) and derive the food list the encoder consumes (`encoder/foods_batch2.json`, one object per dish with zh, en, key and section; every field travels with each raw record).
2. Stability run on that list only: `python -m encoder.stability --repeats 6 --langs zh,en --prompt-version encode_v2.2 --foods encoder/foods_batch2.json --raw results/encoder/stability_raw_batch2.jsonl --report docs/encoder_stability_batch2.md`.
3. Merge: `python -m encoder.merge results/encoder/stability_raw_batch2.jsonl --foods encoder/foods_batch2.json --replace-llm --arbitration-report`. The key comes from the food list, human_checked entries are never touched, and any model-proposed alias that already names another dish is dropped and printed.
4. `python scripts/augment_aliases.py --batch data/batch2_dishes.json` adds traditional characters, pinyin (spaced and joined) and English spelling variants, skipping names owned elsewhere.
5. `python scripts/batch_review.py --batch data/batch2_dishes.json --report docs/encoder_stability_batch2.md` appends the needs_review list, every confidence below 0.8, and the sanity checks (expectations per dish; disagreements are listed, the model's output is kept).
6. `python scripts/export_site_data.py`, sprites via `scripts/prep_assets.py --only-new --palette-from site/assets/dishes`, sections in `data/dish_sections.json`.

