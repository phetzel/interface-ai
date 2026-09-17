"""Ownership races use real flock files; HTTP tests never emit OS input."""
import json
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
        return Desktop(session_reader=lambda: self.session, backend=self.backend,
                       lock_path=self.root/'input.lock', stop_path=self.root/'STOP', **kwargs)

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
            with self.assertRaises(DesktopError) as exc: old.click(1, 2)
            self.assertEqual(exc.exception.code, 'ownership_revoked')
        with self.desktop() as fresh: fresh.click(1, 2)
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
                try: desktop.hotkey('ctrl', 'a')
                except DesktopError as exc: outcome.append(exc.code)
        worker = threading.Thread(target=automate)
        worker.start()
        self.assertTrue(started.wait(2))
        result = []
        handoff = threading.Thread(target=lambda: result.append(self.owner.takeover(self.root/'input.lock', expected=self.owner.read())))
        handoff.start()
        deadline = time.monotonic()+2
        while self.owner.read()['owner'] != 'quiescing' and time.monotonic()<deadline: time.sleep(.01)
        self.assertEqual(self.owner.read()['owner'], 'quiescing')
        self.assertEqual(result, [])
        release.set()
        worker.join(2); handoff.join(2)
        self.assertFalse(worker.is_alive() or handoff.is_alive())
        self.assertEqual(outcome, ['ownership_revoked'])
        self.assertEqual(self.backend.calls, [('down', 'ctrl'), ('up', 'ctrl')])
        self.assertEqual(result[0]['owner'], 'human')

    def test_timeout_never_grants_human_input(self):
        with self.desktop():
            with self.assertRaises(DesktopError) as exc:
                self.owner.takeover(self.root/'input.lock', expected=self.owner.read(), timeout=.03)
        self.assertEqual(exc.exception.code, 'quiesce_timeout')
        self.assertEqual(self.owner.read()['owner'], 'quiescing')

    def test_automation_cannot_input_while_human_owns_same_session(self):
        self.owner.takeover(self.root/'input.lock', expected=self.owner.read())
        with self.desktop() as desktop:
            with self.assertRaises(DesktopError): desktop.click(1, 1)
        with self.desktop(role='human') as desktop: desktop.click(2, 2)
        self.assertEqual(self.backend.calls, [('click', 2, 2)])

    def test_delayed_human_request_rejected_after_resume(self):
        human = self.owner.takeover(self.root/'input.lock', expected=self.owner.read())
        delayed = self.desktop(role='human', epoch=human['epoch'])
        self.owner.change('automation', expected=human)
        with delayed:
            with self.assertRaises(DesktopError): delayed.type_text('secret')
        self.assertEqual(self.backend.calls, [])

    def test_compare_and_swap_and_reset_bind_ownership(self):
        old = self.owner.read()
        self.owner.change('quiescing', expected=old)
        with self.assertRaises(DesktopError): self.owner.change('human', expected=old)
        with self.assertRaises(DesktopError): Ownership(self.root, 'new-session').read()


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
        self.url = 'http://127.0.0.1:'+str(self.server.server_port)

    def request(self, path, *, body=None, headers=None):
        base = {'Host': HOST, 'X-Operator-Token': self.server.token, 'Origin': ORIGIN, 'Content-Type': 'application/json'}
        base.update(headers or {})
        request = Request(self.url+path, data=body, headers=base)
        try: response = urlopen(request, timeout=3)
        except HTTPError as exc: response = exc
        with response: return response.status, response.read(), response.headers

    def test_cross_origin_host_and_token_rejected_before_controller(self):
        body = b'{"lease":{"session":"test","epoch":0}}'
        for headers in [{'Host':'evil.example'}, {'Origin':'https://evil.example'}, {'X-Operator-Token':'wrong'}, {'Sec-Fetch-Site':'cross-site'}, {'Content-Type':'text/plain'}]:
            self.assertEqual(self.request('/takeover', body=body, headers=headers)[0], 403)
        self.controller.takeover.assert_not_called()

    def test_unknown_fields_duplicate_keys_and_payload_bound(self):
        for body in [b'{"lease":{},"secret":"never-log"}', b'{"lease":{},"lease":{}}', b'x'*4097]:
            status, data, _ = self.request('/takeover', body=body)
            self.assertEqual(status, 400)
            self.assertNotIn(b'never-log', data)
        self.controller.takeover.assert_not_called()

    def test_valid_request_and_no_cache_headers(self):
        status, _, headers = self.request('/takeover', body=b'{"lease":{"session":"a","epoch":1}}')
        self.assertEqual(status, 200)
        self.controller.takeover.assert_called_once_with({'session':'a','epoch':1})
        self.assertEqual(headers['Cache-Control'], 'no-store')
        self.assertIn("frame-ancestors 'none'", headers['Content-Security-Policy'])

    def test_frames_and_status_require_operator_token(self):
        for path in ['/status', '/frame']:
            self.assertEqual(self.request(path, headers={'X-Operator-Token':''})[0],403)


class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.session = dict(id='session', mode='bank', width=1280, height=800, windowId=9)
        for name, value in [('RUNTIME', self.root), ('STOP', self.root/'STOP'), ('LOCK', self.root/'input.lock'), ('read_session', lambda:self.session), ('request_stop', lambda:(self.root/'STOP').touch())]:
            patcher = patch('interface_ai.handoff.controller.'+name, value)
            patcher.start(); self.addCleanup(patcher.stop)
        self.controller = Controller(output_root=self.root)
        self.controller.launch = Mock()
        self.lease = {'session':'session','epoch':0}
        self.controller.start('00123', self.lease)
        self.controller.phase = 'awaiting_human'
        self.controller.resume_at = 4

    def human(self):
        self.controller.takeover(self.lease)
        state = self.controller.snapshot()
        return {key:state[key] for key in ('session','epoch')}

    def test_premature_resume_never_launches_worker(self):
        with self.assertRaises(DesktopError): self.controller.resume(self.lease)
        self.controller.launch.assert_called_once_with(0)

    def test_detected_expiry_revokes_before_operator_requests_takeover(self):
        self.controller.phase = 'running'
        with patch('interface_ai.handoff.controller.Desktop'), patch('interface_ai.handoff.controller.Interpreter') as runner:
            runner.return_value.run.return_value = SimpleNamespace(status='failure', code='intervention_required', step='search-member')
            self.controller.run(0, 0)
        paused = self.controller.snapshot()
        self.assertEqual((paused['phase'],paused['owner'],paused['epoch']), ('awaiting_human','quiescing',1))
        with self.assertRaises(DesktopError): self.controller.ownership.check('automation', 0)
        self.controller.takeover({'session':'session','epoch':1})
        self.assertEqual(self.controller.snapshot()['owner'], 'human')

    def test_external_cli_stop_is_reflected_and_revokes_panel_lease(self):
        lease = self.human()
        (self.root/'STOP').touch()
        state = self.controller.snapshot()
        self.assertEqual((state['phase'],state['owner']), ('stopped','stopped'))
        with self.assertRaises(DesktopError): self.controller.verify(lease)

    def test_wrong_screen_or_identity_retains_human_then_valid_return_rotates_epoch(self):
        lease = self.human()
        with patch('interface_ai.handoff.controller.Desktop'), patch('interface_ai.handoff.controller.Interpreter') as runner:
            runner.return_value.observe.return_value.checkpoint.return_value = False
            with self.assertRaises(DesktopError) as exc: self.controller.resume(lease)
            self.assertEqual(exc.exception.code, 'resume_rejected')
            self.assertEqual(self.controller.ownership.read()['owner'], 'human')
            self.controller.launch.assert_called_once_with(0)
            runner.return_value.observe.return_value.checkpoint.return_value = True
            self.controller.resume(lease)
        self.assertEqual(self.controller.ownership.read()['owner'], 'automation')
        self.controller.launch.assert_called_with(4)
        with self.assertRaises(DesktopError): self.controller.verify(lease)

    def test_duplicate_human_sequence_is_consumed_even_on_input_failure(self):
        lease = self.human()
        with patch('interface_ai.handoff.controller.Desktop') as desktop:
            desktop.return_value.__enter__.return_value.execute.side_effect = DesktopError('input_failed','uncertain')
            for _ in range(2):
                with self.assertRaises(DesktopError): self.controller.human_action({'type':'type','text':'secret'},lease,0)
            desktop.return_value.__enter__.return_value.execute.assert_called_once()
        self.assertNotIn('secret', json.dumps(self.controller.audit))

    def test_expired_handoff_stops_without_browser_polling(self):
        lease = self.human()
        self.controller.human_deadline = time.monotonic()-1
        self.controller.expire()
        self.assertEqual(self.controller.phase, 'stopped')
        self.assertEqual(self.controller.reason, 'handoff_expired')
        self.assertTrue((self.root/'STOP').exists())
        with self.assertRaises(DesktopError): self.controller.human_action({'type':'click','x':1,'y':2},lease,0)

    def test_arbitrary_interruption_has_no_resume_cursor(self):
        self.controller.phase = 'running'
        lease = self.human()
        self.assertIsNone(self.controller.resume_at)
        with self.assertRaises(DesktopError): self.controller.resume(lease)


if __name__ == '__main__': unittest.main()
