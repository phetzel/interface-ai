"""Local launcher boundaries and reset cancellation, without Docker or a model."""

import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import Mock, patch
from urllib.request import Request, urlopen
from urllib.error import HTTPError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib import operator_host as host  # noqa: E402


class HostTests(unittest.TestCase):
    def test_invalid_requests_never_reset_or_read_key(self):
        jobs = host.Jobs()
        with patch.object(host, 'Operator') as operator, patch.object(host, 'load_key') as key:
            for data in [
                {'kind': 'switch', 'session': 'x', 'app': '../../evil'},
                {'kind': 'discover', 'session': 'x', 'goal': 'Transfer money'},
                {'kind': 'discover', 'session': 'x', 'goal': ''},
                {'kind': 'switch', 'session': 'x', 'app': 'bank', 'command': 'evil'},
            ]:
                with self.assertRaises(ValueError):
                    jobs.start(data)
            key.assert_not_called()
            operator.assert_not_called()

    def test_stale_session_and_active_input_cannot_be_reset(self):
        jobs = host.Jobs()
        with patch.object(host, 'Operator') as operator:
            for state in [
                dict(session='new', phase='idle'),
                dict(session='x', phase='human'),
                dict(session='x', phase='running'),
            ]:
                operator.return_value.status.return_value = state
                with self.assertRaises(ValueError):
                    jobs.start(dict(kind='switch', session='x', app='native'))
            self.assertIsNone(jobs.job)

    def test_stop_during_reset_stops_new_desktop_without_launching_model(self):
        jobs = host.Jobs()
        jobs.job = dict(id='test', kind='discover', status='running')
        jobs.active = True
        started, release = threading.Event(), threading.Event()

        def reset(*_):
            started.set()
            self.assertTrue(release.wait(3))
            return 0

        with (
            tempfile.TemporaryDirectory() as folder,
            patch.object(host, 'ROOT', Path(folder)),
            patch.object(jobs, 'execute', side_effect=reset) as execute,
            patch.object(host, 'Operator') as operator,
        ):
            operator.return_value.status.return_value = dict(session='new')
            worker = threading.Thread(
                target=jobs.run,
                args=(dict(kind='discover', goal='Find the savings balance for member 00123'),),
            )
            worker.start()
            self.assertTrue(started.wait(3))
            jobs.stop()
            release.set()
            worker.join(3)
            self.assertFalse(worker.is_alive())
            self.assertEqual(execute.call_count, 1)
            self.assertEqual(jobs.job['status'], 'stopped')
            operator.return_value.post.assert_called_with('/stop')
            self.assertFalse(jobs.active)


class HTTPTests(unittest.TestCase):
    def setUp(self):
        self.server = host.Server(('127.0.0.1', 0))
        self.server.jobs = Mock()
        self.server.jobs.snapshot.return_value = {}
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)

    def request(self, *, headers=None, raw=b'{}', path='/jobs'):
        values = {
            'Host': '127.0.0.1:6082',
            'Origin': host.ORIGIN,
            'X-Host-Token': self.server.token,
            'Content-Type': 'application/json',
        }
        values.update(headers or {})
        request = Request(
            'http://127.0.0.1:' + str(self.server.server_port) + path, data=raw, headers=values
        )
        try:
            response = urlopen(request, timeout=3)
        except HTTPError as exc:
            response = exc
        with response:
            return response.status, json.load(response)

    def test_host_origin_token_and_payload_rejected_before_dispatch(self):
        for headers in [
            {'Host': 'evil.example'},
            {'Origin': 'https://evil.example'},
            {'X-Host-Token': 'wrong'},
            {'Sec-Fetch-Site': 'cross-site'},
            {'Content-Type': 'text/plain'},
        ]:
            self.assertEqual(self.request(headers=headers)[0], 403)
        for raw in [b'x' * 1025, b'{"kind":1,"kind":2}']:
            self.assertEqual(self.request(raw=raw)[0], 400)
        self.server.jobs.start.assert_not_called()

    def test_stop_does_not_wait_on_job_lock(self):
        self.assertEqual(self.request(path='/stop')[0], 200)
        self.server.jobs.stop.assert_called_once()
