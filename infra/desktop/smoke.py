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
import re
import urllib.error
import urllib.request
from io import BytesIO

from PIL import Image
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
    for point, rgb in [
        ((10, 10), (15, 23, 42)),
        ((10, 110), (241, 245, 249)),
        ((1270, 790), (241, 245, 249)),
    ]:
        if screen.getpixel(point)[:3] != rgb:
            raise AssertionError('Screen is not the known calibration pad; capture suppressed')


def verify_operator(screen):
    """The observation surface matches X11 and cannot bypass human ownership."""
    origin = 'http://127.0.0.1:6081'
    before = read_json(STATE)
    with urllib.request.urlopen(origin + '/', timeout=3) as response:
        token = re.search(r"const token='([a-f0-9]{64})';", response.read().decode()).group(1)
    headers = {'X-Operator-Token': token}
    with urllib.request.urlopen(
        urllib.request.Request(origin + '/frame', headers=headers), timeout=3
    ) as response:
        assert response.headers['Content-Type'] == 'image/png'
        assert response.headers['Cache-Control'] == 'no-store'
        with Image.open(BytesIO(response.read())) as frame:
            assert_calibration_screen(frame)
            for point in ((90, 180), (310, 180), (530, 180)):
                assert frame.getpixel(point)[:3] == screen.getpixel(point)[:3]
    with urllib.request.urlopen(
        urllib.request.Request(origin + '/status', headers=headers), timeout=3
    ) as response:
        status = json.load(response)
    assert status['phase'] == 'idle' and status['owner'] == 'automation'
    action = {
        'lease': {key: status[key] for key in ('session', 'epoch')},
        'sequence': status['sequence'],
        'action': {'type': 'click', 'x': 100, 'y': 190},
    }
    request = urllib.request.Request(
        origin + '/action',
        data=json.dumps(action).encode(),
        headers=headers | {'Origin': origin, 'Content-Type': 'application/json'},
    )
    try:
        with urllib.request.urlopen(request, timeout=3):
            raise AssertionError('Operator accepted input without human ownership')
    except urllib.error.HTTPError as exc:
        assert exc.code == 409 and json.load(exc)['code'] == 'invalid_transition'
    # The former VNC transports must not provide a second input/observation path.
    for port in (5900, 6080):
        try:
            connection = socket.create_connection(('127.0.0.1', port), timeout=1)
        except ConnectionRefusedError:
            continue
        else:
            connection.close()
            raise AssertionError(f'Legacy viewer port {port} is still listening')
    after = read_json(STATE)
    assert after['clicks'] == before['clicks'] and after['entry'] == before['entry']
    return {
        'dimensions': [WIDTH, HEIGHT],
        'frameMatchesDesktop': True,
        'inputWithoutHumanOwnershipRejected': True,
        'legacyPortsClosed': [5900, 6080],
    }


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
    return {
        'noDefaultIPv4Route': True,
        'blockedTcpProbes': checked,
        'scope': 'Selected IPv4 probes; not a comprehensive network policy audit',
    }


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
    report = {
        'runId': run_id,
        'sessionId': session['id'],
        'status': 'running',
        'kind': 'native-desktop-calibration',
        'adapter': 'interface_ai.desktop.Desktop',
        'modelCalls': 0,
        'architecture': platform.machine(),
        'display': [WIDTH, HEIGHT],
        'checks': [],
        'python': platform.python_version(),
        'packages': {
            name: importlib.metadata.version(name)
            for name in ('PyAutoGUI', 'Pillow', 'PyScreeze', 'python3-xlib')
        },
        'chromium': subprocess.check_output(['chromium', '--version'], text=True).strip(),
        'systemPackagesSha256': hashlib.sha256(
            Path('/opt/desktop/system-packages.txt').read_bytes()
        ).hexdigest(),
    }

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
        record('same_framebuffer_and_guarded_operator', verify_operator(screen))
        for number, x in [(1, 100), (2, 320), (3, 540)]:
            gui.click(x, 190)
            wait_for(f'click {number}', lambda: len(read_json(STATE)['clicks']) == number, 3)
            actual = read_json(STATE)['clicks'][-1]
            if actual != {'target': number, 'x': x, 'y': 190}:
                raise AssertionError(f'Input coordinates did not match the native event: {actual}')
            wait_for(
                'green target',
                lambda: gui.screenshot().getpixel((x + 5, 195))[:3] == (22, 163, 74),
                3,
            )
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
