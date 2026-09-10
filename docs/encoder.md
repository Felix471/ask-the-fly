# Dish encoder v1
Encode Chinese: `.venv\Scripts\python -m encoder.encode "红烧肉" --lang zh`.
Encode English: `.venv\Scripts\python -m encoder.encode "black coffee" --lang en`.
Run stability: `.venv\Scripts\python -m encoder.stability --repeats 6 --langs zh,en`.
Limit a stability run with `--limit N`.
Exercise the complete pipeline without Gemini by adding `--dry-run`.
Raw calls append to `results/encoder/stability_raw.jsonl`.
The generated analysis is `docs/encoder_stability.md`.
Merge raw stability results with `.venv\Scripts\python -m encoder.merge results/encoder/stability_raw.jsonl`.
Use `--into data/another.json` to select another dictionary.
The merge command also accepts a JSON array of complete entries.
Dimensions are exactly sugar, bitter, and water.
Levels are exactly none, low, medium, high, and very_high.
The fixed Hz map is none=0, low=25, medium=50, high=100, very_high=200.
The model assigns levels; application code owns the Hz conversion.
New model entries use `review="llm_v1"`.
Allowed review values are `llm_v1`, `human_checked`, and `proxy`.
Merge never overwrites an entry marked `human_checked`.
Names are NFKC-normalized, lowercased, trimmed, and internal whitespace is collapsed.
Lookup is exact on the normalized key or any normalized alias.
