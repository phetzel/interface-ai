"""Bounded policy for the trusted synthetic bank, independent of caller targets.

This is not authorization for arbitrary web pages: a malicious application can
imitate pixels. Only the reviewed fixture and a single controller are supported.
"""

import re
from types import SimpleNamespace

from interface_ai.desktop.adapter import DesktopError
from interface_ai.vision import VisionError
from .controls import controls

from .admission import admit as admit, capability_path, reference_bundle
from interface_ai.contracts.approval import POLICY_ID as POLICY_ID

# Compatibility name for the environment profile; its path is operator-owned.
REVIEWED_PATH = capability_path()


class BankPolicy:
    def __init__(self):
        self.bundle = reference_bundle()
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
            was_typed = self.keyboard == 'typed'
            self.keyboard = None
            if search and inside(controls(view, 'search-ready')['member-input']):
                self.pending = 'field'
                return
            if search and was_typed and inside(controls(view, 'search-ready')['search-button']):
                return
            if locate('member-heading') and inside(
                controls(view, 'member-ready')['savings-button']
            ):
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
