"""One model-selected click, with a lifetime input reservation and no provider SDK.

This diagnostic is exercised only by the simulated transport suite. It cannot
type, navigate, record a capability or resume a workflow.
A worker owns the adapter across both API turns. Stop/epoch changes invalidate it
while it waits; HTTP request threads never own its X11 connection or input lock.
"""

import base64
from concurrent.futures import Future, TimeoutError as FutureTimeout
from datetime import datetime, timezone
from io import BytesIO
import json
from queue import Empty
import time
import threading
from types import SimpleNamespace

from interface_ai.desktop import Desktop, DesktopError
from interface_ai.desktop.session import request_stop
from interface_ai.policy.bank import REVIEWED_PATH, admit
from interface_ai.policy.evidence import checked_event, safe_code
from interface_ai.replay.interpreter import Observation
from interface_ai.replay.loader import load_bundle
from interface_ai.vision import Box, VisionError
from .reservation import Reservation

POLICY_ID = 'synthetic-search-single-click-v1'


class SearchPolicy:
    def __init__(self):
        self.bundle = load_bundle(REVIEWED_PATH)
        admit(self.bundle)

    def observe(self, desktop):
        desktop.checkpoint()  # Screenshot alone does not check focus/ownership.
        image = desktop.screenshot()
        runner = SimpleNamespace(
            cap=self.bundle.capability,
            bundle=self.bundle,
            guard=desktop.checkpoint,
            emit=lambda *a, **kw: None,
        )
        view = Observation(runner, image)
        try:
            view.target('search-heading')
            label = view.target('member-field')
            # Reviewed interior of this fixed fixture's text field, relative to
            # its label. Replay's smaller aiming region is not the control's bounds.
            box = Box(label.left + 8, label.top + 60, label.left + 520, label.top + 90)
            box.checked(image.size)
        except VisionError:
            raise DesktopError(
                'policy_capture_denied', 'Expected synthetic search screen'
            ) from None
        desktop.checkpoint()
        return image, box

    def authorize(self, action, desktop):
        if set(action) != {'type', 'x', 'y'} or action['type'] != 'click':
            raise DesktopError('policy_operation_denied', 'Probe only permits a field click')
        _, box = self.observe(desktop)
        if not (box.left <= action['x'] < box.right and box.top <= action['y'] < box.bottom):
            raise DesktopError('policy_operation_denied', 'Probe only permits the member field')

    def clear(self):
        pass

    def completed(self):
        pass


def click(action):
    if (
        not isinstance(action, dict)
        or set(action) != {'type', 'button', 'x', 'y'}
        or action['type'] != 'click'
        or action['button'] != 'left'
        or any(type(action[k]) is not int for k in ('x', 'y'))
        or not (0 <= action['x'] < 1280 and 0 <= action['y'] < 800)
    ):
        raise DesktopError('invalid_action', 'Probe accepts exactly one bounded left click')
    return {'type': 'click', 'x': action['x'], 'y': action['y']}


class TransportDiagnostic(Reservation):
    def __init__(self, controller, *, desktop_factory=Desktop, policy_factory=SearchPolicy):
        super().__init__(controller, desktop_factory=desktop_factory, policy_factory=policy_factory)

    def record(self, event):
        event = checked_event(event)
        try:
            with (self.directory / 'events.jsonl').open('a') as stream:
                stream.write(json.dumps(event) + '\n')
        except OSError:
            request_stop()
            raise DesktopError('execution_failed', 'Probe evidence unavailable') from None

    def summary(self):
        return dict(
            format='provider-probe-v1',
            policy=POLICY_ID,
            runId=self.run_id,
            sessionId=self.controller.session['id'],
            epoch=self.epoch,
            status=self.status,
            code=self.code,
            actionsCompleted=self.actions,
            observations=self.observations,
            modelCalls=None,  # Only the host/provider report knows; never claim zero.
            provenance='guarded-transport-probe',
            elapsedMs=round((time.monotonic() - self.started) * 1000),
        )

    def start(self, session):
        with self.controller.mutex:
            if (
                self.worker is not None
                or self.controller.phase != 'idle'
                or self.controller.session['mode'] != 'bank'
                or session != self.controller.session['id']
            ):
                raise DesktopError('invalid_transition', 'Reset to a fresh bank search first')
            state = self.controller.ownership.read()
            if state['owner'] != 'automation':
                raise DesktopError('ownership_revoked', 'Automation does not own the desktop')
            self.epoch = state['epoch']
            self.controller.phase = 'probing'
            self.status = 'running'
            self.started = time.monotonic()
            initial = Future()
            self.worker = threading.Thread(target=self.run, args=(initial,), daemon=True)
            self.worker.start()
        return self.wait(initial)

    def wait(self, future):
        try:
            return future.result(timeout=8)
        except FutureTimeout:
            self.cancelled.set()  # Do not leave an uncertain queued action retryable.
            request_stop()
            raise DesktopError('deadline', 'Probe transport timed out; reset required') from None

    def frame(self, desktop, policy):
        image, _ = policy.observe(desktop)
        output = BytesIO()
        image.save(output, format='PNG')
        raw = output.getvalue()
        if len(raw) > 4 * 1024 * 1024:
            raise DesktopError('policy_capture_denied', 'Observation exceeds size limit')
        desktop.checkpoint()
        self.observations += 1
        return dict(lease=self.lease(), width=1280, height=800, png=base64.b64encode(raw).decode())

    def run(self, initial):
        pending = initial
        try:
            name = (
                datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-probe-' + self.run_id[:8]
            )
            self.directory = self.controller.output_root / name
            self.directory.mkdir(mode=0o700)
            self.persist()
            policy = self.policy_factory()
            with self.desktop_factory(
                self.controller.session['id'],
                epoch=self.epoch,
                timeout=100,
                event_sink=self.record,
                bank_policy_factory=lambda: policy,
            ) as desktop:
                initial.set_result(self.frame(desktop, policy))
                pending = None
                while True:
                    desktop.checkpoint()
                    if self.cancelled.is_set():
                        raise DesktopError('stopped', 'Probe cancelled')
                    try:
                        operation, data, pending = self.commands.get(timeout=0.05)
                    except Empty:
                        continue
                    desktop.checkpoint()
                    if self.cancelled.is_set():
                        raise DesktopError('stopped', 'Probe cancelled')
                    lease = data.get('lease')
                    if (
                        not isinstance(lease, dict)
                        or lease != self.lease()
                        or any(type(lease.get(k)) is not int for k in ('epoch', 'sequence'))
                    ):
                        raise DesktopError('ownership_revoked', 'Stale probe observation')
                    if operation == 'action':
                        if set(data) != {'lease', 'action'} or self.sequence != 0:
                            raise DesktopError('invalid_action', 'Probe action already consumed')
                        self.sequence += 1  # Consume even if dispatch fails; never retry input.
                        action = click(data['action'])
                        desktop.execute(action)  # Adapter applies the probe policy and all guards.
                        self.actions += 1
                        result = self.frame(desktop, policy)
                    elif operation == 'check':
                        if set(data) != {'lease'}:
                            raise DesktopError('invalid_action', 'Unexpected fields')
                        result = {'lease': self.lease()}
                    elif operation == 'finish':
                        if set(data) != {'lease'} or self.sequence != 1 or self.actions != 1:
                            raise DesktopError('invalid_transition', 'One completed click required')
                        self.status = 'passed'
                        result = {'status': 'passed', 'runId': self.run_id}
                    else:
                        raise DesktopError('invalid_action', 'Unsupported probe operation')
                    desktop.checkpoint()
                    if self.status == 'passed':
                        break
                    pending.set_result(result)
                    pending = None
            self.persist()
            pending.set_result(result)
            pending = None
        except Exception as exc:
            self.status, self.code = 'failed', safe_code(getattr(exc, 'code', 'execution_failed'))
            try:
                self.persist()
            except DesktopError:
                self.code = 'execution_failed'
            if pending is not None and not pending.done():
                pending.set_exception(DesktopError(self.code, 'Probe failed; inspect safe report'))
        finally:
            # No network/provider callback can revive this reservation.
            with self.controller.mutex:
                if self.controller.phase == 'probing':
                    self.controller.phase = (
                        'probe_complete' if self.status == 'passed' else 'probe_failed'
                    )
            while not self.commands.empty():
                _, _, future = self.commands.get_nowait()
                if not future.done():
                    future.set_exception(DesktopError('ownership_revoked', 'Probe ended'))

    def persist(self):
        try:
            if self.directory is not None:
                (self.directory / 'summary.json').write_text(
                    json.dumps(self.summary(), indent=2) + '\n'
                )
        except OSError:
            request_stop()
            self.status, self.code = 'failed', 'execution_failed'
            raise DesktopError('execution_failed', 'Probe evidence unavailable') from None

    def abort(self):
        self.cancelled.set()
        request_stop()
