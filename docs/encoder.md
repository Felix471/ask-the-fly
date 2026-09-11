# Dish encoder v2.2
The default prompt is `encode_v2.2`; select `encode_v1`, `encode_v2` or `encode_v2.1` with `--prompt-version VERSION`.
Encode Chinese: `.venv\Scripts\python -m encoder.encode "红烧肉" --lang zh [--prompt-version encode_v2.2]`.
Encode English: `.venv\Scripts\python -m encoder.encode "black coffee" --lang en`.
V2.1 retains v2's osmolarity-based water definition and adds bilingual anchor examples.
V2.2 moves the water anchors so juicy fruit that releases juice when bitten (watermelon, orange, grapes) is `medium`, while firm or starchy fruit (apple, banana) stays `low`. Labels only: water `low` and `medium` share one grid cell (60 Hz), so MN9 results are unchanged.
**One-version rule (2026-09-11).** `data/dishes.json` is encoded at exactly one prompt version at a time: every `llm_v1` entry carries the same `encoder_version`, and a new prompt version is applied as a full re-encode of the whole stability list, never as a partial relabel. Product-owner decisions are recorded as `human_checked` entries that override individual levels (the `reason` field says what the encoder proposed); they keep the `encoder_version` of the run they were reviewed against and survive later merges. Current version: `gemini-3.1-flash-lite@encode_v2.2` (stability: `docs/encoder_stability_v2_2.md`, water agreement 37/41). Human-checked overrides at v2.2: endive and gai lan water = low; curry, espresso and sweet red bean soup water = medium; grapefruit bitter = high; tonic water sugar = high, bitter = very_high, water = medium.
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

Merge raw results with `.venv\Scripts\python -m encoder.merge PATH [--replace-llm] [--arbitration-report]`.
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

Dimensions are exactly sugar, bitter, and water; levels are none, low, medium, high, and very_high.
The fixed Hz map is none=0, low=25, medium=50, high=100, very_high=200.
The model assigns levels; application code owns Hz conversion.
Review values are `llm_v1`, `needs_review`, `human_checked`, and `proxy`; distant cross-language modes create `needs_review` entries.
Names are NFKC-normalized, lowercased, trimmed, and internal whitespace is collapsed.
Lookup is exact on the normalized key or a normalized alias.

## Adding a batch of dishes

1. List the dishes in a batch file (`data/batch2_dishes.json`: key = dictionary key = sprite slug, en/zh display names, section) and derive the food list the encoder consumes (`encoder/foods_batch2.json`, one object per dish with zh, en, key and section; every field travels with each raw record).
2. Stability run on that list only: `python -m encoder.stability --repeats 6 --langs zh,en --prompt-version encode_v2.2 --foods encoder/foods_batch2.json --raw results/encoder/stability_raw_batch2.jsonl --report docs/encoder_stability_batch2.md`.
3. Merge: `python -m encoder.merge results/encoder/stability_raw_batch2.jsonl --foods encoder/foods_batch2.json --replace-llm --arbitration-report`. The key comes from the food list, human_checked entries are never touched, and any model-proposed alias that already names another dish is dropped and printed.
4. `python scripts/augment_aliases.py --batch data/batch2_dishes.json` adds traditional characters, pinyin (spaced and joined) and English spelling variants, skipping names owned elsewhere.
5. `python scripts/batch_review.py --batch data/batch2_dishes.json --report docs/encoder_stability_batch2.md` appends the needs_review list, every confidence below 0.8, and the sanity checks (expectations per dish; disagreements are listed, the model's output is kept).
6. `python scripts/export_site_data.py`, sprites via `scripts/prep_assets.py --only-new --palette-from site/assets/dishes`, sections in `data/dish_sections.json`.

