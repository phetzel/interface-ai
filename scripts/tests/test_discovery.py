"""Offline provider protocol fixtures, never genuine discovery evidence."""

import copy
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.discovery import (  # noqa: E402
    ProbeError,
    bootstrap,
    load_key,
    new_report,
    run_flow,
    selected_click,
)

ACTION = {'type': 'click', 'button': 'left', 'x': 100, 'y': 200}
FIRST = {
    'id': 'resp_fixture1',
    'model': 'gpt-5.6-sol',
    'status': 'completed',
    'usage': {'input_tokens': 100, 'output_tokens': 20, 'total_tokens': 120},
    'output': [
        {'type': 'reasoning', 'encrypted_content': 'MEMORY-ONLY-SENTINEL'},
        {'type': 'computer_call', 'call_id': 'call_fixture1', 'actions': [ACTION]},
    ],
}
SECOND = dict(
    FIRST,
    id='resp_fixture2',
    output=[
        {
            'type': 'message',
            'content': [
                {'type': 'output_text', 'text': 'MODEL-PROSE-MUST-NOT-BE-LOGGED'},
            ],
        }
    ],
)
SCREENSHOT = dict(
    FIRST,
    id='resp_screenshot',
    output=[
        {'type': 'computer_call', 'call_id': 'call_screenshot', 'actions': [{'type': 'screenshot'}]}
    ],
)


class Transport:
    session = 'session-a'

    def __init__(self):
        self.operations = []

    def post(self, operation, data):
        self.operations.append((operation, copy.deepcopy(data)))
        return dict(
            width=1280,
            height=800,
            png='iVBORw0KGgo=',
            lease=dict(
                session=self.session, runId='run-a', epoch=3, sequence=int(operation == 'action')
            ),
        )


class DiscoveryTests(unittest.TestCase):
    def test_pinned_sdk_serializes_both_requests_with_mock_http(self):
        if importlib.util.find_spec('openai') is None:
            self.skipTest('Optional host SDK; also run in the pinned discovery script environment')
        import httpx2
        from openai import OpenAI

        bodies = []

        def respond(request):
            self.assertEqual(str(request.url), 'https://api.openai.com/v1/responses')
            bodies.append(json.loads(request.content))
            value = copy.deepcopy(FIRST if len(bodies) == 1 else SECOND)
            if len(bodies) == 1:
                value['output'][1]['actions'][0]['keys'] = []
            value.update(object='response', created_at=1, parallel_tool_calls=True)
            return httpx2.Response(200, json=value)

        with OpenAI(
            api_key='sk-offline-test',
            max_retries=0,
            base_url='https://api.openai.com/v1',
            http_client=httpx2.Client(transport=httpx2.MockTransport(respond)),
        ) as client:
            report = new_report('offline-sdk-test')
            run_flow(client, Transport(), report, lambda: None)
        self.assertEqual(len(bodies[0]['input']), 1)
        self.assertFalse(bodies[1]['store'])
        self.assertEqual(bodies[1]['input'][-1]['call_id'], 'call_fixture1')
        self.assertEqual(bodies[1]['input'][-1]['output']['type'], 'computer_screenshot')
        self.assertEqual(report['status'], 'passed')
        self.assertEqual(bodies[1]['input'][2]['actions'][0]['keys'], [])

    def test_empty_modifiers_are_normalized_without_mutating_provider_history(self):
        value = copy.deepcopy(FIRST)
        value['output'][1]['actions'][0]['keys'] = []
        call_id, action = selected_click(value)
        self.assertEqual(call_id, 'call_fixture1')
        self.assertEqual(action, ACTION)
        self.assertEqual(value['output'][1]['actions'][0]['keys'], [])

    def test_stateless_round_trip_binds_call_id_and_keeps_transcript_out_of_report(self):
        client = Mock()
        client.responses.create.side_effect = [
            SimpleNamespace(model_dump=lambda **_: copy.deepcopy(FIRST)),
            SimpleNamespace(model_dump=lambda **_: copy.deepcopy(SECOND)),
        ]
        transport, report = Transport(), new_report('offline-protocol-test')
        run_flow(client, transport, report, lambda: None)
        requests = client.responses.create.call_args_list
        self.assertEqual(len(requests), 2)
        for request in requests:
            self.assertFalse(request.kwargs['store'])
            self.assertNotIn('previous_response_id', request.kwargs)
        self.assertEqual(requests[1].kwargs['tool_choice'], 'none')
        history = requests[1].kwargs['input']
        self.assertEqual(history[-1]['call_id'], 'call_fixture1')
        self.assertEqual(history[1:3], FIRST['output'])
        self.assertEqual(
            [op for op, _ in transport.operations], ['start', 'check', 'action', 'check', 'finish']
        )
        self.assertEqual(transport.operations[2][1]['lease']['epoch'], 3)
        self.assertEqual(report['status'], 'passed')
        self.assertNotIn('SENTINEL', json.dumps(report))
        self.assertNotIn('MODEL-PROSE', json.dumps(report))
        self.assertEqual(report['requestsAttempted'], 2)

    def test_rejects_batches_unsupported_tools_refusals_and_safety_checks(self):
        cases = []
        for change in [
            {'actions': [ACTION, ACTION]},
            {'actions': [{'type': 'type', 'text': 'secret'}]},
            {'pending_safety_checks': [{'code': 'challenge'}]},
            {'actions': [dict(ACTION, role='human')]},
            {'actions': [dict(ACTION, x=True)]},
            {'actions': [dict(ACTION, keys=['CTRL'])]},
            {'actions': [dict(ACTION, keys=None)]},
            {'actions': [dict(ACTION, keys='')]},
            {'actions': [dict(ACTION, keys=False)]},
            {'actions': [None]},
        ]:
            value = copy.deepcopy(FIRST)
            value['output'][1].update(change)
            cases.append(value)
        cases.extend(
            [
                dict(FIRST, status='incomplete'),
                dict(FIRST, output=[{'type': 'function_call'}]),
                dict(
                    FIRST,
                    output=FIRST['output']
                    + [{'type': 'message', 'content': [{'type': 'refusal'}]}],
                ),
            ]
        )
        for value in cases:
            with self.subTest(value=value), self.assertRaises(ProbeError):
                selected_click(value)

    def test_initial_screenshot_round_trip_remains_bounded_to_one_click(self):
        client, transport, report = Mock(), Transport(), new_report('offline-protocol-test')
        client.responses.create.side_effect = [
            Mock(model_dump=Mock(return_value=copy.deepcopy(value)))
            for value in (SCREENSHOT, FIRST, SECOND)
        ]
        run_flow(client, transport, report, lambda: None)
        self.assertEqual(report['requestsAttempted'], 3)
        self.assertTrue(report['initialScreenshotRequested'])
        self.assertEqual(report['status'], 'passed')
        self.assertEqual([op for op, _ in transport.operations].count('action'), 1)
        history = client.responses.create.call_args_list[-1].kwargs['input']
        outputs = [item for item in history if item.get('type') == 'computer_call_output']
        self.assertEqual(
            [item['call_id'] for item in outputs], ['call_screenshot', 'call_fixture1']
        )

    def test_repeated_screenshot_request_cannot_loop_or_dispatch(self):
        client, transport, report = Mock(), Transport(), new_report('offline-protocol-test')
        client.responses.create.return_value.model_dump.return_value = copy.deepcopy(SCREENSHOT)
        with self.assertRaises(ProbeError):
            run_flow(client, transport, report, lambda: None)
        self.assertEqual(client.responses.create.call_count, 2)
        self.assertNotIn('action', [op for op, _ in transport.operations])

    def test_stop_before_initial_screenshot_return_blocks_continuation(self):
        client, transport, report = Mock(), Transport(), new_report('offline-protocol-test')
        client.responses.create.return_value.model_dump.return_value = copy.deepcopy(SCREENSHOT)
        post = transport.post

        def stopped(operation, data):
            if operation == 'check' and client.responses.create.call_count:
                raise ProbeError('ownership_revoked')
            return post(operation, data)

        transport.post = stopped
        with self.assertRaisesRegex(ProbeError, 'ownership_revoked'):
            run_flow(client, transport, report, lambda: None)
        self.assertEqual(client.responses.create.call_count, 1)
        self.assertNotIn('action', [op for op, _ in transport.operations])

    def test_provider_failure_is_counted_once_and_raw_error_never_escapes(self):
        client, transport, report = Mock(), Transport(), new_report('offline-protocol-test')
        client.responses.create.side_effect = RuntimeError('SECRET-KEY-AND-REQUEST-BODY')
        with self.assertRaises(ProbeError) as error:
            run_flow(client, transport, report, lambda: None)
        self.assertEqual(str(error.exception), 'provider_failed')
        self.assertEqual(report['requestsAttempted'], 1)
        self.assertEqual(report['responsesCompleted'], 0)
        self.assertTrue(report['usageUnknown'])
        self.assertNotIn('action', [op for op, _ in transport.operations])

    def test_late_response_after_stop_cannot_reach_second_provider_request(self):
        client, transport, report = Mock(), Transport(), new_report('offline-protocol-test')
        client.responses.create.return_value.model_dump.return_value = copy.deepcopy(FIRST)
        post = transport.post

        def stopped(operation, data):
            if operation == 'action':
                raise ProbeError('ownership_revoked')
            return post(operation, data)

        transport.post = stopped
        with self.assertRaisesRegex(ProbeError, 'ownership_revoked'):
            run_flow(client, transport, report, lambda: None)
        self.assertEqual(client.responses.create.call_count, 1)
        self.assertFalse(report['guardedClickPassed'])

    def test_env_file_is_data_not_shell_and_symlinks_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {}, clear=True):
            path = Path(directory) / '.env'
            path.write_text('IGNORED=$(touch nope)\nOPENAI_API_KEY="sk-' + 'x' * 40 + '"\n')
            self.assertEqual(load_key(path), 'sk-' + 'x' * 40)
            link = Path(directory) / 'link'
            link.symlink_to(path)
            with self.assertRaises(ProbeError):
                load_key(link)
            path.write_text('OPENAI_API_KEY=$(touch nope)\n')
            with self.assertRaises(ProbeError):
                load_key(path)
            self.assertFalse((Path(directory) / 'nope').exists())

    def test_bootstrap_subprocess_cannot_inherit_provider_key(self):
        data = dict(session='a' * 36, token='b' * 64)
        with (
            patch.dict(os.environ, {'OPENAI_API_KEY': 'SECRET'}),
            patch(
                'lib.discovery.subprocess.run',
                return_value=SimpleNamespace(stdout=json.dumps(data).encode()),
            ) as run,
        ):
            self.assertEqual(bootstrap(), data)
            self.assertNotIn('OPENAI_API_KEY', run.call_args.kwargs['env'])


if __name__ == '__main__':
    unittest.main()
