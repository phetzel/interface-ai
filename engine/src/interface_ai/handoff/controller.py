"""One volatile run, one declared continuation, no automatic recovery/retry."""

from datetime import datetime, timezone
import json
from pathlib import Path
import threading
import time
import uuid

from interface_ai.contracts.models import Failure
from interface_ai.desktop import Desktop, DesktopError
from interface_ai.desktop.ownership import Ownership
from interface_ai.desktop.session import LOCK, RUNTIME, STOP, read_session, request_stop
from interface_ai.policy.bank import REVIEWED_PATH, admit
from interface_ai.policy.evidence import checked_event, safe_code
from interface_ai.replay.interpreter import Interpreter
from interface_ai.replay.loader import load_bundle, validate_inputs
from interface_ai.vision import Box, VisionError
from .evidence import write_terminal


class Controller:
    def __init__(self, *, output_root=Path('/artifacts')):
        self.session = read_session()
        self.ownership = Ownership(RUNTIME, self.session['id'])
        self.mutex = threading.RLock()
        self.phase = 'idle'
        self.reason = None
        self.current_step = None
        self.last_checkpoint = None
        self.directory = None
        self.output_root = output_root
        self.inputs = None
        self.bundle = load_bundle(REVIEWED_PATH)
        admit(self.bundle)
        self.resume_at = None
        self.human_sequence = 0
        self.human_deadline = None
        self.started = time.monotonic()
        self.audit = []
        self.result = None
        self.worker = None
        self.terminal_phase = None
        self.evidence_failed = False

    def record(self, kind, **details):
        # All callers pass closed constants / validated metadata. Interpreter
        # geometry describes recognized regions, never human input coordinates.
        # Never pass request bodies, text, key names, pixels or OCR values here.
        event = dict(
            kind=kind, elapsedMs=round((time.monotonic() - self.started) * 1000), **details
        )
        self.audit.append(event)
        try:
            if self.directory:
                with (self.directory / 'audit.jsonl').open('a') as stream:
                    stream.write(json.dumps(event) + '\n')
            if self.result is not None:
                # A primitive already dispatched when Stop arrives can finish.
                # Keep its final count without changing the terminal outcome.
                self.persist_terminal()
        except OSError:
            self.evidence_failure()
            raise DesktopError(
                'execution_failed', 'Run evidence unavailable; reset required'
            ) from None

    def interpreter_event(self, event):
        # Use the same closed event vocabulary as CLI replay. Keep it nested so
        # interpreter completion cannot be counted as an OS input action.
        event = checked_event(event)
        with self.mutex:
            if self.result is None and event.get('step') is not None:
                self.current_step = event['step']
            if (
                self.result is None
                and event.get('kind') == 'checkpoint'
                and event.get('status') == 'satisfied'
            ):
                self.last_checkpoint = event['checkpoint']
            self.record('interpreter', event=event)

    def snapshot(self):
        with self.mutex:
            if STOP.exists() and self.phase != 'stopped':
                self.stop()
            self.expire()
            state = self.ownership.read()
            return dict(
                session=self.session['id'],
                epoch=state['epoch'],
                owner=state['owner'],
                phase=self.phase,
                reason=self.reason,
                sequence=self.human_sequence,
                step=self.current_step,
                lastCheckpoint=self.last_checkpoint,
                resumable=self.resume_at is not None,
                modelCalls=0,
                evidenceStatus='failed' if self.evidence_failed else 'available',
            )

    def verify(self, lease):
        state = self.ownership.read()
        if (
            not isinstance(lease, dict)
            or set(lease) != {'session', 'epoch'}
            or type(lease['epoch']) is not int
            or lease['session'] != self.session['id']
            or lease['epoch'] != state['epoch']
            or read_session()['id'] != self.session['id']
        ):
            raise DesktopError('ownership_revoked', 'Discard this request and refresh ownership')
        return state

    def expire(self):
        if (
            self.human_deadline is not None
            and time.monotonic() >= self.human_deadline
            and self.phase == 'human'
        ):
            self.stop('handoff_expired')

    def persist_terminal(self):
        if self.directory is None or self.result is None:
            return
        try:
            session_unchanged = read_session()['id'] == self.session['id']
        except DesktopError:
            session_unchanged = False
        write_terminal(
            self.directory,
            self.result,
            {
                'format': 'handoff-v2',
                'status': self.terminal_phase,
                'resultStatus': self.result.status,
                'reason': getattr(self.result, 'code', None),
                'step': self.current_step,
                'lastCheckpoint': self.last_checkpoint,
                'modelCalls': 0,
                'sessionId': self.session['id'],
                'sessionUnchanged': session_unchanged,
                'capabilitySha256': self.bundle.sha256,
                'auditEvents': len(self.audit),
                'humanActions': sum(
                    e['kind'] == 'human' and e.get('status') == 'completed' for e in self.audit
                ),
                'automationActions': sum(
                    e['kind'] == 'automation' and e.get('status') == 'completed' for e in self.audit
                ),
            },
        )

    def evidence_failure(self):
        # Never recursively try to log a storage error. Fail closed in memory,
        # signal input first, and expose the missing-evidence state to the panel.
        request_stop()
        state = self.ownership.read()
        if state['owner'] != 'stopped':
            self.ownership.change('stopped', expected=state)
        self.phase, self.reason = 'stopped', 'execution_failed'
        self.resume_at = None
        self.evidence_failed = True
        self.result = Failure(code='execution_failed', step=self.current_step)
        self.terminal_phase = 'stopped'

    def finalize(self, result, *, phase=None):
        # Called under mutex. The first terminal outcome wins; no late worker
        # success can replace Stop. The summary can refresh only event counts.
        if self.result is not None:
            return
        self.result = result
        self.phase = self.terminal_phase = phase or result.status
        self.reason = getattr(result, 'code', None)
        self.resume_at = None
        try:
            self.record(
                'lifecycle', status=self.phase, **({'code': self.reason} if self.reason else {})
            )
        except DesktopError:
            if not self.evidence_failed:
                raise

    def stop(self, reason='stopped'):
        request_stop()
        with self.mutex:
            state = self.ownership.read()
            if state['owner'] != 'stopped':
                self.ownership.change('stopped', expected=state)
            if self.phase == 'stopped':
                return
            reason = safe_code(reason)
            self.finalize(Failure(code=reason, step=self.current_step), phase='stopped')
            # Stop after completion disables input but preserves that run's result.
            self.phase = 'stopped'
            if not self.evidence_failed:
                self.reason = reason
            self.resume_at = None

    def start(self, member_id, lease):
        with self.mutex:
            self.verify(lease)
            if self.phase != 'idle' or self.session['mode'] != 'bank':
                raise DesktopError(
                    'invalid_transition', 'Reset the bank desktop before starting another run'
                )
            self.inputs = validate_inputs({'memberId': member_id})
            self.started = time.monotonic()
            name = (
                datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
                + '-handoff-'
                + uuid.uuid4().hex[:8]
            )
            self.directory = self.output_root / name
            self.directory.mkdir(mode=0o700)
            self.record('lifecycle', status='started')
            self.launch(0)

    def launch(self, start_at):
        self.phase, self.reason = 'running', None
        epoch = self.ownership.read()['epoch']
        self.worker = threading.Thread(target=self.run, args=(start_at, epoch), daemon=True)
        self.worker.start()

    @staticmethod
    def detect_expiry(runner, observation):
        if runner.step.id != 'search-member':
            return
        try:
            text = runner.ocr.line(observation.image, Box(400, 235, 880, 290), timeout=1).text
        except VisionError as exc:
            if exc.code == 'ocr_uncertain':
                return
            raise
        runner.guard()
        if text == 'Session expired':
            raise DesktopError(
                'intervention_required', 'Synthetic session expiry requires an operator'
            )

    def run(self, start_at, epoch):
        try:

            def action_event(event):
                with self.mutex:
                    self.record('automation', **checked_event(event))

            with Desktop(self.session['id'], epoch=epoch, event_sink=action_event) as desktop:
                runner = Interpreter(
                    self.bundle,
                    self.inputs,
                    desktop,
                    pause_check=self.detect_expiry,
                    event_sink=self.interpreter_event,
                )
                result = runner.run(start_at=start_at)
            with self.mutex:
                if self.phase != 'running':
                    return  # A manual takeover/stop superseded this worker.
                if STOP.exists():
                    self.stop()
                    return
                if (
                    result.status == 'failure'
                    and result.code == 'intervention_required'
                    and result.step == 'search-member'
                ):
                    # Revoke queued actions immediately on detection, even if the
                    # operator has not opened the panel or requested control yet.
                    self.ownership.change(
                        'quiescing',
                        expected={
                            'session': self.session['id'],
                            'owner': 'automation',
                            'epoch': epoch,
                        },
                    )
                    self.resume_at = 4  # Reviewed boundary: after search, before opening savings.
                    self.phase, self.reason = 'awaiting_human', 'intervention_required'
                    self.record('lifecycle', status='awaiting_human')
                    return
                self.finalize(result)
        except Exception as exc:
            with self.mutex:
                self.stop(safe_code(getattr(exc, 'code', 'execution_failed')))

    def takeover(self, lease):
        # Do not hold mutex while draining: adapter event logging needs it before
        # releasing input.lock. Mark the phase first so the worker cannot resume.
        with self.mutex:
            state = self.verify(lease)
            if self.phase not in ('running', 'awaiting_human'):
                raise DesktopError(
                    'invalid_transition', 'There is no running or paused workflow to take over'
                )
            if self.phase == 'running':
                self.resume_at = None  # An arbitrary interruption has no proven continuation.
            self.phase = 'quiescing'
        try:
            state = self.ownership.takeover(LOCK, expected=state)
        except Exception:
            with self.mutex:
                self.stop('quiesce_timeout')
            raise
        with self.mutex:
            # A concurrent stop must win even after the barrier drained.
            self.ownership.check('human', state['epoch'])
            self.phase, self.reason = 'human', None
            self.human_deadline = time.monotonic() + 900
            self.record('lifecycle', status='human', epoch=state['epoch'])

    def human_action(self, action, lease, sequence):
        with self.mutex:
            self.expire()
            state = self.verify(lease)
            if (
                self.phase != 'human'
                or type(sequence) is not int
                or sequence != self.human_sequence
                or sequence >= 100
            ):
                raise DesktopError(
                    'invalid_transition',
                    'Human input requires current ownership and a fresh sequence',
                )
            self.human_sequence += 1  # Consume before dispatch; uncertain actions must not retry.
            with Desktop(
                self.session['id'],
                role='human',
                epoch=state['epoch'],
                timeout=10,
                event_sink=lambda event: self.record(
                    'human', **checked_event(dict(event, sequence=self.human_sequence))
                ),
            ) as desktop:
                desktop.execute(action)

    def resume(self, lease):
        with self.mutex:
            self.expire()
            state = self.verify(lease)
            if self.phase != 'human' or self.resume_at is None:
                raise DesktopError(
                    'invalid_transition', 'No verified continuation is available; reset required'
                )
            with Desktop(
                self.session['id'], role='human', epoch=state['epoch'], timeout=10
            ) as desktop:
                runner = Interpreter(
                    self.bundle, self.inputs, desktop, event_sink=self.interpreter_event
                )
                runner.step = runner.cap.steps[self.resume_at]
                runner.step_deadline = time.monotonic() + 5
                try:
                    valid = runner.observe().checkpoint('member-ready')
                    runner.guard()
                except (DesktopError, VisionError):
                    valid = False
                runner.emit(
                    'checkpoint',
                    checkpoint='member-ready',
                    status='satisfied' if valid else 'unsatisfied',
                )
                if not valid:
                    self.record('lifecycle', status='rejected', code='resume_rejected')
                    raise DesktopError(
                        'resume_rejected', 'Return to the original member overview before resuming'
                    )
                # Validate and transfer while input.lock still excludes human requests.
                self.ownership.change('automation', expected=state)
                self.record('lifecycle', status='resumed')
            self.launch(self.resume_at)
