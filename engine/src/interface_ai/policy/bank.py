"""Bounded policy for the trusted synthetic bank, independent of caller targets.

This is not authorization for arbitrary web pages: a malicious application can
imitate pixels. Only the reviewed fixture and a single controller are supported.
"""

from pathlib import Path
import re
from types import SimpleNamespace

from interface_ai.desktop.adapter import DesktopError
from interface_ai.replay.loader import load_bundle
from interface_ai.vision import VisionError

POLICY_ID = 'bank-read-only-v1'
APPROVED_SHA256 = '94d37e09907c839e3c04bd1662003ae6529d087e137952e4e844a673d32d9c17'
REVIEWED_PATH = (
    Path(__file__).resolve().parents[4] / 'capabilities/poc/savings-balance/capability.json'
)


def admit(bundle):
    if bundle.sha256 != APPROVED_SHA256:
        raise DesktopError(
            'policy_artifact_denied', 'Capability revision has not been approved for this policy'
        )


class BankPolicy:
    def __init__(self):
        self.bundle = load_bundle(REVIEWED_PATH)
        admit(self.bundle)
        self.keyboard = None
        self.pending = None

    def clear(self):
        self.keyboard = self.pending = None

    def authorize(self, action, desktop):
        from interface_ai.replay.interpreter import Observation

        self.pending = None
        runner = SimpleNamespace(
            cap=self.bundle.capability,
            bundle=self.bundle,
            guard=desktop.checkpoint,
            emit=lambda *a, **kw: None,
        )
        view = Observation(runner, desktop.screenshot())

        def locate(name):
            try:
                return view.target(name)
            except VisionError as exc:
                if exc.code == 'target_missing':
                    return None
                raise DesktopError(
                    'policy_surface_denied', 'Policy target is ambiguous or unsupported'
                ) from None

        def inside(box):
            return (
                box and box.left <= action['x'] < box.right and box.top <= action['y'] < box.bottom
            )

        search = locate('search-heading')
        if not search:
            self.keyboard = None
        if action['type'] == 'click':
            self.keyboard = None
            if search and inside(locate('member-input')):
                self.pending = 'field'
                return
            if locate('member-heading') and inside(locate('savings-button')):
                return
        elif search and self.keyboard:
            if action == {'type': 'hotkey', 'keys': ['ctrl', 'a']}:
                self.pending = 'selected'
                return
            if (
                action['type'] == 'type'
                and self.keyboard in ('field', 'selected')
                and re.fullmatch('[0-9]{5}', action['text'])
            ):
                self.pending = 'typed'
                return
            if action == {'type': 'press', 'key': 'enter'} and self.keyboard == 'typed':
                return
        self.clear()
        raise DesktopError(
            'policy_operation_denied', 'Operation is outside the reviewed read-only workflow'
        )

    def completed(self):
        self.keyboard, self.pending = self.pending, None
