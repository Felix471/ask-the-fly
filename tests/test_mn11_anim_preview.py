"""Deterministic staging guardrails; generated art is local, not required in CI."""
import unittest
from PIL import Image, ImageDraw
from scripts.mn11_anim_preview import OUT, ROOT, STATES, SEQUENCES, register, body_motion, motion_tile


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

    def test_eats_repeats_contact_not_extension(self):
        self.assertGreaterEqual(sum(i == 2 for i, _ in SEQUENCES['eats']), 3)
        self.assertEqual(sum(i == 2 for i, _ in SEQUENCES['proboscis_only']), 1)

    def test_rejection_turns_and_leaves_frame(self):
        self.assertEqual(body_motion('no_response', 0), (0, False))
        self.assertEqual(body_motion('no_response', 7), (0, True))
        self.assertEqual(body_motion('no_response', 17), (-72, True))
        self.assertIsNone(motion_tile(Image.new('RGBA', (48, 48), 'red'), 'no_response', 17).getbbox())

    def test_orange_thorax_does_not_shift_eye(self):
        source = Image.new('RGBA', (200, 180), 'white')
        draw = ImageDraw.Draw(source)
        draw.rectangle((20, 20, 120, 80), fill=(210, 90, 20, 255))
        draw.rectangle((130, 45, 140, 55), fill=(240, 20, 10, 255))
        _, eye = register(source)
        self.assertEqual(eye, (135, 50))


if __name__ == '__main__':
    unittest.main()
