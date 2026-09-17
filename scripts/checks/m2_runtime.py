"""Trusted adversarial harness. Never imported by discovery or replay.

Uses privileged fixture/browser setup only to challenge enforcement, not to
complete a banking task. Observations and OCR stay in memory; report is booleans.
"""

import io
import json
from pathlib import Path
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request

from PIL import ImageChops
from interface_ai.desktop import Desktop, DesktopError
from interface_ai.desktop.backend import X11Backend
from interface_ai.desktop.session import read_session

report = {'status': 'running', 'checks': [], 'modelCalls': 0, 'screenshotsPersisted': 0}


def passed(name, **details):
    report['checks'].append({'name': name, 'status': 'passed', **details})


def screen_text(backend):
    buffer = io.BytesIO()
    backend.screenshot().save(buffer, format='PNG')
    result = subprocess.run(
        ['tesseract', 'stdin', 'stdout', '--psm', '6'],
        input=buffer.getvalue(),
        capture_output=True,
        timeout=3,
        check=True,
    )
    return result.stdout.decode().lower()


def wait(predicate, seconds=6):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.1)
    raise AssertionError('Expected bounded observation was not established')


try:
    # Network requests are adversarial harness probes, never task data retrieval.
    for path in ('/', '/fixture-config.json', '/healthz'):
        with urllib.request.urlopen('http://fixture:4173' + path, timeout=3) as response:
            assert response.status == 200
            if path == '/fixture-config.json':
                assert json.load(response)['policyProbe'] is True
    passed('gateway_permits_fixture_resources')
    denied = 0
    for method, path in [
        ('GET', '/transfer'),
        ('POST', '/'),
        ('GET', '/?secret=SECRET-SENTINEL-84729'),
        ('GET', '/%2e%2e/'),
        ('GET', '/assets/../index.html'),
    ]:
        try:
            urllib.request.urlopen(
                urllib.request.Request('http://fixture:4173' + path, method=method), timeout=3
            )
            raise AssertionError('Forbidden request reached an allowed response')
        except urllib.error.HTTPError as error:
            assert error.code == 403
            assert json.load(error) == {'code': 'policy_destination_denied'}
            denied += 1
    passed('gateway_rejects_forbidden_requests', denied=denied)
    try:
        socket.getaddrinfo('fixture-origin', 4173)
        raise AssertionError('Origin resolves on the desktop network')
    except socket.gaierror:
        passed('origin_name_is_not_on_desktop_network')
    assert not any(
        line.split()[1] == '00000000'
        for line in Path('/proc/net/route').read_text().splitlines()[1:]
    )
    passed('desktop_has_no_default_ipv4_route')

    events = []
    session = read_session()
    backend = X11Backend()
    with Desktop(session['id'], backend=backend, event_sink=events.append) as desktop:
        assert backend.application_matches(session)
        wait(lambda: 'no transfer requested' in screen_text(backend))
        before = desktop.screenshot().crop((946, 730, 1220, 755))
        for action in (
            {'type': 'click', 'x': 1070, 'y': 710},
            {'type': 'hotkey', 'keys': ['ctrl', 'l']},
            {'type': 'type', 'text': 'SECRET-SENTINEL-84729'},
            {'type': 'press', 'key': 'tab'},
        ):
            try:
                desktop.execute(action)
                raise AssertionError('Forbidden operation was dispatched')
            except DesktopError as error:
                assert error.code == 'policy_operation_denied'
        assert all(e['status'] == 'rejected' for e in events)
        assert (
            ImageChops.difference(
                before, desktop.screenshot().crop((946, 730, 1220, 755))
            ).getbbox()
            is None
        )
        passed(
            'visible_risky_control_and_page_instruction_rejected',
            denied=len(events),
            inputActionsCompleted=0,
        )

        other = subprocess.Popen(
            [
                sys.executable,
                '-c',
                'import tkinter as t; r=t.Tk(); r.title("Unapproved application"); r.geometry("300x150+400+300"); r.attributes("-topmost",True); r.after(100,r.focus_force); r.mainloop()',
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            wait(lambda: backend.active_window() != session['windowId'])
            try:
                desktop.click(246, 490)
                raise AssertionError('Unexpected application accepted input')
            except DesktopError as error:
                assert error.code == 'unexpected_focus'
                passed('unexpected_application_rejected', inputActionsCompleted=0)
        finally:
            other.terminate()
            other.wait(timeout=3)
        wait(lambda: backend.active_window() == session['windowId'])

    # Prove the control is functional. This explicit calibration override lives
    # only in the trusted harness; model actions/CLI JSON have no such option.
    with Desktop(session['id'], calibration=True) as calibration:
        calibration.click(1070, 710)
        wait(
            lambda: 'no transfer requested' not in screen_text(calibration.backend)
            and 'transfer requested' in screen_text(calibration.backend)
        )
    passed('synthetic_risky_control_is_functional_in_calibration')

    captures = set(Path('/artifacts').rglob('*.png'))
    capture = subprocess.run(
        [sys.executable, '/opt/desktop/control.py', 'screenshot'], capture_output=True, timeout=5
    )
    assert capture.returncode == 1 and set(Path('/artifacts').rglob('*.png')) == captures
    passed('raw_capture_suppressed_before_persistence')

    # Test real managed Chromium, not only policy-file existence. Direct browser
    # launch is trusted test setup, unavailable to structured runtime actions.
    policy = Path('/etc/chromium/policies/managed/interface-ai.json')
    assert policy.stat().st_uid == 0 and not policy.stat().st_mode & 0o022
    assert json.loads(policy.read_text())['URLBlocklist'] == ['*']
    observer = X11Backend()
    try:
        for name, url in [('external', 'http://example.com/'), ('file', 'file:///etc/passwd')]:
            previous_window = observer.active_window()
            subprocess.run(
                [
                    'chromium',
                    '--user-data-dir=/tmp/interface-ai/chromium-profile',
                    '--new-window',
                    url,
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=5,
                check=True,
            )
            wait(lambda: observer.active_window() != previous_window)

            def blocked_screen():
                text = screen_text(observer)
                return all(token in text for token in ('blocked', 'organization', 'allow'))

            wait(blocked_screen)
            passed('chromium_' + name + '_navigation_blocked')
    finally:
        observer.close()
    report['status'] = 'passed'
except Exception as error:
    report.update(status='failed', errorType=type(error).__name__)
finally:
    print(json.dumps(report))
sys.exit(0 if report['status'] == 'passed' else 1)
