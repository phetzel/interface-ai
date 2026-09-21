"""Real HTTP/child-process lifecycle regressions; no Docker, keys or provider."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib import operator_host as host  # noqa: E402


def wait_file(path):
    deadline = time.monotonic() + 5
    while not path.exists():
        if time.monotonic() >= deadline:
            raise AssertionError('Synthetic child did not start')
        time.sleep(0.01)


class ShutdownTests(unittest.TestCase):
    def test_lifecycle_waits_through_connection_reset_until_listener_closes(self):
        state = dict(service='interface-ai-operator-host-v1', active=False, token='synthetic')
        with (
            patch.object(
                host,
                'local_request',
                side_effect=[
                    state,
                    {},
                    URLError(ConnectionResetError()),
                    state,
                    URLError(ConnectionRefusedError()),
                ],
            ) as request,
            patch.object(host.time, 'sleep'),
        ):
            host.lifecycle('stop')
        self.assertEqual(request.call_count, 5)
        self.assertEqual(request.call_args_list[1].args, ('/shutdown', {}, 'synthetic'))

    def test_http_shutdown_drains_reset_reaps_child_and_blocks_new_jobs(self):
        with (
            tempfile.TemporaryDirectory() as folder,
            patch.object(host, 'ROOT', Path(folder)),
            patch.object(host, 'Operator') as operator,
            patch.object(host, 'load_key'),
            patch.object(host.shutil, 'which', return_value='unused-uv'),
        ):
            root = Path(folder)
            started, release, finished = [
                root / name for name in ('started', 'release', 'finished')
            ]
            script = root / 'reset.py'
            script.write_text(
                'import sys,time\nfrom pathlib import Path\n'
                'Path(sys.argv[1]).touch()\n'
                'while not Path(sys.argv[2]).exists(): time.sleep(.01)\n'
                'Path(sys.argv[3]).touch()\n'
            )
            state = dict(session='test', epoch=0, phase='idle')
            operator.return_value.status.return_value = state
            stopped_after_drain = []
            operator.return_value.post.side_effect = lambda *a, **kw: stopped_after_drain.append(
                finished.exists()
            )
            server = host.Server(('127.0.0.1', 0))
            execute = server.jobs.execute
            children = []

            def reset(args, log, timeout):
                children.append(args)
                return execute(
                    [sys.executable, str(script), str(started), str(release), str(finished)],
                    log,
                    10,
                )

            def serve():
                with server:
                    server.serve_forever(poll_interval=0.02)

            def request(path, body):
                request = Request(
                    f'http://127.0.0.1:{server.server_port}' + path,
                    data=json.dumps(body).encode(),
                    headers={
                        'Host': '127.0.0.1:6082',
                        'Origin': host.ORIGIN,
                        'Content-Type': 'application/json',
                        'X-Host-Token': server.token,
                    },
                )
                try:
                    response = urlopen(request, timeout=3)
                except HTTPError as exc:
                    response = exc
                with response:
                    return response.status

            with patch.object(server.jobs, 'execute', side_effect=reset):
                thread = threading.Thread(target=serve)
                thread.start()
                try:
                    self.assertEqual(
                        request(
                            '/jobs',
                            dict(
                                kind='discover',
                                session='test',
                                goal='Find the savings balance for member 00123',
                            ),
                        ),
                        200,
                    )
                    wait_file(started)
                    child = server.jobs.process
                    self.assertFalse(server.jobs.worker.daemon)
                    self.assertEqual(request('/shutdown', {}), 200)
                    self.assertTrue(thread.is_alive())
                    self.assertIsNone(child.poll())
                    self.assertEqual(
                        request('/jobs', dict(kind='switch', session='test', app='bank')), 400
                    )
                    release.touch()
                    thread.join(5)
                    self.assertFalse(thread.is_alive())
                    self.assertFalse(server.jobs.worker.is_alive())
                    self.assertEqual(child.poll(), 0)
                    self.assertTrue(stopped_after_drain[-1])
                    self.assertEqual(len(children), 1)  # Discovery never started.
                    self.assertEqual(server.jobs.job['status'], 'stopped')
                finally:
                    release.touch()
                    server.shutdown()
                    thread.join(5)

    def test_forced_shutdown_kills_shell_descendants_and_reaps_parent(self):
        with (
            tempfile.TemporaryDirectory() as folder,
            patch.object(host, 'ROOT', Path(folder)),
            patch.object(host, 'Operator'),
        ):
            root = Path(folder)
            ready = root / 'descendant'
            script = root / 'tree.py'
            script.write_text(
                'import os,signal,subprocess,sys,time\nfrom pathlib import Path\n'
                'if len(sys.argv)>2:\n'
                ' signal.signal(signal.SIGTERM, signal.SIG_IGN)\n'
                ' Path(sys.argv[1]).write_text(str(os.getpid()))\n'
                'else: subprocess.Popen([sys.executable,__file__,sys.argv[1],"child"])\n'
                'while True: time.sleep(.1)\n'
            )
            jobs = host.Jobs()
            jobs.active = True
            jobs.job = dict(id='tree', kind='switch', status='running')
            execute = jobs.execute
            with patch.object(
                jobs,
                'execute',
                side_effect=lambda args, log, timeout: execute(
                    [sys.executable, str(script), str(ready)], log, 30
                ),
            ):
                jobs.worker = threading.Thread(
                    target=jobs.run, args=(dict(kind='switch', app='bank'),)
                )
                jobs.worker.start()
                try:
                    wait_file(ready)
                    child = jobs.process
                    descendant = int(ready.read_text())
                    jobs.close(timeout=0)
                    self.assertFalse(jobs.worker.is_alive())
                    self.assertIsNotNone(child.poll())
                    self.assertIsNone(jobs.process)
                    # Linux may briefly retain an adopted zombie; it cannot execute.
                    state = subprocess.run(
                        ['ps', '-o', 'stat=', '-p', str(descendant)], capture_output=True, text=True
                    ).stdout.strip()
                    self.assertTrue(not state or state.startswith('Z'), state)
                finally:
                    jobs.close(timeout=0)

    def test_child_timeout_terminates_the_process_group(self):
        jobs = host.Jobs()
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ValueError, 'timed out'):
                jobs.execute(
                    [sys.executable, '-c', 'import time; time.sleep(10)'],
                    Path(folder) / 'timeout.log',
                    0.05,
                )
            self.assertIsNone(jobs.process)
