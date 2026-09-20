"""Flag an approved section without reserializing or changing any existing bytes."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def mark_bytes(raw: bytes, section: str) -> tuple[bytes, int]:
    text = raw.decode('utf-8')
    foods = json.loads(text)
    if not isinstance(foods, list):
        raise ValueError('expected a food array')
    decoder = json.JSONDecoder()
    cursor = text.index('[') + 1
    inserts = []
    matched = 0
    for food in foods:
        while text[cursor].isspace() or text[cursor] == ',':
            cursor += 1
        parsed, end = decoder.raw_decode(text, cursor)
        if not isinstance(food, dict) or parsed != food:
            raise ValueError('expected food objects')
        if food.get('section_zh') == section or food.get('section_en') == section:
            matched += 1
            if 'not_food' in food:
                if food['not_food'] is not True:
                    raise ValueError(f"conflicting not_food flag: {food.get('key')}")
            else:
                # Insert just after the final value; leave whitespace and line endings intact.
                last = end - 1
                while text[last - 1].isspace():
                    last -= 1
                inserts.append(last)
        cursor = end
    if not matched:
        raise ValueError(f'no entries in section {section!r}')
    for position in reversed(inserts):
        text = text[:position] + ', "not_food": true' + text[position:]
    return text.encode('utf-8'), len(inserts)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--section', required=True)
    parser.add_argument('--foods', type=Path, default=ROOT / 'encoder/foods_batch3.json')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    marked, count = mark_bytes(args.foods.read_bytes(), args.section)
    if not args.dry_run and count:
        args.foods.write_bytes(marked)
    print(f"{'Would flag' if args.dry_run else 'Flagged'} {count} entries")


if __name__ == '__main__':
    main()
