"""Batch 3 tooling, exercised only with synthetic encoder responses."""
from copy import deepcopy
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from encoder import encode, merge, stability
from scripts.mark_not_food import mark_bytes
from scripts.stability_gate import evaluate, write_gate
from scripts.batch3_droplist import drop_entries


FOODS = [dict(key=f"new-{i}", zh=f"测试{i}", en=f"test {i}", not_food=True)
         if i == 0 else dict(key=f"new-{i}", zh=f"测试{i}", en=f"test {i}")
         for i in range(10)]


def rows(foods=FOODS):
    return [stability._run_observation(food, i, lang, rep, True, "encode_v2.3")
            for i, food in enumerate(foods) for lang in ("zh", "en") for rep in range(1, 7)]


class Batch3EncoderTests(unittest.TestCase):
    def test_mark_changes_only_inserted_bytes_and_is_idempotent(self):
        raw = b'[\r\n  {"key":"a", "section_zh":"target"},\r\n  {"key":"b"}\r\n]\r\n'
        marked, count = mark_bytes(raw, "target")
        self.assertEqual(count, 1)
        self.assertEqual(marked.replace(b', "not_food": true', b''), raw)
        self.assertEqual(mark_bytes(marked, "target"), (marked, 0))

    def test_prompt_is_unchanged_unless_flagged(self):
        base = encode._PROMPT_PATH_FOR['encode_v2.3'].read_text(encoding='utf-8')
        base = base.replace('{dish}', 'soap').replace('{input_language}', 'en')
        self.assertEqual(encode.build_prompt('soap', 'en', 'encode_v2.3'), base)
        self.assertEqual(encode.build_prompt('soap', 'en', 'encode_v2.3', not_food=True),
                         base + '\n\n' + encode.ADDENDUM_PATH.read_text(encoding='utf-8').strip() + '\n')

    def test_mock_client_receives_addendum_and_entry_provenance(self):
        fake = stability._fake_entry(FOODS[0], 'encode_v2.3')
        with patch('encoder.client.GeminiEncoder') as cls:
            cls.return_value.model_id = 'synthetic'
            cls.return_value.generate.return_value = json.dumps(fake)
            entry = encode.encode_dish('soap', 'en', not_food=True)
            self.assertIn('not human food', cls.return_value.generate.call_args.args[0])
            self.assertEqual(entry['encoder_addendum'], 'addendum_not_food_v1')
            self.assertEqual(entry['encoder_version'], 'synthetic@encode_v2.3')

    def test_raw_provenance_including_errors(self):
        data = rows()
        self.assertEqual(data[0]['prompt_addendum'], 'addendum_not_food_v1')
        self.assertIsNone(data[12]['prompt_addendum'])
        with patch('encoder.stability.encode_dish', side_effect=ValueError('synthetic error')):
            record = stability._run_observation(FOODS[0], 0, 'en', 1, False, 'encode_v2.3')
        self.assertIn('error', record)
        self.assertEqual(record['prompt_addendum'], 'addendum_not_food_v1')

    def test_gate_boundary_disagreements_and_four_dimensions(self):
        data = rows()
        for row in data:
            if row['food_index'] == 0 and row['lang'] == 'zh':
                row['entry']['ir94e'] = 'low'
        result = evaluate(FOODS, data)
        self.assertTrue(result['passed'])
        self.assertEqual(result['dimensions']['ir94e']['agreement'], .9)
        self.assertEqual(len(result['disagreements']), 1)
        for row in data:
            if row['food_index'] == 1 and row['lang'] == 'zh':
                row['entry']['ir94e'] = 'low'
        self.assertFalse(evaluate(FOODS, data)['passed'])

    def test_gate_within_mean_and_drop_per_group(self):
        data = rows()
        for index in range(6):
            data[index * 12]['entry']['sugar'] = 'high'
        result = evaluate(FOODS, data)
        self.assertAlmostEqual(result['dimensions']['sugar']['consistency'], .95)
        self.assertTrue(result['passed'])
        kept, dropped = drop_entries(FOODS, data)
        self.assertEqual([f['key'] for f in kept], [f['key'] for f in FOODS[6:]])
        self.assertEqual(len(dropped), 6)
        data[6 * 12]['entry']['sugar'] = 'high'
        self.assertFalse(evaluate(FOODS, data)['passed'])

    def test_missing_errors_duplicates_and_bad_provenance(self):
        data = rows()
        self.assertFalse(evaluate(FOODS, data[:-1])['passed'])
        kept, dropped = drop_entries(FOODS, data[:-1])
        self.assertEqual(dropped[0]['key'], FOODS[-1]['key'])
        self.assertEqual(len(kept), 9)
        error = deepcopy(data)
        error[-1].pop('entry')
        error[-1]['error'] = 'synthetic'
        self.assertFalse(evaluate(FOODS, error)['passed'])
        missing_dimension = deepcopy(data)
        missing_dimension[0]['entry'].pop('ir94e')
        mixed_version = deepcopy(data)
        mixed_version[0]['encoder_version'] = 'another@encode_v2.3'
        for corrupt in (data + [data[0]], missing_dimension, mixed_version):
            with self.assertRaises(ValueError):
                drop_entries(FOODS, corrupt)
        bad = deepcopy(data)
        bad[0]['prompt_addendum'] = None
        with self.assertRaises(ValueError):
            evaluate(FOODS, bad)

    def test_drop_distance_and_merge_subset_keep_original_indices(self):
        data = rows()
        for row in data:
            if row['food_index'] == 1 and row['lang'] == 'zh':
                row['entry']['ir94e'] = 'medium'
            if row['food_index'] == 2 and row['lang'] == 'zh':
                row['entry']['ir94e'] = 'low'
        kept, dropped = drop_entries(FOODS, data)
        self.assertEqual([d['key'] for d in dropped], ['new-1'])
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            foods = folder / 'foods.json'
            source = folder / 'raw.jsonl'
            into = folder / 'dishes.json'
            foods.write_text(json.dumps(kept), encoding='utf-8')
            source.write_text('\n'.join(json.dumps(r) for r in data), encoding='utf-8')
            with patch.object(merge, 'FOODS_OVERRIDE', foods):
                count, _, entries = merge.merge(source, into, new_only=True)
                self.assertEqual(count, 9)
                by_key = {e['key']: e for e in entries}
                self.assertEqual(by_key['new-0']['encoder_addendum'], 'addendum_not_food_v1')
                self.assertNotIn('encoder_addendum', by_key['new-2'])
                self.assertEqual(by_key['new-2']['arbitration']['ir94e']['rule'], 'lower_level')
                self.assertTrue(all(e['encoder_version'].endswith('@encode_v2.3') for e in entries))
                before = into.read_bytes()
                with self.assertRaises(merge.MergeError):
                    merge.merge(source, into, new_only=True)
                self.assertEqual(into.read_bytes(), before)
                source.write_text('\n'.join(json.dumps(r) for r in data[:-1]), encoding='utf-8')
                with self.assertRaisesRegex(merge.MergeError, 'incomplete'):
                    merge.merge(source, into)

    def test_gate_report_idempotent_and_historical_wording_untouched(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'report.md'
            stability._write_report(FOODS, rows(), 6, ['zh', 'en'], 'dry-run',
                                    'dry-run@encode_v2.3', 'encode_v2.3', list(stability.DIMENSIONS), path)
            self.assertIn('Not a gate.', path.read_text(encoding='utf-8'))
            write_gate(path, evaluate(FOODS, rows()))
            first = path.read_bytes()
            write_gate(path, evaluate(FOODS, rows()))
            self.assertEqual(first, path.read_bytes())
            self.assertIn("owner's batch-3 thresholds", path.read_text(encoding='utf-8'))
            self.assertTrue(path.read_text(encoding='utf-8').rstrip().endswith('<!-- batch3-gate:end -->'))

    def test_resume_replaces_error_slots_without_duplicate_rows_or_api_calls(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            foods, raw, report = (folder / name for name in ('foods.json', 'raw.jsonl', 'report.md'))
            foods.write_text(json.dumps(FOODS[:1]), encoding='utf-8')
            data = rows(FOODS[:1])
            data[-1].pop('entry')
            data[-1]['error'] = 'synthetic failure'
            raw.write_text('\n'.join(json.dumps(r) for r in data), encoding='utf-8')
            argv = ['stability', '--foods', str(foods), '--raw', str(raw), '--report', str(report),
                    '--prompt-version', 'encode_v2.3', '--dry-run', '--resume']
            with patch('sys.argv', argv), patch('encoder.stability.encode_dish', side_effect=AssertionError('API forbidden')), redirect_stdout(io.StringIO()):
                stability.main()
            fixed = stability._read_records(raw)
            self.assertEqual(len(fixed), 12)
            self.assertTrue(evaluate(FOODS[:1], fixed)['passed'])
            self.assertIn('Report dimensions: sugar, bitter, water, ir94e', report.read_text(encoding='utf-8'))
            before = raw.read_bytes()
            with patch('sys.argv', argv), patch('encoder.stability._run_observation', side_effect=AssertionError('no new rows')), redirect_stdout(io.StringIO()):
                stability.main()
            self.assertEqual(raw.read_bytes(), before)
            data = fixed
            data[0]['prompt_addendum'] = None
            raw.write_text('\n'.join(json.dumps(r) for r in data), encoding='utf-8')
            with patch('sys.argv', argv), self.assertRaisesRegex(ValueError, 'addendum mismatch'):
                stability.main()

    def test_new_only_preserves_existing_entries_and_drops_colliding_aliases(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            source, into = folder / 'source.json', folder / 'into.json'
            old = stability._fake_entry(dict(zh='旧', en='old'), 'encode_v2.3')
            new = stability._fake_entry(dict(zh='新', en='new'), 'encode_v2.3')
            new['aliases'].append('old')
            into.write_text(json.dumps([old]), encoding='utf-8')
            source.write_text(json.dumps([new]), encoding='utf-8')
            _, _, entries = merge.merge(source, into, new_only=True)
            self.assertEqual(next(e for e in entries if e['key'] == 'old'), old)
            self.assertNotIn('old', next(e for e in entries if e['key'] == 'new')['aliases'])


if __name__ == '__main__':
    unittest.main()
