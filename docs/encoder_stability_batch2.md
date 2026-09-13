# Encoder stability

Historical report for the three-dimension `encode_v2.2` batch (sugar, bitter and water). These measurements and review snapshots are unchanged. The same dishes later received Ir94e (amino-acid aversion) from v2.3; its results are in `docs/encoder_stability_v2_3_batch2.md`, and its provenance is recorded in `encoder_version_by_dimension`.

- Model id: `gemini-3.1-flash-lite`
- Encoder version: `gemini-3.1-flash-lite@encode_v2.2`
- Prompt version: `encode_v2.2`
- Response schema version: `schema_v1`
- Date: 2026-09-11
- Foods: 133
- Repeats: 6
- Languages: zh, en
- Report dimensions: sugar, bitter, water
- Total calls: 1596
- Error count: 0

## Cross-language agreement

Headline metric: fraction of foods whose zh and en modal levels agree.

| Dimension | Agreeing foods | Cross-language agreement |
|---|---:|---:|
| sugar | 122/133 | 91.7% |
| bitter | 123/133 | 92.5% |
| water | 115/133 | 86.5% |

## Within-language consistency

Errors have no level and count as zero consistency for their food/language group.

| Dimension | Mean level-consistency | 100% consistent groups |
|---|---:|---:|
| sugar | 100.0% | 100.0% |
| bitter | 100.0% | 100.0% |
| water | 100.0% | 100.0% |

## Cross-language disagreements

| Food (zh / en) | Dimension | zh modal | en modal | zh reasons (one example) | en reason (one example) |
|---|---|---|---|---|---|
| 鱼香肉丝 / yuxiang shredded pork | water | low | medium | it is a stir-fried dish with a thick, viscous sauce rather than a liquid soup | The dish is a stir-fry with a significant amount of sauce and juicy vegetables. |
| 糖醋里脊 / sweet and sour pork | sugar | high | medium | The dish is coated in a thick, sugar-heavy sweet and sour sauce. | the sauce is a balance of sugar and vinegar |
| 水煮鱼 / sichuan boiled fish | water | medium | high | the dish consists of fish fillets in a spicy, oily broth | the dish consists of fish fillets in a large amount of spicy broth |
| 包子 / steamed buns | sugar | low | none | dough contains trace sugar for fermentation | made from flour and water without added sugar |
| 油条 / fried dough sticks | water | none | low | a dry, porous, deep-fried solid | moist solid texture due to deep frying process |
| 豆腐脑 / douhua tofu pudding | sugar | low | medium | usually savory with soy sauce or lightly sweetened in some regions | typically served with sweet syrup or sugar water |
| 臭豆腐 / stinky tofu | sugar | low | none | often served with a savory sauce containing a small amount of sugar | savory dish without added sugar |
| 香菜 / cilantro | water | medium | low | fresh leafy vegetable with high moisture content | moist plant tissue with low solute concentration |
| 凉茶 / herbal tea (liangcha) | water | very_high | high | a decoction of herbs with very low solute concentration | a dilute aqueous infusion of herbal extracts |
| 白酒 / baijiu | water | high | medium | high water content typical of spirits | high alcohol content acts as a solvent but is not pure water |
| 韩式烤肉 / korean bbq | bitter | none | low | no significant bitter components in standard preparation | slight bitterness from charring or grilled vegetables |
| 泰式炒河粉 / pad thai | bitter | low | none | trace bitterness from lime zest or tamarind | no significant bitter ingredients |
| 鹰嘴豆泥 / hummus | bitter | none | low | ingredients are generally savory and nutty without significant bitter compounds | tahini contains sesame which has a mild natural bitterness |
| 汉堡 / hamburger | bitter | low | none | trace bitterness from toasted bun or lettuce | no significant bitter ingredients |
| 肉酱意面 / spaghetti bolognese | bitter | low | none | trace bitterness from herbs like oregano or tomato acidity | no significant bitter ingredients in standard preparation |
| 肉酱意面 / spaghetti bolognese | water | medium | low | the sauce provides a moist, medium-osmolarity environment | cooked pasta and meat sauce are moist solids |
| 塔可 / taco | water | medium | low | contains juicy vegetables like lettuce and tomatoes | moist solid with some vegetable content but not a liquid |
| 麦片 / cereal with milk | sugar | low | medium | oats have a mild natural sweetness but are generally low in sugar unless added | breakfast cereals are typically sweetened |
| 麦片 / cereal with milk | water | low | high | cooked oatmeal is a moist solid with a starchy texture | milk is a dilute liquid with low solute concentration |
| 燕麦粥 / oatmeal | water | high | low | a cooked grain porridge with high moisture content and low solute concentration | a moist, starchy solid porridge |
| 吐司 / toast | water | low | none | moist solid bread | a dry, toasted solid with very low moisture content |
| 酸奶 / yogurt | bitter | none | low | no significant bitter compounds present | contains lactic acid which has a slight sharp or tangy profile that can be perceived as mildly bitter |
| 爆米花 / popcorn | sugar | low | none | typically lightly seasoned or plain, though caramel versions exist | standard popcorn is savory and salty |
| 棉花糖 / marshmallow | water | none | low | a dry, airy solid that dissolves instantly | a soft, aerated solid with low moisture content |
| 美式咖啡 / americano | bitter | high | very_high | brewed coffee is naturally high in bitter compounds | espresso base is highly bitter |
| 美式咖啡 / americano | water | high | very_high | diluted with a large volume of water | diluted with a large amount of water |
| 乌龙茶 / oolong tea | bitter | low | medium | contains mild tannins and caffeine | contains tannins and caffeine providing a distinct bitterness |
| 乌龙茶 / oolong tea | water | very_high | high | a clear, water-based infusion | a clear, dilute aqueous infusion |
| 柠檬茶 / lemon tea | bitter | medium | low | contains tannins from tea and oils from lemon peel | faint bitterness from lemon peel and tea tannins |
| 柠檬水 / lemonade | sugar | none | medium | typically prepared as plain water with lemon slices | typically sweetened with sugar or syrup |
| 柠檬水 / lemonade | water | very_high | medium | mostly plain water with very low solute concentration | dilute aqueous solution of sugar and acid |
| 红酒 / red wine | sugar | low | none | contains trace residual sugars | dry red wine contains negligible residual sugar |
| 红酒 / red wine | water | medium | high | mostly water with dissolved solutes and alcohol | mostly water with low solute concentration |
| 玛格丽特 / margarita | sugar | low | medium | contains a small amount of triple sec or simple syrup | contains triple sec and often simple syrup |
| 芒果 / mango | sugar | medium | high | naturally sweet fruit | naturally high in fructose and glucose |
| 蓝莓 / blueberries | bitter | none | low | no significant bitter compounds | faint bitterness from skin |
| 榴莲 / durian | sugar | high | medium | contains high natural sugar content | naturally high in fructose and sucrose |
| 胡萝卜 / carrot | water | low | medium | moist solid vegetable | high water content and juicy when raw |
| 豆腐 / tofu | water | low | high | it is a moist solid with high water content but high solute density | tofu has a high water content and soft texture |

## Food detail

Consistency cells show `zh/en`; a dash means that language was not requested.

| Food (zh / en) | Sugar modal zh/en | Sugar consistency | Bitter modal zh/en | Bitter consistency | Water modal zh/en | Water consistency | Flag |
|---|---|---:|---|---:|---|---:|---|
| 火锅 / hotpot | low/low | 100.0%/100.0% | low/low | 100.0%/100.0% | high/high | 100.0%/100.0% |  |
| 牛肉面 / beef noodle soup | low/low | 100.0%/100.0% | none/none | 100.0%/100.0% | high/high | 100.0%/100.0% |  |
| 炒饭 / fried rice | none/none | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 炒面 / chow mein | low/low | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 宫保鸡丁 / kung pao chicken | low/low | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 回锅肉 / twice-cooked pork | low/low | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 鱼香肉丝 / yuxiang shredded pork | medium/medium | 100.0%/100.0% | none/none | 100.0%/100.0% | low/medium | 100.0%/100.0% | zh != en |
| 糖醋里脊 / sweet and sour pork | high/medium | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% | zh != en |
| 水煮鱼 / sichuan boiled fish | low/low | 100.0%/100.0% | low/low | 100.0%/100.0% | medium/high | 100.0%/100.0% | zh != en |
| 酸菜鱼 / pickled cabbage fish soup | low/low | 100.0%/100.0% | low/low | 100.0%/100.0% | high/high | 100.0%/100.0% |  |
| 酸辣粉 / hot and sour glass noodles | low/low | 100.0%/100.0% | low/low | 100.0%/100.0% | medium/medium | 100.0%/100.0% |  |
| 小笼包 / xiaolongbao soup dumplings | low/low | 100.0%/100.0% | none/none | 100.0%/100.0% | medium/medium | 100.0%/100.0% |  |
| 包子 / steamed buns | low/none | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% | zh != en |
| 煎饼果子 / jianbing crepe | low/low | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 油条 / fried dough sticks | none/none | 100.0%/100.0% | none/none | 100.0%/100.0% | none/low | 100.0%/100.0% | zh != en |
| 白粥 / congee | none/none | 100.0%/100.0% | none/none | 100.0%/100.0% | high/high | 100.0%/100.0% |  |
| 烤鸭 / peking duck | low/low | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 羊肉串 / lamb skewers | low/low | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 麻辣烫 / malatang | low/low | 100.0%/100.0% | low/low | 100.0%/100.0% | high/high | 100.0%/100.0% |  |
| 螺蛳粉 / luosifen snail noodles | low/low | 100.0%/100.0% | low/low | 100.0%/100.0% | high/high | 100.0%/100.0% |  |
| 凉皮 / cold skin noodles | low/low | 100.0%/100.0% | none/none | 100.0%/100.0% | medium/medium | 100.0%/100.0% |  |
| 馄饨 / wonton soup | none/none | 100.0%/100.0% | none/none | 100.0%/100.0% | high/high | 100.0%/100.0% |  |
| 葱油饼 / scallion pancake | none/none | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 清蒸鱼 / steamed fish | low/low | 100.0%/100.0% | none/none | 100.0%/100.0% | high/high | 100.0%/100.0% |  |
| 炒西兰花 / stir-fried broccoli | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 汤圆 / tangyuan sweet rice balls | high/high | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 粽子 / zongzi | low/low | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 豆腐脑 / douhua tofu pudding | low/medium | 100.0%/100.0% | none/none | 100.0%/100.0% | high/high | 100.0%/100.0% | zh != en |
| 皮蛋 / century egg | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 臭豆腐 / stinky tofu | low/none | 100.0%/100.0% | low/low | 100.0%/100.0% | low/low | 100.0%/100.0% | zh != en |
| 麻辣小龙虾 / spicy crayfish | low/low | 100.0%/100.0% | low/low | 100.0%/100.0% | medium/medium | 100.0%/100.0% |  |
| 辣条 / latiao spicy gluten strips | medium/medium | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 泡面 / instant noodles | low/low | 100.0%/100.0% | none/none | 100.0%/100.0% | high/high | 100.0%/100.0% |  |
| 蛋挞 / egg tart | high/high | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 香菜 / cilantro | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% | medium/low | 100.0%/100.0% | zh != en |
| 豆浆 / soy milk | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% | high/high | 100.0%/100.0% |  |
| 凉茶 / herbal tea (liangcha) | low/low | 100.0%/100.0% | high/high | 100.0%/100.0% | very_high/high | 100.0%/100.0% | zh != en |
| 酸梅汤 / sour plum drink | medium/medium | 100.0%/100.0% | low/low | 100.0%/100.0% | medium/medium | 100.0%/100.0% |  |
| 白酒 / baijiu | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% | high/medium | 100.0%/100.0% | zh != en |
| 寿司 / sushi | low/low | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 刺身 / sashimi | none/none | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 拉面 / ramen | low/low | 100.0%/100.0% | low/low | 100.0%/100.0% | high/high | 100.0%/100.0% |  |
| 乌冬面 / udon | none/none | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 天妇罗 / tempura | low/low | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 章鱼烧 / takoyaki | low/low | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 饭团 / onigiri | none/none | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 照烧鸡 / teriyaki chicken | medium/medium | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 寿喜烧 / sukiyaki | medium/medium | 100.0%/100.0% | none/none | 100.0%/100.0% | high/high | 100.0%/100.0% |  |
| 纳豆 / natto | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 抹茶拿铁 / matcha latte | medium/medium | 100.0%/100.0% | medium/medium | 100.0%/100.0% | high/high | 100.0%/100.0% |  |
| 抹茶 / matcha | none/none | 100.0%/100.0% | high/high | 100.0%/100.0% | none/none | 100.0%/100.0% |  |
| 芥末 / wasabi | none/none | 100.0%/100.0% | medium/medium | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 麻薯 / mochi | low/low | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 泡菜 / kimchi | low/low | 100.0%/100.0% | low/low | 100.0%/100.0% | medium/medium | 100.0%/100.0% |  |
| 石锅拌饭 / bibimbap | low/low | 100.0%/100.0% | low/low | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 韩式烤肉 / korean bbq | low/low | 100.0%/100.0% | none/low | 100.0%/100.0% | low/low | 100.0%/100.0% | zh != en |
| 辣炒年糕 / tteokbokki | medium/medium | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 部队锅 / budae jjigae army stew | low/low | 100.0%/100.0% | low/low | 100.0%/100.0% | high/high | 100.0%/100.0% |  |
| 泰式炒河粉 / pad thai | medium/medium | 100.0%/100.0% | low/none | 100.0%/100.0% | low/low | 100.0%/100.0% | zh != en |
| 冬阴功 / tom yum soup | low/low | 100.0%/100.0% | low/low | 100.0%/100.0% | high/high | 100.0%/100.0% |  |
| 越南河粉 / pho | low/low | 100.0%/100.0% | none/none | 100.0%/100.0% | high/high | 100.0%/100.0% |  |
| 烤肉卷 / kebab | low/low | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 鹰嘴豆泥 / hummus | none/none | 100.0%/100.0% | none/low | 100.0%/100.0% | low/low | 100.0%/100.0% | zh != en |
| 汉堡 / hamburger | low/low | 100.0%/100.0% | low/none | 100.0%/100.0% | low/low | 100.0%/100.0% | zh != en |
| 薯条 / french fries | none/none | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 热狗 / hot dog | low/low | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 三明治 / sandwich | low/low | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 凯撒沙拉 / caesar salad | low/low | 100.0%/100.0% | low/low | 100.0%/100.0% | medium/medium | 100.0%/100.0% |  |
| 牛排 / steak | none/none | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 肉酱意面 / spaghetti bolognese | low/low | 100.0%/100.0% | low/none | 100.0%/100.0% | medium/low | 100.0%/100.0% | zh != en |
| 千层面 / lasagna | low/low | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 塔可 / taco | low/low | 100.0%/100.0% | low/low | 100.0%/100.0% | medium/low | 100.0%/100.0% | zh != en |
| 墨西哥卷饼 / burrito | low/low | 100.0%/100.0% | low/low | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 炸鱼薯条 / fish and chips | none/none | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 培根 / bacon | low/low | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 煎蛋 / fried egg | none/none | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 炒蛋 / scrambled eggs | none/none | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 麦片 / cereal with milk | low/medium | 100.0%/100.0% | none/none | 100.0%/100.0% | low/high | 100.0%/100.0% | zh != en |
| 燕麦粥 / oatmeal | none/none | 100.0%/100.0% | none/none | 100.0%/100.0% | high/low | 100.0%/100.0% | zh != en |
| 吐司 / toast | low/low | 100.0%/100.0% | none/none | 100.0%/100.0% | low/none | 100.0%/100.0% | zh != en |
| 牛角包 / croissant | low/low | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 贝果 / bagel | low/low | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 甜甜圈 / donut | high/high | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 华夫饼 / waffle | medium/medium | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 松饼 / pancakes | low/low | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 奶酪 / cheese | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 酸奶 / yogurt | low/low | 100.0%/100.0% | none/low | 100.0%/100.0% | high/high | 100.0%/100.0% | zh != en |
| 芝士蛋糕 / cheesecake | high/high | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 提拉米苏 / tiramisu | high/high | 100.0%/100.0% | medium/medium | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 布朗尼 / brownie | high/high | 100.0%/100.0% | low/low | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 苹果派 / apple pie | high/high | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 牛奶巧克力 / milk chocolate | high/high | 100.0%/100.0% | low/low | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 花生酱 / peanut butter | low/low | 100.0%/100.0% | low/low | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 爆米花 / popcorn | low/none | 100.0%/100.0% | none/none | 100.0%/100.0% | none/none | 100.0%/100.0% | zh != en |
| 棉花糖 / marshmallow | very_high/very_high | 100.0%/100.0% | none/none | 100.0%/100.0% | none/low | 100.0%/100.0% | zh != en |
| 布丁 / pudding | high/high | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 果冻 / jelly | high/high | 100.0%/100.0% | none/none | 100.0%/100.0% | medium/medium | 100.0%/100.0% |  |
| 面包 / bread | low/low | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 土豆泥 / mashed potatoes | none/none | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 烤红薯 / roasted sweet potato | medium/medium | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 美式咖啡 / americano | none/none | 100.0%/100.0% | high/very_high | 100.0%/100.0% | high/very_high | 100.0%/100.0% | zh != en |
| 卡布奇诺 / cappuccino | none/none | 100.0%/100.0% | medium/medium | 100.0%/100.0% | high/high | 100.0%/100.0% |  |
| 热巧克力 / hot chocolate | high/high | 100.0%/100.0% | medium/medium | 100.0%/100.0% | high/high | 100.0%/100.0% |  |
| 红茶 / black tea | none/none | 100.0%/100.0% | medium/medium | 100.0%/100.0% | very_high/very_high | 100.0%/100.0% |  |
| 乌龙茶 / oolong tea | none/none | 100.0%/100.0% | low/medium | 100.0%/100.0% | very_high/high | 100.0%/100.0% | zh != en |
| 柠檬茶 / lemon tea | medium/medium | 100.0%/100.0% | medium/low | 100.0%/100.0% | medium/medium | 100.0%/100.0% | zh != en |
| 柠檬水 / lemonade | none/medium | 100.0%/100.0% | low/low | 100.0%/100.0% | very_high/medium | 100.0%/100.0% | zh != en |
| 气泡水 / sparkling water | none/none | 100.0%/100.0% | none/none | 100.0%/100.0% | very_high/very_high | 100.0%/100.0% |  |
| 苹果汁 / apple juice | medium/medium | 100.0%/100.0% | none/none | 100.0%/100.0% | medium/medium | 100.0%/100.0% |  |
| 椰子水 / coconut water | low/low | 100.0%/100.0% | none/none | 100.0%/100.0% | very_high/very_high | 100.0%/100.0% |  |
| 红酒 / red wine | low/none | 100.0%/100.0% | medium/medium | 100.0%/100.0% | medium/high | 100.0%/100.0% | zh != en |
| 威士忌 / whiskey | none/none | 100.0%/100.0% | medium/medium | 100.0%/100.0% | high/high | 100.0%/100.0% |  |
| 玛格丽特 / margarita | low/medium | 100.0%/100.0% | low/low | 100.0%/100.0% | medium/medium | 100.0%/100.0% | zh != en |
| 能量饮料 / energy drink | high/high | 100.0%/100.0% | low/low | 100.0%/100.0% | medium/medium | 100.0%/100.0% |  |
| 运动饮料 / sports drink | medium/medium | 100.0%/100.0% | none/none | 100.0%/100.0% | medium/medium | 100.0%/100.0% |  |
| 草莓 / strawberries | medium/medium | 100.0%/100.0% | none/none | 100.0%/100.0% | medium/medium | 100.0%/100.0% |  |
| 葡萄 / grapes | medium/medium | 100.0%/100.0% | none/none | 100.0%/100.0% | medium/medium | 100.0%/100.0% |  |
| 芒果 / mango | medium/high | 100.0%/100.0% | none/none | 100.0%/100.0% | medium/medium | 100.0%/100.0% | zh != en |
| 橙子 / orange | medium/medium | 100.0%/100.0% | low/low | 100.0%/100.0% | medium/medium | 100.0%/100.0% |  |
| 柠檬 / lemon | none/none | 100.0%/100.0% | medium/medium | 100.0%/100.0% | medium/medium | 100.0%/100.0% |  |
| 蓝莓 / blueberries | medium/medium | 100.0%/100.0% | none/low | 100.0%/100.0% | medium/medium | 100.0%/100.0% | zh != en |
| 榴莲 / durian | high/medium | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% | zh != en |
| 樱桃 / cherries | medium/medium | 100.0%/100.0% | none/none | 100.0%/100.0% | medium/medium | 100.0%/100.0% |  |
| 桃子 / peach | medium/medium | 100.0%/100.0% | none/none | 100.0%/100.0% | medium/medium | 100.0%/100.0% |  |
| 菠萝 / pineapple | medium/medium | 100.0%/100.0% | none/none | 100.0%/100.0% | medium/medium | 100.0%/100.0% |  |
| 牛油果 / avocado | none/none | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 番茄 / tomato | low/low | 100.0%/100.0% | none/none | 100.0%/100.0% | medium/medium | 100.0%/100.0% |  |
| 黄瓜 / cucumber | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% | medium/medium | 100.0%/100.0% |  |
| 胡萝卜 / carrot | low/low | 100.0%/100.0% | none/none | 100.0%/100.0% | low/medium | 100.0%/100.0% | zh != en |
| 玉米 / corn on the cob | low/low | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 豆腐 / tofu | none/none | 100.0%/100.0% | none/none | 100.0%/100.0% | low/high | 100.0%/100.0% | zh != en |
| 毛豆 / edamame | none/none | 100.0%/100.0% | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% |  |
| 菠菜 / spinach | none/none | 100.0%/100.0% | low/low | 100.0%/100.0% | high/high | 100.0%/100.0% |  |

## Obvious errors

Heuristic keyword flags only; these are candidates for human review, not ground truth.

No heuristic obvious errors found.

## Errors

none

Purpose: estimate how much of the llm_v1 dictionary needs human review. Not a gate.

## Batch review

Batch keys: 133; merged: 133

### needs_review

| key | levels | dimension | zh | en | chosen |
|---|---|---|---|---|---|
| cereal | sugar low · bitter none · water high | water | low | high | high |
| oatmeal | sugar none · bitter none · water low | water | high | low | low |
| lemonade | sugar medium · bitter low · water medium | sugar | none | medium | medium |
| lemonade | sugar medium · bitter low · water medium | water | very_high | medium | medium |
| tofu | sugar none · bitter none · water high | water | low | high | high |

### confidence < 0.8

| key | levels | dimension | confidence |
|---|---|---|---:|
| stinky-tofu | sugar none · bitter low · water low | bitter | 0.70 |
| ramen | sugar low · bitter low · water high | bitter | 0.75 |

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
| whiskey | water | none / low / medium | high | **no** |
| baijiu | water | none / low / medium | medium | yes |
| red-wine | water | none / low / medium | medium | yes |

Disagreements: 1

