"""Health and reviewed synthetic capture, shared by native and bank sessions."""

import json
import os
import sys
import urllib.request

from interface_ai.desktop import DesktopError
from interface_ai.desktop.backend import X11Backend
from interface_ai.desktop.session import STOP, read_session, request_stop


def ready():
    session = read_session()
    for pid in session['pids'].values():
        os.kill(pid, 0)
    backend = X11Backend()
    try:
        if backend.size() != (session['width'], session['height']):
            raise RuntimeError('Unexpected display dimensions')
        if backend.active_window() != session['windowId']:
            raise RuntimeError('Bootstrapped application is not focused')
    finally:
        backend.close()
    with urllib.request.urlopen('http://127.0.0.1:6080/vnc.html', timeout=2) as response:
        if response.status != 200:
            raise RuntimeError('Viewer is not ready')
    return session | {'inputStopped': STOP.exists()}


def main():
    command = sys.argv[1] if len(sys.argv) > 1 else 'ready'
    if command == 'ready':
        print(json.dumps(ready()))
    elif command == 'stop-input':
        request_stop()
        print('Input stopped. Reset the desktop to allow a new run.')
    elif command == 'screenshot':
        raise DesktopError(
            'policy_capture_denied',
            'Raw screenshot persistence is disabled; use safe evidence export',
        )
    else:
        raise ValueError('Unknown control command')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(f'Desktop control failed: {exc}', file=sys.stderr)
        sys.exit(1)
