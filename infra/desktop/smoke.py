"""Exercise actual desktop input against the synthetic native pad.

Fixed coordinates and the pad oracle are intentional calibration-test fixtures.
They are not a locator strategy or a banking replay implementation.
"""

import fcntl
import hashlib
import importlib.metadata
import json
import platform
import signal
import socket
import struct
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from common import HEIGHT, RUNTIME, SESSION, STATE, STOP, WIDTH, read_json, wait_for, write_json
from control import ready
from interface_ai.desktop import Desktop, DesktopError


def assert_calibration_screen(screen):
    # Safe only in this dedicated, synthetic calibration environment.
    if screen.size != (WIDTH, HEIGHT):
        raise AssertionError(f'Screenshot size mismatch: {screen.size}')
    for point, rgb in [((10, 10), (15, 23, 42)), ((10, 110), (241, 245, 249)),
                       ((1270, 790), (241, 245, 249))]:
        if screen.getpixel(point)[:3] != rgb:
            raise AssertionError('Screen is not the known calibration pad; capture suppressed')


def receive(connection, size):
    data = bytearray()
    while len(data) < size:
        chunk = connection.recv(size - len(data))
        if not chunk:
            raise EOFError('VNC connection closed')
        data.extend(chunk)
    return bytes(data)


def verify_vnc():
    """Use a raw RFB client so view-only is tested beyond a client UI setting.

    Wire format: RFC 6143, sections 7.1, 7.3, 7.5 and 7.6.
    """
    before = read_json(STATE)
    with socket.create_connection(('127.0.0.1', 5900), timeout=3) as connection:
        connection.settimeout(3)
        if receive(connection, 12) != b'RFB 003.008\n':
            raise AssertionError('Expected RFB 3.8')
        connection.sendall(b'RFB 003.008\n')
        count = receive(connection, 1)[0]
        if 1 not in receive(connection, count):
            raise AssertionError('Expected local view-only VNC security handshake')
        connection.sendall(b'\x01')
        if receive(connection, 4) != b'\0\0\0\0':
            raise AssertionError('VNC security handshake failed')
        connection.sendall(b'\x01')  # Shared viewer; never replace an existing viewer.
        header = receive(connection, 24)
        dimensions = struct.unpack('>HH', header[:4])
        if dimensions != (WIDTH, HEIGHT):
            raise AssertionError(f'Viewer dimensions mismatch: {dimensions}')
        receive(connection, struct.unpack('>I', header[20:24])[0])
        pixels = struct.pack('>BBBBHHHBBBxxx', 32, 24, 0, 1, 255, 255, 255, 16, 8, 0)
        connection.sendall(b'\0\0\0\0' + pixels)
        connection.sendall(struct.pack('>BBHi', 2, 0, 1, 0))  # Raw encoding only.
        # Try a click on target 1 and a key press, despite the viewer restriction.
        connection.sendall(struct.pack('>BBHH', 5, 1, 100, 190))
        connection.sendall(struct.pack('>BBHH', 5, 0, 100, 190))
        connection.sendall(struct.pack('>BBHI', 4, 1, 0, ord('x')))
        connection.sendall(struct.pack('>BBHI', 4, 0, 0, ord('x')))
        connection.sendall(struct.pack('>BBHHHH', 3, 0, 90, 180, 4, 4))
        message = receive(connection, 4)
        if message[0] != 0:
            raise AssertionError(f'Expected framebuffer update, got {message[0]}')
        rectangles = struct.unpack('>H', message[2:4])[0]
        if rectangles == 0:
            raise AssertionError('No framebuffer pixels returned')
        sampled = False
        for _ in range(rectangles):
            x, y, width, height, encoding = struct.unpack('>HHHHi', receive(connection, 12))
            if encoding != 0:
                raise AssertionError(f'Unexpected VNC encoding {encoding}')
            data = receive(connection, width * height * 4)
            if x <= 90 < x + width and y <= 180 < y + height:
                offset = ((180 - y) * width + 90 - x) * 4
                if data[offset:offset + 3] != bytes((235, 99, 37)):
                    raise AssertionError('VNC does not show the same blue calibration target')
                sampled = True
        if not sampled:
            raise AssertionError('VNC did not return the requested calibration pixels')
        # Allow the independent UI oracle to publish after the server processes input.
        deadline = time.monotonic() + 0.4
        while time.monotonic() < deadline:
            after = read_json(STATE)
            if after['clicks'] != before['clicks'] or after['entry'] != before['entry']:
                raise AssertionError('VNC accepted input despite view-only policy')
            time.sleep(0.05)
    return {'dimensions': list(dimensions), 'serverRejectedInput': True}


def verify_network():
    routes = Path('/proc/net/route').read_text().splitlines()[1:]
    if any(line.split()[1] == '00000000' for line in routes):
        raise AssertionError('Unexpected default IPv4 route on the internal desktop network')
    checked = []
    for address in ('1.1.1.1', '8.8.8.8'):
        try:
            connection = socket.create_connection((address, 443), timeout=1)
        except OSError:
            checked.append(address)
        else:
            connection.close()
            raise AssertionError(f'Unexpected external connection to {address}:443')
    return {'noDefaultIPv4Route': True, 'blockedTcpProbes': checked,
            'scope': 'Selected IPv4 probes; not a comprehensive network policy audit'}


def main():
    session = ready()
    if session['mode'] != 'native':
        raise RuntimeError('Native smoke requires ./scripts/desktop reset native')
    if session['inputStopped']:
        raise DesktopError('stopped', 'Input stopped; reset before another run')
    with Desktop(session['id']) as gui:
        run(gui, session)


def run(gui, session):
    initial = read_json(STATE)
    if initial['clicks'] or initial['entry'] or initial['submitted'] or initial['scrollTop']:
        raise RuntimeError('Smoke test requires a fresh pad. Run ./scripts/desktop reset first.')
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8]
    output = Path('/artifacts') / run_id
    output.mkdir()
    report = {'runId': run_id, 'sessionId': session['id'], 'status': 'running',
              'kind': 'native-desktop-calibration', 'adapter': 'interface_ai.desktop.Desktop', 'modelCalls': 0,
              'architecture': platform.machine(), 'display': [WIDTH, HEIGHT], 'checks': [],
              'python': platform.python_version(),
              'packages': {name: importlib.metadata.version(name)
                           for name in ('PyAutoGUI', 'Pillow', 'PyScreeze', 'python3-xlib')},
              'chromium': subprocess.check_output(['chromium', '--version'], text=True).strip(),
              'systemPackagesSha256': hashlib.sha256(
                  Path('/opt/desktop/system-packages.txt').read_bytes()).hexdigest()}

    def record(name, details=None):
        event = {'check': name, 'status': 'passed', 'details': details or {}}
        report['checks'].append(event)
        with (output / 'events.jsonl').open('a') as stream:
            stream.write(json.dumps(event) + '\n')
        print(f'PASS {name}', flush=True)

    started = time.monotonic()
    try:
        screen = gui.screenshot()
        assert_calibration_screen(screen)
        screen.save(output / 'before.png')
        record('screenshot_dimensions_and_fixture')
        record('same_framebuffer_and_server_view_only', verify_vnc())
        for number, x in [(1, 100), (2, 320), (3, 540)]:
            gui.click(x, 190)
            wait_for(f'click {number}', lambda: len(read_json(STATE)['clicks']) == number, 3)
            actual = read_json(STATE)['clicks'][-1]
            if actual != {'target': number, 'x': x, 'y': 190}:
                raise AssertionError(f'Input coordinates did not match the native event: {actual}')
            wait_for('green target', lambda: gui.screenshot().getpixel((x + 5, 195))[:3]
                     == (22, 163, 74), 3)
        record('three_pointer_coordinates_and_pixel_changes')
        gui.click(180, 405)
        gui.type_text('synthetic-input')
        gui.press('home')
        gui.hotkey('shift', 'end')
        expected = 'desktop-' + run_id[-8:]
        gui.type_text(expected)
        gui.press('enter')
        wait_for('submitted keyboard text', lambda: read_json(STATE)['submitted'] == expected, 3)
        record('native_typing_selection_and_enter', {'matchedSyntheticInput': True})
        gui.move(1000, 350)
        gui.scroll(-5)
        wait_for('native scroll', lambda: read_json(STATE)['scrollTop'] > 0, 3)
        record('native_scroll', {'topFraction': read_json(STATE)['scrollTop']})
        record('selected_external_egress_blocked', verify_network())
        before_stop = read_json(STATE)['clicks']
        marker = 'smoke stop test ' + run_id
        # Exclusive creation preserves an operator stop arriving concurrently.
        with STOP.open('x') as stop_file:
            stop_file.write(marker)
        try:
            try:
                gui.click(100, 190)
            except DesktopError as exc:
                if exc.code != 'stopped':
                    raise
            else:
                raise AssertionError('Stopped executor dispatched an action')
            if read_json(STATE)['clicks'] != before_stop:
                raise AssertionError('Unexpected input after stop')
        finally:
            if STOP.read_text() == marker:
                STOP.unlink()
        record('cooperative_stop_blocks_dispatch')
        if read_json(SESSION)['id'] != session['id']:
            raise AssertionError('Session changed during the smoke run')
        screen = gui.screenshot()
        assert_calibration_screen(screen)
        screen.save(output / 'after.png')
        record('session_preserved')
        report['status'] = 'passed'
    except Exception as exc:
        report['status'] = 'failed'
        report['error'] = {'type': type(exc).__name__, 'message': str(exc)}
        raise
    finally:
        report['elapsedSeconds'] = round(time.monotonic() - started, 3)
        write_json(output / 'report.json', report)
        print(f'Evidence: {output}', flush=True)


def timeout(*_):
    raise TimeoutError('Smoke test exceeded its 45-second total deadline')


if __name__ == '__main__':
    try:
        with (RUNTIME / 'smoke.lock').open('w') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            signal.signal(signal.SIGALRM, timeout)
            signal.alarm(45)
            main()
    except Exception as exc:
        print(f'Smoke failed: {exc}', file=sys.stderr)
        sys.exit(1)
