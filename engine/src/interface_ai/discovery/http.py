"""Separate host-only capability on the existing loopback operator port."""

import secrets
import re

from interface_ai.desktop import DesktopError
from interface_ai.policy.evidence import safe_code
from interface_ai.replay.loader import ReplayError, strict_json


def handle(handler):
    server, headers = handler.server, handler.headers
    if (
        server.probe is None
        or headers.get_all('Host') != ['127.0.0.1:6081']
        or headers.get_all('Origin') is not None
        or headers.get_all('Sec-Fetch-Site') is not None
        or len(headers.get_all('X-Discovery-Token', [])) != 1
        or re.fullmatch('[a-f0-9]{64}', headers.get('X-Discovery-Token', '')) is None
        or not secrets.compare_digest(headers.get('X-Discovery-Token', ''), server.probe_token)
        or headers.get_all('Content-Type') != ['application/json']
        or headers.get('Transfer-Encoding') is not None
        or len(headers.get_all('Content-Length', [])) != 1
    ):
        handler.reply(403, {'code': 'request_denied'})
        return
    try:
        size = int(headers['Content-Length'])
        if not 0 < size <= 4096:
            raise ValueError()
        data = strict_json(handler.rfile.read(size))
        operation = handler.path.removeprefix('/probe/')
        fields = {
            'start': {'session'},
            'action': {'lease', 'action'},
            'check': {'lease'},
            'finish': {'lease'},
            'abort': set(),
        }
        if not isinstance(data, dict) or operation not in fields or set(data) != fields[operation]:
            raise ValueError()
        if operation == 'start':
            result = server.probe.start(data['session'])
        elif operation == 'abort':
            server.probe.abort()
            result = {'status': 'stopped'}
        else:
            result = server.probe.request(operation, data)
        handler.reply(200, result)
    except DesktopError as exc:
        handler.reply(409, {'code': safe_code(exc.code)})
    except (ReplayError, ValueError, KeyError, TypeError, RecursionError):
        handler.reply(400, {'code': 'invalid_action'})
    except Exception:
        handler.reply(503, {'code': 'execution_failed'})
