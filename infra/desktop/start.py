"""Supervise one disposable X11 desktop; fail if any required process exits."""

import os
import secrets
import signal
import socket
import subprocess
import sys
import time
import uuid
import shutil
from pathlib import Path

from bootstrap import active_application, bank_painted, chromium_command, fixture_ready, sandbox_status

from common import HEIGHT, RUNTIME, SESSION, STATE, WIDTH, read_json, wait_for, write_json

children = []
stopping = False


def request_stop(*_):
    global stopping
    stopping = True


def launch(name, command):
    print(f'Starting {name}', flush=True)
    process = subprocess.Popen(command, start_new_session=True)
    children.append((name, process))
    return process


def command_ready(command):
    return subprocess.run(command, stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL, timeout=2).returncode == 0


def port_ready(port):
    with socket.create_connection(('127.0.0.1', port), timeout=1):
        return True


def main():
    mode = os.environ.get('DESKTOP_APP', 'native')
    if mode not in ('native', 'bank'):
        raise ValueError('DESKTOP_APP must be native or bank')
    if (WIDTH, HEIGHT) != (1280, 800):
        raise ValueError('This calibration pad currently requires a 1280x800 display')
    RUNTIME.mkdir(exist_ok=True)
    for name in ('session.json', 'pad.json', 'STOP', 'ownership.json', 'ownership.next'):
        (RUNTIME / name).unlink(missing_ok=True)
    # Xvfb can leave these behind across a container restart after an abrupt exit.
    Path('/tmp/.X99-lock').unlink(missing_ok=True)
    Path('/tmp/.X11-unix/X99').unlink(missing_ok=True)
    auth = Path(os.environ['XAUTHORITY'])
    auth.touch(mode=0o600)
    subprocess.run(['xauth', '-f', str(auth), 'add', os.environ['DISPLAY'], '.',
                    secrets.token_hex(16)], check=True)
    launch('display', ['Xvfb', os.environ['DISPLAY'], '-screen', '0',
                       f'{WIDTH}x{HEIGHT}x24', '-nolisten', 'tcp', '-auth', str(auth)])
    wait_for('X11 display', lambda: command_ready(['xdpyinfo']))
    launch('window manager', ['openbox'])
    wait_for('window manager', lambda: b'window id' in subprocess.check_output(
        ['xprop', '-root', '_NET_SUPPORTING_WM_CHECK']))
    sandbox = None
    if mode == 'native':
        app = launch('native test pad', [sys.executable, '/opt/desktop/pad.py'])
        wait_for('native test pad', lambda: read_json(STATE).get('ready'))
    else:
        wait_for('local fixture health', fixture_ready, 15)
        shutil.rmtree(RUNTIME / 'chromium-profile', ignore_errors=True)
        app = launch('Chromium', chromium_command())

    def application_ready():
        if app.poll() is not None:
            raise RuntimeError('Application exited during startup; inspect desktop logs')
        return active_application(mode)

    application = wait_for('focused application window', application_ready, 15)
    if mode == 'bank':
        wait_for('painted banking fixture', bank_painted, 15)
        sandbox = wait_for('Chromium renderer sandbox', lambda: sandbox_status(app.pid), 10)
    launch('read-only VNC', ['x11vnc', '-display', os.environ['DISPLAY'], '-auth', str(auth),
                           '-localhost', '-rfbport', '5900', '-forever', '-shared',
                           '-viewonly', '-nopw', '-noxdamage', '-quiet'])
    wait_for('VNC', lambda: port_ready(5900))
    launch('web viewer', ['/usr/bin/websockify', '--web=/usr/share/novnc',
                          '0.0.0.0:6080', '127.0.0.1:5900'])
    wait_for('web viewer', lambda: port_ready(6080))
    write_json(SESSION, {'id': str(uuid.uuid4()), 'display': os.environ['DISPLAY'],
                        'width': WIDTH, 'height': HEIGHT, 'viewer': 'read-only',
                        'mode': mode, **application, 'appPid': app.pid, 'sandbox': sandbox,
                        'pids': {name: process.pid for name, process in children}})
    launch('operator gateway', [sys.executable, '-m', 'interface_ai.handoff.server'])
    wait_for('operator gateway', lambda: port_ready(6081))
    print(f'Desktop ready: {mode}, 1280x800; read-only viewer on port 6080', flush=True)
    while not stopping:
        for name, process in children:
            if process.poll() is not None:
                raise RuntimeError(f'Required process {name} exited: {process.returncode}')
        time.sleep(0.2)


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, request_stop)
    signal.signal(signal.SIGINT, request_stop)
    try:
        main()
    finally:
        SESSION.unlink(missing_ok=True)
        for _, process in reversed(children):
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGTERM)
        deadline = time.monotonic() + 5
        for _, process in reversed(children):
            try:
                process.wait(timeout=max(0.1, deadline - time.monotonic()))
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
