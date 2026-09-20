"""Provider-free transport tests: real ownership files/adapter guards, fake OS input."""

import json
from pathlib import Path
import tempfile
import threading
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from PIL import Image

from interface_ai.desktop import Desktop, DesktopError
from interface_ai.desktop.ownership import Ownership
from interface_ai.discovery.probe import Probe, SearchPolicy, click, provision, credentials
from interface_ai.handoff.server import Server, HOST, ORIGIN
from test_desktop import Backend

ACTION = {'type': 'click', 'button': 'left', 'x': 100, 'y': 200}


class Policy:
    def observe(self, desktop):
        desktop.checkpoint()
        return desktop.screenshot(), None

    def authorize(self, action, desktop):
        desktop.checkpoint()
        if action['x'] != 100 or action['y'] != 200:
            raise DesktopError('policy_operation_denied', 'Not the allowed field')

    def clear(self):
        pass

    def completed(self):
        pass


class ProbeTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.stop = self.root / 'STOP'
        self.clock = time.monotonic
        self.session = dict(id='session-a', mode='bank', width=1280, height=800, windowId=9)
        self.backend = Backend()
        self.backend.screenshot = lambda: Image.new('RGB', (1280, 800))
        self.backend.application_matches = lambda _: True
        self.controller = SimpleNamespace(
            session=self.session,
            ownership=Ownership(self.root, self.session['id']),
            mutex=threading.RLock(),
            phase='idle',
            output_root=self.root,
        )
        self.controller.expire = lambda: None
        self.controller.snapshot = lambda: dict(
            self.controller.ownership.read(),
            phase=self.controller.phase,
            modelCalls=0,
        )
        self.controller.verify = lambda lease: self.assertEqual(
            lease, dict(session=self.session['id'], epoch=self.controller.ownership.read()['epoch'])
        )
        self.controller.stop = self.stop_controller
        self.probe = Probe(self.controller, desktop_factory=self.desktop, policy_factory=Policy)
        for target in (
            'interface_ai.discovery.probe.request_stop',
            'interface_ai.handoff.server.request_stop',
        ):
            patcher = patch(target, self.stop.touch)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.addCleanup(self.close_probe)

    def desktop(self, session_id=None, **kwargs):
        return Desktop(
            session_id,
            backend=self.backend,
            session_reader=lambda: dict(self.session),
            stop_path=self.stop,
            lock_path=self.root / 'input.lock',
            clock=self.clock,
            **kwargs,
        )

    def stop_controller(self):
        self.stop.touch()
        self.controller.ownership.change('stopped', expected=self.controller.ownership.read())
        self.controller.phase = 'stopped'

    def close_probe(self):
        self.probe.abort()
        if self.probe.worker:
            self.probe.worker.join(2)
            self.assertFalse(self.probe.worker.is_alive())

    def start(self):
        return self.probe.start(self.session['id'])['lease']

    def send(self, lease, action=ACTION):
        return self.probe.request('action', {'lease': lease, 'action': action})

    def test_one_click_round_trip_holds_lock_and_saves_only_metadata(self):
        lease = self.start()
        with self.assertRaises(DesktopError) as error:
            self.desktop().__enter__()
        self.assertEqual(error.exception.code, 'busy')
        frame = self.send(lease)
        self.assertEqual(frame['lease']['sequence'], 1)
        result = self.probe.request('finish', {'lease': frame['lease']})
        self.probe.worker.join(2)
        self.assertEqual(result['status'], 'passed')
        self.assertEqual(self.backend.calls, [('click', 100, 200)])
        self.assertEqual(self.controller.phase, 'probe_complete')
        summary = json.loads((self.probe.directory / 'summary.json').read_text())
        self.assertEqual(summary['actionsCompleted'], 1)
        self.assertIsNone(summary['modelCalls'])
        self.assertEqual(
            {p.name for p in self.probe.directory.iterdir()}, {'summary.json', 'events.jsonl'}
        )

    def test_stop_while_provider_waits_rejects_late_click(self):
        lease = self.start()
        self.stop_controller()
        with self.assertRaises(DesktopError):
            self.send(lease)
        self.probe.worker.join(2)
        self.assertEqual(self.backend.calls, [])
        self.assertEqual(self.controller.phase, 'stopped')

    def test_epoch_revocation_prevents_late_click_and_observation(self):
        lease = self.start()
        self.controller.ownership.change('quiescing', expected=self.controller.ownership.read())
        with self.assertRaises(DesktopError):
            self.send(lease)
        self.probe.worker.join(2)
        self.assertEqual(self.backend.calls, [])
        self.assertEqual(self.probe.observations, 1)

    def test_consumed_proposal_cannot_dispatch_twice(self):
        lease = self.start()
        self.send(lease)
        with self.assertRaises(DesktopError):
            self.send(lease)
        self.assertEqual(len(self.backend.calls), 1)

    def test_new_lease_still_cannot_request_a_second_click(self):
        frame = self.send(self.start())
        with self.assertRaises(DesktopError):
            self.send(frame['lease'])
        self.assertEqual(len(self.backend.calls), 1)

    def test_current_screen_policy_denies_unrelated_control(self):
        with self.assertRaises(DesktopError) as error:
            self.send(self.start(), dict(ACTION, x=900))
        self.assertEqual(error.exception.code, 'policy_operation_denied')
        self.assertEqual(self.backend.calls, [])

    def test_malformed_action_and_fake_human_role_never_dispatch(self):
        for action in [
            None,
            [],
            dict(ACTION, role='human'),
            dict(ACTION, x=True),
            dict(ACTION, button='right'),
            {'type': 'type', 'text': 'SECRET'},
        ]:
            with self.subTest(action=action), self.assertRaises(DesktopError):
                click(action)

    def test_focus_loss_before_first_observation_sends_no_frame(self):
        self.backend.window = 99
        with self.assertRaises(DesktopError) as error:
            self.start()
        self.assertEqual(error.exception.code, 'unexpected_focus')
        self.assertEqual(self.probe.observations, 0)

    def test_session_reset_between_model_request_and_action(self):
        lease = self.start()
        self.session['id'] = 'session-b'
        with self.assertRaises(DesktopError):
            self.send(lease)
        self.assertEqual(self.backend.calls, [])

    def test_abandoned_provider_releases_input_at_total_deadline(self):
        now = [0]
        self.clock = lambda: now[0]
        self.start()
        now[0] = 101
        self.probe.worker.join(2)
        self.assertFalse(self.probe.worker.is_alive())
        self.assertEqual(self.probe.code, 'deadline')
        self.assertEqual(self.backend.calls, [])

    def test_real_visual_policy_accepts_field_center_and_checks_new_screen(self):
        policy = SearchPolicy()
        screen = Image.new('RGB', (1280, 800), 'white')
        screen.paste(policy.bundle.templates['search-heading'], (100, 230))
        screen.paste(policy.bundle.templates['member-field'], (126, 415))
        self.backend.screenshot = lambda: screen
        self.probe.policy_factory = lambda: policy
        frame = self.send(self.start(), dict(ACTION, x=400, y=490))
        self.probe.request('finish', {'lease': frame['lease']})
        self.assertEqual(self.backend.calls, [('click', 400, 490)])
        # A visible label is required again at dispatch, not just in the earlier frame.
        screen.paste('white', (0, 0, 1280, 800))
        with self.desktop(bank_policy_factory=lambda: policy) as desktop:
            with self.assertRaises(DesktopError):
                desktop.click(400, 490)
        self.assertEqual(len(self.backend.calls), 1)

    def test_storage_failure_stops_and_does_not_acknowledge_success(self):
        lease = self.start()
        (self.probe.directory / 'events.jsonl').mkdir()
        with self.assertRaises(DesktopError):
            self.send(lease)
        self.assertTrue(self.stop.exists())
        self.assertEqual(len(self.backend.calls), 1)
        self.assertFalse(self.probe.status == 'passed')
        self.assertNotIn('SECRET', (self.probe.directory / 'summary.json').read_text())

    def test_failed_terminal_write_cannot_acknowledge_pass(self):
        frame = self.send(self.start())
        path = self.probe.directory / 'summary.json'
        path.unlink()
        path.mkdir()
        with self.assertRaises(DesktopError):
            self.probe.request('finish', {'lease': frame['lease']})
        self.assertEqual(self.probe.status, 'failed')
        self.assertTrue(self.stop.exists())

    def test_http_separates_tokens_rejects_browser_origin_and_allows_stop(self):
        server = Server(('127.0.0.1', 0), self.controller, probe=self.probe, probe_token='b' * 64)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)

        def post(path, data, extra=None):
            headers = {
                'Host': HOST,
                'Content-Type': 'application/json',
                'X-Discovery-Token': 'b' * 64,
            }
            headers.update(extra or {})
            req = Request(
                'http://127.0.0.1:' + str(server.server_port) + path,
                json.dumps(data).encode(),
                headers=headers,
            )
            try:
                with urlopen(req, timeout=2) as response:
                    return response.status, json.load(response)
            except HTTPError as error:
                return error.code, json.load(error)

        body = {'session': self.session['id']}
        for extra in [
            {'X-Discovery-Token': server.token},
            {'Origin': ORIGIN},
            {'Host': 'attacker.test'},
            {'Sec-Fetch-Site': 'same-origin'},
        ]:
            self.assertEqual(post('/probe/start', body, extra)[0], 403)
        self.assertEqual(post('/probe/start', dict(body, role='human'))[0], 400)
        status, frame = post('/probe/start', body)
        self.assertEqual(status, 200)
        self.assertEqual(server.snapshot()['runKind'], 'provider_probe')
        lease = dict(session=self.session['id'], epoch=frame['lease']['epoch'])
        self.assertEqual(
            post(
                '/stop',
                {'lease': lease},
                {
                    'Origin': ORIGIN,
                    'X-Operator-Token': server.token,
                },
            )[0],
            200,
        )
        self.assertEqual(post('/probe/action', {'lease': frame['lease'], 'action': ACTION})[0], 409)
        self.assertEqual(self.backend.calls, [])

    def test_bootstrap_token_is_private_and_replaced_on_restart(self):
        path = self.root / 'capability.json'
        with patch('interface_ai.discovery.probe.CREDENTIALS', path):
            first = provision('session-a')
            second = provision('session-b')
            self.assertNotEqual(first, second)
            self.assertEqual(credentials(), {'session': 'session-b', 'token': second})
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
