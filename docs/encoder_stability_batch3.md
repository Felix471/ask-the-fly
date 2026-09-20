# Encoder stability

- Model id: `gemini-3.1-flash-lite`
- Encoder version: `gemini-3.1-flash-lite@encode_v2.3`
- Prompt version: `encode_v2.3`
- Response schema version: `schema_v2`
- Date: 2026-09-20
- Foods: 106
- Repeats: 6
- Languages: zh, en
- Report dimensions: sugar, bitter, water, ir94e
- Total calls: 1272
- Error count: 0

## Cross-language agreement

Headline metric: fraction of foods whose zh and en modal levels agree.

| Dimension | Agreeing foods | Cross-language agreement |
|---|---:|---:|
| sugar | 85/106 | 80.2% |
| bitter | 95/106 | 89.6% |
| water | 91/106 | 85.8% |
| ir94e | 95/106 | 89.6% |

## Within-language consistency

Errors have no level and count as zero consistency for their food/language group.

| Dimension | Mean level-consistency | 100% consistent groups |
|---|---:|---:|
| sugar | 100.0% | 100.0% |
| bitter | 100.0% | 100.0% |
| water | 100.0% | 100.0% |
| ir94e | 100.0% | 100.0% |

## Cross-language disagreements

| Food (zh / en) | Dimension | zh modal | en modal | zh reasons (one example) | en reason (one example) |
|---|---|---|---|---|---|
| 烂香蕉 / rotting banana | ir94e | low | medium | proteolysis during decay releases free amino acids | proteolysis releases free amino acids during decay |
| 烂番茄 / rotting tomato | sugar | low | medium | fermentation consumes sugars | fermentation breaks down complex carbohydrates into simple sugars |
| 烂番茄 / rotting tomato | water | high | medium | high moisture content from cellular breakdown | high moisture content remains as the fruit tissue breaks down |
| 变质牛奶 / sour milk | sugar | low | none | lactose is partially broken down but residual sugar remains | natural lactose is not perceived as sweet by flies |
| 变质牛奶 / sour milk | bitter | medium | low | bacterial degradation produces bitter peptides and compounds | contains lactic acid and minor fermentation byproducts |
| 变质牛奶 / sour milk | ir94e | medium | low | proteolysis releases significant free amino acids and peptides | contains small amounts of free amino acids from protein breakdown |
| 酒糟 / spent grain lees | bitter | low | medium | faint bitterness from fermentation byproducts | contains hop residues and grain husks |
| 花蜜 / nectar | water | low | medium | viscous liquid with high solute concentration | aqueous solution with high solute concentration |
| 花蜜 / nectar | ir94e | low | none | contains trace amounts of amino acids | contains negligible amounts of free amino acids or glutamate |
| 蚜虫蜜露 / aphid honeydew | water | medium | low | viscous liquid with significant water content | viscous, syrupy consistency with low free water activity |
| 蚜虫蜜露 / aphid honeydew | ir94e | low | medium | contains trace amounts of amino acids from plant sap | contains significant concentrations of free amino acids from plant phloem |
| 树汁 / tree sap | sugar | medium | high | contains dissolved sugars like sucrose and glucose | contains high concentrations of sucrose and other sugars |
| 树汁 / tree sap | water | high | medium | mostly water with dissolved solutes | viscous liquid with significant water content |
| 牙膏 / toothpaste | water | low | medium | moist paste consistency with high solute concentration | a paste with significant moisture content |
| 蜡烛 / candle | bitter | none | low | chemically inert and lacks bitter alkaloids or compounds | waxes may contain trace bitter compounds or additives |
| 电蚊香液 / mosquito coil liquid | water | medium | high | solvent base is typically a mixture of water and organic solvents | primarily a solvent-based liquid with low solute concentration |
| 醋 / vinegar | water | high | very_high | mostly water with dissolved acetic acid | mostly water with acetic acid |
| 醋 / vinegar | ir94e | low | none | contains trace amino acids from the fermentation process | does not contain significant free amino acids |
| 炸猪排 / tonkatsu | ir94e | low | medium | contains small amounts of umami from the meat and potentially soy-based dipping sauce | tonkatsu sauce is rich in umami from fermented ingredients |
| 亲子丼 / oyakodon | sugar | low | medium | contains mirin and sugar in the dashi-based sauce | the sauce is a mixture of dashi, soy sauce, and mirin/sugar |
| 荞麦面 / soba | sugar | none | low | plain buckwheat noodles have no added sugar | contains a small amount of sugar in the dipping sauce |
| 茶碗蒸 / chawanmushi | sugar | none | low | savory dish without added sugar | contains a small amount of mirin for seasoning |
| 梅干 / umeboshi | sugar | medium | none | typically processed with sugar or honey | traditional preparation is purely salty and sour |
| 日式炸鸡 / karaage | ir94e | low | medium | contains soy sauce in the marinade | heavily seasoned with soy sauce and ginger, providing significant umami |
| 杂菜 / japchae | ir94e | low | medium | contains small amounts of soy sauce or oyster sauce for seasoning | heavily seasoned with soy sauce and sesame oil, providing significant amino acids |
| 嫩豆腐汤 / sundubu jjigae | sugar | none | low | savory dish with no added sugar | contains a small amount of sugar or mirin for balance |
| 嫩豆腐汤 / sundubu jjigae | bitter | none | low | no bitter ingredients used | faint bitterness from chili powder and aromatics |
| 椰浆饭 / nasi lemak | ir94e | low | medium | contains small amounts of anchovies and sambal seasoning | Contains anchovies (ikan bilis) and sambal, which are rich in umami. |
| 绿咖喱 / green curry | water | high | medium | coconut milk base provides a high water content with moderate solutes | coconut milk base provides a medium-solute liquid consistency |
| 印度香饭 / biryani | sugar | none | low | savory dish without added sugar | contains small amounts of sugar or dried fruits in some regional variations |
| 印度香饭 / biryani | bitter | low | none | faint bitterness from whole spices like cloves and cardamom | no significant bitter ingredients |
| 扁豆咖喱 / dal | sugar | low | none | contains small amounts of sugar or sweet aromatics like onions | savory lentil dish without added sugar |
| 扁豆咖喱 / dal | bitter | low | none | spices like turmeric and cumin can have faint bitter notes | no significant bitter ingredients |
| 扁豆咖喱 / dal | ir94e | medium | low | lentils and long-simmered aromatics provide significant free amino acids | contains small amounts of aromatics and spices, sometimes a touch of tomato or onion |
| 马萨拉奶茶 / masala chai | water | medium | high | a liquid beverage with dissolved solutes | a milk-based tea drink with high water content |
| 塔吉锅 / tagine | water | high | medium | stewed dish with significant broth and moisture | stewed dish with a sauce base |
| 西班牙海鲜饭 / paella | sugar | low | none | contains trace sugar from vegetables like onions and tomatoes | savory rice dish without added sugar |
| 西班牙海鲜饭 / paella | bitter | low | none | faint bitterness from saffron and toasted rice crust | no significant bitter ingredients |
| 土豆团子 / gnocchi | ir94e | none | low | no fermented or high-glutamate ingredients typically used | often served with parmesan or light sauce |
| 可丽饼 / crepe | sugar | medium | low | typically contains sugar in the batter and often sweet fillings | batter contains minimal sugar, though toppings may vary |
| 炸肉排 / schnitzel | sugar | low | none | breading may contain a small amount of sugar | savory breaded meat dish with no added sugar |
| 碱水面包 / pretzel | bitter | low | none | The alkaline lye treatment on the crust can impart a very faint bitter note. | no significant bitter components |
| 匈牙利炖牛肉 / goulash | sugar | low | none | contains small amounts of onion and tomato sweetness | savory stew without added sugar |
| 波兰饺子 / pierogi | sugar | low | none | dough and potato fillings may have a trace of sugar | savory dumpling typically filled with potato, cheese, or meat |
| 芝士火锅 / cheese fondue | sugar | low | none | contains trace amounts of sugar from wine or bread | savory dish with no added sugar |
| 马卡龙 / macarons | sugar | very_high | high | primarily composed of sugar and almond flour | primary ingredients are sugar and almond flour |
| 肉汁奶酪薯条 / poutine | water | low | medium | moist solid dish with gravy and cheese curds | gravy provides a medium-osmolarity liquid component |
| 黑豆炖肉 / feijoada | sugar | low | none | small amount of sugar often added for braising balance | savory stew with no added sugar |
| 黑豆炖肉 / feijoada | bitter | none | low | no significant bitter ingredients | faint bitterness from black beans and cured meats |
| 黑豆炖肉 / feijoada | water | medium | high | braised dish with a sauce consistency | a stew with a significant liquid broth component |
| 酱油 / soy sauce | sugar | none | low | standard soy sauce contains no added sugar | contains small amounts of added sugar or natural carbohydrates |
| 鱼露 / fish sauce | bitter | low | none | faint bitterness from fermentation process | not inherently bitter |
| 番茄酱 / ketchup | sugar | medium | high | contains significant added sugar for balance | contains significant amounts of added sugar |
| 番茄酱 / ketchup | water | low | medium | thick, viscous paste with low free water content | viscous liquid with moderate solute concentration |
| 黄芥末 / yellow mustard | water | low | medium | a moist paste with low free water content | a condiment with a paste-like consistency containing vinegar and water |
| 是拉差辣酱 / sriracha | bitter | none | low | no significant bitter components | faint bitterness from chili peppers and garlic |
| 苹果酒 / cider | sugar | low | medium | contains residual sugars from apples but is generally fermented dry | contains residual sugars from fermented apple juice |
| 金汤力 / gin and tonic | water | high | medium | mostly diluted liquid with moderate solute concentration | it is a carbonated beverage with dissolved solutes |

## Food detail

Consistency cells show `zh/en`; a dash means that language was not requested.

| Food (zh / en) | Sugar modal zh/en | Sugar consistency | Bitter modal zh/en | Bitter consistency | Water modal zh/en | Water consistency | Ir94E modal zh/en | Ir94E consistency | Flag |
|---|---|---:|---|---:|---|---:|---|---:|---|
| 粪便 / feces | none/none | 100.0%/100.0% | high/high | 100.0%/100.0% | low/low | 100.0%/100.0% | high/high | 100.0%/100.0% |  |
| 泔水 / food waste swill | medium/medium | 100.0%/100.0% | medium/medium | 100.0%/100.0% | high/high | 100.0%/100.0% | medium/medium | 100.0%/100.0% |  |
| 烂香蕉 / rotting banana | high/high | 100.0%/100.0% | low/low | 100.0%/100.0% | medium/medium | 100.0%/100.0% | low/medium | 100.0%/100.0% | zh != en |
| 烂苹果 / rotting apple | medium/medium | 100.0%/100.0% | low/low | 100.0%/100.0% | medium/medium | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 烂番茄 / rotting tomato | low/medium | 100.0%/100.0% | medium/medium | 100.0%/100.0% | high/medium | 100.0%/100.0% | medium/medium | 100.0%/100.0% | zh != en |
| 臭鸡蛋 / rotten egg | none/none | 100.0%/100.0% | high/high | 100.0%/100.0% | medium/medium | 100.0%/100.0% | high/high | 100.0%/100.0% |  |
| 变质牛奶 / sour milk | low/none | 100.0%/100.0% | medium/low | 100.0%/100.0% | high/high | 100.0%/100.0% | medium/low | 100.0%/100.0% | zh != en |
| 酒糟 / spent grain lees | low/low | 100.0%/100.0% | low/medium | 100.0%/100.0% | low/low | 100.0%/100.0% | medium/medium | 100.0%/100.0% | zh != en |
| 发酵中的面团 / fermenting dough | low/low | 100.0%/100.0% | low/low | 100.0%/100.0% | low/low | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 泡菜汁 / kimchi brine | low/low | 100.0%/100.0% | low/low | 100.0%/100.0% | medium/medium | 100.0%/100.0% | high/high | 100.0%/100.0% |  |
| 啤酒渣 / beer dregs | low/low | 100.0%/100.0% | high/high | 100.0%/100.0% | low/low | 100.0%/100.0% | medium/medium | 100.0%/100.0% |  |
| 咖啡渣 / coffee grounds | none/none | 100.0%/100.0% | very_high/very_high | 100.0%/100.0% | low/low | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 花蜜 / nectar | very_high/very_high | 100.0%/100.0% | none/none | 100.0%/100.0% | low/medium | 100.0%/100.0% | low/none | 100.0%/100.0% | zh != en |
| 蚜虫蜜露 / aphid honeydew | very_high/very_high | 100.0%/100.0% | none/none | 100.0%/100.0% | medium/low | 100.0%/100.0% | low/medium | 100.0%/100.0% | zh != en |
| 树汁 / tree sap | medium/high | 100.0%/100.0% | low/low | 100.0%/100.0% | high/medium | 100.0%/100.0% | low/low | 100.0%/100.0% | zh != en |
| 花粉 / pollen | low/low | 100.0%/100.0% | low/low | 100.0%/100.0% | none/none | 100.0%/100.0% | medium/medium | 100.0%/100.0% |  |
| 汗水 / sweat | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% | high/high | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 眼泪 / tears | none/none | 100.0%/100.0% | none/none | 100.0%/100.0% | very_high/very_high | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 牙膏 / toothpaste | low/low | 100.0%/100.0% | high/high | 100.0%/100.0% | low/medium | 100.0%/100.0% | none/none | 100.0%/100.0% | zh != en |
| 洗洁精 / dish soap | none/none | 100.0%/100.0% | very_high/very_high | 100.0%/100.0% | high/high | 100.0%/100.0% | none/none | 100.0%/100.0% |  |
| 肥皂 / soap | none/none | 100.0%/100.0% | very_high/very_high | 100.0%/100.0% | low/low | 100.0%/100.0% | none/none | 100.0%/100.0% |  |
| 蜡烛 / candle | none/none | 100.0%/100.0% | none/low | 100.0%/100.0% | none/none | 100.0%/100.0% | none/none | 100.0%/100.0% | zh != en |
| 电蚊香液 / mosquito coil liquid | none/none | 100.0%/100.0% | very_high/very_high | 100.0%/100.0% | medium/high | 100.0%/100.0% | none/none | 100.0%/100.0% | zh != en |
| 醋 / vinegar | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% | high/very_high | 100.0%/100.0% | low/none | 100.0%/100.0% | zh != en |
| 腐乳 / furu | low/low | 100.0%/100.0% | low/low | 100.0%/100.0% | low/low | 100.0%/100.0% | high/high | 100.0%/100.0% |  |
| 大阪烧 / okonomiyaki | low/low | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% | medium/medium | 100.0%/100.0% |  |
| 烤鸡串 / yakitori | low/low | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% | medium/medium | 100.0%/100.0% |  |
| 日式煎饺 / gyoza | low/low | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% | medium/medium | 100.0%/100.0% |  |
| 炸猪排 / tonkatsu | low/low | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% | low/medium | 100.0%/100.0% | zh != en |
| 咖喱猪排饭 / katsu curry | low/low | 100.0%/100.0% | low/low | 100.0%/100.0% | low/low | 100.0%/100.0% | medium/medium | 100.0%/100.0% |  |
| 鳗鱼饭 / unagi don | medium/medium | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% | medium/medium | 100.0%/100.0% |  |
| 亲子丼 / oyakodon | low/medium | 100.0%/100.0% | none/none | 100.0%/100.0% | medium/medium | 100.0%/100.0% | medium/medium | 100.0%/100.0% | zh != en |
| 牛肉饭 / gyudon | low/low | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% | medium/medium | 100.0%/100.0% |  |
| 荞麦面 / soba | none/low | 100.0%/100.0% | low/low | 100.0%/100.0% | low/low | 100.0%/100.0% | low/low | 100.0%/100.0% | zh != en |
| 玉子烧 / tamagoyaki | low/low | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 茶碗蒸 / chawanmushi | none/low | 100.0%/100.0% | none/none | 100.0%/100.0% | high/high | 100.0%/100.0% | medium/medium | 100.0%/100.0% | zh != en |
| 鲷鱼烧 / taiyaki | high/high | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% | none/none | 100.0%/100.0% |  |
| 铜锣烧 / dorayaki | high/high | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% | none/none | 100.0%/100.0% |  |
| 梅干 / umeboshi | medium/none | 100.0%/100.0% | low/low | 100.0%/100.0% | low/low | 100.0%/100.0% | low/low | 100.0%/100.0% | zh != en |
| 日式炸鸡 / karaage | low/low | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% | low/medium | 100.0%/100.0% | zh != en |
| 泡菜汤 / kimchi jjigae | low/low | 100.0%/100.0% | low/low | 100.0%/100.0% | high/high | 100.0%/100.0% | medium/medium | 100.0%/100.0% |  |
| 参鸡汤 / samgyetang | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% | high/high | 100.0%/100.0% | medium/medium | 100.0%/100.0% |  |
| 杂菜 / japchae | low/low | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% | low/medium | 100.0%/100.0% | zh != en |
| 紫菜包饭 / kimbap | low/low | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 嫩豆腐汤 / sundubu jjigae | none/low | 100.0%/100.0% | none/low | 100.0%/100.0% | high/high | 100.0%/100.0% | medium/medium | 100.0%/100.0% | zh != en |
| 糖饼 / hotteok | high/high | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% | none/none | 100.0%/100.0% |  |
| 叻沙 / laksa | low/low | 100.0%/100.0% | low/low | 100.0%/100.0% | high/high | 100.0%/100.0% | medium/medium | 100.0%/100.0% |  |
| 椰浆饭 / nasi lemak | low/low | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% | low/medium | 100.0%/100.0% | zh != en |
| 沙爹 / satay | medium/medium | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% | medium/medium | 100.0%/100.0% |  |
| 仁当牛肉 / beef rendang | low/low | 100.0%/100.0% | low/low | 100.0%/100.0% | low/low | 100.0%/100.0% | medium/medium | 100.0%/100.0% |  |
| 越南法棍 / banh mi | low/low | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% | medium/medium | 100.0%/100.0% |  |
| 绿咖喱 / green curry | low/low | 100.0%/100.0% | low/low | 100.0%/100.0% | high/medium | 100.0%/100.0% | medium/medium | 100.0%/100.0% | zh != en |
| 芒果糯米饭 / mango sticky rice | high/high | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% | none/none | 100.0%/100.0% |  |
| 青木瓜沙拉 / som tam | medium/medium | 100.0%/100.0% | low/low | 100.0%/100.0% | medium/medium | 100.0%/100.0% | medium/medium | 100.0%/100.0% |  |
| 海南鸡饭 / hainanese chicken rice | low/low | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% | medium/medium | 100.0%/100.0% |  |
| 印度香饭 / biryani | none/low | 100.0%/100.0% | low/none | 100.0%/100.0% | low/low | 100.0%/100.0% | medium/medium | 100.0%/100.0% | zh != en |
| 黄油鸡 / butter chicken | low/low | 100.0%/100.0% | none/none | 100.0%/100.0% | medium/medium | 100.0%/100.0% | medium/medium | 100.0%/100.0% |  |
| 萨莫萨 / samosa | none/none | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 馕 / naan | none/none | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% | none/none | 100.0%/100.0% |  |
| 扁豆咖喱 / dal | low/none | 100.0%/100.0% | low/none | 100.0%/100.0% | high/high | 100.0%/100.0% | medium/low | 100.0%/100.0% | zh != en |
| 马萨拉奶茶 / masala chai | medium/medium | 100.0%/100.0% | low/low | 100.0%/100.0% | medium/high | 100.0%/100.0% | none/none | 100.0%/100.0% | zh != en |
| 法拉费 / falafel | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% | low/low | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 沙威玛 / shawarma | low/low | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% | medium/medium | 100.0%/100.0% |  |
| 果仁蜜饼 / baklava | very_high/very_high | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% | none/none | 100.0%/100.0% |  |
| 塔吉锅 / tagine | low/low | 100.0%/100.0% | none/none | 100.0%/100.0% | high/medium | 100.0%/100.0% | medium/medium | 100.0%/100.0% | zh != en |
| 库斯库斯 / couscous | none/none | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% | none/none | 100.0%/100.0% |  |
| 西非什锦饭 / jollof rice | low/low | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% | medium/medium | 100.0%/100.0% |  |
| 英吉拉 / injera | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% | low/low | 100.0%/100.0% | medium/medium | 100.0%/100.0% |  |
| 北非蛋 / shakshuka | low/low | 100.0%/100.0% | low/low | 100.0%/100.0% | medium/medium | 100.0%/100.0% | medium/medium | 100.0%/100.0% |  |
| 西班牙海鲜饭 / paella | low/none | 100.0%/100.0% | low/none | 100.0%/100.0% | low/low | 100.0%/100.0% | medium/medium | 100.0%/100.0% | zh != en |
| 意式烩饭 / risotto | none/none | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% | medium/medium | 100.0%/100.0% |  |
| 培根蛋面 / carbonara | none/none | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% | medium/medium | 100.0%/100.0% |  |
| 土豆团子 / gnocchi | none/none | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% | none/low | 100.0%/100.0% | zh != en |
| 普罗旺斯炖菜 / ratatouille | low/low | 100.0%/100.0% | low/low | 100.0%/100.0% | high/high | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 可丽饼 / crepe | medium/low | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% | none/none | 100.0%/100.0% | zh != en |
| 炸肉排 / schnitzel | low/none | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% | low/low | 100.0%/100.0% | zh != en |
| 德式香肠 / bratwurst | low/low | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% | medium/medium | 100.0%/100.0% |  |
| 碱水面包 / pretzel | none/none | 100.0%/100.0% | low/none | 100.0%/100.0% | low/low | 100.0%/100.0% | none/none | 100.0%/100.0% | zh != en |
| 匈牙利炖牛肉 / goulash | low/none | 100.0%/100.0% | low/low | 100.0%/100.0% | high/high | 100.0%/100.0% | medium/medium | 100.0%/100.0% | zh != en |
| 罗宋汤 / borscht | low/low | 100.0%/100.0% | none/none | 100.0%/100.0% | high/high | 100.0%/100.0% | medium/medium | 100.0%/100.0% |  |
| 波兰饺子 / pierogi | low/none | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% | low/low | 100.0%/100.0% | zh != en |
| 芝士火锅 / cheese fondue | low/none | 100.0%/100.0% | low/low | 100.0%/100.0% | low/low | 100.0%/100.0% | medium/medium | 100.0%/100.0% | zh != en |
| 希腊沙拉 / greek salad | low/low | 100.0%/100.0% | low/low | 100.0%/100.0% | medium/medium | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 马卡龙 / macarons | very_high/high | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% | none/none | 100.0%/100.0% | zh != en |
| 帕芙洛娃 / pavlova | very_high/very_high | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% | none/none | 100.0%/100.0% |  |
| 吉事果 / churros | high/high | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% | none/none | 100.0%/100.0% |  |
| 肉汁奶酪薯条 / poutine | low/low | 100.0%/100.0% | none/none | 100.0%/100.0% | low/medium | 100.0%/100.0% | medium/medium | 100.0%/100.0% | zh != en |
| 蛤蜊浓汤 / clam chowder | low/low | 100.0%/100.0% | none/none | 100.0%/100.0% | high/high | 100.0%/100.0% | medium/medium | 100.0%/100.0% |  |
| 烤肋排 / bbq ribs | medium/medium | 100.0%/100.0% | low/low | 100.0%/100.0% | low/low | 100.0%/100.0% | medium/medium | 100.0%/100.0% |  |
| 芝士通心粉 / mac and cheese | none/none | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% | medium/medium | 100.0%/100.0% |  |
| 酸橘汁腌鱼 / ceviche | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% | medium/medium | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 恩潘纳达 / empanada | low/low | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 黑豆炖肉 / feijoada | low/none | 100.0%/100.0% | none/low | 100.0%/100.0% | medium/high | 100.0%/100.0% | medium/medium | 100.0%/100.0% | zh != en |
| 牛油果酱 / guacamole | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% | low/low | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 澳式肉派 / meat pie | low/low | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% | medium/medium | 100.0%/100.0% |  |
| 维吉麦 / vegemite | none/none | 100.0%/100.0% | high/high | 100.0%/100.0% | low/low | 100.0%/100.0% | high/high | 100.0%/100.0% |  |
| 酱油 / soy sauce | none/low | 100.0%/100.0% | low/low | 100.0%/100.0% | medium/medium | 100.0%/100.0% | high/high | 100.0%/100.0% | zh != en |
| 鱼露 / fish sauce | none/none | 100.0%/100.0% | low/none | 100.0%/100.0% | medium/medium | 100.0%/100.0% | high/high | 100.0%/100.0% | zh != en |
| 番茄酱 / ketchup | medium/high | 100.0%/100.0% | none/none | 100.0%/100.0% | low/medium | 100.0%/100.0% | low/low | 100.0%/100.0% | zh != en |
| 黄芥末 / yellow mustard | none/none | 100.0%/100.0% | medium/medium | 100.0%/100.0% | low/medium | 100.0%/100.0% | low/low | 100.0%/100.0% | zh != en |
| 是拉差辣酱 / sriracha | medium/medium | 100.0%/100.0% | none/low | 100.0%/100.0% | medium/medium | 100.0%/100.0% | low/low | 100.0%/100.0% | zh != en |
| 蛋黄酱 / mayonnaise | low/low | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 康普茶 / kombucha | medium/medium | 100.0%/100.0% | low/low | 100.0%/100.0% | medium/medium | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 苹果酒 / cider | low/medium | 100.0%/100.0% | low/low | 100.0%/100.0% | medium/medium | 100.0%/100.0% | none/none | 100.0%/100.0% | zh != en |
| 蜂蜜酒 / mead | high/high | 100.0%/100.0% | none/none | 100.0%/100.0% | medium/medium | 100.0%/100.0% | none/none | 100.0%/100.0% |  |
| 金汤力 / gin and tonic | medium/medium | 100.0%/100.0% | very_high/very_high | 100.0%/100.0% | high/medium | 100.0%/100.0% | none/none | 100.0%/100.0% | zh != en |

## Obvious errors

Heuristic keyword flags only; these are candidates for human review, not ground truth.

No heuristic obvious errors found.

## Errors

none

Purpose: estimate review needs; the batch-3 gate follows below.

## Batch review

Batch keys: 105; merged: 105

### needs_review

| key | levels | dimension | zh | en | chosen |
|---|---|---|---|---|---|

### confidence < 0.8

| key | levels | dimension | confidence |
|---|---|---|---:|
| food-waste-swill | sugar medium · bitter medium · water high · ir94e medium | sugar | 0.70 |
| food-waste-swill | sugar medium · bitter medium · water high · ir94e medium | bitter | 0.75 |
| rotting-banana | sugar high · bitter low · water medium · ir94e medium | bitter | 0.70 |
| rotting-banana | sugar high · bitter low · water medium · ir94e medium | ir94e | 0.75 |
| rotting-apple | sugar medium · bitter low · water medium · ir94e low | bitter | 0.70 |
| rotting-apple | sugar medium · bitter low · water medium · ir94e low | ir94e | 0.70 |
| rotting-tomato | sugar low · bitter medium · water medium · ir94e medium | bitter | 0.75 |
| spent-grain-lees | sugar low · bitter low · water low · ir94e medium | bitter | 0.70 |
| fermenting-dough | sugar low · bitter low · water low · ir94e low | bitter | 0.70 |
| fermenting-dough | sugar low · bitter low · water low · ir94e low | ir94e | 0.75 |
| kimchi-brine | sugar low · bitter low · water medium · ir94e high | bitter | 0.75 |
| coffee-grounds | sugar none · bitter very_high · water low · ir94e low | ir94e | 0.70 |
| tree-sap | sugar medium · bitter low · water medium · ir94e low | bitter | 0.70 |
| tree-sap | sugar medium · bitter low · water medium · ir94e low | ir94e | 0.60 |
| pollen | sugar low · bitter low · water none · ir94e medium | bitter | 0.70 |
| sweat | sugar none · bitter low · water high · ir94e low | bitter | 0.70 |
| samosa | sugar none · bitter none · water low · ir94e low | ir94e | 0.75 |
| falafel | sugar none · bitter low · water low · ir94e low | ir94e | 0.70 |
| ceviche | sugar none · bitter low · water medium · ir94e low | bitter | 0.75 |
| guacamole | sugar none · bitter low · water low · ir94e low | ir94e | 0.78 |
| yellow-mustard | sugar none · bitter medium · water low · ir94e low | ir94e | 0.70 |
| sriracha | sugar medium · bitter none · water medium · ir94e low | ir94e | 0.75 |
| mayonnaise | sugar low · bitter none · water low · ir94e low | ir94e | 0.75 |
| kombucha | sugar medium · bitter low · water medium · ir94e low | ir94e | 0.70 |

### sanity checks (model output kept; disagreements listed)

| key | dimension | expected | model | ok |
|---|---|---|---|---|
| durian | bitter | none / low | none | yes |
| cilantro | sugar | none | none | yes |
| wasabi | sugar | none | none | yes |
| natto | sugar | none | none | yes |
| stinky-tofu | sugar | none | none | yes |
| century-egg | sugar | none | none | yes |
| sparkling-water | water | very_high / high | very_high | yes |
| black-tea | water | very_high / high | very_high | yes |
| oolong-tea | water | very_high / high | high | yes |
| americano | water | very_high / high | high | yes |
| whiskey | water | none / low / medium | low | yes |
| baijiu | water | none / low / medium | medium | yes |
| red-wine | water | none / low / medium | medium | yes |

Disagreements: 0

<!-- batch3-gate:start -->
## Batch 3 stability gate

These are the owner's batch-3 thresholds; batch 2 had none.
Each dimension requires cross-language agreement >= 90% and mean within-language consistency >= 95%.
Metrics use the report definitions and six repeats, including missing/error observations in the denominator.
All four dimensions and D07 completeness must pass. This does not approve drops or publication.

| Dimension | Cross-language agreement | Within-language consistency | Result |
|---|---:|---:|---|
| sugar | 80.19% | 100.00% | FAIL |
| bitter | 89.62% | 100.00% | FAIL |
| water | 85.85% | 100.00% | FAIL |
| ir94e | 89.62% | 100.00% | FAIL |

Every cross-language disagreement (including missing modes):

| Key | Dimension | zh modal | en modal |
|---|---|---|---|
| rotting-tomato | sugar | low | medium |
| sour-milk | sugar | low | none |
| tree-sap | sugar | medium | high |
| oyakodon | sugar | low | medium |
| soba | sugar | none | low |
| chawanmushi | sugar | none | low |
| umeboshi | sugar | medium | none |
| sundubu-jjigae | sugar | none | low |
| biryani | sugar | none | low |
| dal | sugar | low | none |
| paella | sugar | low | none |
| crepe | sugar | medium | low |
| schnitzel | sugar | low | none |
| goulash | sugar | low | none |
| pierogi | sugar | low | none |
| cheese-fondue | sugar | low | none |
| macarons | sugar | very_high | high |
| feijoada | sugar | low | none |
| soy-sauce | sugar | none | low |
| ketchup | sugar | medium | high |
| cider | sugar | low | medium |
| sour-milk | bitter | medium | low |
| spent-grain-lees | bitter | low | medium |
| candle | bitter | none | low |
| sundubu-jjigae | bitter | none | low |
| biryani | bitter | low | none |
| dal | bitter | low | none |
| paella | bitter | low | none |
| pretzel | bitter | low | none |
| feijoada | bitter | none | low |
| fish-sauce | bitter | low | none |
| sriracha | bitter | none | low |
| rotting-tomato | water | high | medium |
| nectar | water | low | medium |
| aphid-honeydew | water | medium | low |
| tree-sap | water | high | medium |
| toothpaste | water | low | medium |
| mosquito-coil-liquid | water | medium | high |
| vinegar | water | high | very_high |
| green-curry | water | high | medium |
| masala-chai | water | medium | high |
| tagine | water | high | medium |
| poutine | water | low | medium |
| feijoada | water | medium | high |
| ketchup | water | low | medium |
| yellow-mustard | water | low | medium |
| gin-and-tonic | water | high | medium |
| rotting-banana | ir94e | low | medium |
| sour-milk | ir94e | medium | low |
| nectar | ir94e | low | none |
| aphid-honeydew | ir94e | low | medium |
| vinegar | ir94e | low | none |
| tonkatsu | ir94e | low | medium |
| karaage | ir94e | low | medium |
| japchae | ir94e | low | medium |
| nasi-lemak | ir94e | low | medium |
| dal | ir94e | medium | low |
| gnocchi | ir94e | none | low |


**Batch 3: FAIL**
<!-- batch3-gate:end -->

## Owner decision on the batch-3 gate (2026-09-19)

The aggregate 90% cross-language bar was not met on any dimension (sugar 80.2%, bitter 89.6%, water 85.8%, Ir94e 89.6%); within-language consistency was 100% on all four. Batch 2 also fell short of this bar on water (86.5%), before the bar existed. The owner decided that the merge proceeds by the per-entry rule: umeboshi, the only two-level conflict (sugar zh medium / en none), is dropped; the other 105 entries are merged with the normal arbitration, because all remaining disagreements are one level apart and are arbitrated, and because the not-food entries that a threshold-driven drop would remove (nectar, aphid honeydew, tree sap) are the point of that section. The 12 entries that disagree on two or more dimensions (sour milk, dal, feijoada, rotting tomato, nectar, aphid honeydew, tree sap, vinegar, sundubu jjigae, biryani, paella, ketchup) are marked `needs_review` for the owner's hand check before release.

