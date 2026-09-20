"""Propose batch-3 drops for decision point 2; no dictionary or raw-data mutation."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from encoder.batch3 import LANGS, statistics
from encoder.levels import levels_for
from encoder.stability import DIMENSIONS, _read_records


def drop_entries(foods, records):
    _, modes, consistencies = statistics(foods, records)
    kept, dropped = [], []
    for index, food in enumerate(foods):
        reasons = []
        for dimension in DIMENSIONS:
            zh, en = (modes[index, lang, dimension] for lang in LANGS)
            if zh is not None and en is not None:
                distance = abs(levels_for(dimension).index(zh) - levels_for(dimension).index(en))
                if distance >= 2:
                    reasons.append(dict(rule='cross_language_distance', dimension=dimension,
                                        zh=zh, en=en, distance=distance))
            for lang in LANGS:
                consistency = consistencies[index, lang, dimension]
                if consistency < .95:
                    reasons.append(dict(rule='within_language_consistency', dimension=dimension,
                                        lang=lang, modal=modes[index, lang, dimension],
                                        consistency=consistency, threshold=.95))
        if reasons:
            dropped.append(dict(key=food['key'], food_index=index, reasons=reasons))
        else:
            kept.append(food)
    return kept, dropped


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raw', type=Path, default=ROOT / 'results/encoder/stability_raw_batch3.jsonl')
    parser.add_argument('--foods', type=Path, default=ROOT / 'encoder/foods_batch3.json')
    parser.add_argument('--out', type=Path, default=ROOT / 'encoder/foods_batch3_merged.json')
    parser.add_argument('--dropped', type=Path, default=ROOT / 'results/encoder/batch3_dropped.json')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    foods = json.loads(args.foods.read_text(encoding='utf-8'))
    kept, dropped = drop_entries(foods, _read_records(args.raw))
    report = dict(status='proposed; owner decision point 2 pending', source=str(args.raw),
                  approved_count=len(foods), kept_count=len(kept), dropped=dropped)
    if not args.dry_run:
        inputs = {args.foods.resolve(), args.raw.resolve()}
        if args.out.resolve() in inputs or args.dropped.resolve() in inputs or args.out.resolve() == args.dropped.resolve():
            parser.error('outputs must be distinct from each other and from the approved list/raw observations')
        for path, value in ((args.out, kept), (args.dropped, report)):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
