# Encoder stability

- Model id: `gemini-3.1-flash-lite`
- Encoder version: `gemini-3.1-flash-lite@encode_v2.1`
- Prompt version: `encode_v2.1`
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
| water | 35/41 | 85.4% |

## Within-language consistency

Errors have no level and count as zero consistency for their food/language group.

| Dimension | Mean level-consistency | 100% consistent groups |
|---|---:|---:|
| water | 100.0% | 100.0% |

## Cross-language disagreements

| Food (zh / en) | Dimension | zh modal | en modal | zh reasons (one example) | en reason (one example) |
|---|---|---|---|---|---|
| 红烧肉 / braised pork belly | water | low | medium | moist solid with a thick, reduced sauce | the sauce is a savory liquid with moderate solute concentration |
| 番茄炒蛋 / tomato and egg stir-fry | water | high | medium | contains significant moisture from the tomatoes and egg juices | contains significant moisture from the tomatoes and egg juices |
| 浓缩咖啡 / espresso | water | medium | high | liquid coffee extract with moderate solute concentration | liquid base with low solute concentration relative to total volume |
| 红豆汤 / sweet red bean soup | water | high | medium | a liquid-based soup with low solute concentration | a liquid-based soup with dissolved sugar and starch |
| 苦菊 / endive | water | high | low | it has high water content typical of fresh leafy greens | a moist vegetable but not a liquid or high-water-content solution |
| 芥蓝 / gai lan | water | low | high | a moist vegetable tissue but not a liquid | high water content typical of leafy green vegetables |

## Food detail

Consistency cells show `zh/en`; a dash means that language was not requested.

| Food (zh / en) | Water modal zh/en | Water consistency | Flag |
|---|---|---:|---|
| 红烧肉 / braised pork belly | low/medium | 100.0%/100.0% | zh != en |
| 番茄炒蛋 / tomato and egg stir-fry | high/medium | 100.0%/100.0% | zh != en |
| 白米饭 / steamed white rice | low/low | 100.0%/100.0% |  |
| 饺子 / dumplings | medium/medium | 100.0%/100.0% |  |
| 披萨 / pizza | low/low | 100.0%/100.0% |  |
| 炸鸡 / fried chicken | none/none | 100.0%/100.0% |  |
| 水 / water | very_high/very_high | 100.0%/100.0% |  |
| 绿茶 / green tea | very_high/very_high | 100.0%/100.0% |  |
| 可乐 / cola | medium/medium | 100.0%/100.0% |  |
| 牛奶 / milk | high/high | 100.0%/100.0% |  |
| 珍珠奶茶 / bubble tea | medium/medium | 100.0%/100.0% |  |
| 橙汁 / orange juice | medium/medium | 100.0%/100.0% |  |
| 啤酒 / beer | high/high | 100.0%/100.0% |  |
| 印度淡色艾尔 / IPA beer | high/high | 100.0%/100.0% |  |
| 黑咖啡 / black coffee | high/high | 100.0%/100.0% |  |
| 拿铁 / latte | high/high | 100.0%/100.0% |  |
| 浓缩咖啡 / espresso | medium/high | 100.0%/100.0% | zh != en |
| 汤力水 / tonic water | medium/medium | 100.0%/100.0% |  |
| 蛋糕 / cake | low/low | 100.0%/100.0% |  |
| 冰淇淋 / ice cream | low/low | 100.0%/100.0% |  |
| 蜂蜜 / honey | low/low | 100.0%/100.0% |  |
| 糖果 / candy | low/low | 100.0%/100.0% |  |
| 月饼 / mooncake | low/low | 100.0%/100.0% |  |
| 红豆汤 / sweet red bean soup | high/medium | 100.0%/100.0% | zh != en |
| 苦瓜 / bitter melon | low/low | 100.0%/100.0% |  |
| 黑巧克力 / dark chocolate 85% | none/none | 100.0%/100.0% |  |
| 苦菊 / endive | high/low | 100.0%/100.0% | zh != en |
| 芥蓝 / gai lan | low/high | 100.0%/100.0% | zh != en |
| 西柚 / grapefruit | low/low | 100.0%/100.0% |  |
| 味噌汤 / miso soup | medium/medium | 100.0%/100.0% |  |
| 清汤 / clear broth | very_high/very_high | 100.0%/100.0% |  |
| 麻婆豆腐 / mapo tofu | high/high | 100.0%/100.0% |  |
| 咖喱 / curry | medium/medium | 100.0%/100.0% |  |
| 薯片 / potato chips | none/none | 100.0%/100.0% |  |
| 咸饼干 / crackers | none/none | 100.0%/100.0% |  |
| 曲奇 / cookies | low/low | 100.0%/100.0% |  |
| 坚果 / mixed nuts | none/none | 100.0%/100.0% |  |
| 牛肉干 / beef jerky | none/none | 100.0%/100.0% |  |
| 西瓜 / watermelon | low/low | 100.0%/100.0% |  |
| 苹果 / apple | low/low | 100.0%/100.0% |  |
| 香蕉 / banana | low/low | 100.0%/100.0% |  |

## Obvious errors

Heuristic keyword flags only; these are candidates for human review, not ground truth.

No heuristic obvious errors found.

## Errors

none

Purpose: estimate how much of the llm_v1 dictionary needs human review. Not a gate.
