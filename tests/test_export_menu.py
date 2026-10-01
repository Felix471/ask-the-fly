# SPDX-License-Identifier: MIT
"""Determinism and rejection tests for the generated menu."""
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import export_menu, validate_release  # noqa: E402


class MenuExport(unittest.TestCase):
    def test_real_menu_and_tamper(self):
        expected = export_menu.render_menu(ROOT)
        self.assertEqual(expected, export_menu.render_menu(ROOT))
        self.assertEqual((ROOT / 'site/data/menu.json').read_bytes(), expected)
        self.assertEqual(validate_release.check_menu(ROOT), [])
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for rel in list(export_menu.INPUTS.values()) + list(export_menu.SITE_COPIES.values()) + ['site/data/menu.json']:
                target = root / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / rel, target)
            path = root / 'site/data/menu.json'
            payload = json.loads(path.read_bytes())
            payload['dishes'][0]['female']['mn9'] += 1
            path.write_text(json.dumps(payload), encoding='utf8')
            self.assertTrue(validate_release.check_menu(root))

    def test_synthetic_ties_and_missing_bucket(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            levels = {axis: {'none': 0, 'high': 120} for axis in export_menu.AXES}
            def cell(sugar, mn9):
                return {'hz': {'sugar': levels['sugar'][sugar], 'bitter': 0, 'water': 0, 'ir94e': 0},
                        'mn9_mean': mn9, 'mn11d_mean': 0, 'mn11v_mean': 0, 'state': 'no_response'}
            table = {'levels': levels, 'cells_sha256': 'test', 'cells': [cell('none', 5), cell('high', 10)]}
            objects = {
                'dishes': [{'key': key, 'display': {'zh': key, 'en': key}, 'sugar': sugar,
                            'bitter': 'none', 'water': 'none', 'ir94e': 'none'}
                           for key, sugar in [('a', 'high'), ('b', 'high'), ('c', 'none')]],
                'sections': {'sections': [{'zh': 'test', 'en': 'test', 'keys': ['a', 'b', 'c']}]},
                'female': table, 'male': table,
                'fly_lines': {'buckets': [{'state': 'no_response', 'when': {}, 'zh': ['a','b','c'], 'en': ['a','b','c']}]},
                'fallbacks': {'fallbacks': {}},
            }
            for name, rel in export_menu.INPUTS.items():
                path = root / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(objects[name]), encoding='utf8')
            for name, rel in export_menu.SITE_COPIES.items():
                path = root / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(root / export_menu.INPUTS[name], path)
            result = export_menu.build_menu(root)
            self.assertEqual([d['female']['rank'] for d in result['dishes']], [1,1,3])
            self.assertEqual(result['lists']['female_top'][0]['keys'], ['a','b'])
            first = export_menu.render_menu(root)
            self.assertEqual(first, export_menu.render_menu(root))
            target = root / 'site/data/menu.json'; target.write_bytes(first)
            with patch.object(export_menu, 'ROOT', root), patch.object(sys, 'argv', ['export_menu.py','--check']):
                self.assertEqual(export_menu.main(), 0)
                target.write_bytes(b'{}')
                self.assertEqual(export_menu.main(), 1)
            objects['fly_lines']['buckets'] = []
            (root / export_menu.INPUTS['fly_lines']).write_text(json.dumps(objects['fly_lines']),encoding='utf8')
            with self.assertRaisesRegex(ValueError, 'No speech bucket'):
                export_menu.build_menu(root)

