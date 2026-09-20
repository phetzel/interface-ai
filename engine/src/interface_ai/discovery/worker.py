"""One bounded discovery reservation behind the shared session coordinator."""

import base64
import hashlib
from concurrent.futures import Future, TimeoutError as FutureTimeout
from datetime import datetime, timezone
from io import BytesIO
import json
from queue import Empty
import re
import threading
import time

from interface_ai.contracts.models import Failure
from interface_ai.desktop import Desktop, DesktopError
from interface_ai.policy.evidence import checked_event, safe_code
from interface_ai.replay.loader import validate_inputs
from interface_ai.handoff.evidence import atomic_write
from .probe import Probe
from .policy import DiscoveryPolicy
from .actions import normalize


class Discovery(Probe):
    def __init__(self, controller, *, desktop_factory=Desktop, policy_factory=DiscoveryPolicy):
        super().__init__(controller, desktop_factory=desktop_factory, policy_factory=policy_factory)
        self.inputs = None
        self.trace = []
        self.responses = []
        self.proposals = []
        self.last_progress = None
        self.stuck = 0
        self.result = None
        self.policy = None
        self.observation_refs = []

    def start(self, session, member_id):
        c = self.controller
        with c.mutex:
            if (
                self.worker is not None
                or c.phase != 'idle'
                or c.session['mode'] != 'bank'
                or session != c.session['id']
            ):
                raise DesktopError('invalid_transition', 'Discovery requires a fresh bank session')
            self.inputs = validate_inputs({'memberId': member_id})
            state = c.ownership.read()
            c.ownership.check('automation', state['epoch'])
            self.epoch = state['epoch']
            self.started = c.started = time.monotonic()
            name = (
                datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
                + '-discovery-'
                + self.run_id[:8]
            )
            self.directory = c.output_root / name
            self.directory.mkdir(mode=0o700)
            c.directory = self.directory
            c.inputs = self.inputs
            c.external = self
            c.run_kind = 'discovery'
            c.phase = self.status = 'running'
            c.resume_at = None
            self.persist()
            initial = Future()
            self.worker = c.worker = threading.Thread(target=self.run, args=(initial,), daemon=True)
            self.worker.start()
        return self.wait(initial)

    def wait(self, future):
        try:
            return future.result(timeout=30)
        except FutureTimeout:
            self.abort()
            raise DesktopError(
                'deadline', 'Uncertain discovery transport; inspect the operator'
            ) from None

    def summary(self):
        return dict(
            format='discovery-desktop-v1',
            provenance='guarded-goal-discovery',
            runId=self.run_id,
            sessionId=self.controller.session['id'],
            epoch=self.epoch,
            status=self.status,
            code=self.code,
            actionsCompleted=self.actions,
            proposals=self.sequence,
            observations=self.observations,
            modelCalls=None,
            elapsedMs=round((time.monotonic() - self.started) * 1000),
            limits={'requests': 20, 'actions': 40, 'seconds': 120},
            screenshots='memory-only',
            responses=self.responses,
        )

    def persist(self):
        if self.directory is None:
            return
        try:
            atomic_write(
                self.directory / 'summary.json',
                (json.dumps(self.summary(), indent=2) + '\n').encode(),
            )
            atomic_write(
                self.directory / 'trajectory.json',
                (json.dumps(self.trace, indent=2) + '\n').encode(),
            )
            atomic_write(
                self.directory / 'proposals.json',
                (json.dumps(self.proposals, indent=2) + '\n').encode(),
            )
            atomic_write(
                self.directory / 'observations.json',
                (json.dumps(self.observation_refs, indent=2) + '\n').encode(),
            )
            result = self.controller.result or self.result
            if result is not None:
                atomic_write(
                    self.directory / 'result.json',
                    (result.model_dump_json(indent=2) + '\n').encode(),
                )
        except OSError:
            self.cancelled.set()
            from interface_ai.desktop.session import request_stop

            request_stop()
            raise DesktopError('execution_failed', 'Discovery evidence unavailable') from None

    def record(self, event):
        event = checked_event(event)
        with self.controller.mutex:
            self.controller.record('automation', **event)

    def observe(self, desktop):
        view, state, result = self.policy.view(desktop)
        if len(self.observation_refs) >= 512:
            raise DesktopError('discovery_budget', 'Observation limit reached')
        ref = dict(
            id=f'observation-{len(self.observation_refs) + 1:03d}',
            checkpoint=state,
            sha256=hashlib.sha256(view.image.tobytes()).hexdigest(),
        )
        view.reference = ref['id']
        self.observation_refs.append(ref)
        return view, state, result

    def frame(self, desktop, *, view=None):
        view, state, result = view or self.observe(desktop)
        self.observations += 1
        self.controller.last_checkpoint = state
        desktop.checkpoint()
        if result is not None:
            self.result = result
            return {
                'lease': self.lease(),
                'directory': self.directory.name,
                'actionsCompleted': self.actions,
                'result': result.model_dump(),
            }
        output = BytesIO()
        view.image.save(output, format='PNG')
        raw = output.getvalue()
        if len(raw) > 4 * 1024 * 1024:
            raise DesktopError('policy_capture_denied', 'Observation too large')
        desktop.checkpoint()
        return dict(
            lease=self.lease(),
            directory=self.directory.name,
            width=1280,
            height=800,
            png=base64.b64encode(raw).decode(),
            actionsCompleted=self.actions,
        )

    def check_lease(self, data):
        lease = data.get('lease')
        if (
            not isinstance(lease, dict)
            or lease != self.lease()
            or any(type(lease.get(k)) is not int for k in ('epoch', 'sequence'))
        ):
            raise DesktopError('ownership_revoked', 'Observation is stale or already consumed')

    def propose(self, desktop, data):
        if set(data) != {'lease', 'actions', 'callId', 'responseId'} or any(
            not isinstance(data[k], str) or not re.fullmatch('[A-Za-z0-9_.:-]{1,128}', data[k])
            for k in ('callId', 'responseId')
        ):
            raise DesktopError('invalid_action', 'Invalid provider metadata')
        if self.sequence >= 20 or self.actions >= 40:
            raise DesktopError('discovery_budget', 'Discovery limit reached')
        self.sequence += 1  # Consume before validation/dispatch: no uncertain retry.
        raw = data['actions']
        if not isinstance(raw, list) or not 1 <= len(raw) <= 4:
            raise DesktopError('invalid_action', 'Batch must contain one to four actions')
        actions = [normalize(a, self.inputs.memberId) for a in raw]
        if self.actions + sum(a is not None for a in actions) > 40:
            raise DesktopError('discovery_budget', 'Action budget exhausted')
        if data['responseId'] in self.responses:
            raise DesktopError('invalid_action', 'Duplicate response')
        self.responses.append(data['responseId'])
        proposal = dict(
            sequence=self.sequence,
            responseId=data['responseId'],
            callId=data['callId'],
            items=[
                dict(index=i, action=a['type'] if a else raw[i]['type'], status='not_dispatched')
                for i, a in enumerate(actions)
            ],
        )
        self.proposals.append(proposal)
        self.persist()
        for index, action in enumerate(actions):
            desktop.checkpoint()
            if self.cancelled.is_set():
                raise DesktopError('stopped', 'Discovery cancelled')
            before, state, result = self.observe(desktop)
            if action is None:
                if raw[index]['type'] == 'wait':
                    for _ in range(4):
                        desktop.checkpoint()
                        time.sleep(0.05)
                proposal['items'][index]['status'] = 'observed'
                self.persist()
                continue
            if result is not None:
                proposal['items'][index]['status'] = 'rejected'
                raise DesktopError('invalid_action', 'Input after completion rejected')
            # Record intent first. Only an adapter completion becomes a recorded
            # executed action. Raw typed values/key names never enter this trace.
            entry = dict(
                id=f'action-{self.actions + 1:03d}',
                proposal=self.sequence,
                callId=data['callId'],
                responseId=data['responseId'],
                actionIndex=index,
                epoch=self.epoch,
                sessionId=self.controller.session['id'],
                action=action['type'],
                before=state,
                beforeObservation=before.reference,
                status='started',
            )
            self.trace.append(entry)
            self.persist()
            try:
                desktop.execute(action)
            except DesktopError as exc:
                entry.update(status='uncertain', code=safe_code(exc.code))
                proposal['items'][index]['status'] = 'uncertain'
                self.persist()
                raise
            self.actions += 1
            entry['status'] = 'dispatched'
            if action['type'] == 'click':
                entry.update(target=self.policy.last_target, point=[action['x'], action['y']])
            if action['type'] == 'type':
                entry['inputBinding'] = 'memberId'
            self.persist()
            # Reobserve after every primitive, including within a provider batch.
            # Waiting for a submitted search/account transition is a local effect
            # check, not a script choosing the next action.
            transition = action['type'] in ('press', 'type') or entry.get('target') in (
                'search-button',
                'savings-button',
            )
            deadline = time.monotonic() + 4
            while True:
                try:
                    after, after_state, result = self.observe(desktop)
                except DesktopError as exc:
                    if exc.code != 'policy_capture_denied' or time.monotonic() >= deadline:
                        raise
                    time.sleep(0.05)
                    continue
                if not transition or after_state != state:
                    break
                if time.monotonic() >= deadline:
                    raise DesktopError('checkpoint_timeout', 'Expected a visible action effect')
                time.sleep(0.05)
            desktop.checkpoint()
            entry.update(after=after_state, afterObservation=after.reference, status='completed')
            proposal['items'][index]['status'] = 'completed'
            self.persist()
        observed = self.observe(desktop)
        signature = (observed[1], self.policy.keyboard)
        self.stuck = self.stuck + 1 if signature == self.last_progress else 0
        self.last_progress = signature
        if self.stuck >= 3:
            raise DesktopError('discovery_stuck', 'Repeated observations made no progress')
        return self.frame(desktop, view=observed)

    def run(self, initial):
        pending = initial
        try:
            self.policy = self.policy_factory(self.inputs)
            with self.desktop_factory(
                self.controller.session['id'],
                epoch=self.epoch,
                timeout=120,
                event_sink=self.record,
                bank_policy_factory=lambda: self.policy,
            ) as desktop:
                view = self.observe(desktop)
                if view[1] != 'search-ready':
                    raise DesktopError('policy_capture_denied', 'Start on the fresh member search')
                initial.set_result(self.frame(desktop, view=view))
                pending = None
                while self.result is None:
                    desktop.checkpoint()
                    if self.cancelled.is_set():
                        raise DesktopError('stopped', 'Discovery cancelled')
                    try:
                        operation, data, pending = self.commands.get(timeout=0.05)
                    except Empty:
                        continue
                    desktop.checkpoint()
                    self.check_lease(data)
                    if operation == 'check' and set(data) == {'lease'}:
                        result = {'lease': self.lease()}
                    elif operation == 'propose':
                        result = self.propose(desktop, data)
                    else:
                        raise DesktopError('invalid_action', 'Unsupported discovery operation')
                    desktop.checkpoint()
                    if self.result is not None:
                        break
                    pending.set_result(result)
                    pending = None
            with self.controller.mutex:
                if self.controller.phase == 'running':
                    self.status = 'passed' if self.result.status == 'success' else 'failed'
                    self.controller.finalize(self.result)
                else:
                    raise DesktopError('ownership_revoked', 'Discovery lost ownership')
            self.persist()
            pending.set_result(result)
            pending = None
        except Exception as exc:
            self.code = safe_code(getattr(exc, 'code', 'execution_failed'))
            self.status = 'failed'
            self.result = Failure(code=self.code)
            with self.controller.mutex:
                c = self.controller
                if c.phase == 'running':
                    if self.code in ('stopped', 'stale_session', 'ownership_revoked'):
                        c.stop(self.code)
                    else:
                        state = c.ownership.read()
                        c.ownership.change('quiescing', expected=state)
                        c.interruption = self.result
                        c.phase, c.reason = 'awaiting_human', self.code
                        c.record('lifecycle', status='awaiting_human', code=self.code)
                try:
                    self.persist()
                except DesktopError:
                    c.evidence_failure()
            if pending is not None and not pending.done():
                pending.set_exception(
                    DesktopError(self.code, 'Discovery failed; inspect the operator')
                )
        finally:
            while not self.commands.empty():
                _, _, future = self.commands.get_nowait()
                if not future.done():
                    future.set_exception(DesktopError('ownership_revoked', 'Discovery ended'))

    def abort(self):
        self.cancelled.set()
        # A provider callback must never seize or stop a human's new ownership.
        with self.controller.mutex:
            if self.controller.external is self and self.controller.phase == 'running':
                self.controller.stop()
