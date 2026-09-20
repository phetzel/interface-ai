"""Read-only controls recognized from bank pixels, independent of action order.

The trusted environment profile supplies label geometry/OCR rules. Its replay
steps are never executed or sent to the provider by discovery.
"""

import time
from interface_ai.contracts.models import SavingsOutput, Success, BusinessOutcome
from interface_ai.desktop import DesktopError
from interface_ai.policy.bank import REVIEWED_PATH, admit
from interface_ai.replay.loader import load_bundle
from interface_ai.replay.recognition import Recognition
from interface_ai.vision import Box, VisionError

OUTPUT_FIELDS = dict(
    memberId='account-member-id',
    memberName='member-name',
    accountType='account-type',
    currency='currency',
    amountMinor='balance',
)


class DiscoveryPolicy:
    def __init__(self, inputs):
        self.inputs = inputs
        self.bundle = load_bundle(REVIEWED_PATH)
        admit(self.bundle)
        self.keyboard = self.pending = None
        self.last_target = None

    def view(self, desktop):
        runner = Recognition(self.bundle, self.inputs, desktop)
        runner.step_deadline = time.monotonic() + 6
        view = runner.observe()
        try:
            for heading, checkpoint in [
                ('account-heading', 'account-ready'),
                ('member-heading', 'member-ready'),
            ]:
                try:
                    view.target(heading)
                except VisionError as exc:
                    if exc.code == 'target_missing':
                        continue
                    raise
                if not view.checkpoint(checkpoint):
                    raise DesktopError(
                        'identity_mismatch', 'The visible account/member does not match'
                    )
                result = None
                if checkpoint == 'account-ready':
                    result = Success(
                        output=SavingsOutput.model_validate(
                            {key: view.field(name) for key, name in OUTPUT_FIELDS.items()}
                        )
                    )
                runner.guard()
                return view, checkpoint, result
            if view.checkpoint('search-ready'):
                if view.checkpoint('member-not-found'):
                    return view, 'member-not-found', BusinessOutcome(outcome='member_not_found')
                entered = view.checkpoint('input-entered')
                runner.guard()
                return view, 'input-entered' if entered else 'search-ready', None
            # Unknown screens, including password/session-expiry dialogs, are never
            # provider observations. The operator may inspect the same desktop.
            raise DesktopError('policy_capture_denied', 'Expected a verified synthetic bank screen')
        except VisionError as exc:
            raise DesktopError(exc.code, 'Visual verification rejected the observation') from None

    @staticmethod
    def controls(view, state):
        if state in ('search-ready', 'input-entered'):
            label = view.target('member-field')
            return {
                'member-input': Box(
                    label.left + 8, label.top + 57, label.left + 520, label.top + 90
                ),
                'search-button': Box(
                    label.left + 535, label.top + 57, label.left + 640, label.top + 90
                ),
            }
        if state == 'member-ready':
            # Matching a label is narrower than its button. Include the button's
            # reviewed padding, but never the neighboring account row.
            label = view.target('savings-button')
            return {
                'savings-button': Box(
                    label.left - 12, label.top - 12, label.right + 30, label.bottom + 12
                )
            }
        return {}

    def authorize(self, action, desktop):
        self.pending = self.last_target = None
        view, state, result = self.view(desktop)
        if result is not None:
            raise DesktopError('policy_operation_denied', 'Task is already complete')
        if action['type'] == 'click':
            self.keyboard = None
            matches = [
                name
                for name, box in self.controls(view, state).items()
                if box.left <= action['x'] < box.right and box.top <= action['y'] < box.bottom
            ]
            if len(matches) == 1:
                target = matches[0]
                if target == 'search-button' and state != 'input-entered':
                    raise DesktopError(
                        'policy_operation_denied', 'Verify member input before submitting'
                    )
                self.last_target = target
                self.pending = 'field' if target == 'member-input' else None
                return
        elif state in ('search-ready', 'input-entered') and self.keyboard:
            if action == {'type': 'hotkey', 'keys': ['ctrl', 'a']}:
                self.pending = 'selected'
                return
            if action == {'type': 'type', 'text': self.inputs.memberId} and self.keyboard in (
                'field',
                'selected',
            ):
                self.pending = 'typed'
                return
            if action == {'type': 'press', 'key': 'enter'} and state == 'input-entered':
                return
        self.clear()
        raise DesktopError(
            'policy_operation_denied', 'Input is outside visible read-only bank controls'
        )

    def clear(self):
        self.keyboard = self.pending = None

    def completed(self):
        self.keyboard, self.pending = self.pending, None
