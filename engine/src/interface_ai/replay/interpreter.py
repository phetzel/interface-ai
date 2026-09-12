"""Execute the artifact's finite sequence; no bank-specific workflow calls."""
import re
import time
from pydantic import ValidationError

from interface_ai.contracts.models import (Anchor, BusinessOutcome, Extract, Failure,
                                          InputAssertion, SavingsOutput, Success)
from interface_ai.vision import Box, OCR, VisionError, parse_usd, unique_match
from .loader import ReplayError


class Observation:
    def __init__(self, runner, image):
        self.runner, self.image = runner, image
        self.targets, self.fields = {}, {}

    def region(self, specification):
        box = specification.box
        if specification.relativeTo is not None:
            parent = self.target(specification.relativeTo)
            box = [parent.left+box[0], parent.top+box[1], parent.left+box[2], parent.top+box[3]]
        if specification.clipToDisplay:
            box = [max(0, box[0]), max(0, box[1]), min(self.image.width, box[2]), min(self.image.height, box[3])]
        return Box(*box).checked(self.image.size)

    def target(self, name):
        if name not in self.targets:
            self.runner.guard()
            target = self.runner.cap.targets[name]
            region = self.region(target.region)
            if isinstance(target, Anchor):
                try:
                    match = unique_match(self.image, self.runner.bundle.templates[target.asset], region, threshold=target.threshold)
                except VisionError as exc:
                    self.runner.emit('target', target=name, status='rejected', code=exc.code, **exc.details)
                    raise
                region = match.box
                self.runner.emit('target', target=name, status='matched', score=round(match.score, 6), candidateCount=1, box=list(region.tuple()))
            self.targets[name] = region
        return self.targets[name]

    def field(self, name):
        if name not in self.fields:
            spec = self.runner.cap.fields[name]
            region = self.region(spec.region)
            self.runner.guard()
            remaining = self.runner.step_deadline - self.runner.clock()
            reading = self.runner.ocr.line(self.image, region, timeout=min(3, remaining))
            self.runner.guard()
            value = reading.text
            if spec.parser == 'usd_minor':
                value = parse_usd(value)
            elif spec.parser == 'member_id' and not re.fullmatch('[0-9]{5}', value):
                raise ReplayError('invalid_identity', 'Visible identity is not an exact member ID')
            self.runner.emit('reading', field=name, confidence=round(reading.confidence, 3), box=list(region.tuple()))
            self.fields[name] = value
        return self.fields[name]

    def checkpoint(self, name):
        checkpoint = self.runner.cap.checkpoints[name]
        try:
            for target in checkpoint.targets:
                self.target(target)
            for assertion in checkpoint.assertions:
                expected = assertion.prefix+self.runner.inputs.memberId+assertion.suffix if isinstance(assertion, InputAssertion) else assertion.text
                if self.field(assertion.field) != expected:
                    return False
            return True
        except VisionError as exc:
            if exc.code in ('target_missing', 'ocr_uncertain'):
                return False
            raise


class Interpreter:
    def __init__(self, bundle, inputs, desktop, *, event_sink=None, capture_sink=None,
                 observer_factory=Observation, ocr=None, clock=time.monotonic):
        self.bundle, self.cap, self.inputs, self.desktop = bundle, bundle.capability, inputs, desktop
        self.event_sink = event_sink or (lambda event: None)
        self.capture_sink = capture_sink or (lambda name, image: None)
        self.clock, self.observer_factory = clock, observer_factory
        self.ocr = ocr or OCR(expected_data_hash=self.cap.environment.ocrModelSha256,
                              minimum_confidence=self.cap.environment.minimumConfidence)
        self.step = None
        self.step_deadline = self.clock()

    def emit(self, kind, **details):
        self.event_sink({'kind': kind, 'step': self.step.id if self.step else None, **details})

    def guard(self):
        self.desktop.checkpoint()
        if self.clock() >= self.step_deadline:
            raise ReplayError('checkpoint_timeout', 'Step deadline exceeded')

    def observe(self):
        self.guard()
        image = self.desktop.screenshot()
        if image.size != (self.cap.environment.width, self.cap.environment.height):
            raise ReplayError('unsupported_environment', 'Screenshot dimensions do not match the artifact')
        return self.observer_factory(self, image)

    def wait_after_action(self):
        while True:
            observation = self.observe()
            matches = [post for post in self.step.postconditions if observation.checkpoint(post.checkpoint)]
            self.guard()  # Reject observations that completed after stop/deadline.
            if len(matches) > 1:
                raise ReplayError('ambiguous_checkpoint', 'Multiple postconditions matched the same screenshot')
            if matches:
                post = matches[0]
                self.emit('checkpoint', checkpoint=post.checkpoint, status='satisfied')
                self.capture_sink(self.step.id+'-after', observation.image)
                return post.outcome
            time.sleep(min(.05, max(0, self.step_deadline-self.clock())))

    def run(self):
        try:
            for step in self.cap.steps:
                self.step = step
                self.step_deadline = self.clock() + step.timeoutSeconds
                self.emit('step', action=step.action, status='started')
                observation = self.observe()
                if not observation.checkpoint(step.precondition):
                    raise ReplayError('precondition_failed', 'Required screen checkpoint is not satisfied')
                self.guard()
                if isinstance(step, Extract):
                    values = {key: observation.field(field) for key, field in step.fields.model_dump().items()}
                    output = SavingsOutput.model_validate(values)
                    if output.memberId != self.inputs.memberId:
                        raise ReplayError('identity_mismatch', 'Output identity does not match the invocation')
                    self.guard()
                    self.capture_sink(step.id+'-final', observation.image)
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
            code = 'invalid_output' if isinstance(exc, ValidationError) else getattr(exc, 'code', 'execution_failed')
            expected = [self.step.precondition] if code == 'precondition_failed' else [p.checkpoint for p in getattr(self.step, 'postconditions', [])]
            if isinstance(self.step, Extract) and code != 'precondition_failed':
                expected = ['validated-output']
            self.emit('step', action=self.step.action if self.step else None, status='failed', code=code)
            return Failure(code=code, step=self.step.id if self.step else None, expected=expected,
                           observed='checkpoint_not_satisfied' if code in ('precondition_failed', 'checkpoint_timeout') else 'rejected')
        return Failure(code='missing_completion')
