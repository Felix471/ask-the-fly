# SPDX-License-Identifier: MIT
"""Promotion operates only on an isolated copy; approved site art stays untouched."""
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from scripts import prep_male_sprites as sprites


class MaleSpritePromotionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        shutil.copytree(sprites.OUTPUT / 'tip', self.root / 'assets/male_candidates/tip')
        (self.root / 'site/assets').mkdir(parents=True)
        (self.root / 'site/config.json').write_text('{"site_url":"https://askthefly.app/"}\n')

    def test_promote_copies_all_42_frames_and_records_readiness(self):
        sprites.promote('tip', self.root)
        for source in sprites.source_paths():
            target = self.root / 'site/assets' / (source.parent.name + '_male') / source.name
            self.assertEqual(target.read_bytes(), (self.root / 'assets/male_candidates/tip' / source.name).read_bytes())
        self.assertEqual(len(list((self.root / 'site/assets').rglob('*.png'))), 42)
        config = json.loads((self.root / 'site/config.json').read_text())
        self.assertEqual(config, {'site_url': 'https://askthefly.app/', 'male_sprite_variant': 'tip'})
        with self.assertRaises(FileExistsError):
            sprites.promote('tip', self.root)

    def test_either_existing_folder_refuses_before_writing(self):
        for name in ('fly_male', 'response_male'):
            with self.subTest(name=name):
                folder = self.root / 'site/assets' / name
                folder.mkdir()
                with self.assertRaises(FileExistsError):
                    sprites.promote('tip', self.root)
                self.assertEqual(list(folder.iterdir()), [])
                self.assertEqual(len(list(folder.parent.iterdir())), 1)
                folder.rmdir()

    def test_missing_frame_or_unknown_variant_creates_nothing(self):
        (self.root / 'assets/male_candidates/tip/idle_1.png').unlink()
        with self.assertRaises(FileNotFoundError):
            sprites.promote('tip', self.root)
        with self.assertRaises(ValueError):
            sprites.promote('../tip', self.root)
        self.assertEqual(list((self.root / 'site/assets').iterdir()), [])
        self.assertNotIn('male_sprite_variant', json.loads((self.root / 'site/config.json').read_text()))
