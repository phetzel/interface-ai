"""Small helpers for the environment smoke test, not a replay engine."""

import json
import os
import time
from pathlib import Path

RUNTIME = Path('/tmp/interface-ai')
SESSION = RUNTIME / 'session.json'
STATE = RUNTIME / 'pad.json'
STOP = RUNTIME / 'STOP'
WIDTH = int(os.environ.get('DESKTOP_WIDTH', '1280'))
HEIGHT = int(os.environ.get('DESKTOP_HEIGHT', '800'))


def write_json(path, data):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(data, indent=2) + '\n')
    temporary.replace(path)


def read_json(path):
    return json.loads(path.read_text())


def wait_for(description, predicate, timeout=10):
    deadline = time.monotonic() + timeout
    last_error = None
    while time.monotonic() < deadline:
        try:
            value = predicate()
            if value:
                return value
        except (OSError, ValueError) as exc:
            last_error = exc
        time.sleep(0.05)
    raise TimeoutError(f'{description} not ready within {timeout}s; last error: {last_error}')
