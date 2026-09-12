# Encoder stability

- Model id: `gemini-3.1-flash-lite`
- Encoder version: `gemini-3.1-flash-lite@encode_v2.3`
- Prompt version: `encode_v2.3`
- Response schema version: `schema_v2`
- Date: 2026-09-12
- Foods: 41
- Repeats: 6
- Languages: zh, en
- Report dimensions: ir94e
- Total calls: 492
- Error count: 0

## Cross-language agreement

Headline metric: fraction of foods whose zh and en modal levels agree.

| Dimension | Agreeing foods | Cross-language agreement |
|---|---:|---:|
| ir94e | 39/41 | 95.1% |

## Within-language consistency

Errors have no level and count as zero consistency for their food/language group.

| Dimension | Mean level-consistency | 100% consistent groups |
|---|---:|---:|
| ir94e | 100.0% | 100.0% |

## Cross-language disagreements

| Food (zh / en) | Dimension | zh modal | en modal | zh reasons (one example) | en reason (one example) |
|---|---|---|---|---|---|
| 芥蓝 / gai lan | ir94e | none | low | no fermented or aged ingredients in raw state | often seasoned with a small amount of oyster sauce or soy sauce |
| 清汤 / clear broth | ir94e | low | medium | contains trace amounts of amino acids from the base stock | contains free amino acids from long-simmered meat or vegetable stock |

## Food detail

Consistency cells show `zh/en`; a dash means that language was not requested.

| Food (zh / en) | Ir94E modal zh/en | Ir94E consistency | Flag |
|---|---|---:|---|
| 红烧肉 / braised pork belly | medium/medium | 100.0%/100.0% |  |
| 番茄炒蛋 / tomato and egg stir-fry | low/low | 100.0%/100.0% |  |
| 白米饭 / steamed white rice | none/none | 100.0%/100.0% |  |
| 饺子 / dumplings | medium/medium | 100.0%/100.0% |  |
| 披萨 / pizza | medium/medium | 100.0%/100.0% |  |
| 炸鸡 / fried chicken | low/low | 100.0%/100.0% |  |
| 水 / water | none/none | 100.0%/100.0% |  |
| 绿茶 / green tea | none/none | 100.0%/100.0% |  |
| 可乐 / cola | none/none | 100.0%/100.0% |  |
| 牛奶 / milk | low/low | 100.0%/100.0% |  |
| 珍珠奶茶 / bubble tea | none/none | 100.0%/100.0% |  |
| 橙汁 / orange juice | none/none | 100.0%/100.0% |  |
| 啤酒 / beer | low/low | 100.0%/100.0% |  |
| 印度淡色艾尔 / IPA beer | low/low | 100.0%/100.0% |  |
| 黑咖啡 / black coffee | none/none | 100.0%/100.0% |  |
| 拿铁 / latte | none/none | 100.0%/100.0% |  |
| 浓缩咖啡 / espresso | none/none | 100.0%/100.0% |  |
| 汤力水 / tonic water | none/none | 100.0%/100.0% |  |
| 蛋糕 / cake | none/none | 100.0%/100.0% |  |
| 冰淇淋 / ice cream | none/none | 100.0%/100.0% |  |
| 蜂蜜 / honey | none/none | 100.0%/100.0% |  |
| 糖果 / candy | none/none | 100.0%/100.0% |  |
| 月饼 / mooncake | low/low | 100.0%/100.0% |  |
| 红豆汤 / sweet red bean soup | none/none | 100.0%/100.0% |  |
| 苦瓜 / bitter melon | none/none | 100.0%/100.0% |  |
| 黑巧克力 / dark chocolate 85% | none/none | 100.0%/100.0% |  |
| 苦菊 / endive | none/none | 100.0%/100.0% |  |
| 芥蓝 / gai lan | none/low | 100.0%/100.0% | zh != en |
| 西柚 / grapefruit | none/none | 100.0%/100.0% |  |
| 味噌汤 / miso soup | medium/medium | 100.0%/100.0% |  |
| 清汤 / clear broth | low/medium | 100.0%/100.0% | zh != en |
| 麻婆豆腐 / mapo tofu | medium/medium | 100.0%/100.0% |  |
| 咖喱 / curry | medium/medium | 100.0%/100.0% |  |
| 薯片 / potato chips | low/low | 100.0%/100.0% |  |
| 咸饼干 / crackers | none/none | 100.0%/100.0% |  |
| 曲奇 / cookies | none/none | 100.0%/100.0% |  |
| 坚果 / mixed nuts | none/none | 100.0%/100.0% |  |
| 牛肉干 / beef jerky | medium/medium | 100.0%/100.0% |  |
| 西瓜 / watermelon | none/none | 100.0%/100.0% |  |
| 苹果 / apple | none/none | 100.0%/100.0% |  |
| 香蕉 / banana | none/none | 100.0%/100.0% |  |

## Obvious errors

Heuristic keyword flags only; these are candidates for human review, not ground truth.

No heuristic obvious errors found.

## Errors

none

Purpose: estimate how much of the llm_v1 dictionary needs human review. Not a gate.
