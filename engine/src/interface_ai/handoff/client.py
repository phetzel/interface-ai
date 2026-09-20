"""Trusted local CLI client; no operator HTML/token scraping or native input."""

import json
import re
import time
from urllib.error import HTTPError
from urllib.request import Request, build_opener, HTTPRedirectHandler, ProxyHandler

from interface_ai.desktop import DesktopError
from interface_ai.desktop.session import RUNTIME
from interface_ai.files import read_regular
from interface_ai.policy.evidence import safe_code
from interface_ai.replay.loader import strict_json


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def replay(capability, member_id, session):
    credentials = strict_json(read_regular(RUNTIME / 'discovery-capability.json', 1024))
    if credentials.get('session') != session or not re.fullmatch(
        '[a-f0-9]{64}', credentials.get('token', '')
    ):
        raise DesktopError('stale_session', 'Coordinator credentials require a fresh session')
    opener = build_opener(ProxyHandler({}), NoRedirect())

    def post(operation, data):
        req = Request(
            'http://127.0.0.1:6081/run/' + operation,
            data=json.dumps(data).encode(),
            headers={'Content-Type': 'application/json', 'X-Discovery-Token': credentials['token']},
        )
        try:
            with opener.open(req, timeout=10) as response:
                raw = response.read(2 * 1024 * 1024 + 1)
                if len(raw) > 2 * 1024 * 1024:
                    raise ValueError()
                return strict_json(raw)
        except HTTPError as exc:
            try:
                code = safe_code(strict_json(exc.read(4096)).get('code'))
            except Exception:
                code = 'execution_failed'
            raise DesktopError(code, 'Coordinator rejected the request') from None
        except (OSError, ValueError):
            raise DesktopError(
                'session_unavailable', 'Coordinator unavailable; inspect the panel'
            ) from None

    state = post(
        'start', {'session': session, 'capability': str(capability), 'memberId': member_id}
    )
    deadline = time.monotonic() + 180
    while state['phase'] in ('running', 'quiescing'):
        if time.monotonic() >= deadline:
            raise DesktopError(
                'deadline', 'CLI wait ended; inspect or stop the existing run in the panel'
            )
        time.sleep(0.2)
        state = post('status', {'session': session, 'runId': state['runId']})
    if not re.fullmatch('[0-9]{8}T[0-9]{6}Z-replay-[a-f0-9]{8}', state.get('runId', '')):
        raise DesktopError('execution_failed', 'Invalid coordinator run reference')
    return state
