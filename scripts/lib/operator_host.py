"""Loopback control plane for explicit operator requests, never model actions.

Only fixed desktop resets and the existing bounded discovery command are allowed.
The desktop has no route to this service, Docker socket, SDK, or provider key.
"""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import hashlib
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import threading
import time
from urllib.request import Request, build_opener, ProxyHandler
import uuid

from .acceptance import ROOT
from .discovery import load_key
from .discovery_request import DiscoveryRequest
from .operator import Operator

ADDRESS = ('127.0.0.1', 6082)
ORIGIN = 'http://127.0.0.1:6081'
BASE = 'http://127.0.0.1:6082'
APPS = {
    'bank': ('bank', 'default', 'Northstar bank'),
    'bank-iframe': ('bank', 'iframe', 'Bank · nested iframes'),
    'bank-translated': ('bank', 'translated', 'Bank · shifted layout'),
    'bank-expired': ('bank', 'expired', 'Bank · session recovery'),
    'native': ('native', 'default', 'Native input pad'),
}
FINGERPRINT = hashlib.sha256(
    b''.join(p.read_bytes() for p in sorted((ROOT / 'scripts/lib').glob('*.py')))
).hexdigest()


class RequestError(ValueError):
    pass


TERMINAL = (
    'idle',
    'success',
    'failure',
    'business_outcome',
    'stopped',
    'probe_complete',
    'probe_failed',
)


def decode(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('Duplicate field')
            result[key] = value
        return result

    return json.loads(raw, object_pairs_hook=pairs)


class Jobs:
    def __init__(self):
        self.lock = threading.Lock()
        self.cancel = threading.Event()
        self.job = None
        self.session = None
        self.active = False

    def snapshot(self):
        with self.lock:
            return dict(
                service='interface-ai-operator-host-v1',
                root=str(ROOT),
                fingerprint=FINGERPRINT,
                active=self.active,
                apps=[{'id': key, 'label': value[2]} for key, value in APPS.items()],
                job=dict(self.job) if self.job else None,
                session=self.session,
            )

    def start(self, data):
        if not isinstance(data, dict) or data.get('kind') not in ('switch', 'discover'):
            raise RequestError('Choose an app or a supported discovery goal')
        kind = data['kind']
        if set(data) != {'kind', 'session', 'app' if kind == 'switch' else 'goal'}:
            raise RequestError('Unexpected request fields')
        if kind == 'switch':
            if data['app'] not in APPS:
                raise RequestError('Choose an available demo app')
        else:
            try:
                DiscoveryRequest.parse(data['goal'])
            except ValueError as exc:
                raise RequestError(str(exc)) from None
            if not isinstance(data['goal'], str) or not data['goal'].strip():
                raise RequestError('Enter a savings-balance goal')
            if not shutil.which('uv'):
                raise RequestError('Install uv for discovery; saved workflows work offline')
            # Validate availability without exposing, storing, or passing the key.
            try:
                load_key()
            except Exception:
                raise RequestError('Set OPENAI_API_KEY in the private .env file first') from None
        with self.lock:
            if self.active:
                raise RequestError('An operator job is already running')
            self.cancel.clear()
            operator = Operator()
            current = operator.status()
            if current['session'] != data['session']:
                raise RequestError('Desktop changed; reload the operator')
            if current['phase'] not in TERMINAL:
                raise RequestError('Stop the current run or release control before switching apps')
            # Revoke the old session before launching reset. A stale second tab
            # cannot start a replay while the host is replacing the desktop.
            operator.post('/stop', lease=Operator.lease(current))
            if self.cancel.is_set():
                raise RequestError('Start cancelled by Stop')
            self.active = True
            self.job = dict(
                id=uuid.uuid4().hex,
                kind=kind,
                status='running',
                stage='Starting desktop',
                app=data.get('app', 'bank'),
            )
            self.session = current['session']
            threading.Thread(target=self.run, args=(data,), daemon=True).start()

    def update(self, **values):
        with self.lock:
            self.job.update(values)

    def execute(self, args, log, timeout):
        environment = {k: v for k, v in os.environ.items() if not k.startswith('OPENAI_')}
        environment['INTERFACE_AI_HOST_CHILD'] = '1'
        environment['CAPABILITY'] = 'discovered-savings'
        with log.open('wb') as stream:
            process = subprocess.Popen(
                args, cwd=ROOT, env=environment, stdout=stream, stderr=stream
            )
            try:
                # Reset is allowed to drain on Stop, then the new session is stopped.
                # Discovery polls the revoked desktop lease before every model call.
                return process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                raise ValueError('Job timed out; reset before retrying') from None

    def run(self, data):
        directory = ROOT / 'tmp/operator-jobs' / self.job['id']
        try:
            directory.mkdir(parents=True, mode=0o700)
            app = APPS[data['app']] if data['kind'] == 'switch' else APPS['bank']
            if self.execute(['./scripts/desktop', 'reset', *app[:2]], directory / 'reset.log', 180):
                raise ValueError(
                    'Desktop could not start; inspect ' + str(directory.relative_to(ROOT))
                )
            operator = Operator()
            current = operator.status()
            with self.lock:
                self.session = current['session']
            if self.cancel.is_set():
                operator.post('/stop')
                self.update(status='stopped', stage='Stopped')
                return
            if data['kind'] == 'switch':
                self.update(status='passed', stage=app[2] + ' ready')
                return
            self.update(stage='Discovering with OpenAI')
            log = directory / 'discovery.log'
            code = self.execute(
                [
                    'uv',
                    'run',
                    '--locked',
                    '--script',
                    'scripts/discover',
                    '--goal',
                    data['goal'],
                    '--session',
                    current['session'],
                ],
                log,
                170,
            )
            # Only the fixed command's evidence path and closed report metadata reach the UI.
            lines = log.read_text()[-8192:].splitlines()
            evidence = next((Path(x[10:]) for x in lines if x.startswith('Evidence: ')), None)
            if (
                evidence is None
                or evidence.resolve().parent != (ROOT / 'tmp/discovery-runs').resolve()
            ):
                raise ValueError('Discovery ended without a report; inspect the operator job log')
            report = json.loads((evidence / 'report.json').read_text())
            passed = code == 0 and report['status'] == 'passed' and not self.cancel.is_set()
            self.update(
                status='passed' if passed else ('stopped' if self.cancel.is_set() else 'failed'),
                stage='Candidate recorded · review required'
                if passed
                else 'Discovery stopped or failed',
                evidence=str(evidence.relative_to(ROOT)),
                requests=report['requestsAttempted'],
                candidate=bool(report.get('candidate')),
            )
        except Exception as exc:
            self.update(
                status='failed',
                stage=str(exc)
                if isinstance(exc, ValueError)
                else 'Job failed; inspect tmp/operator-jobs',
            )
        finally:
            if self.cancel.is_set():
                self.stop_desktop()
            with self.lock:
                self.active = False

    @staticmethod
    def stop_desktop():
        try:
            Operator().post('/stop')
        except Exception:
            pass  # A reset may be replacing the server; run() stops the new session too.

    def stop(self):
        self.cancel.set()
        self.stop_desktop()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def setup(self):
        super().setup()
        self.connection.settimeout(5)

    def allowed(self):
        return (
            self.headers.get_all('Host') == ['127.0.0.1:6082']
            and self.headers.get_all('Origin') == [ORIGIN]
            and self.headers.get('Sec-Fetch-Site', 'same-site') in ('same-site', 'same-origin')
        )

    def reply(self, code, body):
        data = json.dumps(body).encode()
        self.send_response(code)
        if self.allowed():
            self.send_header('Access-Control-Allow-Origin', ORIGIN)
            self.send_header('Vary', 'Origin')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self):
        if not self.allowed() or self.path not in ('/jobs', '/stop', '/shutdown'):
            self.reply(403, {})
            return
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', ORIGIN)
        self.send_header('Access-Control-Allow-Methods', 'POST')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-Host-Token')
        self.send_header('Content-Length', '0')
        self.end_headers()

    def do_GET(self):
        if not self.allowed() or self.path != '/status':
            self.reply(403, {})
            return
        self.reply(200, dict(self.server.jobs.snapshot(), token=self.server.token))

    def do_POST(self):
        if (
            not self.allowed()
            or self.headers.get_all('X-Host-Token') != [self.server.token]
            or self.headers.get_all('Content-Type') != ['application/json']
            or self.headers.get('Transfer-Encoding') is not None
            or len(self.headers.get_all('Content-Length', [])) != 1
        ):
            self.reply(403, {})
            return
        try:
            size = int(self.headers['Content-Length'])
            if not 0 < size <= 1024:
                raise ValueError('Invalid request size')
            data = decode(self.rfile.read(size))
            if self.path == '/jobs':
                self.server.jobs.start(data)
            elif self.path in ('/stop', '/shutdown') and data == {}:
                if self.path == '/stop' or self.server.jobs.active:
                    self.server.jobs.stop()
                if self.path == '/shutdown':
                    threading.Thread(target=self.server.shutdown, daemon=True).start()
            else:
                raise ValueError('Unknown operation')
            self.reply(200, self.server.jobs.snapshot())
        except RequestError as exc:
            self.reply(400, {'message': str(exc)})
        except (ValueError, TypeError, KeyError):
            self.reply(400, {'message': 'Invalid request or unavailable operation'})
        except Exception:
            self.reply(503, {'message': 'Desktop unavailable; refresh and retry'})


class Server(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address=ADDRESS):
        self.jobs = Jobs()
        self.token = secrets.token_hex(32)
        super().__init__(address, Handler)


def local_request(path='/status', body=None, token=None):
    headers = {'Origin': ORIGIN, 'Content-Type': 'application/json'}
    if token:
        headers['X-Host-Token'] = token
    request = Request(
        BASE + path, data=json.dumps(body).encode() if body is not None else None, headers=headers
    )
    with build_opener(ProxyHandler({})).open(request, timeout=10) as response:
        return json.load(response)


def lifecycle(operation):
    try:
        status = local_request()
    except Exception:
        status = None
    if status and status.get('service') != 'interface-ai-operator-host-v1':
        raise RuntimeError('Port 6082 is occupied by another service')
    if status and status.get('active') and operation != 'stop':
        raise RuntimeError('Stop the active operator job before restarting its local service')
    if status and (
        operation == 'stop'
        or status['root'] != str(ROOT)
        or status.get('fingerprint') != FINGERPRINT
    ):
        local_request('/shutdown', {}, status['token'])
        time.sleep(0.6)
        status = None
    if operation == 'stop' or status:
        return
    directory = ROOT / 'tmp/operator-host'
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    environment = {k: v for k, v in os.environ.items() if not k.startswith('OPENAI_')}
    with (directory / 'server.log').open('ab') as log:
        subprocess.Popen(
            ['python3', str(ROOT / 'scripts/operator-host'), 'serve'],
            cwd=ROOT,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=log,
            start_new_session=True,
        )
    for _ in range(30):
        time.sleep(0.1)
        try:
            if local_request()['root'] == str(ROOT):
                return
        except Exception:
            pass
    raise RuntimeError(
        'Operator host service failed to start; inspect tmp/operator-host/server.log'
    )
