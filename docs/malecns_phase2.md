<!-- male-v1-phase2:begin -->
# Male-v1 Phase 2 grid and comparison

Completed UTC: 2026-09-19T20:05:58.446073+00:00; Brian2 2.9.0 / cython; workers 16; 400 × 30 = 12,000 trials; seed rule: 20260910 + 1000 * (cell_index % 40) + trial, trial 0..29, cell_index in the female grid's cell order; wall 6845.778 s; peak worker RSS 1.040379 GiB. Audit PASS: 12,000 trials, 156,000 readout-neuron trials, 1,296,000 Poisson-unit trials, 400 cells, 174 dishes, 15,051 pairs and 400 replays.

MaleCNS v1.0 whole CNS: 166,700 neurons, 6,242,085 edges, 89,859,938 synapses, >=5 synapses per connection and 33 autapses removed; w_syn 0.17875 mV and bilateral Tastekin-typed sugar/bitter/water/ir94e sets (34/38/17/19). Primary MN9 L10331 decides, with R16949 recorded secondary; MN11D/MN11V/CEM are per-trial three/two/six-cell means. The female uses FlyWire v783, all connections, Shiu's 0.275 mV and unilateral Shiu sets (23/42/18/18), its frozen primary MN9 and two-cell MN11D. These are two experiments side by side, not one calibrated model. Shared encoder levels and our >=5 Hz state threshold are design choices; states use unrounded 30-trial means. Ir94e is amino-acid aversion.

1. The male brain uses MaleCNS v1.0 with connections of >= 5 synapses and a synaptic weight of 0.65 x Shiu's (0.17875 mV), a calibration taken from an independent project (blendi-remade/fly-brain-minecraft) and replicated by us; the female uses FlyWire v783, all connections, Shiu's 0.275 mV.
2. The male is stimulated bilaterally with Tastekin-typed GRN sets; the female unilaterally with Shiu's sets. The two flies do not share one stimulus protocol.
3. The male brain misses one of our four behavioural gates: bitter alone at 25 Hz gives 1.07 Hz on MN9 against our 1.0 Hz limit (docs/malecns_phase0.md, M1j); invisible in the product below the 5 Hz activity threshold, but recorded.
4. When the two flies disagree, the cause may be sex, reconstruction, cell typing, sign assignment, weight, or stimulus protocol; this pipeline cannot separate them. This sentence appears on the result page whenever they disagree, not only in the README.

## R3: states over 400 cells

| state | male | female |
| --- | --- | --- |
| eats | 9 | 185 |
| mouth_moves | 0 | 52 |
| proboscis_only | 62 | 4 |
| no_response | 329 | 159 |

## R3: states over 174 dishes

| state | male | female |
| --- | --- | --- |
| eats | 12 | 96 |
| mouth_moves | 0 | 26 |
| proboscis_only | 90 | 2 |
| no_response | 72 | 50 |

| below 5 Hz dishes | male | female |
| --- | --- | --- |
| count | 72 | 76 |

Distinct occupied grid cells: female 55; male 55.

Female state (rows) × male state (columns):

| female / male | eats | mouth_moves | proboscis_only | no_response |
| --- | --- | --- | --- | --- |
| eats | 12 | 0 | 61 | 23 |
| mouth_moves | 0 | 0 | 14 | 12 |
| proboscis_only | 0 | 0 | 0 | 2 |
| no_response | 0 | 0 | 15 | 35 |

## R4: dish pairs

Agreement: 10723 / 15051 = 71.244%. Neither fly ties in 13543 pairs; strict agreement 74.585%. Both flies tie in 622 pairs.

First means the earlier dish in the frozen dictionary; ties use abs(score difference) <1e-9.

| female / male | first | second | tie |
| --- | --- | --- | --- |
| first | 5271 | 1937 | 74 |
| second | 1505 | 4830 | 83 |
| tie | 376 | 353 | 622 |

## R5: pair attribution

| quantity | pairs |
| --- | --- |
| disagreeing_pairs | 4328 |
| removed_by_water | 862 |
| removed_by_ir94e | 1459 |
| removed_by_either | 1664 |
| removed_only_by_both | 76 |
| removed_by_neither | 2664 |

“By either” is the union of the two single-channel interventions; “by neither” is its complement among disagreeing pairs, including the separately listed only-by-both subset. These categories overlap. The female scores stay fixed.

## R6: dish attribution

| quantity | count |
| --- | --- |
| dishes_lower | 103 |
| dishes_partly_water | 60 |
| dishes_fully_water | 18 |
| dishes_partly_ir94e | 53 |
| dishes_fully_ir94e | 9 |
| sum_lower | 3599 |
| sum_lower_water | 3399 |
| sum_lower_ir94e | 3606 |

Counterfactual lower counts are recomputed over every female-winning pair, so they may include newly lost pairs. Partly includes fully; ranks are 1 plus the number of strictly higher stored scores.

## R7: channel sign over dishes

| channel | fly | lower | equal | higher | dishes |
| --- | --- | --- | --- | --- | --- |
| water | male | 37 | 18 | 109 | 164 |
| water | female | 0 | 36 | 128 | 164 |
| ir94e | male | 61 | 1 | 24 | 86 |
| ir94e | female | 66 | 20 | 0 | 86 |

## Descriptive statements

The flies agree on 71.244% of the 15051 dish pairs.
The male fly's primary MN9 is below 5 Hz for 72 of 174 dishes (female 76).
Water removes 862 and Ir94e removes 1459 of the 4328 disagreeing pairs; 2664 are removed by neither.

## Every dish

| key | en | zh | sugar | bitter | water | ir94e | female_score | female_rank | female_state | male_score | male_rank | male_state | lower | lower_water | lower_ir94e |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| americano | americano | 美式咖啡 | none | high | high | none | 0.133 | 128 | no_response | 0.0 | 152 | no_response | 45 | 45 | 45 |
| apple | apple | 苹果 | medium | none | low | none | 70.567 | 20 | eats | 31.833 | 13 | proboscis_only | 0 | 0 | 9 |
| apple-juice | apple juice | 苹果汁 | medium | none | medium | none | 70.567 | 20 | eats | 31.833 | 13 | proboscis_only | 0 | 0 | 9 |
| apple-pie | apple pie | 苹果派 | high | none | low | none | 85.833 | 4 | eats | 77.467 | 4 | eats | 0 | 0 | 2 |
| avocado | avocado | 牛油果 | none | none | low | low | 0.0 | 132 | no_response | 9.033 | 72 | proboscis_only | 0 | 0 | 0 |
| bacon | bacon | 培根 | low | none | low | medium | 1.567 | 100 | mouth_moves | 10.2 | 58 | proboscis_only | 1 | 1 | 1 |
| bagel | bagel | 贝果 | low | none | low | none | 61.767 | 39 | eats | 14.4 | 38 | proboscis_only | 9 | 1 | 34 |
| baijiu | baijiu | 白酒 | none | low | medium | none | 0.0 | 132 | no_response | 3.5 | 106 | no_response | 0 | 0 | 0 |
| banana | banana | 香蕉 | medium | none | low | none | 70.567 | 20 | eats | 31.833 | 13 | proboscis_only | 0 | 0 | 9 |
| beef jerky | beef jerky | 牛肉干 | low | none | none | medium | 0.433 | 125 | mouth_moves | 4.1 | 105 | no_response | 14 | 0 | 0 |
| beef-noodle-soup | beef noodle soup | 牛肉面 | low | none | high | medium | 25.033 | 61 | eats | 15.867 | 34 | proboscis_only | 1 | 31 | 41 |
| beer | beer | 啤酒 | none | medium | high | low | 0.4 | 126 | no_response | 0.6 | 138 | no_response | 24 | 25 | 9 |
| bibimbap | bibimbap | 石锅拌饭 | low | low | low | medium | 0.667 | 114 | mouth_moves | 2.567 | 110 | no_response | 19 | 4 | 1 |
| bitter melon | bitter melon | 苦瓜 | none | very_high | medium | none | 0.0 | 132 | no_response | 0.0 | 152 | no_response | 0 | 0 | 0 |
| black coffee | black coffee | 黑咖啡 | none | very_high | high | none | 0.0 | 132 | no_response | 0.0 | 152 | no_response | 0 | 0 | 0 |
| black-tea | black tea | 红茶 | none | medium | very_high | none | 21.733 | 75 | eats | 1.233 | 128 | no_response | 67 | 98 | 53 |
| blueberries | blueberries | 蓝莓 | medium | none | medium | none | 70.567 | 20 | eats | 31.833 | 13 | proboscis_only | 0 | 0 | 9 |
| braised pork belly | braised pork belly | 红烧肉 | medium | none | low | medium | 7.967 | 90 | eats | 7.1 | 86 | proboscis_only | 26 | 0 | 0 |
| bread | bread | 面包 | low | none | low | none | 61.767 | 39 | eats | 14.4 | 38 | proboscis_only | 9 | 1 | 34 |
| brownie | brownie | 布朗尼 | high | low | low | none | 71.567 | 13 | eats | 0.533 | 140 | no_response | 127 | 120 | 111 |
| bubble tea | bubble tea | 珍珠奶茶 | high | low | medium | none | 71.567 | 13 | eats | 0.533 | 140 | no_response | 127 | 120 | 111 |
| budae-jjigae | budae jjigae army stew | 部队锅 | low | low | high | medium | 23.633 | 65 | eats | 5.933 | 95 | proboscis_only | 48 | 46 | 34 |
| burrito | burrito | 墨西哥卷饼 | low | low | low | medium | 0.667 | 114 | mouth_moves | 2.567 | 110 | no_response | 19 | 4 | 1 |
| caesar-salad | caesar salad | 凯撒沙拉 | low | low | medium | medium | 0.667 | 114 | mouth_moves | 2.567 | 110 | no_response | 19 | 4 | 1 |
| cake | cake | 蛋糕 | high | none | low | none | 85.833 | 4 | eats | 77.467 | 4 | eats | 0 | 0 | 2 |
| candy | candy | 糖果 | very_high | none | low | none | 97.233 | 1 | eats | 96.8 | 2 | eats | 1 | 1 | 1 |
| cappuccino | cappuccino | 卡布奇诺 | none | medium | high | none | 6.233 | 97 | proboscis_only | 0.767 | 136 | no_response | 51 | 76 | 37 |
| carrot | carrot | 胡萝卜 | low | none | low | none | 61.767 | 39 | eats | 14.4 | 38 | proboscis_only | 9 | 1 | 34 |
| century-egg | century egg | 皮蛋 | none | low | low | medium | 0.0 | 132 | no_response | 1.233 | 128 | no_response | 0 | 0 | 0 |
| cereal | cereal with milk | 麦片 | low | none | medium | none | 61.767 | 39 | eats | 14.4 | 38 | proboscis_only | 9 | 1 | 34 |
| cheese | cheese | 奶酪 | none | low | low | medium | 0.0 | 132 | no_response | 1.233 | 128 | no_response | 0 | 0 | 0 |
| cheesecake | cheesecake | 芝士蛋糕 | high | none | low | low | 67.367 | 36 | eats | 1.867 | 126 | no_response | 96 | 72 | 0 |
| cherries | cherries | 樱桃 | medium | none | medium | none | 70.567 | 20 | eats | 31.833 | 13 | proboscis_only | 0 | 0 | 9 |
| chow-mein | chow mein | 炒面 | low | none | low | medium | 1.567 | 100 | mouth_moves | 10.2 | 58 | proboscis_only | 1 | 1 | 1 |
| cilantro | cilantro | 香菜 | none | low | low | none | 0.0 | 132 | no_response | 3.5 | 106 | no_response | 0 | 0 | 0 |
| clear broth | clear broth | 清汤 | none | none | very_high | low | 17.5 | 78 | eats | 19.933 | 29 | proboscis_only | 0 | 58 | 96 |
| coconut-water | coconut water | 椰子水 | low | none | very_high | none | 70.8 | 19 | eats | 5.767 | 102 | proboscis_only | 89 | 25 | 77 |
| cola | cola | 可乐 | high | low | medium | none | 71.567 | 13 | eats | 0.533 | 140 | no_response | 127 | 120 | 111 |
| congee | congee | 白粥 | none | none | high | none | 22.3 | 74 | eats | 0.0 | 152 | no_response | 100 | 100 | 100 |
| cookies | cookies | 曲奇 | high | none | low | none | 85.833 | 4 | eats | 77.467 | 4 | eats | 0 | 0 | 2 |
| corn-on-the-cob | corn on the cob | 玉米 | low | none | low | none | 61.767 | 39 | eats | 14.4 | 38 | proboscis_only | 9 | 1 | 34 |
| crackers | crackers | 咸饼干 | none | none | none | none | 0.0 | 132 | no_response | 0.0 | 152 | no_response | 0 | 0 | 0 |
| croissant | croissant | 牛角包 | low | none | low | none | 61.767 | 39 | eats | 14.4 | 38 | proboscis_only | 9 | 1 | 34 |
| cucumber | cucumber | 黄瓜 | none | low | medium | none | 0.0 | 132 | no_response | 3.5 | 106 | no_response | 0 | 0 | 0 |
| curry | curry | 咖喱 | low | low | medium | medium | 0.667 | 114 | mouth_moves | 2.567 | 110 | no_response | 19 | 4 | 1 |
| dark chocolate 85% | dark chocolate 85% | 黑巧克力 | low | high | none | none | 0.0 | 132 | no_response | 0.0 | 152 | no_response | 0 | 0 | 0 |
| donut | donut | 甜甜圈 | high | none | low | none | 85.833 | 4 | eats | 77.467 | 4 | eats | 0 | 0 | 2 |
| douhua | douhua tofu pudding | 豆腐脑 | low | none | high | medium | 25.033 | 61 | eats | 15.867 | 34 | proboscis_only | 1 | 31 | 41 |
| dumplings | dumplings | 饺子 | none | none | low | medium | 0.0 | 132 | no_response | 6.467 | 92 | proboscis_only | 0 | 0 | 0 |
| durian | durian | 榴莲 | medium | none | low | none | 70.567 | 20 | eats | 31.833 | 13 | proboscis_only | 0 | 0 | 9 |
| edamame | edamame | 毛豆 | none | none | low | low | 0.0 | 132 | no_response | 9.033 | 72 | proboscis_only | 0 | 0 | 0 |
| egg-tart | egg tart | 蛋挞 | high | none | low | none | 85.833 | 4 | eats | 77.467 | 4 | eats | 0 | 0 | 2 |
| endive | endive | 苦菊 | none | high | low | none | 0.0 | 132 | no_response | 0.0 | 152 | no_response | 0 | 0 | 0 |
| energy-drink | energy drink | 能量饮料 | high | low | medium | none | 71.567 | 13 | eats | 0.533 | 140 | no_response | 127 | 120 | 111 |
| espresso | espresso | 浓缩咖啡 | none | very_high | medium | none | 0.0 | 132 | no_response | 0.0 | 152 | no_response | 0 | 0 | 0 |
| fish-and-chips | fish and chips | 炸鱼薯条 | none | none | low | low | 0.0 | 132 | no_response | 9.033 | 72 | proboscis_only | 0 | 0 | 0 |
| french-fries | french fries | 薯条 | none | none | low | none | 0.0 | 132 | no_response | 0.0 | 152 | no_response | 0 | 0 | 0 |
| fried chicken | fried chicken | 炸鸡 | low | none | low | low | 9.267 | 79 | eats | 11.1 | 47 | proboscis_only | 1 | 0 | 21 |
| fried-egg | fried egg | 煎蛋 | none | none | low | low | 0.0 | 132 | no_response | 9.033 | 72 | proboscis_only | 0 | 0 | 0 |
| fried-rice | fried rice | 炒饭 | none | none | low | low | 0.0 | 132 | no_response | 9.033 | 72 | proboscis_only | 0 | 0 | 0 |
| gai lan | gai lan | 芥蓝 | none | low | low | none | 0.0 | 132 | no_response | 3.5 | 106 | no_response | 0 | 0 | 0 |
| grapefruit | grapefruit | 西柚 | low | high | medium | none | 0.1 | 130 | no_response | 0.0 | 152 | no_response | 44 | 44 | 44 |
| grapes | grapes | 葡萄 | medium | none | medium | none | 70.567 | 20 | eats | 31.833 | 13 | proboscis_only | 0 | 0 | 9 |
| green tea | green tea | 绿茶 | none | medium | very_high | none | 21.733 | 75 | eats | 1.233 | 128 | no_response | 67 | 98 | 53 |
| hamburger | hamburger | 汉堡 | low | none | low | medium | 1.567 | 100 | mouth_moves | 10.2 | 58 | proboscis_only | 1 | 1 | 1 |
| herbal-tea | herbal tea (liangcha) | 凉茶 | low | high | high | none | 8.233 | 89 | eats | 0.0 | 152 | no_response | 85 | 85 | 85 |
| honey | honey | 蜂蜜 | very_high | none | low | none | 97.233 | 1 | eats | 96.8 | 2 | eats | 1 | 1 | 1 |
| hot-and-sour-noodles | hot and sour glass noodles | 酸辣粉 | low | low | medium | medium | 0.667 | 114 | mouth_moves | 2.567 | 110 | no_response | 19 | 4 | 1 |
| hot-chocolate | hot chocolate | 热巧克力 | high | medium | high | none | 63.833 | 38 | eats | 0.167 | 146 | no_response | 111 | 136 | 96 |
| hot-dog | hot dog | 热狗 | low | none | low | low | 9.267 | 79 | eats | 11.1 | 47 | proboscis_only | 1 | 0 | 21 |
| hotpot | hotpot | 火锅 | low | low | high | medium | 23.633 | 65 | eats | 5.933 | 95 | proboscis_only | 48 | 46 | 34 |
| hummus | hummus | 鹰嘴豆泥 | none | none | low | low | 0.0 | 132 | no_response | 9.033 | 72 | proboscis_only | 0 | 0 | 0 |
| ice cream | ice cream | 冰淇淋 | high | none | low | none | 85.833 | 4 | eats | 77.467 | 4 | eats | 0 | 0 | 2 |
| instant-noodles | instant noodles | 泡面 | low | none | high | medium | 25.033 | 61 | eats | 15.867 | 34 | proboscis_only | 1 | 31 | 41 |
| ipa beer | IPA beer | IPA啤酒 | none | high | high | none | 0.133 | 128 | no_response | 0.0 | 152 | no_response | 45 | 45 | 45 |
| jelly | jelly | 果冻 | high | none | medium | none | 85.833 | 4 | eats | 77.467 | 4 | eats | 0 | 0 | 2 |
| jianbing | jianbing crepe | 煎饼果子 | low | none | low | medium | 1.567 | 100 | mouth_moves | 10.2 | 58 | proboscis_only | 1 | 1 | 1 |
| kebab | kebab | 烤肉卷 | low | none | low | low | 9.267 | 79 | eats | 11.1 | 47 | proboscis_only | 1 | 0 | 21 |
| kimchi | kimchi | 泡菜 | low | low | medium | medium | 0.667 | 114 | mouth_moves | 2.567 | 110 | no_response | 19 | 4 | 1 |
| korean-bbq | korean bbq | 韩式烤肉 | low | none | low | medium | 1.567 | 100 | mouth_moves | 10.2 | 58 | proboscis_only | 1 | 1 | 1 |
| kung-pao-chicken | kung pao chicken | 宫保鸡丁 | low | none | low | medium | 1.567 | 100 | mouth_moves | 10.2 | 58 | proboscis_only | 1 | 1 | 1 |
| lamb-skewers | lamb skewers | 羊肉串 | low | none | low | low | 9.267 | 79 | eats | 11.1 | 47 | proboscis_only | 1 | 0 | 21 |
| lasagna | lasagna | 千层面 | low | none | low | medium | 1.567 | 100 | mouth_moves | 10.2 | 58 | proboscis_only | 1 | 1 | 1 |
| latiao | latiao spicy gluten strips | 辣条 | medium | none | low | medium | 7.967 | 90 | eats | 7.1 | 86 | proboscis_only | 26 | 0 | 0 |
| latte | latte | 拿铁 | none | medium | high | none | 6.233 | 97 | proboscis_only | 0.767 | 136 | no_response | 51 | 76 | 37 |
| lemon | lemon | 柠檬 | none | medium | medium | none | 0.0 | 132 | no_response | 0.167 | 146 | no_response | 0 | 0 | 0 |
| lemon-tea | lemon tea | 柠檬茶 | medium | low | medium | none | 54.733 | 47 | eats | 1.967 | 122 | no_response | 84 | 77 | 73 |
| lemonade | lemonade | 柠檬水 | high | low | medium | none | 71.567 | 13 | eats | 0.533 | 140 | no_response | 127 | 120 | 111 |
| liangpi | cold skin noodles | 凉皮 | low | none | medium | medium | 1.567 | 100 | mouth_moves | 10.2 | 58 | proboscis_only | 1 | 1 | 1 |
| luosifen | luosifen snail noodles | 螺蛳粉 | low | low | high | medium | 23.633 | 65 | eats | 5.933 | 95 | proboscis_only | 48 | 46 | 34 |
| malatang | malatang | 麻辣烫 | low | low | high | medium | 23.633 | 65 | eats | 5.933 | 95 | proboscis_only | 48 | 46 | 34 |
| mango | mango | 芒果 | medium | none | medium | none | 70.567 | 20 | eats | 31.833 | 13 | proboscis_only | 0 | 0 | 9 |
| mapo tofu | mapo tofu | 麻婆豆腐 | low | low | medium | medium | 0.667 | 114 | mouth_moves | 2.567 | 110 | no_response | 19 | 4 | 1 |
| margarita | margarita | 玛格丽特 | low | low | medium | none | 40.1 | 57 | eats | 4.133 | 104 | no_response | 63 | 39 | 60 |
| marshmallow | marshmallow | 棉花糖 | very_high | none | none | none | 91.767 | 3 | eats | 101.967 | 1 | eats | 0 | 0 | 0 |
| mashed-potatoes | mashed potatoes | 土豆泥 | none | none | low | none | 0.0 | 132 | no_response | 0.0 | 152 | no_response | 0 | 0 | 0 |
| matcha | matcha | 抹茶 | none | high | none | none | 0.0 | 132 | no_response | 0.0 | 152 | no_response | 0 | 0 | 0 |
| matcha-latte | matcha latte | 抹茶拿铁 | medium | medium | high | none | 48.433 | 51 | eats | 1.2 | 133 | no_response | 89 | 123 | 75 |
| milk | milk | 牛奶 | low | none | high | low | 42.467 | 54 | eats | 17.0 | 30 | proboscis_only | 1 | 11 | 48 |
| milk-chocolate | milk chocolate | 牛奶巧克力 | high | low | low | none | 71.567 | 13 | eats | 0.533 | 140 | no_response | 127 | 120 | 111 |
| miso soup | miso soup | 味噌汤 | low | low | medium | medium | 0.667 | 114 | mouth_moves | 2.567 | 110 | no_response | 19 | 4 | 1 |
| mixed nuts | mixed nuts | 坚果 | none | low | none | none | 0.0 | 132 | no_response | 0.567 | 139 | no_response | 0 | 0 | 0 |
| mochi | mochi | 麻薯 | low | none | low | none | 61.767 | 39 | eats | 14.4 | 38 | proboscis_only | 9 | 1 | 34 |
| mooncake | mooncake | 月饼 | high | none | low | low | 67.367 | 36 | eats | 1.867 | 126 | no_response | 96 | 72 | 0 |
| natto | natto | 纳豆 | none | low | low | high | 0.0 | 132 | no_response | 0.9 | 134 | no_response | 0 | 0 | 0 |
| oatmeal | oatmeal | 燕麦粥 | none | none | medium | none | 0.0 | 132 | no_response | 0.0 | 152 | no_response | 0 | 0 | 0 |
| onigiri | onigiri | 饭团 | none | none | low | low | 0.0 | 132 | no_response | 9.033 | 72 | proboscis_only | 0 | 0 | 0 |
| oolong-tea | oolong tea | 乌龙茶 | none | low | high | none | 22.633 | 72 | eats | 8.7 | 83 | proboscis_only | 37 | 64 | 32 |
| orange | orange | 橙子 | medium | low | medium | none | 54.733 | 47 | eats | 1.967 | 122 | no_response | 84 | 77 | 73 |
| orange juice | orange juice | 橙汁 | medium | low | medium | none | 54.733 | 47 | eats | 1.967 | 122 | no_response | 84 | 77 | 73 |
| pad-thai | pad thai | 泰式炒河粉 | medium | none | low | medium | 7.967 | 90 | eats | 7.1 | 86 | proboscis_only | 26 | 0 | 0 |
| pancakes | pancakes | 松饼 | low | none | low | none | 61.767 | 39 | eats | 14.4 | 38 | proboscis_only | 9 | 1 | 34 |
| peach | peach | 桃子 | medium | none | medium | none | 70.567 | 20 | eats | 31.833 | 13 | proboscis_only | 0 | 0 | 9 |
| peanut-butter | peanut butter | 花生酱 | low | low | low | low | 7.4 | 96 | eats | 4.267 | 103 | no_response | 29 | 15 | 27 |
| peking-duck | peking duck | 烤鸭 | low | none | low | medium | 1.567 | 100 | mouth_moves | 10.2 | 58 | proboscis_only | 1 | 1 | 1 |
| pho | pho | 越南河粉 | low | none | high | medium | 25.033 | 61 | eats | 15.867 | 34 | proboscis_only | 1 | 31 | 41 |
| pickled-cabbage-fish | pickled cabbage fish soup | 酸菜鱼 | low | low | high | medium | 23.633 | 65 | eats | 5.933 | 95 | proboscis_only | 48 | 46 | 34 |
| pineapple | pineapple | 菠萝 | medium | none | medium | none | 70.567 | 20 | eats | 31.833 | 13 | proboscis_only | 0 | 0 | 9 |
| pizza | pizza | 披萨 | low | none | low | medium | 1.567 | 100 | mouth_moves | 10.2 | 58 | proboscis_only | 1 | 1 | 1 |
| popcorn | popcorn | 爆米花 | none | none | none | none | 0.0 | 132 | no_response | 0.0 | 152 | no_response | 0 | 0 | 0 |
| potato chips | potato chips | 薯片 | none | none | none | low | 0.0 | 132 | no_response | 0.9 | 134 | no_response | 0 | 0 | 0 |
| pudding | pudding | 布丁 | high | none | low | none | 85.833 | 4 | eats | 77.467 | 4 | eats | 0 | 0 | 2 |
| ramen | ramen | 拉面 | low | low | high | medium | 23.633 | 65 | eats | 5.933 | 95 | proboscis_only | 48 | 46 | 34 |
| red-wine | red wine | 红酒 | none | medium | medium | low | 0.0 | 132 | no_response | 0.033 | 151 | no_response | 0 | 0 | 0 |
| roasted-sweet-potato | roasted sweet potato | 烤红薯 | medium | none | low | none | 70.567 | 20 | eats | 31.833 | 13 | proboscis_only | 0 | 0 | 9 |
| sandwich | sandwich | 三明治 | low | none | low | low | 9.267 | 79 | eats | 11.1 | 47 | proboscis_only | 1 | 0 | 21 |
| sashimi | sashimi | 刺身 | none | none | low | low | 0.0 | 132 | no_response | 9.033 | 72 | proboscis_only | 0 | 0 | 0 |
| scallion-pancake | scallion pancake | 葱油饼 | none | none | low | low | 0.0 | 132 | no_response | 9.033 | 72 | proboscis_only | 0 | 0 | 0 |
| scrambled-eggs | scrambled eggs | 炒蛋 | none | none | low | low | 0.0 | 132 | no_response | 9.033 | 72 | proboscis_only | 0 | 0 | 0 |
| sichuan-boiled-fish | sichuan boiled fish | 水煮鱼 | low | low | medium | medium | 0.667 | 114 | mouth_moves | 2.567 | 110 | no_response | 19 | 4 | 1 |
| sour-plum-drink | sour plum drink | 酸梅汤 | medium | low | medium | none | 54.733 | 47 | eats | 1.967 | 122 | no_response | 84 | 77 | 73 |
| soy-milk | soy milk | 豆浆 | none | low | high | low | 2.733 | 99 | no_response | 6.467 | 92 | proboscis_only | 28 | 47 | 15 |
| spaghetti-bolognese | spaghetti bolognese | 肉酱意面 | low | none | low | medium | 1.567 | 100 | mouth_moves | 10.2 | 58 | proboscis_only | 1 | 1 | 1 |
| sparkling-water | sparkling water | 气泡水 | none | none | very_high | none | 45.8 | 52 | eats | 0.0 | 152 | no_response | 121 | 121 | 121 |
| spicy-crayfish | spicy crayfish | 麻辣小龙虾 | low | low | medium | medium | 0.667 | 114 | mouth_moves | 2.567 | 110 | no_response | 19 | 4 | 1 |
| spinach | spinach | 菠菜 | none | low | high | none | 22.633 | 72 | eats | 8.7 | 83 | proboscis_only | 37 | 64 | 32 |
| sports-drink | sports drink | 运动饮料 | medium | none | medium | none | 70.567 | 20 | eats | 31.833 | 13 | proboscis_only | 0 | 0 | 9 |
| steak | steak | 牛排 | none | none | low | low | 0.0 | 132 | no_response | 9.033 | 72 | proboscis_only | 0 | 0 | 0 |
| steamed white rice | steamed white rice | 白米饭 | none | none | low | none | 0.0 | 132 | no_response | 0.0 | 152 | no_response | 0 | 0 | 0 |
| steamed-buns | steamed buns | 包子 | none | none | low | none | 0.0 | 132 | no_response | 0.0 | 152 | no_response | 0 | 0 | 0 |
| steamed-fish | steamed fish | 清蒸鱼 | low | none | high | low | 42.467 | 54 | eats | 17.0 | 30 | proboscis_only | 1 | 11 | 48 |
| stinky-tofu | stinky tofu | 臭豆腐 | none | low | low | medium | 0.0 | 132 | no_response | 1.233 | 128 | no_response | 0 | 0 | 0 |
| stir-fried-broccoli | stir-fried broccoli | 炒西兰花 | none | low | low | low | 0.0 | 132 | no_response | 2.1 | 121 | no_response | 0 | 0 | 0 |
| strawberry | strawberries | 草莓 | medium | none | medium | none | 70.567 | 20 | eats | 31.833 | 13 | proboscis_only | 0 | 0 | 9 |
| sukiyaki | sukiyaki | 寿喜烧 | medium | none | high | medium | 36.367 | 58 | eats | 10.267 | 57 | proboscis_only | 17 | 18 | 7 |
| sushi | sushi | 寿司 | low | none | low | low | 9.267 | 79 | eats | 11.1 | 47 | proboscis_only | 1 | 0 | 21 |
| sweet red bean soup | sweet red bean soup | 红豆汤 | medium | none | medium | none | 70.567 | 20 | eats | 31.833 | 13 | proboscis_only | 0 | 0 | 9 |
| sweet-and-sour-pork | sweet and sour pork | 糖醋里脊 | medium | none | low | low | 35.333 | 59 | eats | 7.267 | 85 | proboscis_only | 44 | 11 | 6 |
| taco | taco | 塔可 | low | low | low | medium | 0.667 | 114 | mouth_moves | 2.567 | 110 | no_response | 19 | 4 | 1 |
| takoyaki | takoyaki | 章鱼烧 | low | none | low | medium | 1.567 | 100 | mouth_moves | 10.2 | 58 | proboscis_only | 1 | 1 | 1 |
| tangyuan | tangyuan sweet rice balls | 汤圆 | high | none | low | none | 85.833 | 4 | eats | 77.467 | 4 | eats | 0 | 0 | 2 |
| tempura | tempura | 天妇罗 | low | none | low | low | 9.267 | 79 | eats | 11.1 | 47 | proboscis_only | 1 | 0 | 21 |
| teriyaki-chicken | teriyaki chicken | 照烧鸡 | medium | none | low | medium | 7.967 | 90 | eats | 7.1 | 86 | proboscis_only | 26 | 0 | 0 |
| tiramisu | tiramisu | 提拉米苏 | high | medium | low | low | 20.367 | 77 | eats | 0.067 | 150 | no_response | 76 | 97 | 61 |
| toast | toast | 吐司 | low | none | none | none | 34.667 | 60 | eats | 16.233 | 33 | proboscis_only | 1 | 0 | 7 |
| tofu | tofu | 豆腐 | none | none | low | none | 0.0 | 132 | no_response | 0.0 | 152 | no_response | 0 | 0 | 0 |
| tom-yum | tom yum soup | 冬阴功 | low | low | high | medium | 23.633 | 65 | eats | 5.933 | 95 | proboscis_only | 48 | 46 | 34 |
| tomato | tomato | 番茄 | low | none | medium | low | 9.267 | 79 | eats | 11.1 | 47 | proboscis_only | 1 | 0 | 21 |
| tomato and egg stir-fry | tomato and egg stir-fry | 番茄炒蛋 | low | none | medium | low | 9.267 | 79 | eats | 11.1 | 47 | proboscis_only | 1 | 0 | 21 |
| tonic water | tonic water | 汤力水 | high | very_high | medium | none | 0.2 | 127 | no_response | 0.0 | 152 | no_response | 47 | 47 | 47 |
| tteokbokki | tteokbokki | 辣炒年糕 | medium | none | low | medium | 7.967 | 90 | eats | 7.1 | 86 | proboscis_only | 26 | 0 | 0 |
| twice-cooked-pork | twice-cooked pork | 回锅肉 | low | none | low | medium | 1.567 | 100 | mouth_moves | 10.2 | 58 | proboscis_only | 1 | 1 | 1 |
| udon | udon | 乌冬面 | none | none | low | medium | 0.0 | 132 | no_response | 6.467 | 92 | proboscis_only | 0 | 0 | 0 |
| waffle | waffle | 华夫饼 | medium | none | low | none | 70.567 | 20 | eats | 31.833 | 13 | proboscis_only | 0 | 0 | 9 |
| wasabi | wasabi | 芥末 | none | medium | low | none | 0.0 | 132 | no_response | 0.167 | 146 | no_response | 0 | 0 | 0 |
| water | water | 水 | none | none | very_high | none | 45.8 | 52 | eats | 0.0 | 152 | no_response | 121 | 121 | 121 |
| watermelon | watermelon | 西瓜 | medium | none | medium | none | 70.567 | 20 | eats | 31.833 | 13 | proboscis_only | 0 | 0 | 9 |
| whiskey | whiskey | 威士忌 | none | medium | low | none | 0.0 | 132 | no_response | 0.167 | 146 | no_response | 0 | 0 | 0 |
| wontons | wonton soup | 馄饨 | none | none | high | medium | 0.033 | 131 | no_response | 13.933 | 46 | proboscis_only | 0 | 2 | 43 |
| xiaolongbao | xiaolongbao soup dumplings | 小笼包 | low | none | medium | medium | 1.567 | 100 | mouth_moves | 10.2 | 58 | proboscis_only | 1 | 1 | 1 |
| yogurt | yogurt | 酸奶 | low | none | high | low | 42.467 | 54 | eats | 17.0 | 30 | proboscis_only | 1 | 11 | 48 |
| youtiao | fried dough sticks | 油条 | none | none | none | none | 0.0 | 132 | no_response | 0.0 | 152 | no_response | 0 | 0 | 0 |
| yuxiang-shredded-pork | yuxiang shredded pork | 鱼香肉丝 | medium | none | low | medium | 7.967 | 90 | eats | 7.1 | 86 | proboscis_only | 26 | 0 | 0 |
| zongzi | zongzi | 粽子 | low | none | low | low | 9.267 | 79 | eats | 11.1 | 47 | proboscis_only | 1 | 0 | 21 |

## Execution and verification

The [runner](../sim/malecns/male_v1_grid.py) uses the declared seeds and store/restore path. The [lookup builder](../sim/malecns/build_lookup_male.py), [comparison](../sim/malecns/male_female_comparison.py) and [replay packer](../scripts/pack_replay_male.py) produce additive artifacts. The independent [audit](../sim/malecns/audit_male_v1_grid.py) reconstructs the raw events, Poisson trains, statistics, comparison and replay bytes. Each replay is grid trial 0, one of the 30 trials behind the lookup mean; its MN9 counts equal that trial’s rates, not the 30-trial mean. [Synthetic tests](../sim/malecns/test_male_v1_grid_outputs.py) exercise corruption rejection. Verify both generated blocks with `.venv\Scripts\python -m sim.malecns.report_male_v1_grid --check`; the [generator](../sim/malecns/report_male_v1_grid.py) preserves the declaration and later sections.

| replay size statistic | bytes |
| --- | --- |
| min_bytes | 1046 |
| median_bytes | 1253110.5 |
| max_bytes | 1431378 |
| total_bytes | 484287949 |
| index_bytes | 230977 |
| manifest_bytes | 91501 |

<!-- male-v1-phase2:end -->
