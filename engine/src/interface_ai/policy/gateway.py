"""Fixed-upstream HTTP gateway; never a general forward proxy.

No request URL, headers, body, response body, or raw exception is logged. The
origin sits on a network that the desktop cannot join through this service.
"""

from http.client import HTTPConnection
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import re

ROUTES = frozenset(('/', '/index.html', '/legacy-frame.html', '/fixture-config.json', '/healthz'))
ASSET = re.compile(r'/assets/[A-Za-z0-9_-]+\.(?:js|css|woff2?|png|svg)')
MAX_BODY = 4 * 1024 * 1024
RESPONSE_HEADERS = ('Content-Type', 'Content-Security-Policy', 'X-Content-Type-Options')


def allowed_request(method, path, headers):
    # Raw origin-form only: no normalization that turns an unapproved path into
    # an approved one, no query/body/upgrade channel, no duplicate Host ambiguity.
    hosts = headers.get_all('Host', [])
    return (
        method in ('GET', 'HEAD')
        and (path in ROUTES or ASSET.fullmatch(path) is not None)
        and (hosts == ['fixture:4173'] or (hosts == ['127.0.0.1:4173'] and path == '/healthz'))
        and not any(
            headers.get_all(key)
            for key in ('Content-Length', 'Transfer-Encoding', 'Upgrade', 'Expect')
        )
    )


def upstream_response(method, path):
    connection = HTTPConnection('fixture-origin', 4173, timeout=3)
    try:
        connection.request(
            method, path, headers={'Host': 'fixture-origin:4173', 'Connection': 'close'}
        )
        response = connection.getresponse()
        if response.status != 200:  # Never follow or forward redirects.
            return None
        body = response.read(MAX_BODY + 1)
        if len(body) > MAX_BODY:
            return None
        headers = {
            key: response.getheader(key) for key in RESPONSE_HEADERS if response.getheader(key)
        }
        return headers, body
    finally:
        connection.close()


class Gateway(BaseHTTPRequestHandler):
    server_version = 'interface-ai-policy'
    sys_version = ''

    def setup(self):
        super().setup()
        self.connection.settimeout(4)

    def log_message(self, *_):
        pass

    def send_error(self, code, message=None, explain=None):
        self.deny(403, 'policy_destination_denied')

    def deny(self, status, code):
        body = ('{"code":"' + code + '"}\n').encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        if self.command != 'HEAD':
            self.wfile.write(body)
        self.close_connection = True

    def dispatch(self):
        if not allowed_request(self.command, self.path, self.headers):
            self.deny(403, 'policy_destination_denied')
            return
        try:
            response = upstream_response(self.command, self.path)
        except Exception:
            response = None
        if response is None:
            self.deny(502, 'policy_upstream_rejected')
            return
        headers, body = response
        self.send_response(200)
        for key, value in headers.items():
            self.send_header(key, value)
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        if self.command != 'HEAD':
            self.wfile.write(body)

    do_GET = do_HEAD = do_POST = do_PUT = do_DELETE = do_CONNECT = do_OPTIONS = do_PATCH = (
        do_TRACE
    ) = dispatch


if __name__ == '__main__':
    ThreadingHTTPServer(('0.0.0.0', 4173), Gateway).serve_forever()
