"""Fixed-coordinate browser calibration through the shared desktop adapter.

This verifies input/observation plumbing. It does not locate visual anchors, read
balances, return business results, or constitute a reusable capability replay.
"""

import argparse
import importlib.metadata
import json
from pathlib import Path
import platform
import signal
import sys
import time
import uuid
from datetime import datetime, timezone

from PIL import ImageChops
from interface_ai.desktop import Desktop, DesktopError
from bootstrap import assert_known_surface, sandbox_status
from common import write_json
from control import ready
from smoke import verify_network


def changed_pixels(before, after, region):
    difference = ImageChops.difference(before.crop(region), after.crop(region)).convert('L')
    return sum(count for value, count in enumerate(difference.histogram()) if value > 32)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--member-id', choices=['00123', '00456'], default='00123')
    args = parser.parse_args()
    session = ready()
    if session['mode'] != 'bank':
        raise RuntimeError('Browser smoke requires ./scripts/desktop reset bank')
    if session['inputStopped']:
        raise DesktopError('stopped', 'Input stopped; reset before another run')
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-bank-' + uuid.uuid4().hex[:8]
    output = Path('/artifacts') / run_id
    output.mkdir()
    report = {
        'runId': run_id,
        'sessionId': session['id'],
        'kind': 'fixed-coordinate-browser-calibration',
        'adapter': 'interface_ai.desktop.Desktop',
        'status': 'running',
        'modelCalls': 0,
        'businessOutputExtracted': False,
        'display': [1280, 800],
        'architecture': platform.machine(),
        'python': platform.python_version(),
        'packages': {
            name: importlib.metadata.version(name)
            for name in ('PyAutoGUI', 'Pillow', 'python3-xlib')
        },
        'checks': [],
        'events': [],
    }
    started = time.monotonic()

    def record(name, details=None):
        report['checks'].append({'name': name, 'status': 'passed', 'details': details or {}})
        print('PASS ' + name, flush=True)

    def export(desktop, name):
        screen = desktop.screenshot()
        assert_known_surface(screen, 'bank')
        screen.save(output / name)
        return screen

    try:
        with Desktop(
            session['id'], event_sink=report['events'].append, calibration=True
        ) as desktop:
            initial = export(desktop, '01-search.png')
            # A fresh, unshifted search panel has white pixels here; member overview does not.
            if initial.getpixel((120, 350)) != (255, 255, 255):
                raise RuntimeError('Expected a fresh default search screen; reset bank first')
            record('initial_fixture_pixels_and_display')
            sandbox = sandbox_status(session['appPid'])
            if not sandbox:
                raise RuntimeError('No verified sandboxed renderer')
            record('renderer_sandbox_enabled', sandbox)
            desktop.click(240, 493)
            desktop.type_text('replace-me')
            desktop.hotkey('ctrl', 'a')
            desktop.type_text(args.member_id)
            typed = export(desktop, '02-typed.png')
            count = changed_pixels(initial, typed, (145, 478, 325, 508))
            if count < 70:
                raise AssertionError('No substantial text-field pixel change after input')
            record('native_click_type_and_selection', {'changedFieldPixels': count})
            desktop.press('enter')
            desktop.wait(
                'member overview paint',
                lambda: desktop.screenshot().getpixel((120, 350)) == (237, 242, 237),
                timeout=6,
            )
            member = export(desktop, '03-member.png')
            record('native_enter_changes_to_member_view')
            desktop.click(1065, 630)
            desktop.wait(
                'account view paint',
                lambda: changed_pixels(member, desktop.screenshot(), (125, 480, 810, 640)) > 1500,
                timeout=5,
            )
            export(desktop, '04-account.png')
            record('native_click_changes_account_region')
            # Return through the visible fixture breadcrumb, using desktop input.
            desktop.click(161, 175)
            desktop.wait(
                'search view paint',
                lambda: desktop.screenshot().getpixel((120, 350)) == (255, 255, 255),
                timeout=5,
            )
            export(desktop, '05-reset-search.png')
            record('fixture_ui_returns_to_search')
            record('selected_external_egress_blocked', verify_network())
            record('session_preserved', {'sessionId': desktop.id})
            report['status'] = 'passed'
    except Exception as exc:
        report['status'] = 'failed'
        report['error'] = {
            'type': type(exc).__name__,
            'code': getattr(exc, 'code', 'smoke_failed'),
            'message': str(exc),
        }
        raise
    finally:
        report['elapsedSeconds'] = round(time.monotonic() - started, 3)
        write_json(output / 'report.json', report)
        with (output / 'events.jsonl').open('w') as stream:
            for event in report['events']:
                stream.write(json.dumps(event) + '\n')
        print(f'Evidence: {output}', flush=True)


def timeout(*_):
    raise TimeoutError('Browser smoke exceeded its 45-second total deadline')


if __name__ == '__main__':
    signal.signal(signal.SIGALRM, timeout)
    signal.alarm(45)
    try:
        main()
    except Exception as exc:
        print(f'Browser smoke failed: {exc}', file=sys.stderr)
        sys.exit(1)
