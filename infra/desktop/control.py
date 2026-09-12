"""Readiness, safe synthetic capture, and cooperative stop for the desktop PoC."""

import json
import os
import sys
import urllib.request
from pathlib import Path

from common import HEIGHT, SESSION, STATE, STOP, WIDTH, read_json


def ready():
    session = read_json(SESSION)
    for pid in session['pids'].values():
        os.kill(pid, 0)
    if not read_json(STATE)['ready']:
        raise RuntimeError('Native test pad is not visible')
    import pyautogui
    if tuple(pyautogui.size()) != (WIDTH, HEIGHT):
        raise RuntimeError('Unexpected display dimensions')
    with urllib.request.urlopen('http://127.0.0.1:6080/vnc.html', timeout=2) as response:
        if response.status != 200:
            raise RuntimeError('Viewer is not ready')
    return session


def main():
    command = sys.argv[1] if len(sys.argv) > 1 else 'ready'
    if command == 'ready':
        print(json.dumps(ready()))
    elif command == 'stop-input':
        STOP.write_text('operator stop\n')
        print('Cooperative stop requested. Reset the desktop to allow a new smoke run.')
    elif command == 'screenshot':
        ready()
        import pyautogui
        from smoke import assert_calibration_screen
        screenshot = pyautogui.screenshot()
        assert_calibration_screen(screenshot)
        path = Path('/artifacts/desktop.png')
        screenshot.save(path)
        print(str(path))
    else:
        raise ValueError(f'Unknown command: {command}')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(f'Desktop {sys.argv[1:]} failed: {exc}', file=sys.stderr)
        sys.exit(1)
