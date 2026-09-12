# Encoder stability

- Model id: `gemini-3.1-flash-lite`
- Encoder version: `gemini-3.1-flash-lite@encode_v2.3`
- Prompt version: `encode_v2.3`
- Response schema version: `schema_v2`
- Date: 2026-09-12
- Foods: 133
- Repeats: 6
- Languages: zh, en
- Report dimensions: ir94e
- Total calls: 1596
- Error count: 0

## Cross-language agreement

Headline metric: fraction of foods whose zh and en modal levels agree.

| Dimension | Agreeing foods | Cross-language agreement |
|---|---:|---:|
| ir94e | 121/133 | 91.0% |

## Within-language consistency

Errors have no level and count as zero consistency for their food/language group.

| Dimension | Mean level-consistency | 100% consistent groups |
|---|---:|---:|
| ir94e | 100.0% | 100.0% |

## Cross-language disagreements

| Food (zh / en) | Dimension | zh modal | en modal | zh reasons (one example) | en reason (one example) |
|---|---|---|---|---|---|
| 炒饭 / fried rice | ir94e | medium | low | uses soy sauce and often meat or egg, providing significant free amino acids | contains small amounts of soy sauce or egg providing minor amino acids |
| 包子 / steamed buns | ir94e | low | none | filling often contains small amounts of soy sauce or meat juices | no fermented or glutamate-rich ingredients |
| 清蒸鱼 / steamed fish | ir94e | low | medium | contains a small amount of soy sauce used for seasoning | soy sauce and the natural amino acids from the fish provide a savory profile |
| 豆腐脑 / douhua tofu pudding | ir94e | medium | low | savory versions use soy sauce or meat-based stocks as a main component | trace amounts of soy-derived amino acids |
| 皮蛋 / century egg | ir94e | medium | high | high levels of free amino acids and peptides due to the alkaline fermentation process | extremely high levels of free amino acids and ammonia due to alkaline fermentation |
| 寿司 / sushi | ir94e | low | medium | contains small amounts of soy sauce and potentially fish/seaweed | contains umami from fish and soy sauce |
| 烤肉卷 / kebab | ir94e | medium | low | contains grilled meat and savory sauces rich in amino acids | contains some amino acids from meat and seasoning |
| 热狗 / hot dog | ir94e | low | medium | Contains processed meat and condiments like mustard or ketchup which provide trace amino acids. | cured meat and processed sausage contain significant free amino acids |
| 牛排 / steak | ir94e | low | medium | contains natural amino acids from muscle tissue | rich in natural glutamate from muscle tissue and browning reactions |
| 榴莲 / durian | ir94e | none | low | no significant free amino acids or glutamate sources | contains natural amino acids contributing to its savory, pungent depth |
| 豆腐 / tofu | ir94e | none | low | fresh tofu contains minimal free amino acids compared to fermented soy products | contains small amounts of naturally occurring amino acids from soy |
| 菠菜 / spinach | ir94e | low | none | contains small amounts of free amino acids | no significant free glutamate content |

## Food detail

Consistency cells show `zh/en`; a dash means that language was not requested.

| Food (zh / en) | Ir94E modal zh/en | Ir94E consistency | Flag |
|---|---|---:|---|
| 火锅 / hotpot | medium/medium | 100.0%/100.0% |  |
| 牛肉面 / beef noodle soup | medium/medium | 100.0%/100.0% |  |
| 炒饭 / fried rice | medium/low | 100.0%/100.0% | zh != en |
| 炒面 / chow mein | medium/medium | 100.0%/100.0% |  |
| 宫保鸡丁 / kung pao chicken | medium/medium | 100.0%/100.0% |  |
| 回锅肉 / twice-cooked pork | medium/medium | 100.0%/100.0% |  |
| 鱼香肉丝 / yuxiang shredded pork | medium/medium | 100.0%/100.0% |  |
| 糖醋里脊 / sweet and sour pork | low/low | 100.0%/100.0% |  |
| 水煮鱼 / sichuan boiled fish | medium/medium | 100.0%/100.0% |  |
| 酸菜鱼 / pickled cabbage fish soup | medium/medium | 100.0%/100.0% |  |
| 酸辣粉 / hot and sour glass noodles | medium/medium | 100.0%/100.0% |  |
| 小笼包 / xiaolongbao soup dumplings | medium/medium | 100.0%/100.0% |  |
| 包子 / steamed buns | low/none | 100.0%/100.0% | zh != en |
| 煎饼果子 / jianbing crepe | medium/medium | 100.0%/100.0% |  |
| 油条 / fried dough sticks | none/none | 100.0%/100.0% |  |
| 白粥 / congee | none/none | 100.0%/100.0% |  |
| 烤鸭 / peking duck | medium/medium | 100.0%/100.0% |  |
| 羊肉串 / lamb skewers | low/low | 100.0%/100.0% |  |
| 麻辣烫 / malatang | medium/medium | 100.0%/100.0% |  |
| 螺蛳粉 / luosifen snail noodles | medium/medium | 100.0%/100.0% |  |
| 凉皮 / cold skin noodles | medium/medium | 100.0%/100.0% |  |
| 馄饨 / wonton soup | medium/medium | 100.0%/100.0% |  |
| 葱油饼 / scallion pancake | low/low | 100.0%/100.0% |  |
| 清蒸鱼 / steamed fish | low/medium | 100.0%/100.0% | zh != en |
| 炒西兰花 / stir-fried broccoli | low/low | 100.0%/100.0% |  |
| 汤圆 / tangyuan sweet rice balls | none/none | 100.0%/100.0% |  |
| 粽子 / zongzi | low/low | 100.0%/100.0% |  |
| 豆腐脑 / douhua tofu pudding | medium/low | 100.0%/100.0% | zh != en |
| 皮蛋 / century egg | medium/high | 100.0%/100.0% | zh != en |
| 臭豆腐 / stinky tofu | medium/medium | 100.0%/100.0% |  |
| 麻辣小龙虾 / spicy crayfish | medium/medium | 100.0%/100.0% |  |
| 辣条 / latiao spicy gluten strips | medium/medium | 100.0%/100.0% |  |
| 泡面 / instant noodles | medium/medium | 100.0%/100.0% |  |
| 蛋挞 / egg tart | none/none | 100.0%/100.0% |  |
| 香菜 / cilantro | none/none | 100.0%/100.0% |  |
| 豆浆 / soy milk | low/low | 100.0%/100.0% |  |
| 凉茶 / herbal tea (liangcha) | none/none | 100.0%/100.0% |  |
| 酸梅汤 / sour plum drink | none/none | 100.0%/100.0% |  |
| 白酒 / baijiu | none/none | 100.0%/100.0% |  |
| 寿司 / sushi | low/medium | 100.0%/100.0% | zh != en |
| 刺身 / sashimi | low/low | 100.0%/100.0% |  |
| 拉面 / ramen | medium/medium | 100.0%/100.0% |  |
| 乌冬面 / udon | medium/medium | 100.0%/100.0% |  |
| 天妇罗 / tempura | low/low | 100.0%/100.0% |  |
| 章鱼烧 / takoyaki | medium/medium | 100.0%/100.0% |  |
| 饭团 / onigiri | low/low | 100.0%/100.0% |  |
| 照烧鸡 / teriyaki chicken | medium/medium | 100.0%/100.0% |  |
| 寿喜烧 / sukiyaki | medium/medium | 100.0%/100.0% |  |
| 纳豆 / natto | high/high | 100.0%/100.0% |  |
| 抹茶拿铁 / matcha latte | none/none | 100.0%/100.0% |  |
| 抹茶 / matcha | none/none | 100.0%/100.0% |  |
| 芥末 / wasabi | none/none | 100.0%/100.0% |  |
| 麻薯 / mochi | none/none | 100.0%/100.0% |  |
| 泡菜 / kimchi | medium/medium | 100.0%/100.0% |  |
| 石锅拌饭 / bibimbap | medium/medium | 100.0%/100.0% |  |
| 韩式烤肉 / korean bbq | medium/medium | 100.0%/100.0% |  |
| 辣炒年糕 / tteokbokki | medium/medium | 100.0%/100.0% |  |
| 部队锅 / budae jjigae army stew | medium/medium | 100.0%/100.0% |  |
| 泰式炒河粉 / pad thai | medium/medium | 100.0%/100.0% |  |
| 冬阴功 / tom yum soup | medium/medium | 100.0%/100.0% |  |
| 越南河粉 / pho | medium/medium | 100.0%/100.0% |  |
| 烤肉卷 / kebab | medium/low | 100.0%/100.0% | zh != en |
| 鹰嘴豆泥 / hummus | low/low | 100.0%/100.0% |  |
| 汉堡 / hamburger | medium/medium | 100.0%/100.0% |  |
| 薯条 / french fries | none/none | 100.0%/100.0% |  |
| 热狗 / hot dog | low/medium | 100.0%/100.0% | zh != en |
| 三明治 / sandwich | low/low | 100.0%/100.0% |  |
| 凯撒沙拉 / caesar salad | medium/medium | 100.0%/100.0% |  |
| 牛排 / steak | low/medium | 100.0%/100.0% | zh != en |
| 肉酱意面 / spaghetti bolognese | medium/medium | 100.0%/100.0% |  |
| 千层面 / lasagna | medium/medium | 100.0%/100.0% |  |
| 塔可 / taco | medium/medium | 100.0%/100.0% |  |
| 墨西哥卷饼 / burrito | medium/medium | 100.0%/100.0% |  |
| 炸鱼薯条 / fish and chips | low/low | 100.0%/100.0% |  |
| 培根 / bacon | medium/medium | 100.0%/100.0% |  |
| 煎蛋 / fried egg | low/low | 100.0%/100.0% |  |
| 炒蛋 / scrambled eggs | low/low | 100.0%/100.0% |  |
| 麦片 / cereal with milk | none/none | 100.0%/100.0% |  |
| 燕麦粥 / oatmeal | none/none | 100.0%/100.0% |  |
| 吐司 / toast | none/none | 100.0%/100.0% |  |
| 牛角包 / croissant | none/none | 100.0%/100.0% |  |
| 贝果 / bagel | none/none | 100.0%/100.0% |  |
| 甜甜圈 / donut | none/none | 100.0%/100.0% |  |
| 华夫饼 / waffle | none/none | 100.0%/100.0% |  |
| 松饼 / pancakes | none/none | 100.0%/100.0% |  |
| 奶酪 / cheese | medium/medium | 100.0%/100.0% |  |
| 酸奶 / yogurt | low/low | 100.0%/100.0% |  |
| 芝士蛋糕 / cheesecake | low/low | 100.0%/100.0% |  |
| 提拉米苏 / tiramisu | low/low | 100.0%/100.0% |  |
| 布朗尼 / brownie | none/none | 100.0%/100.0% |  |
| 苹果派 / apple pie | none/none | 100.0%/100.0% |  |
| 牛奶巧克力 / milk chocolate | none/none | 100.0%/100.0% |  |
| 花生酱 / peanut butter | low/low | 100.0%/100.0% |  |
| 爆米花 / popcorn | none/none | 100.0%/100.0% |  |
| 棉花糖 / marshmallow | none/none | 100.0%/100.0% |  |
| 布丁 / pudding | none/none | 100.0%/100.0% |  |
| 果冻 / jelly | none/none | 100.0%/100.0% |  |
| 面包 / bread | none/none | 100.0%/100.0% |  |
| 土豆泥 / mashed potatoes | none/none | 100.0%/100.0% |  |
| 烤红薯 / roasted sweet potato | none/none | 100.0%/100.0% |  |
| 美式咖啡 / americano | none/none | 100.0%/100.0% |  |
| 卡布奇诺 / cappuccino | none/none | 100.0%/100.0% |  |
| 热巧克力 / hot chocolate | none/none | 100.0%/100.0% |  |
| 红茶 / black tea | none/none | 100.0%/100.0% |  |
| 乌龙茶 / oolong tea | none/none | 100.0%/100.0% |  |
| 柠檬茶 / lemon tea | none/none | 100.0%/100.0% |  |
| 柠檬水 / lemonade | none/none | 100.0%/100.0% |  |
| 气泡水 / sparkling water | none/none | 100.0%/100.0% |  |
| 苹果汁 / apple juice | none/none | 100.0%/100.0% |  |
| 椰子水 / coconut water | none/none | 100.0%/100.0% |  |
| 红酒 / red wine | low/low | 100.0%/100.0% |  |
| 威士忌 / whiskey | none/none | 100.0%/100.0% |  |
| 玛格丽特 / margarita | none/none | 100.0%/100.0% |  |
| 能量饮料 / energy drink | none/none | 100.0%/100.0% |  |
| 运动饮料 / sports drink | none/none | 100.0%/100.0% |  |
| 草莓 / strawberries | none/none | 100.0%/100.0% |  |
| 葡萄 / grapes | none/none | 100.0%/100.0% |  |
| 芒果 / mango | none/none | 100.0%/100.0% |  |
| 橙子 / orange | none/none | 100.0%/100.0% |  |
| 柠檬 / lemon | none/none | 100.0%/100.0% |  |
| 蓝莓 / blueberries | none/none | 100.0%/100.0% |  |
| 榴莲 / durian | none/low | 100.0%/100.0% | zh != en |
| 樱桃 / cherries | none/none | 100.0%/100.0% |  |
| 桃子 / peach | none/none | 100.0%/100.0% |  |
| 菠萝 / pineapple | none/none | 100.0%/100.0% |  |
| 牛油果 / avocado | low/low | 100.0%/100.0% |  |
| 番茄 / tomato | low/low | 100.0%/100.0% |  |
| 黄瓜 / cucumber | none/none | 100.0%/100.0% |  |
| 胡萝卜 / carrot | none/none | 100.0%/100.0% |  |
| 玉米 / corn on the cob | none/none | 100.0%/100.0% |  |
| 豆腐 / tofu | none/low | 100.0%/100.0% | zh != en |
| 毛豆 / edamame | low/low | 100.0%/100.0% |  |
| 菠菜 / spinach | low/none | 100.0%/100.0% | zh != en |

## Obvious errors

Heuristic keyword flags only; these are candidates for human review, not ground truth.

No heuristic obvious errors found.

## Errors

none

Purpose: estimate how much of the llm_v1 dictionary needs human review. Not a gate.
