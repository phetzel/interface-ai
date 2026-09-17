"""Loopback-published operator gateway. No request logging or screen persistence."""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
import json
from pathlib import Path
import secrets
import threading

from interface_ai.desktop import DesktopError
from interface_ai.desktop.backend import X11Backend
from interface_ai.desktop.session import request_stop
from interface_ai.policy.evidence import safe_code
from interface_ai.replay.loader import ReplayError, strict_json
from .controller import Controller

HOST = '127.0.0.1:6081'
ORIGIN = 'http://' + HOST


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def setup(self):
        super().setup()
        self.connection.settimeout(5)

    def reply(self, status, value, content_type='application/json'):
        data = json.dumps(value).encode() if content_type == 'application/json' else value
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header(
            'Content-Security-Policy',
            "default-src 'none'; script-src 'nonce-"
            + self.server.token
            + "'; style-src 'unsafe-inline'; img-src blob:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'",
        )
        self.end_headers()
        self.wfile.write(data)

    def allowed(self, *, token=True):
        return (
            self.headers.get_all('Host') == [HOST]
            and self.headers.get('Sec-Fetch-Site', 'same-origin') in ('same-origin', 'none')
            and (
                not token
                or secrets.compare_digest(
                    self.headers.get('X-Operator-Token', ''), self.server.token
                )
            )
        )

    def do_GET(self):
        if not self.allowed(token=self.path != '/'):
            self.reply(403, {'code': 'request_denied'})
            return
        try:
            if self.path == '/':
                assets = Path(__file__).parent
                html = (assets / 'operator.html').read_text()
                html = html.replace('/*__STYLES__*/', (assets / 'operator.css').read_text())
                # Serve one document: no new public asset routes or token URLs.
                script = (
                    "const token='"
                    + self.server.token
                    + "';\n"
                    + (assets / 'operator.js').read_text()
                )
                html = html.replace('/*__SCRIPT__*/', script).replace(
                    '__TOKEN__', self.server.token
                )
                self.reply(200, html.encode(), 'text/html; charset=utf-8')
            elif self.path == '/status':
                # Polling must not occupy request slots waiting behind input.
                # Leave capacity for /stop, which signals before taking mutex.
                controller = self.server.controller
                if not controller.mutex.acquire(blocking=False):
                    self.reply(503, {'code': 'busy'})
                    return
                try:
                    state = controller.snapshot()
                finally:
                    controller.mutex.release()
                self.reply(200, state)
            elif self.path == '/frame':
                # Observation only. Independent connection; never take input.lock
                # from an active run, save pixels, or send them to any model.
                backend = X11Backend()
                try:
                    image = backend.screenshot()
                finally:
                    backend.close()
                output = BytesIO()
                image.save(output, format='PNG')
                self.reply(200, output.getvalue(), 'image/png')
            else:
                self.reply(404, {'code': 'request_denied'})
        except Exception:
            self.reply(503, {'code': 'session_unavailable'})

    def do_POST(self):
        if (
            not self.allowed()
            or self.headers.get_all('Origin') != [ORIGIN]
            or self.headers.get('Content-Type') != 'application/json'
            or self.headers.get('Transfer-Encoding') is not None
            or len(self.headers.get_all('Content-Length', [])) != 1
        ):
            self.reply(403, {'code': 'request_denied'})
            return
        try:
            size = int(self.headers['Content-Length'])
            if not 0 < size <= 4096:
                raise ValueError()
            data = strict_json(self.rfile.read(size))
            fields = {
                '/start': {'lease', 'memberId'},
                '/takeover': {'lease'},
                '/action': {'lease', 'sequence', 'action'},
                '/resume': {'lease'},
                '/stop': {'lease'},
            }
            if (
                not isinstance(data, dict)
                or self.path not in fields
                or set(data) != fields[self.path]
            ):
                raise ValueError()
            controller = self.server.controller
            if self.path == '/start':
                controller.start(data['memberId'], data['lease'])
            elif self.path == '/takeover':
                controller.takeover(data['lease'])
            elif self.path == '/action':
                controller.human_action(data['action'], data['lease'], data['sequence'])
            elif self.path == '/resume':
                controller.resume(data['lease'])
            else:
                controller.verify(data['lease'])
                # Stop must interrupt an in-flight human action without waiting
                # for its controller mutex; adapter cleanup still drains normally.
                request_stop()
                with controller.mutex:
                    controller.stop()
            self.reply(200, controller.snapshot())
        except DesktopError as exc:
            self.reply(409, {'code': safe_code(exc.code)})
        except ReplayError as exc:
            if exc.code == 'invalid_input':
                self.reply(400, {'code': 'invalid_input'})
            else:
                self.reply(503, {'code': 'execution_failed'})
        except (ValueError, KeyError, TypeError, RecursionError):
            self.reply(400, {'code': 'invalid_action'})
        except Exception:
            self.reply(503, {'code': 'execution_failed'})


class Server(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address, controller):
        self.controller = controller
        self.token = secrets.token_hex(32)
        self.slots = threading.BoundedSemaphore(6)
        super().__init__(address, Handler)

    def process_request(self, request, client_address):
        if not self.slots.acquire(blocking=False):
            self.shutdown_request(request)
            return
        try:
            super().process_request(request, client_address)
        except Exception:
            self.slots.release()
            raise

    def process_request_thread(self, request, client_address):
        try:
            super().process_request_thread(request, client_address)
        finally:
            self.slots.release()

    def service_actions(self):
        # This runs on the accepting thread, not a request worker. Never wait
        # behind input here: doing so prevents even /stop from being accepted.
        # Retry expiry on the next poll after bounded input releases the mutex.
        if not self.controller.mutex.acquire(blocking=False):
            return
        try:
            self.controller.expire()
        finally:
            self.controller.mutex.release()


if __name__ == '__main__':
    with Server(('0.0.0.0', 6081), Controller()) as server:
        server.serve_forever(poll_interval=0.5)
