"""Copy length limits retain legacy behavior and enforce each language's cap."""
import contextlib
import io
import unittest
from unittest.mock import patch
from pathlib import Path
import tempfile

from scripts.import_copy import apply_strings


class CopyLengthTests(unittest.TestCase):
    def test_explicit_removal_requires_absent_source_and_preserves_other_keys(self):
        shipped = {lang: {'draft': 'old', 'keep': 'kept'} for lang in ('en', 'zh')}
        with tempfile.TemporaryDirectory() as tmp, patch('scripts.import_copy.current_strings', return_value=shipped):
            root = Path(tmp)
            (root / 'index.html').write_text('', encoding='utf-8')
            with patch('scripts.import_copy.ROOT', root), patch('scripts.import_copy.STRINGS_JS', root / 'strings.js'), patch('scripts.import_copy.INDEX_HTML', root / 'index.html'), patch('scripts.import_copy.site_url', return_value='https://askthefly.app/'):
                with self.assertRaises(ValueError):
                    apply_strings([dict(key='draft', en='x', zh='x')], True, remove_keys=['draft'])
                apply_strings([dict(key='keep', en='kept', zh='kept')], False, remove_keys=['draft'])
                output = (root / 'strings.js').read_text(encoding='utf-8')
                self.assertNotIn('draft', output)
                self.assertEqual(output.count('kept'), 2)
                self.assertEqual(apply_strings([], True), 2)

    def check_entry(self, key, en, zh, limit):
        entry = dict(key=key, context="test", en=en, zh=zh, max_length=limit)
        output = io.StringIO()
        with patch("scripts.import_copy.current_strings", return_value={"en": {}, "zh": {}}):
            with contextlib.redirect_stdout(output):
                warnings = apply_strings([entry], check=True, allow_new=True)
        return warnings, output.getvalue()

    def test_language_limits_inclusive_and_independent(self):
        limits = {"en": 90, "zh": 45}
        self.assertEqual(self.check_entry("card.disagree", "x" * 90, "字" * 45, limits)[0], 0)
        for en, zh, lang in [("x" * 91, "字" * 45, "en"), ("x" * 90, "字" * 46, "zh")]:
            count, output = self.check_entry("card.disagree", en, zh, limits)
            self.assertEqual(count, 1)
            self.assertIn(f"card.disagree.{lang}", output)

    def test_scalar_limits_still_apply_to_both_languages(self):
        self.assertEqual(self.check_entry("old", "abcd", "四个汉字", 4)[0], 0)
        self.assertEqual(self.check_entry("old", "abcde", "五个汉字啊", 4)[0], 2)

    def test_meta_uses_language_limits_too(self):
        limits = {"en": 6, "zh": 3}
        self.assertEqual(self.check_entry("meta.title", "abcdef", "三个字", limits)[0], 0)
        self.assertEqual(self.check_entry("meta.title", "abcdefg", "四个汉字", limits)[0], 2)
