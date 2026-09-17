"""Session files belong to the isolated desktop, never the host session."""

import json
import os
from pathlib import Path

RUNTIME = Path(os.environ.get('INTERFACE_AI_RUNTIME', '/tmp/interface-ai'))
SESSION = RUNTIME / 'session.json'
STOP = RUNTIME / 'STOP'
LOCK = RUNTIME / 'input.lock'


def read_session():
    data = json.loads(SESSION.read_text())
    if data.get('width') != 1280 or data.get('height') != 800:
        raise RuntimeError('Unsupported desktop dimensions; expected 1280x800')
    if data.get('mode') not in ('native', 'bank'):
        raise RuntimeError('Unsupported or outdated desktop session; rebuild/reset it')
    return data


def request_stop():
    # Stop has its own path and does not need the executor lock.
    STOP.write_text('operator stop\n')
