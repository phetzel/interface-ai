"""Separate host-only capability on the existing loopback operator port."""

import secrets
import re

from interface_ai.desktop import DesktopError
from interface_ai.policy.evidence import safe_code
from interface_ai.replay.loader import ReplayError, strict_json, load_bundle


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
        if handler.path.startswith(('/run/', '/review/')):
            result = run_request(server.controller, handler.path, data)
            handler.reply(200, result)
            return
        discovery = handler.path.startswith('/discover/')
        worker = server.discovery if discovery else server.probe
        operation = handler.path.removeprefix('/discover/' if discovery else '/probe/')
        fields = (
            {
                'start': {'session', 'memberId'},
                'propose': {'lease', 'actions', 'callId', 'responseId'},
                'check': {'lease'},
                'abort': set(),
            }
            if discovery
            else {
                'start': {'session'},
                'action': {'lease', 'action'},
                'check': {'lease'},
                'finish': {'lease'},
                'abort': set(),
            }
        )
        if (
            worker is None
            or not isinstance(data, dict)
            or operation not in fields
            or set(data) != fields[operation]
        ):
            raise ValueError()
        if operation == 'start':
            result = (
                worker.start(data['session'], data['memberId'])
                if discovery
                else worker.start(data['session'])
            )
        elif operation == 'abort':
            worker.abort()
            result = {'status': 'stopped'}
        else:
            result = worker.request(operation, data)
        handler.reply(200, result)
    except DesktopError as exc:
        handler.reply(409, {'code': safe_code(exc.code)})
    except (ReplayError, ValueError, KeyError, TypeError, RecursionError):
        handler.reply(400, {'code': 'invalid_action'})
    except Exception:
        handler.reply(503, {'code': 'execution_failed'})


def run_request(controller, path, data):
    review = path.startswith('/review/')
    path = path.replace('/review/', '/run/', 1)
    fields = {
        '/run/start': {'session', 'capability', 'memberId'},
        '/run/status': {'session', 'runId'},
    }
    if not isinstance(data, dict) or path not in fields or set(data) != fields[path]:
        raise ValueError()
    with controller.mutex:
        if data['session'] != controller.session['id']:
            raise DesktopError('stale_session', 'Refresh the desktop session')
        if path == '/run/start':
            admission = None
            if review:
                from interface_ai.policy.candidate import review_candidate

                bundle, admission = review_candidate(data['capability'])
            else:
                bundle = load_bundle(data['capability'])
            state = controller.ownership.read()
            controller.start(
                data['memberId'],
                {'session': state['session'], 'epoch': state['epoch']},
                bundle=bundle,
                origin='cli',
                admission=admission,
            )
        elif controller.directory is None or data['runId'] != controller.directory.name:
            raise DesktopError('invalid_transition', 'The requested run is not active')
        return controller.snapshot()
