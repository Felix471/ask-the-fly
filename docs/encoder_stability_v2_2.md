# Encoder stability

- Model id: `gemini-3.1-flash-lite`
- Encoder version: `gemini-3.1-flash-lite@encode_v2.2`
- Prompt version: `encode_v2.2`
- Response schema version: `schema_v1`
- Date: 2026-09-11
- Foods: 41
- Repeats: 6
- Languages: zh, en
- Report dimensions: water
- Total calls: 492
- Error count: 0

## Cross-language agreement

Headline metric: fraction of foods whose zh and en modal levels agree.

| Dimension | Agreeing foods | Cross-language agreement |
|---|---:|---:|
| water | 37/41 | 90.2% |

## Within-language consistency

Errors have no level and count as zero consistency for their food/language group.

| Dimension | Mean level-consistency | 100% consistent groups |
|---|---:|---:|
| water | 100.0% | 100.0% |

## Cross-language disagreements

| Food (zh / en) | Dimension | zh modal | en modal | zh reasons (one example) | en reason (one example) |
|---|---|---|---|---|---|
| 黑咖啡 / black coffee | water | high | very_high | mostly water with low solute concentration | primarily water with low solute concentration |
| 汤力水 / tonic water | water | very_high | medium | primarily carbonated water with low solute concentration | a carbonated beverage with dissolved solutes |
| 苦菊 / endive | water | medium | high | fresh leafy vegetable with high water content | high water content typical of fresh leafy vegetables |
| 芥蓝 / gai lan | water | low | high | moist vegetable tissue but not a liquid or high-water-content fruit | high water content in the stems and leaves |

## Food detail

Consistency cells show `zh/en`; a dash means that language was not requested.

| Food (zh / en) | Water modal zh/en | Water consistency | Flag |
|---|---|---:|---|
| 红烧肉 / braised pork belly | low/low | 100.0%/100.0% |  |
| 番茄炒蛋 / tomato and egg stir-fry | medium/medium | 100.0%/100.0% |  |
| 白米饭 / steamed white rice | low/low | 100.0%/100.0% |  |
| 饺子 / dumplings | low/low | 100.0%/100.0% |  |
| 披萨 / pizza | low/low | 100.0%/100.0% |  |
| 炸鸡 / fried chicken | low/low | 100.0%/100.0% |  |
| 水 / water | very_high/very_high | 100.0%/100.0% |  |
| 绿茶 / green tea | very_high/very_high | 100.0%/100.0% |  |
| 可乐 / cola | medium/medium | 100.0%/100.0% |  |
| 牛奶 / milk | high/high | 100.0%/100.0% |  |
| 珍珠奶茶 / bubble tea | medium/medium | 100.0%/100.0% |  |
| 橙汁 / orange juice | medium/medium | 100.0%/100.0% |  |
| 啤酒 / beer | high/high | 100.0%/100.0% |  |
| 印度淡色艾尔 / IPA beer | high/high | 100.0%/100.0% |  |
| 黑咖啡 / black coffee | high/very_high | 100.0%/100.0% | zh != en |
| 拿铁 / latte | high/high | 100.0%/100.0% |  |
| 浓缩咖啡 / espresso | high/high | 100.0%/100.0% |  |
| 汤力水 / tonic water | very_high/medium | 100.0%/100.0% | zh != en |
| 蛋糕 / cake | low/low | 100.0%/100.0% |  |
| 冰淇淋 / ice cream | low/low | 100.0%/100.0% |  |
| 蜂蜜 / honey | low/low | 100.0%/100.0% |  |
| 糖果 / candy | low/low | 100.0%/100.0% |  |
| 月饼 / mooncake | low/low | 100.0%/100.0% |  |
| 红豆汤 / sweet red bean soup | high/high | 100.0%/100.0% |  |
| 苦瓜 / bitter melon | medium/medium | 100.0%/100.0% |  |
| 黑巧克力 / dark chocolate 85% | none/none | 100.0%/100.0% |  |
| 苦菊 / endive | medium/high | 100.0%/100.0% | zh != en |
| 芥蓝 / gai lan | low/high | 100.0%/100.0% | zh != en |
| 西柚 / grapefruit | medium/medium | 100.0%/100.0% |  |
| 味噌汤 / miso soup | medium/medium | 100.0%/100.0% |  |
| 清汤 / clear broth | very_high/very_high | 100.0%/100.0% |  |
| 麻婆豆腐 / mapo tofu | medium/medium | 100.0%/100.0% |  |
| 咖喱 / curry | high/high | 100.0%/100.0% |  |
| 薯片 / potato chips | none/none | 100.0%/100.0% |  |
| 咸饼干 / crackers | none/none | 100.0%/100.0% |  |
| 曲奇 / cookies | low/low | 100.0%/100.0% |  |
| 坚果 / mixed nuts | none/none | 100.0%/100.0% |  |
| 牛肉干 / beef jerky | none/none | 100.0%/100.0% |  |
| 西瓜 / watermelon | medium/medium | 100.0%/100.0% |  |
| 苹果 / apple | low/low | 100.0%/100.0% |  |
| 香蕉 / banana | low/low | 100.0%/100.0% |  |

## Obvious errors

Heuristic keyword flags only; these are candidates for human review, not ground truth.

No heuristic obvious errors found.

## Errors

none

Purpose: estimate how much of the llm_v1 dictionary needs human review. Not a gate.
