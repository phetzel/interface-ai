"""Fake-provider boundary tests for full discovery; not genuine model evidence."""

import copy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.discovery import ProbeError
from lib.discovery_flow import goal, run_discovery, recorded_candidate
from lib.discovery_request import DiscoveryRequest
from test_discovery import FIRST, Transport as ProbeTransport


class Transport(ProbeTransport):
    def __init__(self, complete=False):
        super().__init__()
        self.complete = complete

    def post(self, op, data):
        frame = super().post(op, data)
        frame.update(directory='discovery-test', actionsCompleted=1)
        if self.complete and op == 'propose':
            frame['result'] = {'status': 'success', 'output': {'amountMinor': 123456}}
            frame['candidate'] = dict(status='candidate', directory='candidate', sha256='a' * 64)
        return frame


def report():
    return dict(requestsAttempted=0, responsesCompleted=0, responses=[], usageUnknown=False)


class FlowTests(unittest.TestCase):
    def client(self):
        client = Mock()
        client.responses.create.return_value.model_dump.return_value = copy.deepcopy(FIRST)
        return client

    def test_goal_has_input_but_no_script_or_manual_artifact(self):
        text = goal('00123')
        self.assertIn('00123', text)
        self.assertNotIn('capability', text)
        self.assertNotIn('coordinate', text)
        self.assertNotIn('open-savings', text)

    def test_local_validation_ends_loop_without_trusting_model_balance(self):
        client = self.client()
        transport = Transport(complete=True)
        saved = report()
        result = run_discovery(client, transport, saved, lambda: None, '00123')
        self.assertEqual(result['output']['amountMinor'], 123456)
        self.assertEqual(saved['status'], 'passed')
        self.assertEqual(client.responses.create.call_count, 1)
        self.assertFalse(client.responses.create.call_args.kwargs['store'])
        self.assertNotIn('MEMORY-ONLY', json.dumps(saved))

    def test_explicit_goal_reaches_model_but_is_not_retained_in_metadata(self):
        request = DiscoveryRequest.parse('Please get the savings balance for member 00123.')
        client = self.client()
        saved = report()
        run_discovery(
            client, Transport(complete=True), saved, lambda: None, '00123', request=request
        )
        prompt = client.responses.create.call_args.kwargs['input'][0]['content'][0]['text']
        self.assertIn(request.goal, prompt)
        self.assertIn(request.entry_point, prompt)
        self.assertNotIn(request.goal, json.dumps(saved))

    def test_incomplete_recording_preserves_lookup_but_fails_discovery(self):
        for candidate in (
            None,
            {},
            {'status': 'incomplete', 'code': 'recording_incomplete'},
            {'status': 'candidate'},
            {'status': 'candidate', 'directory': '../wrong', 'sha256': 'a' * 64},
        ):
            with self.subTest(candidate=candidate):
                transport = Transport(complete=True)
                post = transport.post

                def missing_recording(op, data):
                    frame = post(op, data)
                    if op == 'propose':
                        frame['candidate'] = candidate
                    return frame

                transport.post = missing_recording
                saved = report()
                result = run_discovery(self.client(), transport, saved, lambda: None, '00123')
                self.assertEqual(result['status'], 'success')
                self.assertEqual(result['output']['amountMinor'], 123456)
                self.assertEqual(saved['status'], 'failed')
                self.assertEqual(saved['code'], 'recording_incomplete')
                self.assertFalse(recorded_candidate(saved['candidate']))

    def test_twenty_request_budget_is_enforced(self):
        client = self.client()
        saved = report()
        with self.assertRaisesRegex(ProbeError, 'discovery_budget'):
            run_discovery(client, Transport(), saved, lambda: None, '00123', clock=lambda: 0)
        self.assertEqual(client.responses.create.call_count, 20)

    def test_late_response_cannot_trigger_another_provider_call(self):
        client = self.client()
        transport = Transport()
        old = transport.post

        def post(op, data):
            if op == 'propose':
                raise ProbeError('ownership_revoked')
            return old(op, data)

        transport.post = post
        with self.assertRaisesRegex(ProbeError, 'ownership_revoked'):
            run_discovery(client, transport, report(), lambda: None, '00123')
        self.assertEqual(client.responses.create.call_count, 1)

    def test_provider_warning_is_not_acknowledged(self):
        client = self.client()
        value = copy.deepcopy(FIRST)
        value['output'][1]['pending_safety_checks'] = [{'code': 'challenge'}]
        client.responses.create.return_value.model_dump.return_value = value
        transport = Transport()
        with self.assertRaisesRegex(ProbeError, 'provider_safety_check'):
            run_discovery(client, transport, report(), lambda: None, '00123')
        self.assertNotIn('propose', [op for op, _ in transport.operations])
