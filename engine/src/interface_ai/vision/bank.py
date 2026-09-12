"""Manually calibrated PoC recognition for the synthetic bank, not an interpreter.

Only screenshots and declared member input enter here. No fixture source, DOM,
oracle, network, or desktop input. Click points are resolved afresh from pixels.
"""
import hashlib
import json
from pathlib import Path
import re

from PIL import Image
from .primitives import Box, VisionError, find_matches, unique_match
from .ocr import OCR, parse_usd

ANCHORS = Path(__file__).with_name('anchors')
ENGLISH_SHA256 = '7d4322bd2a7749724879683fc3912cb542f19906c83bcc1a52132556427170b2'
THRESHOLD = .92


def validate_member_id(member_id):
    if not isinstance(member_id, str) or not re.fullmatch('[0-9]{5}', member_id):
        raise VisionError('invalid_member_id', 'Member ID must be exactly five ASCII digits')


class BankVision:
    def __init__(self, *, event_sink=None):
        manifest = json.loads((ANCHORS / 'manifest.json').read_text())
        self.templates = {}
        for name, entry in manifest.items():
            path = ANCHORS / (name + '.png')
            if hashlib.sha256(path.read_bytes()).hexdigest() != entry['sha256']:
                raise VisionError('anchor_integrity', 'Visual anchor hash does not match calibration')
            with Image.open(path) as image:
                self.templates[name] = image.convert('RGB')
        self.ocr = OCR(expected_data_hash=ENGLISH_SHA256)
        self.event_sink = event_sink or (lambda event: None)

    def locate(self, name, image, region=None):
        if image.size != (1280, 800):
            raise VisionError('unsupported_display', 'Recognition requires the calibrated 1280x800 display')
        try:
            match = unique_match(image, self.templates[name], region, threshold=THRESHOLD)
        except VisionError as exc:
            self.event_sink({'kind': 'match', 'target': name, 'status': 'rejected',
                             'code': exc.code, **exc.details})
            raise
        self.event_sink({'kind': 'match', 'target': name, 'status': 'matched',
                         'candidateCount': 1, 'score': round(match.score, 6), 'box': match.box.tuple()})
        return match.box

    def heading(self, image, view):
        return self.locate(view+'-heading', image, Box(70, 180, 650, 330))

    def read(self, image, region, field):
        try:
            reading = self.ocr.line(image, region)
        except VisionError as exc:
            self.event_sink({'kind': 'ocr', 'field': field, 'status': 'rejected', 'code': exc.code})
            raise
        self.event_sink({'kind': 'ocr', 'field': field, 'status': 'read',
                         'confidence': round(reading.confidence, 3), 'box': region.tuple()})
        return reading.text

    def search_target(self, image):
        heading = self.heading(image, 'search')
        field = self.locate('member-field', image, heading.relative((0, 140, 700, 260), image.size))
        # The declared target is inside the input below its visible label.
        return field.relative((80, 60, 160, 90), image.size).center

    def identity(self, image, heading, member_id):
        validate_member_id(member_id)
        actual = self.read(image, heading.relative((140, 140, 228, 158), image.size), 'memberId')
        if actual != member_id:
            raise VisionError('identity_mismatch', 'Visible member identity does not match the requested member')
        name = self.read(image, heading.relative((78, 110, 400, 138), image.size), 'memberName')
        if not re.fullmatch("[A-Za-z][A-Za-z .'-]{1,79}", name):
            raise VisionError('invalid_identity', 'Visible member name is not a supported reading')
        return {'memberId': actual, 'memberName': name}

    def savings_target(self, image, member_id):
        heading = self.heading(image, 'member')
        self.identity(image, heading, member_id)
        region = Box(heading.left, heading.top+250, min(heading.left+1080, image.width), image.height)
        savings = self.locate('savings-label', image, region)
        button = self.locate('view-account', image, savings.relative((700, -10, 985, 45), image.size))
        return button.center

    def savings_balance(self, image, member_id):
        heading = self.heading(image, 'account')
        identity = self.identity(image, heading, member_id)
        account = self.read(image, heading.relative((974, 225, 1043, 249), image.size), 'accountType')
        currency = self.read(image, heading.relative((990, 296, 1043, 321), image.size), 'currency')
        if account != 'Savings' or currency != 'USD':
            raise VisionError('account_mismatch', 'Visible account type or currency is not the requested savings context')
        balance = self.read(image, heading.relative((30, 278, 720, 353), image.size), 'balance')
        return identity | {'accountType': account, 'currency': currency, 'amountMinor': parse_usd(balance)}


def wait_for_heading(desktop, vision, view, *, timeout=5):
    def observe():
        screen = desktop.screenshot()
        try:
            vision.heading(screen, view)
            return screen
        except VisionError as exc:
            if exc.code == 'target_missing':
                return None
            raise
    return desktop.wait('visible '+view+' heading', observe, timeout=timeout)
