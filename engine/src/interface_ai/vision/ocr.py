"""Bounded Tesseract subprocess with PNG stdin and TSV stdout; no image files."""
import csv
from dataclasses import dataclass, field
from io import BytesIO, StringIO
import math
import os
from pathlib import Path
import re
import subprocess
import hashlib

from PIL import Image, ImageOps
from .primitives import VisionError

DATA = Path('/usr/share/tesseract-ocr/5/tessdata/eng.traineddata')


@dataclass(frozen=True)
class Reading:
    text: str = field(repr=False)
    confidence: float


class OCR:
    def __init__(self, *, expected_data_hash, minimum_confidence=80):
        if type(minimum_confidence) not in (int, float) or not 0 <= minimum_confidence <= 100:
            raise VisionError('invalid_threshold', 'OCR confidence must be between 0 and 100')
        self.minimum_confidence = minimum_confidence
        if hashlib.sha256(DATA.read_bytes()).hexdigest() != expected_data_hash:
            raise VisionError('ocr_environment', 'Unexpected English OCR model; recalibration required')

    def line(self, image, region, *, timeout=3):
        if type(timeout) not in (int, float) or not math.isfinite(timeout) or not 0 < timeout <= 10:
            raise VisionError('invalid_deadline', 'OCR timeout must be in (0, 10] seconds')
        region.checked(image.size)
        crop = image.crop(region.tuple()).convert('L')
        crop = crop.resize((crop.width*3, crop.height*3), Image.Resampling.LANCZOS)
        crop = ImageOps.expand(crop, border=24, fill=255)
        buffer = BytesIO()
        crop.save(buffer, format='PNG')
        command = ['tesseract', 'stdin', 'stdout', '--tessdata-dir', str(DATA.parent),
                   '-l', 'eng', '--oem', '1', '--psm', '7', '--dpi', '300', 'tsv']
        try:
            result = subprocess.run(command, input=buffer.getvalue(), capture_output=True,
                                    timeout=timeout, env=os.environ | {'OMP_THREAD_LIMIT': '1'})
        except subprocess.TimeoutExpired:
            raise VisionError('ocr_timeout', 'OCR exceeded its deadline') from None
        except OSError:
            raise VisionError('ocr_unavailable', 'Local OCR executable is unavailable') from None
        if result.returncode:
            # Raw process output might include recognized data; do not export it.
            raise VisionError('ocr_failed', 'Local OCR process failed')
        return self.parse_tsv(result.stdout.decode('utf-8'))

    def parse_tsv(self, text):
        try:
            rows = [row for row in csv.DictReader(StringIO(text), delimiter='\t')
                    if row['level'] == '5' and row['text'].strip()]
            scores = [float(row['conf']) for row in rows]
            if not rows or any(not math.isfinite(score) or not self.minimum_confidence <= score <= 100 for score in scores):
                raise VisionError('ocr_uncertain', 'OCR text is absent or below the confidence threshold')
            return Reading(' '.join(row['text'].strip() for row in rows), min(scores))
        except (KeyError, TypeError, ValueError):
            raise VisionError('ocr_failed', 'Invalid local OCR result') from None


def parse_usd(text):
    # Exact format; no floating point, O/0 substitutions, sign or missing decimals.
    if not isinstance(text, str) or not re.fullmatch(r'\$(?:0|[1-9][0-9]{0,2}(?:,[0-9]{3})*|[1-9][0-9]*)\.[0-9]{2}', text):
        raise VisionError('invalid_amount', 'Balance is not an exact supported USD amount')
    whole, cents = text[1:].replace(',', '').split('.')
    if len(whole) > 12:
        raise VisionError('invalid_amount', 'Balance exceeds the supported numeric range')
    return int(whole)*100 + int(cents)
