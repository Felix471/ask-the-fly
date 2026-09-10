# Encoder stability

- Model id: `gemini-3.1-flash-lite`
- Encoder version: `gemini-3.1-flash-lite@encode_v1`
- Prompt version: `encode_v1`
- Response schema version: `schema_v1`
- Date: 2026-09-10
- Foods: 40
- Repeats: 6
- Languages: zh, en
- Total calls: 480
- Error count: 2

## Cross-language agreement

Headline metric: fraction of foods whose zh and en modal levels agree.

| Dimension | Agreeing foods | Cross-language agreement |
|---|---:|---:|
| sugar | 37/40 | 92.5% |
| bitter | 39/40 | 97.5% |
| water | 39/40 | 97.5% |

## Within-language consistency

Errors have no level and count as zero consistency for their food/language group.

| Dimension | Mean level-consistency | 100% consistent groups |
|---|---:|---:|
| sugar | 99.2% | 96.2% |
| bitter | 99.6% | 98.8% |
| water | 99.6% | 98.8% |

## Cross-language disagreements

| Food (zh / en) | Dimension | zh modal | en modal | zh reasons (one example) | en reason (one example) |
|---|---|---|---|---|---|
| 珍珠奶茶 / bubble tea | sugar | very_high | high | contains high amounts of sugar in the milk tea base and syrup-soaked tapioca pearls | typically contains significant amounts of added syrup or sugar |
| 啤酒 / beer | water | very_high | high | primarily composed of water | primarily composed of water |
| 汤力水 / tonic water | bitter | high | very_high | contains quinine which provides a distinct bitter flavor | contains quinine which is intensely bitter |
| 薯片 / potato chips | sugar | low | none | often contains trace amounts of sugar in seasoning blends | standard potato chips are savory and contain no added sugar |
| 饼干 / crackers | sugar | medium | none | most cookies contain a significant amount of sugar for flavor and texture | typically savory and starch-based without added sweeteners |

## Food detail

Consistency cells show `zh/en`; a dash means that language was not requested.

| Food (zh / en) | Sugar modal zh/en | Sugar consistency | Bitter modal zh/en | Bitter consistency | Water modal zh/en | Water consistency | Flag |
|---|---|---:|---|---:|---|---:|---|
| 红烧肉 / braised pork belly | medium/medium | 100.0%/100.0% | none/none | 100.0%/100.0% | medium/medium | 100.0%/100.0% |  |
| 番茄炒蛋 / tomato and egg stir-fry | low/low | 100.0%/100.0% | none/none | 100.0%/100.0% | medium/medium | 100.0%/100.0% |  |
| 白米饭 / steamed white rice | low/low | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 饺子 / dumplings | low/low | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 披萨 / pizza | low/low | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 炸鸡 / fried chicken | low/low | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 水 / water | none/none | 100.0%/100.0% | none/none | 100.0%/100.0% | very_high/very_high | 100.0%/100.0% |  |
| 绿茶 / green tea | none/none | 100.0%/100.0% | medium/medium | 100.0%/100.0% | very_high/very_high | 100.0%/100.0% |  |
| 可乐 / cola | very_high/very_high | 100.0%/100.0% | low/low | 100.0%/100.0% | very_high/very_high | 100.0%/100.0% |  |
| 牛奶 / milk | low/low | 100.0%/100.0% | none/none | 100.0%/100.0% | high/high | 100.0%/100.0% |  |
| 珍珠奶茶 / bubble tea | very_high/high | 100.0%/100.0% | low/low | 100.0%/100.0% | high/high | 100.0%/100.0% | zh != en |
| 橙汁 / orange juice | high/high | 100.0%/100.0% | low/low | 100.0%/100.0% | very_high/very_high | 100.0%/100.0% |  |
| 啤酒 / beer | low/low | 100.0%/100.0% | medium/medium | 100.0%/100.0% | very_high/high | 100.0%/100.0% | zh != en |
| 印度淡色艾尔 / IPA beer | none/none | 100.0%/100.0% | high/high | 100.0%/100.0% | high/high | 100.0%/100.0% |  |
| 黑咖啡 / black coffee | none/none | 100.0%/100.0% | high/high | 100.0%/100.0% | high/high | 100.0%/100.0% |  |
| 拿铁 / latte | none/none | 100.0%/83.3% | medium/medium | 100.0%/100.0% | high/high | 100.0%/100.0% |  |
| 浓缩咖啡 / espresso | none/none | 100.0%/100.0% | very_high/very_high | 100.0%/100.0% | medium/medium | 100.0%/100.0% |  |
| 汤力水 / tonic water | high/high | 100.0%/100.0% | high/very_high | 100.0%/100.0% | very_high/very_high | 100.0%/100.0% | zh != en |
| 蛋糕 / cake | high/high | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 冰淇淋 / ice cream | high/high | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 蜂蜜 / honey | very_high/very_high | 66.7%/100.0% | none/none | 66.7%/100.0% | low/low | 66.7%/100.0% |  |
| 糖果 / candy | very_high/very_high | 100.0%/100.0% | none/none | 100.0%/100.0% | none/none | 100.0%/100.0% |  |
| 月饼 / mooncake | high/high | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 红豆汤 / sweet red bean soup | high/high | 100.0%/100.0% | none/none | 100.0%/100.0% | high/high | 100.0%/100.0% |  |
| 苦瓜 / bitter melon | none/none | 100.0%/100.0% | very_high/very_high | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 黑巧克力 / dark chocolate 85% | low/low | 100.0%/100.0% | high/high | 100.0%/100.0% | none/none | 100.0%/100.0% |  |
| 苦菊 / endive | none/none | 100.0%/100.0% | high/high | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 芥蓝 / gai lan | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 西柚 / grapefruit | low/low | 100.0%/100.0% | high/high | 100.0%/100.0% | high/high | 100.0%/100.0% |  |
| 味噌汤 / miso soup | low/low | 100.0%/100.0% | low/low | 100.0%/100.0% | high/high | 100.0%/100.0% |  |
| 清汤 / clear broth | none/none | 100.0%/100.0% | none/none | 100.0%/100.0% | very_high/very_high | 100.0%/100.0% |  |
| 麻婆豆腐 / mapo tofu | low/low | 100.0%/100.0% | low/low | 100.0%/100.0% | medium/medium | 100.0%/100.0% |  |
| 咖喱 / curry | low/low | 100.0%/100.0% | low/low | 100.0%/100.0% | medium/medium | 100.0%/100.0% |  |
| 薯片 / potato chips | low/none | 100.0%/100.0% | none/none | 100.0%/100.0% | none/none | 100.0%/100.0% | zh != en |
| 饼干 / crackers | medium/none | 100.0%/100.0% | none/none | 100.0%/100.0% | none/none | 100.0%/100.0% | zh != en |
| 坚果 / mixed nuts | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% | none/none | 100.0%/100.0% |  |
| 牛肉干 / beef jerky | low/low | 100.0%/100.0% | none/none | 100.0%/100.0% | none/none | 100.0%/100.0% |  |
| 西瓜 / watermelon | medium/medium | 100.0%/100.0% | none/none | 100.0%/100.0% | high/high | 100.0%/100.0% |  |
| 苹果 / apple | medium/medium | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 香蕉 / banana | medium/medium | 100.0%/83.3% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% |  |

## Obvious errors

Heuristic keyword flags only; these are candidates for human review, not ground truth.

- 黑巧克力 / dark chocolate 85% (zh): water is none despite liquid-name keyword.
- 黑巧克力 / dark chocolate 85% (en): water is none despite liquid-name keyword.

## Errors

- 蜂蜜 / honey; lang=zh; repeat=1; error=ClientError: 429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'You exceeded your current q
- 蜂蜜 / honey; lang=zh; repeat=2; error=ClientError: 429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'You exceeded your current q

Purpose: estimate how much of the llm_v1 dictionary needs human review. Not a gate.
