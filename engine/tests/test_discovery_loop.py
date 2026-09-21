"""Simulated provider/OS fixtures; do not claim genuine discovery."""

import json
from pathlib import Path
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from PIL import Image
from interface_ai.contracts.models import SavingsOutput, Success
from interface_ai.desktop import Desktop, DesktopError
from interface_ai.discovery.actions import normalize
from interface_ai.discovery.worker import Discovery
from interface_ai.handoff.controller import Controller
from interface_ai.replay.loader import ReplayError
from test_desktop import Backend

CLICK = {'type': 'click', 'button': 'left', 'x': 100, 'y': 200}


class Policy:
    def __init__(self, inputs):
        self.inputs = inputs
        self.keyboard = None
        self.last_target = None

    def view(self, desktop):
        desktop.checkpoint()
        calls = desktop.backend.calls
        result = None
        if ('click', 900, 600) in calls:
            state = 'account-ready'
            result = Success(
                output=SavingsOutput(
                    memberId='00123',
                    memberName='Demo Member A',
                    accountType='Savings',
                    currency='USD',
                    amountMinor=123456,
                )
            )
        elif ('down', 'enter') in calls:
            state = 'member-ready'
        elif ''.join(c[1] for c in calls if c[0] == 'type') == '00123':
            state = 'input-entered'
        else:
            state = 'search-ready'
        return SimpleNamespace(image=Image.new('RGB', (1280, 800))), state, result

    def authorize(self, action, desktop):
        desktop.checkpoint()
        if action['type'] == 'click':
            if action['x'] not in (100, 900):
                raise DesktopError('policy_operation_denied', 'Denied')
            self.last_target = 'member-input' if action['x'] == 100 else 'savings-button'

    def completed(self):
        pass

    def clear(self):
        pass


class DiscoveryLoopTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.session = dict(id='session-a', mode='bank', width=1280, height=800, windowId=9)
        self.backend = Backend()
        self.backend.application_matches = lambda _: True
        self.backend.screenshot = lambda: Image.new('RGB', (1280, 800))
        for name, value in [
            ('RUNTIME', self.root),
            ('LOCK', self.root / 'input.lock'),
            ('STOP', self.root / 'STOP'),
            ('read_session', lambda: dict(self.session)),
            ('request_stop', lambda: (self.root / 'STOP').touch()),
        ]:
            patcher = patch('interface_ai.handoff.controller.' + name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.c = Controller(output_root=self.root)
        self.now = None
        self.discovery = Discovery(
            self.c, desktop_factory=self.desktop, policy_factory=Policy, recorder_factory=None
        )
        self.addCleanup(self.close)

    def desktop(self, session_id, **kw):
        return Desktop(
            session_id,
            backend=self.backend,
            session_reader=lambda: dict(self.session),
            stop_path=self.root / 'STOP',
            lock_path=self.root / 'input.lock',
            clock=lambda: self.now if self.now is not None else time.monotonic(),
            **kw,
        )

    def close(self):
        self.discovery.abort()
        if self.discovery.worker:
            self.discovery.worker.join(2)

    def start(self):
        return self.discovery.start('session-a', '00123')

    def send(self, frame, actions):
        return self.discovery.request(
            'propose',
            {
                'lease': frame['lease'],
                'actions': actions,
                'callId': f'call_{self.discovery.sequence}',
                'responseId': f'resp_{self.discovery.sequence}',
            },
        )

    def test_actual_dispatched_path_and_local_result(self):
        frame = self.start()
        frame = self.send(
            frame,
            [CLICK, {'type': 'type', 'text': '00123'}, {'type': 'keypress', 'keys': ['ENTER']}],
        )
        frame = self.send(
            frame, [dict(CLICK, x=900, y=600), {'type': 'wait'}, {'type': 'screenshot'}]
        )
        self.discovery.worker.join(2)
        self.assertEqual(frame['result']['output']['amountMinor'], 123456)
        self.assertEqual(self.c.snapshot()['phase'], 'success')
        self.assertIsNone(self.c.snapshot()['modelCalls'])
        trace = json.loads((self.discovery.directory / 'trajectory.json').read_text())
        self.assertEqual([e['action'] for e in trace], ['click', 'type', 'press', 'click'])
        self.assertTrue(
            all(
                e['status'] == 'completed' and e['beforeObservation'] and e['afterObservation']
                for e in trace
            )
        )
        self.assertEqual(trace[1]['inputBinding'], 'memberId')
        self.assertNotIn('00123', json.dumps(trace))
        self.assertFalse(list(self.discovery.directory.glob('*.png')))

    def test_stop_blocks_late_response(self):
        frame = self.start()
        self.c.stop()
        with self.assertRaises(DesktopError):
            self.send(frame, [CLICK])
        self.assertEqual(self.backend.calls, [])
        self.assertEqual(self.c.snapshot()['phase'], 'stopped')

    def test_recorder_failure_preserves_result_and_reports_incomplete_discovery(self):
        frame = self.start()
        self.discovery.recorder = SimpleNamespace(
            observe=lambda *_: None,
            finish=Mock(side_effect=ReplayError('recording_incomplete', 'Synthetic failure')),
        )
        frame = self.send(
            frame,
            [CLICK, {'type': 'type', 'text': '00123'}, {'type': 'keypress', 'keys': ['ENTER']}],
        )
        frame = self.send(frame, [dict(CLICK, x=900, y=600)])
        self.discovery.worker.join(2)
        self.assertEqual(frame['result']['output']['amountMinor'], 123456)
        self.assertEqual(frame['candidate']['status'], 'incomplete')
        summary = json.loads((self.discovery.directory / 'summary.json').read_text())
        result = json.loads((self.discovery.directory / 'result.json').read_text())
        self.assertEqual(summary['status'], 'failed')
        self.assertEqual(summary['code'], 'recording_incomplete')
        self.assertEqual(result['status'], 'success')
        self.assertFalse((self.discovery.directory / 'candidate/capability.json').exists())

    def test_human_takeover_drops_late_response_and_new_observations(self):
        frame = self.start()
        before = self.discovery.observations
        self.c.takeover({'session': 'session-a', 'epoch': 0})
        with self.assertRaises(DesktopError):
            self.send(frame, [CLICK])
        self.assertEqual(self.discovery.observations, before)
        self.assertEqual(self.c.snapshot()['owner'], 'human')
        self.assertFalse(self.c.snapshot()['resumable'])
        self.discovery.abort()
        self.assertEqual(self.c.snapshot()['owner'], 'human')

    def test_partial_batch_cannot_replay_input_after_stop(self):
        frame = self.start()
        self.backend.hook = self.c.stop
        with self.assertRaises(DesktopError):
            self.send(frame, [CLICK, CLICK])
        self.assertEqual(self.backend.calls, [('click', 100, 200)])
        with self.assertRaises(DesktopError):
            self.send(frame, [CLICK, CLICK])
        self.assertEqual(len(self.backend.calls), 1)

    def test_consumed_observation_and_duplicate_response(self):
        frame = self.start()
        self.send(frame, [CLICK])
        with self.assertRaises(DesktopError):
            self.send(frame, [CLICK])
        self.assertEqual(len(self.backend.calls), 1)

    def test_no_progress_pauses_without_input(self):
        frame = self.start()
        with self.assertRaises(DesktopError) as error:
            for _ in range(5):
                frame = self.send(frame, [{'type': 'screenshot'}])
        self.assertEqual(error.exception.code, 'discovery_stuck')
        self.assertEqual(self.c.snapshot()['phase'], 'awaiting_human')
        self.assertEqual(self.backend.calls, [])

    def test_budget_and_reset_reject_before_dispatch(self):
        frame = self.start()
        self.discovery.actions = 40
        with self.assertRaises(DesktopError) as error:
            self.send(frame, [CLICK])
        self.assertEqual(error.exception.code, 'discovery_budget')
        self.assertEqual(self.backend.calls, [])

    def test_deadline_releases_reservation(self):
        self.now = 0
        self.start()
        self.now = 121
        self.discovery.worker.join(2)
        self.assertFalse(self.discovery.worker.is_alive())
        self.assertEqual(self.discovery.code, 'deadline')

    def test_wrong_screen_policy_cannot_be_overridden(self):
        frame = self.start()
        with self.assertRaises(DesktopError) as error:
            self.send(frame, [dict(CLICK, x=500)])
        self.assertEqual(error.exception.code, 'policy_operation_denied')
        self.assertEqual(self.backend.calls, [])

    def test_normalization_rejects_other_text_keys_and_extras(self):
        for action in [
            dict(CLICK, role='human'),
            dict(CLICK, x=True),
            {'type': 'type', 'text': 'secret'},
            {'type': 'keypress', 'keys': ['CTRL', 'L']},
            {'type': 'wait', 'seconds': 100},
            {'type': 'drag', 'path': []},
        ]:
            with self.subTest(action=action), self.assertRaises(DesktopError):
                normalize(action, '00123')
        self.assertEqual(
            normalize({'type': 'keypress', 'keys': ['ENTER']}, '00123'),
            {'type': 'press', 'key': 'enter'},
        )
