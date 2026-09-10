# Dish encoder v2
The default prompt is `encode_v2`; select an older prompt with `--prompt-version encode_v1`.
Encode Chinese: `.venv\Scripts\python -m encoder.encode "红烧肉" --lang zh [--prompt-version encode_v2]`.
Encode English: `.venv\Scripts\python -m encoder.encode "black coffee" --lang en`.
V2 redefines water as free water at low solute concentration (osmolarity), not liquid volume.
Thus plain water, clear tea, and clear broth are `very_high`; sweet/salty drinks and sauces are `medium`; moist solids and syrups are `low`.
Sugar and bitter definitions are unchanged from `encode_v1`.

Run stability: `.venv\Scripts\python -m encoder.stability --repeats 6 --langs zh,en`.
Use `--prompt-version VERSION`; the default is `encode_v2`.
Use `--dimensions water` (or a comma list) to restrict report tables; raw JSONL entries still contain all dimensions.
Use `--raw PATH` and `--report PATH` to choose outputs; defaults are `results/encoder/stability_raw.jsonl` and `docs/encoder_stability.md`.
Limit a new run with `--limit N`; exercise it without Gemini with `--dry-run`.
Retry failed rows with `--retry-errors`; regenerate only the report with `--report-only`.
Each raw row records `prompt_version`; `encoder_version` is `model_id@prompt_version`.

Merge raw results with `.venv\Scripts\python -m encoder.merge PATH [--replace-llm]`.
`--replace-llm` explicitly selects the default replacement of matching `llm_v1` entries even across encoder versions.
Merge never overwrites `human_checked` entries and reports every changed level as `key | dimension | old -> new`.
Use `--into data/another.json` to select another dictionary; JSON arrays of complete entries are also accepted.
Ambiguous names never become keys or aliases; `data/ambiguous_names.json` defines their separate dishes.
List splits with `--split-list`; paired `zh_entry`/`en_entry` inputs must agree on levels.
Sample review candidates with `--sample N --seed S`; record owner review with `--mark-checked KEY [KEY ...]`.

Dimensions are exactly sugar, bitter, and water; levels are none, low, medium, high, and very_high.
The fixed Hz map is none=0, low=25, medium=50, high=100, very_high=200.
The model assigns levels; application code owns Hz conversion.
Review values are `llm_v1`, `human_checked`, and `proxy`; new model entries use `llm_v1`.
Names are NFKC-normalized, lowercased, trimmed, and internal whitespace is collapsed.
Lookup is exact on the normalized key or a normalized alias.
