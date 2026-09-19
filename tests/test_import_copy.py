"""Copy length limits retain legacy behavior and enforce each language's cap."""
import contextlib
import io
import unittest
from unittest.mock import patch

from scripts.import_copy import apply_strings


class CopyLengthTests(unittest.TestCase):
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
