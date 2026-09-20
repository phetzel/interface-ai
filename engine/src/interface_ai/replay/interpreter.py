"""Execute the artifact's finite sequence; no bank-specific workflow calls."""

import time
from pydantic import ValidationError

from interface_ai.contracts.models import (
    BusinessOutcome,
    Extract,
    Failure,
    SavingsOutput,
    Success,
)
from .recognition import Observation, Recognition
from .loader import ReplayError


class Interpreter(Recognition):
    def __init__(
        self,
        bundle,
        inputs,
        desktop,
        *,
        event_sink=None,
        capture_sink=None,
        observer_factory=Observation,
        ocr=None,
        clock=time.monotonic,
        pause_check=None,
    ):
        super().__init__(
            bundle,
            inputs,
            desktop,
            event_sink=event_sink,
            observer_factory=observer_factory,
            ocr=ocr,
            clock=clock,
        )
        self.capture_sink = capture_sink or (lambda name, image: None)
        self.pause_check = pause_check

    def wait_after_action(self):
        while True:
            observation = self.observe()
            if self.pause_check:
                self.pause_check(self, observation)
            matches = [
                post for post in self.step.postconditions if observation.checkpoint(post.checkpoint)
            ]
            self.guard()  # Reject observations that completed after stop/deadline.
            if len(matches) > 1:
                raise ReplayError(
                    'ambiguous_checkpoint', 'Multiple postconditions matched the same screenshot'
                )
            if matches:
                post = matches[0]
                self.emit('checkpoint', checkpoint=post.checkpoint, status='satisfied')
                self.capture_sink(self.step.id + '-after', observation.image)
                return post.outcome
            time.sleep(min(0.05, max(0, self.step_deadline - self.clock())))

    def run(self, *, start_at=0):
        try:
            for step in self.cap.steps[start_at:]:
                self.step = step
                self.step_deadline = self.clock() + step.timeoutSeconds
                self.emit('step', action=step.action, status='started')
                observation = self.observe()
                if not observation.checkpoint(step.precondition):
                    raise ReplayError(
                        'precondition_failed', 'Required screen checkpoint is not satisfied'
                    )
                self.guard()
                if isinstance(step, Extract):
                    values = {
                        key: observation.field(field)
                        for key, field in step.fields.model_dump().items()
                    }
                    output = SavingsOutput.model_validate(values)
                    if output.memberId != self.inputs.memberId:
                        raise ReplayError(
                            'identity_mismatch', 'Output identity does not match the invocation'
                        )
                    self.guard()
                    self.capture_sink(step.id + '-final', observation.image)
                    self.emit('step', action=step.action, status='completed')
                    return Success(output=output)
                if step.action == 'click':
                    x, y = observation.target(step.target).center
                    action = {'type': 'click', 'x': x, 'y': y}
                elif step.action == 'type':
                    action = {'type': 'type', 'text': self.inputs.memberId}
                elif step.action == 'press':
                    action = {'type': 'press', 'key': step.key}
                else:
                    action = {'type': 'hotkey', 'keys': step.keys}
                self.guard()
                self.desktop.execute(action)
                outcome = self.wait_after_action()
                self.emit('step', action=step.action, status='completed')
                if outcome:
                    return BusinessOutcome(outcome=outcome)
        except Exception as exc:
            from interface_ai.policy.evidence import safe_code

            code = (
                'invalid_output'
                if isinstance(exc, ValidationError)
                else getattr(exc, 'code', 'execution_failed')
            )
            code = safe_code(code)
            expected = (
                [self.step.precondition]
                if code == 'precondition_failed'
                else [p.checkpoint for p in getattr(self.step, 'postconditions', [])]
            )
            if isinstance(self.step, Extract) and code != 'precondition_failed':
                expected = ['validated-output']
            self.emit(
                'step', action=self.step.action if self.step else None, status='failed', code=code
            )
            return Failure(
                code=code,
                step=self.step.id if self.step else None,
                expected=expected,
                observed='checkpoint_not_satisfied'
                if code in ('precondition_failed', 'checkpoint_timeout')
                else 'rejected',
            )
        return Failure(code='missing_completion')
