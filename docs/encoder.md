# Dish encoder v2.1
The default prompt is `encode_v2.1`; select `encode_v1` or `encode_v2` with `--prompt-version VERSION`.
Encode Chinese: `.venv\Scripts\python -m encoder.encode "红烧肉" --lang zh [--prompt-version encode_v2.1]`.
Encode English: `.venv\Scripts\python -m encoder.encode "black coffee" --lang en`.
V2.1 retains v2's osmolarity-based water definition and adds bilingual anchor examples.
Plain water, clear tea, and clear broth are `very_high`; dilute milk and most soups are `high`; sweet/salty drinks and sauces are `medium`; moist solids and syrups are `low`; dry solids are `none`.
Sugar and bitter definitions are unchanged from `encode_v1`.

Run stability: `.venv\Scripts\python -m encoder.stability --repeats 6 --langs zh,en`.
Use `--prompt-version VERSION`; the default is `encode_v2.1`.
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
