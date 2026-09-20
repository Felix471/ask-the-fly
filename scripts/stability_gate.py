"""Evaluate the owner's batch-3 thresholds without any API calls."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from encoder.batch3 import LANGS, REPEATS, statistics
from encoder.merge import validate_stability
from encoder.stability import DIMENSIONS, _markdown_cell, _read_records, _write_report

START = '<!-- batch3-gate:start -->'
END = '<!-- batch3-gate:end -->'


def evaluate(foods, records):
    _, modes, consistencies = statistics(foods, records)
    dimensions = {}
    disagreements = []
    for dimension in DIMENSIONS:
        agreeing = 0
        for index, food in enumerate(foods):
            zh, en = (modes[index, lang, dimension] for lang in LANGS)
            if zh is not None and zh == en:
                agreeing += 1
            else:
                disagreements.append(dict(key=food['key'], dimension=dimension, zh=zh, en=en))
        scores = [consistencies[index, lang, dimension]
                  for index in range(len(foods)) for lang in LANGS]
        agreement = agreeing / len(foods)
        consistency = sum(scores) / len(scores)
        # Integer counts avoid rounding an actual boundary pass/fail in the display.
        modal_count = sum(round(score * REPEATS) for score in scores)
        passed = agreeing * 100 >= 90 * len(foods) and modal_count * 100 >= 95 * REPEATS * len(scores)
        dimensions[dimension] = dict(agreeing=agreeing, agreement=agreement,
                                     consistency=consistency, passed=passed)
    problems = validate_stability(records, foods, langs=LANGS, repeats=REPEATS)
    return dict(passed=not problems and all(d['passed'] for d in dimensions.values()),
                foods=len(foods), dimensions=dimensions, disagreements=disagreements,
                completeness_problems=problems,
                synthetic=any(r.get('model_id') == 'dry-run' for r in records))


def write_gate(path, result):
    text = path.read_text(encoding='utf-8')
    if START in text:
        before, rest = text.split(START, 1)
        _, after = rest.split(END, 1)
        text = before.rstrip() + '\n' + after.lstrip()
    text = text.replace('Purpose: estimate how much of the llm_v1 dictionary needs human review. Not a gate.',
                        'Purpose: estimate review needs; the batch-3 gate follows below.')
    lines = [START, '## Batch 3 stability gate', '',
             "These are the owner's batch-3 thresholds; batch 2 had none.",
             'Each dimension requires cross-language agreement >= 90% and mean within-language consistency >= 95%.',
             'Metrics use the report definitions and six repeats, including missing/error observations in the denominator.',
             'All four dimensions and D07 completeness must pass. This does not approve drops or publication.', '']
    if result['synthetic']:
        lines += ['**SYNTHETIC DRY RUN: not encoding evidence.**', '']
    lines += ['| Dimension | Cross-language agreement | Within-language consistency | Result |',
              '|---|---:|---:|---|']
    for dimension, detail in result['dimensions'].items():
        lines.append(f"| {dimension} | {detail['agreement']:.2%} | {detail['consistency']:.2%} | {'PASS' if detail['passed'] else 'FAIL'} |")
    lines += ['', 'Every cross-language disagreement (including missing modes):', '',
              '| Key | Dimension | zh modal | en modal |', '|---|---|---|---|']
    lines += [f"| {_markdown_cell(d['key'])} | {d['dimension']} | {d['zh'] or 'missing'} | {d['en'] or 'missing'} |"
              for d in result['disagreements']] or ['| none | | | |']
    lines += ['', *('- ' + p for p in result['completeness_problems']),
              f"\n**Batch 3: {'PASS' if result['passed'] else 'FAIL'}**", END, '']
    path.write_text(text.rstrip() + '\n\n' + '\n'.join(lines), encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--foods', type=Path, default=ROOT / 'encoder/foods_batch3.json')
    parser.add_argument('--raw', type=Path, default=ROOT / 'results/encoder/stability_raw_batch3.jsonl')
    parser.add_argument('--report', type=Path, default=ROOT / 'docs/encoder_stability_batch3.md')
    args = parser.parse_args()
    foods = json.loads(args.foods.read_text(encoding='utf-8'))
    records = _read_records(args.raw)
    result = evaluate(foods, records)
    version = next((r['encoder_version'] for r in records), 'unknown@encode_v2.3')
    _write_report(foods, records, REPEATS, list(LANGS), version.rsplit('@', 1)[0], version,
                  'encode_v2.3', list(DIMENSIONS), args.report)
    write_gate(args.report, result)
    print(f"Batch 3 stability gate: {'PASS' if result['passed'] else 'FAIL'}; {args.report}")
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
