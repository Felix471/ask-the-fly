# Dictionary batch 3 — v2.1.0 preparation

Batch 3 adds 105 entries to the existing 174, for 279 entries in 14 bilingual
sections, including 23 entries in Not food. The owner approved the copy (DP3),
including the bilingual README honesty row, and the sprites (DP2). The release
date 2026-09-19 is a placeholder for the reviewer to set at merge; this report
does not record a deployment or tag.

## Encoder run and gate decision

The batch used one v2.3 pass for all four dimensions (six repeats in each language),
not a v2.2 pass followed by an Ir94e-only pass: 106 candidates × 2 languages × 6
repeats = **1,272 calls, zero errors**. Within-language consistency was 100% on
all four dimensions. Cross-language agreement was sugar **80.2%**, bitter
**89.6%**, water **85.8%**, Ir94e **89.6%**. These metrics describe all 106
candidates before the drop and hand review, not the final 105 entries.

The [recorded stability gate](encoder_stability_batch3.md#batch-3-stability-gate)
required >=90% cross-language agreement and >=95% mean within-language consistency
on every dimension, plus D07 completeness. **The aggregate gate remains FAIL**:
all four cross-language measures missed the bar. No threshold was changed and
no rerun was used to obtain a pass. The source report dates its run 2026-09-20;
its owner-decision block and this release preparation are dated 2026-09-19.

The [owner decision](encoder_stability_batch3.md#owner-decision-on-the-batch-3-gate-2026-09-19)
allows the merge under the per-entry rule: drop umeboshi, the only two-level
conflict (sugar zh medium / en none), and retain the other 105 with normal
arbitration of their adjacent-level disagreements. The decision explicitly
retains nectar, aphid honeydew and tree sap, central to the Not food section;
batch 2's 86.5% water agreement predates this gate. The twelve entries disagreeing
on two or more dimensions were subsequently hand-checked before release.

Ten hand checks accept the arbitrated mappings unchanged. The two owner overrides
are recorded as design decisions in `data/dishes.json`, retaining the v2.3 encoder
version and the original language modes where present:

- **Ketchup:** sugar medium → high and Ir94e low → medium. Recorded owner reason:
  “ketchup is >20 g sugar per 100 g and concentrated tomato”.
- **Rotting tomato:** bitter medium → low and water medium → high; sugar low and
  Ir94e medium stay unchanged. Recorded owner reason: “rotting is fermentation,
  not bitterness, and tomato is glutamate-rich”. These are the recorded mapping
  rationales, not claims established by the brain model.

## Not-food provenance and sprites

All 23 Not food entries record `encoder_addendum: "addendum_not_food_v1"`.
The [versioned addendum](../encoder/prompts/addendum_not_food_v1.md) instructs the
same encoder to estimate free sugars, bitter compounds, water and free amino
acids/glutamate as presented to a landing fly, using the same four-dimension
JSON schema. Food entries do not use it. Ir94e remains amino-acid aversion.
Names, classification and estimated mappings are our design; the frozen lookup
supplies the response to those inputs. The classification and response do not
judge edibility. The approved README honesty row states this in both languages.

Eight existing dishes now own sprites previously borrowed from other dishes:
soy milk, americano, cappuccino, hot chocolate, oolong tea, sparkling water,
apple juice and milk chocolate. All 105 retained additions have their own sprites.
The art stage generated 106 candidates; the dropped umeboshi sprite was subsequently
removed from the shipping assets. Every one of the 279 dictionary entries resolves
to an existing, exclusively owned sprite; the ownership validator rejects missing,
borrowed or shared sprites. The release audit reports zero orphans; no gate was relaxed.

[Asset provenance](assets.md) records the exact prompts locally in
`assets/raw/prompts/batch3_replacements.md` and `assets/raw/prompts/batch3_new.md`,
with raw-image provenance and before/after hashes. The existing pipeline prepares
96 × 96 RGBA sprites with the established palette. Raw art and prompts remain
local; only processed sprites ship. Run `scripts/audit_sprites.py --check` for
the ownership report.

## Reproducibility and release summary

`scripts/report_batch3.py` regenerates the following marked block from
`data/dishes.json`, `data/dish_sections.json`, the batch candidate list, the frozen
174-key fixture and `sim.lookup.LookupTable` on `data/lookup_table_v1_2.json` and
`data/lookup_table_male.json`. `--check` compares the block exactly without writing.
No simulation or encoder call is needed. The 174-reference female v1.2.1 and male
v2.0.0 fixtures remain unchanged; all 279 entries must map to both lookup tables
and a shipped male trial-0 replay (70 distinct occupied cells).

The previous `releaseSummary` text, preserved verbatim from the v2.0.1 metadata:

- en: Independent male fly added; female results unchanged.
- zh: 新增独立计算的雄蝇；雌蝇结果不变。

The owner-approved replacement is “105 new entries, 14 sections, and not-food
labels.” / “新增 105 个条目、14 个分类与非食物标记。”

<!-- batch3-tables:begin -->
## Taxonomy and additions

| Section (zh / en) | Full menu | New entries |
| --- | --- | --- |
| 中餐 / Chinese | 38 | 0 |
| 日本 / Japanese | 25 | 14 |
| 韩国 / Korean | 11 | 6 |
| 东南亚 / Southeast Asian | 12 | 9 |
| 南亚 / South Asian | 6 | 5 |
| 中东与非洲 / Middle East & Africa | 10 | 8 |
| 欧洲 / European | 26 | 14 |
| 美洲与大洋洲 / Americas & Oceania | 23 | 9 |
| 甜点与零食 / Sweets & snacks | 29 | 3 |
| 饮料 / Drinks | 29 | 2 |
| 酒 / Alcohol | 9 | 3 |
| 调料 / Condiments | 12 | 9 |
| 水果与蔬菜 / Fruit & vegetables | 26 | 0 |
| 不是给人吃的 / Not food | 23 | 23 |

Total: 279 entries, including 105 additions; 23 additions are in Not food.

### 中餐 / Chinese (0 new)

No new entries.

### 日本 / Japanese (14 new)

| Key | 中文 | English |
| --- | --- | --- |
| chawanmushi | 茶碗蒸 | chawanmushi |
| dorayaki | 铜锣烧 | dorayaki |
| gyoza | 日式煎饺 | gyoza |
| gyudon | 牛肉饭 | gyudon |
| karaage | 日式炸鸡 | karaage |
| katsu-curry | 咖喱猪排饭 | katsu curry |
| okonomiyaki | 大阪烧 | okonomiyaki |
| oyakodon | 亲子丼 | oyakodon |
| soba | 荞麦面 | soba |
| taiyaki | 鲷鱼烧 | taiyaki |
| tamagoyaki | 玉子烧 | tamagoyaki |
| tonkatsu | 炸猪排 | tonkatsu |
| unagi-don | 鳗鱼饭 | unagi don |
| yakitori | 烤鸡串 | yakitori |

### 韩国 / Korean (6 new)

| Key | 中文 | English |
| --- | --- | --- |
| hotteok | 糖饼 | hotteok |
| japchae | 杂菜 | japchae |
| kimbap | 紫菜包饭 | kimbap |
| kimchi-jjigae | 泡菜汤 | kimchi jjigae |
| samgyetang | 参鸡汤 | samgyetang |
| sundubu-jjigae | 嫩豆腐汤 | sundubu jjigae |

### 东南亚 / Southeast Asian (9 new)

| Key | 中文 | English |
| --- | --- | --- |
| banh-mi | 越南法棍 | banh mi |
| beef-rendang | 仁当牛肉 | beef rendang |
| green-curry | 绿咖喱 | green curry |
| hainanese-chicken-rice | 海南鸡饭 | hainanese chicken rice |
| laksa | 叻沙 | laksa |
| mango-sticky-rice | 芒果糯米饭 | mango sticky rice |
| nasi-lemak | 椰浆饭 | nasi lemak |
| satay | 沙爹 | satay |
| som-tam | 青木瓜沙拉 | som tam |

### 南亚 / South Asian (5 new)

| Key | 中文 | English |
| --- | --- | --- |
| biryani | 印度香饭 | biryani |
| butter-chicken | 黄油鸡 | butter chicken |
| dal | 扁豆咖喱 | dal |
| naan | 馕 | naan |
| samosa | 萨莫萨 | samosa |

### 中东与非洲 / Middle East & Africa (8 new)

| Key | 中文 | English |
| --- | --- | --- |
| baklava | 果仁蜜饼 | baklava |
| couscous | 库斯库斯 | couscous |
| falafel | 法拉费 | falafel |
| injera | 英吉拉 | injera |
| jollof-rice | 西非什锦饭 | jollof rice |
| shakshuka | 北非蛋 | shakshuka |
| shawarma | 沙威玛 | shawarma |
| tagine | 塔吉锅 | tagine |

### 欧洲 / European (14 new)

| Key | 中文 | English |
| --- | --- | --- |
| borscht | 罗宋汤 | borscht |
| bratwurst | 德式香肠 | bratwurst |
| carbonara | 培根蛋面 | carbonara |
| cheese-fondue | 芝士火锅 | cheese fondue |
| crepe | 可丽饼 | crepe |
| gnocchi | 土豆团子 | gnocchi |
| goulash | 匈牙利炖牛肉 | goulash |
| greek-salad | 希腊沙拉 | greek salad |
| paella | 西班牙海鲜饭 | paella |
| pierogi | 波兰饺子 | pierogi |
| pretzel | 碱水面包 | pretzel |
| ratatouille | 普罗旺斯炖菜 | ratatouille |
| risotto | 意式烩饭 | risotto |
| schnitzel | 炸肉排 | schnitzel |

### 美洲与大洋洲 / Americas & Oceania (9 new)

| Key | 中文 | English |
| --- | --- | --- |
| bbq-ribs | 烤肋排 | bbq ribs |
| ceviche | 酸橘汁腌鱼 | ceviche |
| clam-chowder | 蛤蜊浓汤 | clam chowder |
| empanada | 恩潘纳达 | empanada |
| feijoada | 黑豆炖肉 | feijoada |
| guacamole | 牛油果酱 | guacamole |
| mac-and-cheese | 芝士通心粉 | mac and cheese |
| meat-pie | 澳式肉派 | meat pie |
| poutine | 肉汁奶酪薯条 | poutine |

### 甜点与零食 / Sweets & snacks (3 new)

| Key | 中文 | English |
| --- | --- | --- |
| churros | 吉事果 | churros |
| macarons | 马卡龙 | macarons |
| pavlova | 帕芙洛娃 | pavlova |

### 饮料 / Drinks (2 new)

| Key | 中文 | English |
| --- | --- | --- |
| kombucha | 康普茶 | kombucha |
| masala-chai | 马萨拉奶茶 | masala chai |

### 酒 / Alcohol (3 new)

| Key | 中文 | English |
| --- | --- | --- |
| cider | 苹果酒 | cider |
| gin-and-tonic | 金汤力 | gin and tonic |
| mead | 蜂蜜酒 | mead |

### 调料 / Condiments (9 new)

| Key | 中文 | English |
| --- | --- | --- |
| fish-sauce | 鱼露 | fish sauce |
| furu | 腐乳 | furu |
| ketchup | 番茄酱 | ketchup |
| mayonnaise | 蛋黄酱 | mayonnaise |
| soy-sauce | 酱油 | soy sauce |
| sriracha | 是拉差辣酱 | sriracha |
| vegemite | 维吉麦 | vegemite |
| vinegar | 醋 | vinegar |
| yellow-mustard | 黄芥末 | yellow mustard |

### 水果与蔬菜 / Fruit & vegetables (0 new)

No new entries.

### 不是给人吃的 / Not food (23 new)

| Key | 中文 | English |
| --- | --- | --- |
| aphid-honeydew | 蚜虫蜜露 | aphid honeydew |
| beer-dregs | 啤酒渣 | beer dregs |
| candle | 蜡烛 | candle |
| coffee-grounds | 咖啡渣 | coffee grounds |
| dish-soap | 洗洁精 | dish soap |
| feces | 粪便 | feces |
| fermenting-dough | 发酵中的面团 | fermenting dough |
| food-waste-swill | 泔水 | food waste swill |
| kimchi-brine | 泡菜汁 | kimchi brine |
| mosquito-coil-liquid | 电蚊香液 | mosquito coil liquid |
| nectar | 花蜜 | nectar |
| pollen | 花粉 | pollen |
| rotten-egg | 臭鸡蛋 | rotten egg |
| rotting-apple | 烂苹果 | rotting apple |
| rotting-banana | 烂香蕉 | rotting banana |
| rotting-tomato | 烂番茄 | rotting tomato |
| soap | 肥皂 | soap |
| sour-milk | 变质牛奶 | sour milk |
| spent-grain-lees | 酒糟 | spent grain lees |
| sweat | 汗水 | sweat |
| tears | 眼泪 | tears |
| toothpaste | 牙膏 | toothpaste |
| tree-sap | 树汁 | tree sap |

## Hand-checked entries

All twelve are `human_checked`. Levels below are the final owner-reviewed mappings, in sugar / bitter / water / Ir94e order; the original encoder version is retained.

| Entry | Final levels | Decision |
| --- | --- | --- |
| 蚜虫蜜露 / aphid honeydew | very_high / none / low / low | Arbitrated levels accepted unchanged. |
| 印度香饭 / biryani | none / none / low / medium | Arbitrated levels accepted unchanged. |
| 扁豆咖喱 / dal | none / none / high / medium | Arbitrated levels accepted unchanged. |
| 黑豆炖肉 / feijoada | none / none / medium / medium | Arbitrated levels accepted unchanged. |
| 番茄酱 / ketchup | high / none / low / medium | Override; see reasons above. |
| 花蜜 / nectar | very_high / none / low / none | Arbitrated levels accepted unchanged. |
| 西班牙海鲜饭 / paella | none / none / low / medium | Arbitrated levels accepted unchanged. |
| 烂番茄 / rotting tomato | low / low / high / medium | Override; see reasons above. |
| 变质牛奶 / sour milk | none / low / high / medium | Arbitrated levels accepted unchanged. |
| 嫩豆腐汤 / sundubu jjigae | none / none / high / medium | Arbitrated levels accepted unchanged. |
| 树汁 / tree sap | medium / low / medium / low | Arbitrated levels accepted unchanged. |
| 醋 / vinegar | none / low / high / none | Arbitrated levels accepted unchanged. |

## Scores from the frozen lookup tables

MN9 Hz is the stored 30-trial primary-readout mean, shown to six decimal places. States are the stored designed labels, using our existing >=5 Hz MN9/MN11D rule; they are not measured feeding or an edibility judgment. Female and male are independent experiments.

Top/bottom 10 means the first/last ten entries by exact stored MN9, including **all** ties at the cutoff. Rank ranges count entries from the indicated end; tied names are alphabetical by key, not tie-broken. Equal scores with different states have separate rows.

### Female — top 10 (including ties)

| Positions from top | MN9 Hz | State | Entries (zh / en) |
| --- | --- | --- | --- |
| 1–5 | 97.233000 | eats | 果仁蜜饼 / baklava; 糖果 / candy; 蜂蜜 / honey; 花蜜 / nectar; 帕芙洛娃 / pavlova |
| 6 | 91.767000 | eats | 棉花糖 / marshmallow |
| 7 | 86.033000 | eats | 蚜虫蜜露 / aphid honeydew |
| 8–23 | 85.833000 | eats | 苹果派 / apple pie; 蛋糕 / cake; 吉事果 / churros; 曲奇 / cookies; 甜甜圈 / donut; 铜锣烧 / dorayaki; 蛋挞 / egg tart; 糖饼 / hotteok; 冰淇淋 / ice cream; 果冻 / jelly; 马卡龙 / macarons; 芒果糯米饭 / mango sticky rice; 蜂蜜酒 / mead; 布丁 / pudding; 鲷鱼烧 / taiyaki; 汤圆 / tangyuan sweet rice balls |

### Female — bottom 10 (including ties)

| Positions from bottom | MN9 Hz | State | Entries (zh / en) |
| --- | --- | --- | --- |
| 1–78 | 0.000000 | no_response | 牛油果 / avocado; 白酒 / baijiu; 啤酒渣 / beer dregs; 印度香饭 / biryani; 苦瓜 / bitter melon; 黑咖啡 / black coffee; 蜡烛 / candle; 培根蛋面 / carbonara; 皮蛋 / century egg; 酸橘汁腌鱼 / ceviche; 奶酪 / cheese; 芝士火锅 / cheese fondue; 香菜 / cilantro; 咖啡渣 / coffee grounds; 库斯库斯 / couscous; 咸饼干 / crackers; 黄瓜 / cucumber; 黑巧克力 / dark chocolate 85%; 洗洁精 / dish soap; 饺子 / dumplings; 毛豆 / edamame; 苦菊 / endive; 浓缩咖啡 / espresso; 法拉费 / falafel; 粪便 / feces; 黑豆炖肉 / feijoada; 炸鱼薯条 / fish and chips; 鱼露 / fish sauce; 薯条 / french fries; 煎蛋 / fried egg; 炒饭 / fried rice; 芥蓝 / gai lan; 金汤力 / gin and tonic; 土豆团子 / gnocchi; 匈牙利炖牛肉 / goulash; 牛油果酱 / guacamole; 鹰嘴豆泥 / hummus; 英吉拉 / injera; 柠檬 / lemon; 芝士通心粉 / mac and cheese; 土豆泥 / mashed potatoes; 抹茶 / matcha; 坚果 / mixed nuts; 电蚊香液 / mosquito coil liquid; 馕 / naan; 纳豆 / natto; 燕麦粥 / oatmeal; 饭团 / onigiri; 西班牙海鲜饭 / paella; 波兰饺子 / pierogi; 爆米花 / popcorn; 薯片 / potato chips; 碱水面包 / pretzel; 红酒 / red wine; 意式烩饭 / risotto; 臭鸡蛋 / rotten egg; 参鸡汤 / samgyetang; 萨莫萨 / samosa; 刺身 / sashimi; 葱油饼 / scallion pancake; 炸肉排 / schnitzel; 炒蛋 / scrambled eggs; 肥皂 / soap; 荞麦面 / soba; 变质牛奶 / sour milk; 酱油 / soy sauce; 牛排 / steak; 白米饭 / steamed white rice; 包子 / steamed buns; 臭豆腐 / stinky tofu; 炒西兰花 / stir-fried broccoli; 豆腐 / tofu; 乌冬面 / udon; 维吉麦 / vegemite; 芥末 / wasabi; 威士忌 / whiskey; 黄芥末 / yellow mustard; 油条 / fried dough sticks |

### Male — top 10 (including ties)

| Positions from top | MN9 Hz | State | Entries (zh / en) |
| --- | --- | --- | --- |
| 1 | 101.967000 | eats | 棉花糖 / marshmallow |
| 2–6 | 96.800000 | eats | 果仁蜜饼 / baklava; 糖果 / candy; 蜂蜜 / honey; 花蜜 / nectar; 帕芙洛娃 / pavlova |
| 7–22 | 77.467000 | eats | 苹果派 / apple pie; 蛋糕 / cake; 吉事果 / churros; 曲奇 / cookies; 甜甜圈 / donut; 铜锣烧 / dorayaki; 蛋挞 / egg tart; 糖饼 / hotteok; 冰淇淋 / ice cream; 果冻 / jelly; 马卡龙 / macarons; 芒果糯米饭 / mango sticky rice; 蜂蜜酒 / mead; 布丁 / pudding; 鲷鱼烧 / taiyaki; 汤圆 / tangyuan sweet rice balls |

### Male — bottom 10 (including ties)

| Positions from bottom | MN9 Hz | State | Entries (zh / en) |
| --- | --- | --- | --- |
| 1–38 | 0.000000 | no_response | 美式咖啡 / americano; 啤酒渣 / beer dregs; 苦瓜 / bitter melon; 黑咖啡 / black coffee; 蜡烛 / candle; 咖啡渣 / coffee grounds; 白粥 / congee; 库斯库斯 / couscous; 咸饼干 / crackers; 黑巧克力 / dark chocolate 85%; 洗洁精 / dish soap; 苦菊 / endive; 浓缩咖啡 / espresso; 粪便 / feces; 薯条 / french fries; 金汤力 / gin and tonic; 土豆团子 / gnocchi; 西柚 / grapefruit; 凉茶 / herbal tea (liangcha); IPA啤酒 / IPA beer; 土豆泥 / mashed potatoes; 抹茶 / matcha; 电蚊香液 / mosquito coil liquid; 馕 / naan; 燕麦粥 / oatmeal; 爆米花 / popcorn; 碱水面包 / pretzel; 臭鸡蛋 / rotten egg; 肥皂 / soap; 气泡水 / sparkling water; 白米饭 / steamed white rice; 包子 / steamed buns; 豆腐 / tofu; 汤力水 / tonic water; 牙膏 / toothpaste; 维吉麦 / vegemite; 水 / water; 油条 / fried dough sticks |

### State distribution of the 105 additions

| State | Female | Male |
| --- | --- | --- |
| eats | 43 | 10 |
| mouth_moves | 19 | 0 |
| proboscis_only | 0 | 48 |
| no_response | 43 | 47 |

### Female — Not food ranking (23 entries)

| Positions from top | MN9 Hz | State | Entries (zh / en) |
| --- | --- | --- | --- |
| 1 | 97.233000 | eats | 花蜜 / nectar |
| 2 | 86.033000 | eats | 蚜虫蜜露 / aphid honeydew |
| 3 | 33.800000 | eats | 烂香蕉 / rotting banana |
| 4 | 23.633000 | eats | 烂番茄 / rotting tomato |
| 5–6 | 22.667000 | eats | 烂苹果 / rotting apple; 树汁 / tree sap |
| 7 | 17.500000 | eats | 眼泪 / tears |
| 8 | 12.400000 | eats | 泔水 / food waste swill |
| 9 | 7.400000 | eats | 发酵中的面团 / fermenting dough |
| 10 | 2.733000 | no_response | 汗水 / sweat |
| 11 | 0.667000 | mouth_moves | 酒糟 / spent grain lees |
| 12 | 0.200000 | no_response | 泡菜汁 / kimchi brine |
| 13 | 0.100000 | no_response | 牙膏 / toothpaste |
| 14 | 0.033000 | no_response | 花粉 / pollen |
| 15–23 | 0.000000 | no_response | 啤酒渣 / beer dregs; 蜡烛 / candle; 咖啡渣 / coffee grounds; 洗洁精 / dish soap; 粪便 / feces; 电蚊香液 / mosquito coil liquid; 臭鸡蛋 / rotten egg; 肥皂 / soap; 变质牛奶 / sour milk |

### Male — Not food ranking (23 entries)

| Positions from top | MN9 Hz | State | Entries (zh / en) |
| --- | --- | --- | --- |
| 1 | 96.800000 | eats | 花蜜 / nectar |
| 2 | 19.933000 | proboscis_only | 眼泪 / tears |
| 3 | 9.067000 | proboscis_only | 蚜虫蜜露 / aphid honeydew |
| 4 | 6.467000 | proboscis_only | 汗水 / sweat |
| 5 | 5.933000 | proboscis_only | 烂番茄 / rotting tomato |
| 6 | 4.333000 | no_response | 变质牛奶 / sour milk |
| 7 | 4.267000 | no_response | 发酵中的面团 / fermenting dough |
| 8–9 | 2.733000 | no_response | 烂苹果 / rotting apple; 树汁 / tree sap |
| 10 | 2.567000 | no_response | 酒糟 / spent grain lees |
| 11 | 1.100000 | no_response | 花粉 / pollen |
| 12 | 1.067000 | no_response | 泡菜汁 / kimchi brine |
| 13 | 0.700000 | no_response | 泔水 / food waste swill |
| 14 | 0.467000 | no_response | 烂香蕉 / rotting banana |
| 15–23 | 0.000000 | no_response | 啤酒渣 / beer dregs; 蜡烛 / candle; 咖啡渣 / coffee grounds; 洗洁精 / dish soap; 粪便 / feces; 电蚊香液 / mosquito coil liquid; 臭鸡蛋 / rotten egg; 肥皂 / soap; 牙膏 / toothpaste |
<!-- batch3-tables:end -->

## Release-preparation verification

- 410 Python tests and 95 Node tests pass; the expanded CI quick subset passes
  94 tests locally. The existing 174-key fixtures are unchanged.
- All 16 registered browser checks pass, including F23 and live F24 across both
  languages, female/male/both selection and both modes (12 F24 combinations).
- Twelve plate-label cases pass at 360, 390 and 430 px in both languages: the
  automatic longest-name selection and the explicit Hainanese chicken rice,
  mosquito coil liquid and food waste swill selection.
- The Chinese nectar/steak share card QR decodes to
  `https://askthefly.app/?v=2&d=k.nectar,k.steak&lang=zh&seed=0`.
- Report regeneration, release validation, copy check (zero warnings), sprite
  ownership (279 owned; zero missing/borrowed/shared/orphan sprites), male export
  verification (70 occupied replays) and `git diff --check` pass.

Local screenshots: `results/batch3/r1_ui/library_{zh,en}_390.png` and
`results/batch3/r1_ui/not_food_{zh,en}_{female,male,both}_390.png`; card:
`results/batch3/r1_card-nectar-steak-zh.png`. These are ignored review artifacts.
Hosted CI and Workers Builds remain to be checked when the branch is submitted;
merge, deployment and tagging remain with the owner.
