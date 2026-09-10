# Encoder stability

- Model id: `dry-run`
- Encoder version: `dry-run@encode_v1`
- Prompt version: `encode_v1`
- Date: 2026-09-10
- Foods: 5
- Repeats: 3
- Languages: zh, en
- Total calls: 30
- Error count: 0

## Stability summary

Errors have no level and count as zero consistency for their food/language group.

| Dimension | Mean level-consistency | 100% consistent groups | Cross-language modal agreement |
|---|---:|---:|---:|
| sugar | 100.0% | 100.0% | 100.0% |
| bitter | 100.0% | 100.0% | 100.0% |
| water | 100.0% | 100.0% | 100.0% |

## Food detail

Consistency cells show `zh/en`; a dash means that language was not requested.

| Food (zh / en) | Sugar modal zh/en | Sugar consistency | Bitter modal zh/en | Bitter consistency | Water modal zh/en | Water consistency | Flag |
|---|---|---:|---|---:|---|---:|---|
| 红烧肉 / braised pork belly | low/low | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 番茄炒蛋 / tomato and egg stir-fry | none/none | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 白米饭 / steamed white rice | none/none | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 饺子 / dumplings | none/none | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 披萨 / pizza | none/none | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% |  |

## Obvious errors

Heuristic keyword flags only; these are candidates for human review, not ground truth.

No heuristic obvious errors found.

Purpose: estimate how much of the llm_v1 dictionary needs human review. Not a gate.
