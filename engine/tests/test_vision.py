import subprocess
import unittest
from unittest.mock import patch

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from interface_ai.vision import Box, VisionError, find_matches, unique_match, OCR, parse_usd
from interface_ai.policy.profile import reference_bundle

ENGLISH_SHA256 = reference_bundle().capability.environment.ocrModelSha256


class VisionTests(unittest.TestCase):
    def setUp(self):
        self.anchor = Image.fromarray(
            np.random.default_rng(7).integers(0, 255, (19, 31), dtype=np.uint8)
        )
        self.scene = Image.new('L', (400, 250), 240)

    def assert_code(self, code, operation):
        with self.assertRaises(VisionError) as error:
            operation()
        self.assertEqual(error.exception.code, code)

    def test_anchor_relocates_after_translation(self):
        for x, y in [(70, 45), (110, 85)]:
            scene = self.scene.copy()
            scene.paste(self.anchor, (x, y))
            self.assertEqual(unique_match(scene, self.anchor).box, Box(x, y, x + 31, y + 19))

    def test_duplicate_targets_reject_despite_one_higher_score(self):
        self.scene.paste(self.anchor, (40, 40))
        near = np.asarray(self.anchor).copy()
        near[0, 0] = 128
        self.scene.paste(Image.fromarray(near), (140, 140))
        self.assertEqual(len(find_matches(self.scene, self.anchor)), 2)
        self.assert_code('ambiguous_target', lambda: unique_match(self.scene, self.anchor))

    def test_region_resolves_only_the_declared_context(self):
        self.scene.paste(self.anchor, (40, 40))
        self.scene.paste(self.anchor, (140, 140))
        self.assertEqual(
            unique_match(self.scene, self.anchor, Box(120, 120, 200, 200)).box.left, 140
        )

    def test_missing_or_nondistinctive_anchor_rejects(self):
        self.assert_code('target_missing', lambda: unique_match(self.scene, self.anchor))
        self.assert_code(
            'invalid_anchor', lambda: unique_match(self.scene, Image.new('L', (20, 20), 240))
        )

    def test_invalid_geometry_and_thresholds_reject(self):
        for box in [
            Box(-1, 0, 20, 20),
            Box(0, 0, 500, 20),
            Box(10, 0, 10, 20),
            Box(True, 0, 20, 20),
        ]:
            self.assert_code('invalid_region', lambda: find_matches(self.scene, self.anchor, box))
        for threshold in [float('nan'), 0.1, 1.1, True]:
            self.assert_code(
                'invalid_threshold',
                lambda: find_matches(self.scene, self.anchor, threshold=threshold),
            )

    def test_amount_parsing_preserves_cents_without_guessing(self):
        for text, expected in [
            ('$0.00', 0),
            ('$12.03', 1203),
            ('$9,876.54', 987654),
            ('$1234.05', 123405),
        ]:
            self.assertEqual(parse_usd(text), expected)
        for text in [
            '',
            '—',
            '$O.00',
            '$1,23.45',
            '$01.23',
            '$12',
            '$12.3',
            '$12.345',
            '-$1.00',
            '$1.00 USD',
            '$ 1.00',
            '$1.00\n',
        ]:
            self.assert_code('invalid_amount', lambda: parse_usd(text))

    def test_model_hash_mismatch_fails_before_ocr(self):
        self.assert_code('ocr_environment', lambda: OCR(expected_data_hash='incorrect'))

    def test_actual_ocr_uses_memory_pipes_and_preserves_zeroes(self):
        ocr = OCR(expected_data_hash=ENGLISH_SHA256)
        image = Image.new('RGB', (340, 70), 'white')
        ImageDraw.Draw(image).text(
            (12, 10),
            '00340',
            fill='black',
            font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 32),
        )
        real_run = subprocess.run
        calls = []

        def capture(command, **kwargs):
            calls.append((command, kwargs))
            return real_run(command, **kwargs)

        with patch('interface_ai.vision.ocr.subprocess.run', side_effect=capture):
            reading = ocr.line(image, Box(0, 0, 340, 70))
        self.assertEqual(reading.text, '00340')
        self.assertNotIn('00340', repr(reading))
        self.assertEqual(calls[0][0][1:3], ['stdin', 'stdout'])
        self.assertTrue(calls[0][1]['input'].startswith(b'\x89PNG'))

    def test_blank_or_low_confidence_ocr_rejects(self):
        ocr = OCR(expected_data_hash=ENGLISH_SHA256)
        self.assert_code(
            'ocr_uncertain',
            lambda: ocr.line(Image.new('RGB', (150, 50), 'white'), Box(0, 0, 150, 50)),
        )
        for confidence in ['79', 'nan', '-1']:
            tsv = 'level\tconf\ttext\n5\t' + confidence + '\tsentinel\n'
            self.assert_code('ocr_uncertain', lambda: ocr.parse_tsv(tsv))

    def test_ocr_subprocess_deadline_is_enforced(self):
        ocr = OCR(expected_data_hash=ENGLISH_SHA256)
        image = Image.new('RGB', (100, 40), 'white')
        with patch(
            'interface_ai.vision.ocr.subprocess.run',
            side_effect=subprocess.TimeoutExpired('tesseract', 0.01),
        ):
            self.assert_code(
                'ocr_timeout', lambda: ocr.line(image, Box(0, 0, 100, 40), timeout=0.01)
            )


if __name__ == '__main__':
    unittest.main()
