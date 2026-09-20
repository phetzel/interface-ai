"""Ownership races use real flock files; HTTP tests never emit OS input."""

import json
import hashlib
from pathlib import Path
import tempfile
import threading
import time
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch
from urllib.request import Request, urlopen
from urllib.error import HTTPError

from interface_ai.desktop import Desktop, DesktopError
from interface_ai.desktop.ownership import Ownership
from interface_ai.handoff.server import Server, HOST, ORIGIN
from interface_ai.handoff.controller import Controller
from interface_ai.contracts.models import Failure, BusinessOutcome
from test_desktop import Backend


class OwnershipTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.session = dict(id='same-session', width=1280, height=800, windowId=9, mode='native')
        self.backend = Backend()
        self.owner = Ownership(self.root, self.session['id'])

    def desktop(self, **kwargs):
        return Desktop(
            session_reader=lambda: self.session,
            backend=self.backend,
            lock_path=self.root / 'input.lock',
            stop_path=self.root / 'STOP',
            **kwargs,
        )

    def test_revocation_interrupts_typing_and_old_epoch_stays_invalid_after_resume(self):
        events = []
        old = self.desktop(event_sink=events.append)
        self.backend.hook = lambda: self.owner.change('quiescing', expected=self.owner.read())
        with old:
            with self.assertRaisesRegex(DesktopError, 'ownership'):
                old.type_text('SECRET-SENTINEL-84729')
        self.assertEqual(self.backend.calls, [('type', 'S')])
        human = self.owner.change('human', expected=self.owner.read())
        self.owner.change('automation', expected=human)
        self.backend.hook = lambda: None
        with old:
            with self.assertRaises(DesktopError) as exc:
                old.click(1, 2)
            self.assertEqual(exc.exception.code, 'ownership_revoked')
        with self.desktop() as fresh:
            fresh.click(1, 2)
        self.assertNotIn('SECRET', json.dumps(events))

    def test_handoff_waits_for_inflight_input_and_modifier_cleanup(self):
        started, release = threading.Event(), threading.Event()

        def hook():
            started.set()
            self.assertTrue(release.wait(2))

        self.backend.hook = hook
        outcome = []

        def automate():
            with self.desktop() as desktop:
                try:
                    desktop.hotkey('ctrl', 'a')
                except DesktopError as exc:
                    outcome.append(exc.code)

        worker = threading.Thread(target=automate)
        worker.start()
        self.assertTrue(started.wait(2))
        result = []
        handoff = threading.Thread(
            target=lambda: result.append(
                self.owner.takeover(self.root / 'input.lock', expected=self.owner.read())
            )
        )
        handoff.start()
        deadline = time.monotonic() + 2
        while self.owner.read()['owner'] != 'quiescing' and time.monotonic() < deadline:
            time.sleep(0.01)
        self.assertEqual(self.owner.read()['owner'], 'quiescing')
        self.assertEqual(result, [])
        release.set()
        worker.join(2)
        handoff.join(2)
        self.assertFalse(worker.is_alive() or handoff.is_alive())
        self.assertEqual(outcome, ['ownership_revoked'])
        self.assertEqual(self.backend.calls, [('down', 'ctrl'), ('up', 'ctrl')])
        self.assertEqual(result[0]['owner'], 'human')

    def test_timeout_never_grants_human_input(self):
        with self.desktop():
            with self.assertRaises(DesktopError) as exc:
                self.owner.takeover(
                    self.root / 'input.lock', expected=self.owner.read(), timeout=0.03
                )
        self.assertEqual(exc.exception.code, 'quiesce_timeout')
        self.assertEqual(self.owner.read()['owner'], 'quiescing')

    def test_automation_cannot_input_while_human_owns_same_session(self):
        self.owner.takeover(self.root / 'input.lock', expected=self.owner.read())
        with self.desktop() as desktop:
            with self.assertRaises(DesktopError):
                desktop.click(1, 1)
        with self.desktop(role='human') as desktop:
            desktop.click(2, 2)
        self.assertEqual(self.backend.calls, [('click', 2, 2)])

    def test_delayed_human_request_rejected_after_resume(self):
        human = self.owner.takeover(self.root / 'input.lock', expected=self.owner.read())
        delayed = self.desktop(role='human', epoch=human['epoch'])
        self.owner.change('automation', expected=human)
        with delayed:
            with self.assertRaises(DesktopError):
                delayed.type_text('secret')
        self.assertEqual(self.backend.calls, [])

    def test_compare_and_swap_and_reset_bind_ownership(self):
        old = self.owner.read()
        self.owner.change('quiescing', expected=old)
        with self.assertRaises(DesktopError):
            self.owner.change('human', expected=old)
        with self.assertRaises(DesktopError):
            Ownership(self.root, 'new-session').read()


class OperatorHTTPTests(unittest.TestCase):
    def setUp(self):
        self.controller = Mock()
        self.controller.mutex = threading.RLock()
        self.controller.snapshot.return_value = {'phase': 'human'}
        self.server = Server(('127.0.0.1', 0), self.controller)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.url = 'http://127.0.0.1:' + str(self.server.server_port)

    def request(self, path, *, body=None, headers=None):
        base = {
            'Host': HOST,
            'X-Operator-Token': self.server.token,
            'Origin': ORIGIN,
            'Content-Type': 'application/json',
        }
        base.update(headers or {})
        request = Request(self.url + path, data=body, headers=base)
        try:
            response = urlopen(request, timeout=3)
        except HTTPError as exc:
            response = exc
        with response:
            return response.status, response.read(), response.headers

    def test_cross_origin_host_and_token_rejected_before_controller(self):
        body = b'{"lease":{"session":"test","epoch":0}}'
        for headers in [
            {'Host': 'evil.example'},
            {'Origin': 'https://evil.example'},
            {'X-Operator-Token': 'wrong'},
            {'Sec-Fetch-Site': 'cross-site'},
            {'Content-Type': 'text/plain'},
        ]:
            self.assertEqual(self.request('/takeover', body=body, headers=headers)[0], 403)
        self.controller.takeover.assert_not_called()

    def test_unknown_fields_duplicate_keys_and_payload_bound(self):
        for body in [b'{"lease":{},"secret":"never-log"}', b'{"lease":{},"lease":{}}', b'x' * 4097]:
            status, data, _ = self.request('/takeover', body=body)
            self.assertEqual(status, 400)
            self.assertNotIn(b'never-log', data)
        self.controller.takeover.assert_not_called()

    def test_valid_request_and_no_cache_headers(self):
        status, _, headers = self.request('/takeover', body=b'{"lease":{"session":"a","epoch":1}}')
        self.assertEqual(status, 200)
        self.controller.takeover.assert_called_once_with({'session': 'a', 'epoch': 1})
        self.assertEqual(headers['Cache-Control'], 'no-store')
        self.assertIn("frame-ancestors 'none'", headers['Content-Security-Policy'])

    def test_frames_and_status_require_operator_token(self):
        for path in ['/status', '/frame']:
            self.assertEqual(self.request(path, headers={'X-Operator-Token': ''})[0], 403)


class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.session = dict(id='session', mode='bank', width=1280, height=800, windowId=9)
        for name, value in [
            ('RUNTIME', self.root),
            ('STOP', self.root / 'STOP'),
            ('LOCK', self.root / 'input.lock'),
            ('read_session', lambda: self.session),
            ('request_stop', lambda: (self.root / 'STOP').touch()),
        ]:
            patcher = patch('interface_ai.handoff.controller.' + name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.controller = Controller(output_root=self.root)
        self.controller.launch = Mock()
        self.lease = {'session': 'session', 'epoch': 0}
        self.controller.start('00123', self.lease)
        self.controller.phase = 'awaiting_human'
        self.controller.resume_at = 4

    def human(self):
        self.controller.takeover(self.lease)
        state = self.controller.snapshot()
        return {key: state[key] for key in ('session', 'epoch')}

    def terminal(self, phase, code=None):
        directory = self.controller.directory
        summary = json.loads((directory / 'summary.json').read_text())
        encoded = (directory / 'result.json').read_bytes()
        result = json.loads(encoded)
        self.assertEqual(summary['status'], phase)
        self.assertEqual(summary['reason'], code)
        self.assertEqual(summary['resultSha256'], hashlib.sha256(encoded).hexdigest())
        self.assertEqual(summary['auditEvents'], len(self.controller.audit))
        self.assertEqual(summary['sessionId'], self.session['id'])
        self.assertEqual(summary['resultStatus'], result['status'])
        return summary

    def test_stop_finalizes_once_and_late_worker_cannot_replace_it(self):
        self.controller.phase = 'running'
        self.controller.current_step = 'search-member'
        self.controller.last_checkpoint = 'input-entered'
        begun, release = threading.Event(), threading.Event()

        def late_result(**kwargs):
            begun.set()
            self.assertTrue(release.wait(2))
            self.controller.record('automation', status='completed')
            return BusinessOutcome(outcome='member_not_found')

        with (
            patch('interface_ai.handoff.controller.Desktop'),
            patch('interface_ai.handoff.controller.Interpreter') as runner,
        ):
            runner.return_value.run.side_effect = late_result
            worker = threading.Thread(target=self.controller.run, args=(0, 0))
            worker.start()
            self.assertTrue(begun.wait(2))
            self.controller.stop()
            epoch = self.controller.ownership.read()['epoch']
            self.controller.stop()
            release.set()
            worker.join(2)
            self.assertFalse(worker.is_alive())
        summary = self.terminal('stopped', 'stopped')
        self.assertEqual(summary['step'], 'search-member')
        self.assertEqual(summary['lastCheckpoint'], 'input-entered')
        self.assertEqual(summary['automationActions'], 1)
        self.assertEqual(self.controller.ownership.read()['epoch'], epoch)
        self.assertEqual(sum(e.get('status') == 'stopped' for e in self.controller.audit), 1)

    def test_worker_exception_and_terminal_storage_failure_fail_closed(self):
        self.controller.phase = 'running'
        with patch('interface_ai.handoff.controller.Desktop', side_effect=RuntimeError('SECRET')):
            self.controller.run(0, 0)
        self.terminal('stopped', 'execution_failed')
        self.assertNotIn('SECRET', (self.controller.directory / 'summary.json').read_text())
        # Separate run: a full disk cannot restore ownership or recurse logging.
        self.controller.result = None
        self.controller.phase = 'running'
        with patch('interface_ai.handoff.controller.write_terminal', side_effect=OSError('SECRET')):
            self.controller.finalize(BusinessOutcome(outcome='member_not_found'))
        self.assertTrue((self.root / 'STOP').exists())
        self.assertEqual(self.controller.snapshot()['evidenceStatus'], 'failed')
        self.assertEqual(self.controller.ownership.read()['owner'], 'stopped')
        self.assertIsNone(self.controller.resume_at)

    def test_successful_business_outcome_is_not_rewritten_by_later_stop(self):
        self.controller.finalize(BusinessOutcome(outcome='member_not_found'))
        self.terminal('business_outcome')
        self.controller.stop()
        self.terminal('business_outcome')
        self.assertEqual(self.controller.phase, 'stopped')

    def test_http_member_validation_is_client_error_without_worker_or_input(self):
        self.controller.phase = 'idle'
        self.controller.launch.reset_mock()
        with Server(('127.0.0.1', 0), self.controller) as server:
            serving = threading.Thread(target=server.serve_forever, daemon=True)
            serving.start()
            try:
                headers = {
                    'Host': HOST,
                    'Origin': ORIGIN,
                    'X-Operator-Token': server.token,
                    'Content-Type': 'application/json',
                }
                cases = [
                    ({'lease': self.lease, 'memberId': value}, 400, 'invalid_input')
                    for value in ['123', 123, 'SECRET-SENTINEL']
                ]
                cases += [
                    (
                        {'lease': self.lease, 'memberId': '00123', 'extra': True},
                        400,
                        'invalid_action',
                    ),
                    (
                        {'lease': dict(self.lease, epoch=99), 'memberId': '00123'},
                        409,
                        'ownership_revoked',
                    ),
                ]
                for body, status, code in cases:
                    req = Request(
                        'http://127.0.0.1:' + str(server.server_port) + '/start',
                        data=json.dumps(body).encode(),
                        headers=headers,
                    )
                    with self.assertRaises(HTTPError) as error:
                        urlopen(req, timeout=2)
                    with error.exception as response:
                        self.assertEqual(response.status, status)
                        self.assertEqual(json.load(response), {'code': code})
            finally:
                server.shutdown()
                serving.join(2)
        self.controller.launch.assert_not_called()

    def test_premature_resume_never_launches_worker(self):
        with self.assertRaises(DesktopError):
            self.controller.resume(self.lease)
        self.controller.launch.assert_called_once_with(0)

    def test_detected_expiry_revokes_before_operator_requests_takeover(self):
        self.controller.phase = 'running'
        with (
            patch('interface_ai.handoff.controller.Desktop'),
            patch('interface_ai.handoff.controller.Interpreter') as runner,
        ):
            runner.return_value.run.return_value = Failure(
                code='intervention_required', step='search-member'
            )
            self.controller.run(0, 0)
        paused = self.controller.snapshot()
        self.assertEqual(
            (paused['phase'], paused['owner'], paused['epoch']), ('awaiting_human', 'quiescing', 1)
        )
        with self.assertRaises(DesktopError):
            self.controller.ownership.check('automation', 0)
        self.controller.takeover({'session': 'session', 'epoch': 1})
        self.assertEqual(self.controller.snapshot()['owner'], 'human')

    def test_external_cli_stop_is_reflected_and_revokes_panel_lease(self):
        lease = self.human()
        (self.root / 'STOP').touch()
        state = self.controller.snapshot()
        self.assertEqual((state['phase'], state['owner']), ('stopped', 'stopped'))
        with self.assertRaises(DesktopError):
            self.controller.verify(lease)

    def test_wrong_screen_or_identity_retains_human_then_valid_return_rotates_epoch(self):
        lease = self.human()
        with (
            patch('interface_ai.handoff.controller.Desktop'),
            patch('interface_ai.handoff.controller.Interpreter') as runner,
        ):
            runner.return_value.observe.return_value.checkpoint.return_value = False
            with self.assertRaises(DesktopError) as exc:
                self.controller.resume(lease)
            self.assertEqual(exc.exception.code, 'resume_rejected')
            self.assertEqual(self.controller.ownership.read()['owner'], 'human')
            self.controller.launch.assert_called_once_with(0)
            runner.return_value.observe.return_value.checkpoint.return_value = True
            self.controller.resume(lease)
        self.assertEqual(self.controller.ownership.read()['owner'], 'automation')
        self.controller.launch.assert_called_with(4)
        with self.assertRaises(DesktopError):
            self.controller.verify(lease)

    def test_duplicate_human_sequence_is_consumed_even_on_input_failure(self):
        lease = self.human()
        with patch('interface_ai.handoff.controller.Desktop') as desktop:
            desktop.return_value.__enter__.return_value.execute.side_effect = DesktopError(
                'input_failed', 'uncertain'
            )
            for _ in range(2):
                with self.assertRaises(DesktopError):
                    self.controller.human_action({'type': 'type', 'text': 'secret'}, lease, 0)
            desktop.return_value.__enter__.return_value.execute.assert_called_once()
        self.assertNotIn('secret', json.dumps(self.controller.audit))

    def test_expired_handoff_stops_without_browser_polling(self):
        lease = self.human()
        self.controller.human_deadline = time.monotonic() - 1
        self.controller.expire()
        self.assertEqual(self.controller.phase, 'stopped')
        self.assertEqual(self.controller.reason, 'handoff_expired')
        self.terminal('stopped', 'handoff_expired')
        self.assertTrue((self.root / 'STOP').exists())
        with self.assertRaises(DesktopError):
            self.controller.human_action({'type': 'click', 'x': 1, 'y': 2}, lease, 0)

    def test_arbitrary_interruption_has_no_resume_cursor(self):
        self.controller.phase = 'running'
        lease = self.human()
        self.assertIsNone(self.controller.resume_at)
        with self.assertRaises(DesktopError):
            self.controller.resume(lease)

    def http_input_stop(self, action, expected_calls, *, poll_count=0):
        """Real HTTP/controller/adapter; only the OS backend is simulated."""
        lease = self.human()
        begun, release, maintenance, stopped = (threading.Event() for _ in range(4))
        backend = Backend()

        def slow_input():
            begun.set()
            if not release.wait(4):
                raise RuntimeError('Test input was not released')

        backend.hook = slow_input

        def desktop(session, **kwargs):
            return Desktop(
                session,
                backend=backend,
                session_reader=lambda: dict(self.session, mode='native'),
                stop_path=self.root / 'STOP',
                lock_path=self.root / 'input.lock',
                **kwargs,
            )

        class ObservedServer(Server):
            def service_actions(inner):
                if begun.is_set():
                    maintenance.set()
                super().service_actions()

        def signal_stop():
            (self.root / 'STOP').touch()
            stopped.set()

        with ObservedServer(('127.0.0.1', 0), self.controller) as server:
            results, errors, workers = {}, [], []

            def request(label, path, body=None):
                headers = {
                    'Host': HOST,
                    'Origin': ORIGIN,
                    'X-Operator-Token': server.token,
                    'Content-Type': 'application/json',
                }
                req = Request(
                    'http://127.0.0.1:' + str(server.server_port) + path,
                    data=json.dumps(body).encode() if body is not None else None,
                    headers=headers,
                )
                try:
                    try:
                        response = urlopen(req, timeout=5)
                    except HTTPError as exc:
                        response = exc
                    with response:
                        results[label] = (response.status, json.load(response))
                except Exception as exc:
                    errors.append(exc)

            def spawn(label, path, body=None):
                worker = threading.Thread(target=request, args=(label, path, body), daemon=True)
                workers.append(worker)
                worker.start()

            serving = threading.Thread(
                target=server.serve_forever, kwargs={'poll_interval': 0.01}, daemon=True
            )
            with (
                patch('interface_ai.handoff.controller.Desktop', desktop),
                patch('interface_ai.handoff.server.request_stop', signal_stop),
            ):
                serving.start()
                try:
                    spawn('action', '/action', {'lease': lease, 'sequence': 0, 'action': action})
                    self.assertTrue(begun.wait(2))
                    self.assertTrue(maintenance.wait(2))
                    # Polls return promptly instead of holding all request slots.
                    for i in range(poll_count):
                        spawn('poll' + str(i), '/status')
                        workers[-1].join(1)
                        self.assertFalse(workers[-1].is_alive(), 'Status waited behind input')
                        self.assertEqual(results['poll' + str(i)], (503, {'code': 'busy'}))
                    spawn('stop', '/stop', {'lease': lease})
                    self.assertTrue(
                        stopped.wait(1), 'HTTP Stop was not signaled while input held mutex'
                    )
                    self.assertFalse(release.is_set())
                finally:
                    release.set()
                    for worker in workers:
                        worker.join(5)
                    server.shutdown()
                    serving.join(2)
            self.assertEqual(errors, [])
            self.assertFalse(any(worker.is_alive() for worker in workers))
            self.assertEqual(results['action'], (409, {'code': 'stopped'}))
            self.assertEqual(results['stop'][0], 200)
            self.assertEqual(results['stop'][1]['phase'], 'stopped')
        self.assertEqual(backend.calls, expected_calls)
        self.terminal('stopped', 'stopped')
        self.assertEqual(self.controller.snapshot()['owner'], 'stopped')
        with self.assertRaises(DesktopError):
            self.controller.human_action({'type': 'click', 'x': 1, 'y': 1}, lease, 1)
        with self.assertRaises(DesktopError):
            self.controller.resume(lease)
        self.assertEqual(backend.calls, expected_calls)

    def test_http_stop_interrupts_typing_despite_status_polling(self):
        self.http_input_stop(
            {'type': 'type', 'text': 'SECRET-SENTINEL-84729'}, [('type', 'S')], poll_count=12
        )
        self.assertNotIn('SECRET', json.dumps(self.controller.audit))

    def test_http_stop_interrupts_hotkey_and_releases_modifier(self):
        self.http_input_stop(
            {'type': 'hotkey', 'keys': ['ctrl', 'a']}, [('down', 'ctrl'), ('up', 'ctrl')]
        )

    def test_http_maintenance_retries_expiry_after_busy_input_without_polling(self):
        self.human()
        self.controller.human_deadline = time.monotonic() - 1
        maintenance = threading.Event()

        class ObservedServer(Server):
            def service_actions(inner):
                super().service_actions()
                maintenance.set()

        with ObservedServer(('127.0.0.1', 0), self.controller) as server:
            serving = threading.Thread(
                target=server.serve_forever, kwargs={'poll_interval': 0.01}, daemon=True
            )
            try:
                with self.controller.mutex:
                    serving.start()
                    self.assertTrue(maintenance.wait(1), 'Accepting loop blocked on maintenance')
                    self.assertFalse((self.root / 'STOP').exists())
                deadline = time.monotonic() + 2
                while not (self.root / 'STOP').exists() and time.monotonic() < deadline:
                    time.sleep(0.01)
                self.assertTrue((self.root / 'STOP').exists())
            finally:
                server.shutdown()
                serving.join(2)
        self.assertEqual(self.controller.phase, 'stopped')
        self.assertEqual(self.controller.reason, 'handoff_expired')
        self.terminal('stopped', 'handoff_expired')

    def test_handoff_retains_sanitized_interpreter_failure_context(self):
        self.controller.phase = 'running'
        events = [
            {'kind': 'step', 'step': 'open-savings', 'action': 'click', 'status': 'started'},
            {
                'kind': 'checkpoint',
                'step': 'open-savings',
                'checkpoint': 'member-ready',
                'status': 'satisfied',
            },
            {'kind': 'reading', 'step': 'open-savings', 'field': 'member-id', 'confidence': 98},
            {
                'kind': 'target',
                'step': 'open-savings',
                'target': 'savings-label',
                'status': 'rejected',
                'code': 'ambiguous_target',
                'candidateCount': 2,
            },
            {
                'kind': 'step',
                'step': 'open-savings',
                'action': 'click',
                'status': 'failed',
                'code': 'ambiguous_target',
            },
        ]

        def interpreter(*args, event_sink, **kwargs):
            def run(**kwargs):
                for event in events:
                    event_sink(event)
                return Failure(code='ambiguous_target', step='open-savings')

            return SimpleNamespace(run=run)

        with (
            patch('interface_ai.handoff.controller.Desktop'),
            patch('interface_ai.handoff.controller.Interpreter', interpreter),
        ):
            self.controller.run(0, 0)
        state = self.controller.snapshot()
        self.assertEqual(
            (state['step'], state['reason'], state['lastCheckpoint']),
            ('open-savings', 'ambiguous_target', 'member-ready'),
        )
        retained = [
            json.loads(line)
            for line in (self.controller.directory / 'audit.jsonl').read_text().splitlines()
        ]
        self.assertEqual([e['event'] for e in retained if e['kind'] == 'interpreter'], events)
        summary = json.loads((self.controller.directory / 'summary.json').read_text())
        self.assertEqual(summary['automationActions'], 0)
        self.assertEqual(summary['humanActions'], 0)

    def test_handoff_diagnostics_reject_unreviewed_identifiers_and_business_values(self):
        before = list(self.controller.audit)
        for event in [
            {'kind': 'reading', 'field': 'member-id', 'text': 'SECRET-SENTINEL-84729'},
            {'kind': 'step', 'step': 'SECRET-SENTINEL-84729', 'status': 'failed'},
            {'kind': 'reading', 'field': 'member-id', 'confidence': float('nan')},
        ]:
            with self.assertRaises(DesktopError) as exc:
                self.controller.interpreter_event(event)
            self.assertEqual(exc.exception.code, 'evidence_rejected')
        self.assertEqual(self.controller.audit, before)
        self.assertIsNone(self.controller.snapshot()['step'])

    def test_cli_and_panel_compete_for_one_coordinator_run(self):
        from interface_ai.discovery.http import run_request
        from interface_ai.policy.bank import REVIEWED_PATH

        self.controller.phase = 'idle'
        self.controller.launch = Mock(
            side_effect=lambda _: setattr(self.controller, 'phase', 'running')
        )
        barrier = threading.Barrier(2)
        outcomes = []

        def start(cli):
            barrier.wait(timeout=2)
            try:
                if cli:
                    run_request(
                        self.controller,
                        '/run/start',
                        dict(session='session', memberId='00123', capability=str(REVIEWED_PATH)),
                    )
                else:
                    self.controller.start('00123', self.lease)
                outcomes.append('started')
            except DesktopError as exc:
                outcomes.append(exc.code)

        workers = [threading.Thread(target=start, args=(cli,)) for cli in (True, False)]
        for worker in workers:
            worker.start()
        for worker in workers:
            worker.join(3)
        self.assertCountEqual(outcomes, ['started', 'invalid_transition'])
        self.assertEqual(self.controller.launch.call_count, 1)

    def test_non_expiry_failure_offers_human_control_without_resume(self):
        self.controller.phase = 'running'
        with (
            patch('interface_ai.handoff.controller.Desktop'),
            patch('interface_ai.handoff.controller.Interpreter') as runner,
        ):
            runner.return_value.run.return_value = Failure(
                code='ambiguous_target', step='open-savings'
            )
            self.controller.run(0, 0)
        state = self.controller.snapshot()
        self.assertEqual((state['phase'], state['owner']), ('awaiting_human', 'quiescing'))
        self.assertFalse(state['resumable'])
        self.assertEqual(state['result']['code'], 'ambiguous_target')
        self.controller.takeover({'session': 'session', 'epoch': state['epoch']})
        state = self.controller.snapshot()
        with self.assertRaises(DesktopError):
            self.controller.resume({'session': 'session', 'epoch': state['epoch']})


if __name__ == '__main__':
    unittest.main()
