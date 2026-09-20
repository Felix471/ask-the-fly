#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Apply the owner-approved batch-3 taxonomy, including only merged dictionary keys.

The 174-key mapping below transcribes DP1's new_of and S (2026-09-19).
It is self-contained: no ignored reviewer scripts or encoder run outputs are read.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

APPROVED_SECTIONS = [{'zh': '中餐',
  'en': 'Chinese',
  'keys': ['beef-noodle-soup',
           'braised pork belly',
           'century-egg',
           'chow-mein',
           'clear broth',
           'congee',
           'dumplings',
           'fried-rice',
           'hot-and-sour-noodles',
           'hotpot',
           'instant-noodles',
           'jianbing',
           'kung-pao-chicken',
           'lamb-skewers',
           'liangpi',
           'luosifen',
           'malatang',
           'mapo tofu',
           'peking-duck',
           'pickled-cabbage-fish',
           'roasted-sweet-potato',
           'scallion-pancake',
           'sichuan-boiled-fish',
           'spicy-crayfish',
           'steamed white rice',
           'steamed-buns',
           'steamed-fish',
           'stinky-tofu',
           'stir-fried-broccoli',
           'sweet red bean soup',
           'sweet-and-sour-pork',
           'tomato and egg stir-fry',
           'twice-cooked-pork',
           'wontons',
           'xiaolongbao',
           'youtiao',
           'yuxiang-shredded-pork',
           'zongzi']},
 {'zh': '日本',
  'en': 'Japanese',
  'keys': ['miso soup',
           'natto',
           'onigiri',
           'ramen',
           'sashimi',
           'sukiyaki',
           'sushi',
           'takoyaki',
           'tempura',
           'teriyaki-chicken',
           'udon']},
 {'zh': '韩国',
  'en': 'Korean',
  'keys': ['bibimbap', 'budae-jjigae', 'kimchi', 'korean-bbq', 'tteokbokki']},
 {'zh': '东南亚', 'en': 'Southeast Asian', 'keys': ['pad-thai', 'pho', 'tom-yum']},
 {'zh': '南亚', 'en': 'South Asian', 'keys': ['curry']},
 {'zh': '中东与非洲', 'en': 'Middle East & Africa', 'keys': ['hummus', 'kebab']},
 {'zh': '欧洲',
  'en': 'European',
  'keys': ['bread',
           'cheese',
           'croissant',
           'fish-and-chips',
           'fried-egg',
           'lasagna',
           'oatmeal',
           'pizza',
           'scrambled-eggs',
           'spaghetti-bolognese',
           'toast',
           'waffle']},
 {'zh': '美洲与大洋洲',
  'en': 'Americas & Oceania',
  'keys': ['bacon',
           'bagel',
           'burrito',
           'caesar-salad',
           'cereal',
           'french-fries',
           'fried chicken',
           'hamburger',
           'hot-dog',
           'mashed-potatoes',
           'pancakes',
           'sandwich',
           'steak',
           'taco']},
 {'zh': '甜点与零食',
  'en': 'Sweets & snacks',
  'keys': ['apple-pie',
           'beef jerky',
           'brownie',
           'cake',
           'candy',
           'cheesecake',
           'cookies',
           'crackers',
           'dark chocolate 85%',
           'donut',
           'douhua',
           'egg-tart',
           'ice cream',
           'jelly',
           'latiao',
           'marshmallow',
           'milk-chocolate',
           'mixed nuts',
           'mochi',
           'mooncake',
           'popcorn',
           'potato chips',
           'pudding',
           'tangyuan',
           'tiramisu',
           'yogurt']},
 {'zh': '饮料',
  'en': 'Drinks',
  'keys': ['americano',
           'apple-juice',
           'black coffee',
           'black-tea',
           'bubble tea',
           'cappuccino',
           'coconut-water',
           'cola',
           'energy-drink',
           'espresso',
           'green tea',
           'herbal-tea',
           'hot-chocolate',
           'latte',
           'lemon-tea',
           'lemonade',
           'matcha',
           'matcha-latte',
           'milk',
           'oolong-tea',
           'orange juice',
           'sour-plum-drink',
           'soy-milk',
           'sparkling-water',
           'sports-drink',
           'tonic water',
           'water']},
 {'zh': '酒',
  'en': 'Alcohol',
  'keys': ['baijiu', 'beer', 'ipa beer', 'margarita', 'red-wine', 'whiskey']},
 {'zh': '调料', 'en': 'Condiments', 'keys': ['honey', 'peanut-butter', 'wasabi']},
 {'zh': '水果与蔬菜',
  'en': 'Fruit & vegetables',
  'keys': ['apple',
           'avocado',
           'banana',
           'bitter melon',
           'blueberries',
           'carrot',
           'cherries',
           'cilantro',
           'corn-on-the-cob',
           'cucumber',
           'durian',
           'edamame',
           'endive',
           'gai lan',
           'grapefruit',
           'grapes',
           'lemon',
           'mango',
           'orange',
           'peach',
           'pineapple',
           'spinach',
           'strawberry',
           'tofu',
           'tomato',
           'watermelon']},
 {'zh': '不是给人吃的', 'en': 'Not food', 'keys': [], 'not_food': True}]


def build_sections(dishes: list[dict], batch: list[dict], popular: list[str]) -> dict:
    sections = copy.deepcopy(APPROVED_SECTIONS)
    present = {dish['key'] for dish in dishes}
    if len(present) != len(dishes):
        raise ValueError('duplicate dictionary keys')
    original = {key for section in sections for key in section['keys']}
    if original - present:
        raise ValueError(f'missing approved existing keys: {sorted(original - present)}')
    by_zh = {section['zh']: section for section in sections}
    assigned = set(original)
    batch_keys = set()
    for item in batch:
        key = item['key']
        if key in batch_keys or key in original:
            raise ValueError(f'duplicate batch key: {key}')
        batch_keys.add(key)
        section = by_zh.get(item['section_zh'])
        if section is None or section['en'] != item['section_en']:
            raise ValueError(f'unknown or mismatched batch section: {key}')
        if key in present:
            section['keys'].append(key)
            assigned.add(key)
    if present - assigned:
        raise ValueError(f'unassigned dictionary keys: {sorted(present - assigned)}')
    if any(key not in present for key in popular):
        raise ValueError('popular contains an unknown dictionary key')
    return {'schema': 'dish_sections_v2', 'sections': sections, 'popular': list(popular)}


def main() -> int:
    read = lambda path: json.loads((ROOT / path).read_text(encoding='utf-8'))
    path = ROOT / 'data/dish_sections.json'
    payload = build_sections(read('data/dishes.json'), read('encoder/foods_batch3.json'),
                             read('data/dish_sections.json')['popular'])
    encoded = json.dumps(payload, ensure_ascii=False, indent=1) + '\n'
    if path.read_text(encoding='utf-8') != encoded:
        path.write_text(encoded, encoding='utf-8', newline='\n')
    for section in payload['sections']:
        print(f"{section['en']}: {len(section['keys'])}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
