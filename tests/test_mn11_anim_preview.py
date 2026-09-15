"""Deterministic staging guardrails; generated art is local, not required in CI."""
import unittest
from PIL import Image, ImageDraw
from scripts.mn11_anim_preview import OUT, ROOT, STATES, SEQUENCES, register


class AnimationPreviewTests(unittest.TestCase):
    def test_output_is_outside_site(self):
        self.assertTrue(OUT.is_relative_to(ROOT / 'results'))
        self.assertFalse(OUT.is_relative_to(ROOT / 'site'))

    def test_common_eye_anchor(self):
        outputs = []
        for dx in (0, 12):
            source = Image.new('RGBA', (200, 180), 'white')
            ImageDraw.Draw(source).rectangle((130 + dx, 45, 140 + dx, 55), fill=(240, 20, 10, 255))
            result, eye = register(source)
            self.assertEqual(eye, (135 + dx, 50))
            self.assertEqual(result.size, (320, 320))
            self.assertEqual(result.getbbox(), (240, 115, 251, 126))
            outputs.append(result.tobytes())
        self.assertEqual(*outputs)

    def test_missing_anchor_rejected(self):
        with self.assertRaises(ValueError):
            register(Image.new('RGBA', (200, 180), 'white'))

    def test_all_sequences_valid(self):
        self.assertEqual(set(STATES), set(SEQUENCES))
        for sequence in SEQUENCES.values():
            for frame, duration in sequence:
                self.assertIn(frame, range(4))
                self.assertGreater(duration, 0)
        self.assertIn((2, 80), SEQUENCES['proboscis_only'])


if __name__ == '__main__':
    unittest.main()
