import json
import unittest
from pathlib import Path
from fontTools.ttLib import TTFont
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


class PixelBubbleTests(unittest.TestCase):
    def test_every_chinese_speech_glyph_has_pixel_font_coverage(self):
        copy = json.loads((ROOT / 'copy/fly_lines.json').read_text(encoding='utf8'))
        wanted = set(''.join(line for b in copy['buckets'] for line in b['zh']))
        with TTFont(ROOT / 'site/assets/fonts/fusion-pixel-12px-zh.woff2') as font:
            cmap = font.getBestCmap()
        self.assertEqual(sorted(ch for ch in wanted if not ch.isspace() and ord(ch) not in cmap), [])

    def test_emotions_are_local_sprite_names_not_system_emoji(self):
        source = (ROOT / 'site/taste_states.js').read_text(encoding='utf8')
        self.assertNotIn('❤️', source)
        self.assertNotIn('🤔', source)
        self.assertIn("mouth_moves: 'sweat'", source)
        self.assertTrue((ROOT / 'site/assets/response/emotions-v1.png').is_file())

    def test_atlas_is_three_square_cells_with_real_transparency(self):
        with Image.open(ROOT / 'site/assets/response/emotions-v1.png') as image:
            self.assertEqual(image.width, image.height * 3)
            self.assertEqual(image.mode, 'RGBA')
            self.assertEqual(image.getchannel('A').getextrema(), (0, 255))


if __name__ == '__main__':
    unittest.main()
