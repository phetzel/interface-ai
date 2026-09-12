"""Real adapter guard checks; native pad state is a calibration-only oracle.

Run after reset native, passing a session ID observed before that reset:
docker compose exec -T desktop python - --stale-session OLD_ID < this_file.py
This deliberately leaves input stopped; reset before another run.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import threading
import time

sys.path.insert(0, '/opt/desktop')
from common import STATE, read_json, wait_for, write_json
from control import ready
from interface_ai.desktop import Desktop, DesktopError
from interface_ai.desktop.session import request_stop

parser = argparse.ArgumentParser()
parser.add_argument('--stale-session', required=True)
args = parser.parse_args()
session = ready()
assert session['mode'] == 'native' and not session['inputStopped']
assert args.stale_session != session['id']
initial = read_json(STATE)
assert not initial['entry'] and not initial['clicks']
output = Path('/artifacts') / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-guards')
output.mkdir()
report = {'kind': 'real-desktop-guard-checks', 'status': 'running', 'modelCalls': 0,
          'sessionId': session['id'], 'previousSessionId': args.stale_session, 'checks': []}

def record(name, **details):
    report['checks'].append({'name': name, 'status': 'passed', 'details': details})
    print('PASS ' + name, flush=True)

def cli_reject(code, session_id, action):
    result = subprocess.run([sys.executable, '-m', 'interface_ai.cli', 'action',
                             '--session', session_id, '--json', json.dumps(action)],
                            text=True, capture_output=True, timeout=5)
    assert result.returncode == 1 and json.loads(result.stderr)['code'] == code

def reject(code, operation):
    try:
        operation()
    except DesktopError as exc:
        assert exc.code == code
    else:
        raise AssertionError('Expected rejection: ' + code)

try:
    cli_reject('invalid_action', session['id'], {'type': 'click', 'x': -1, 'y': 190})
    cli_reject('stale_session', args.stale_session, {'type': 'click', 'x': 100, 'y': 190})
    assert read_json(STATE) == initial
    record('invalid_and_previous_session_cli_requests_do_not_mutate_pad')
    with Desktop(session['id']) as desktop:
        cli_reject('busy', session['id'], {'type': 'click', 'x': 100, 'y': 190})
        assert read_json(STATE) == initial
        record('second_process_rejected_while_controller_holds_lock')
        desktop.click(180, 405)
        stop_errors = []
        def stop_after_input_arrives():
            try:
                wait_for('first native character', lambda: bool(read_json(STATE)['entry']), 3)
                request_stop()
            except Exception as exc:
                stop_errors.append(str(exc))
        stopper = threading.Thread(target=stop_after_input_arrives)
        stopper.start()
        try:
            reject('stopped', lambda: desktop.type_text('x' * 256))
        finally:
            stopper.join(timeout=4)
        assert not stopper.is_alive() and not stop_errors
        time.sleep(.15)  # Let the independent native oracle publish dispatched keys.
        count = len(read_json(STATE)['entry'])
        assert 0 < count < 256
        record('stop_interrupts_real_typing', charactersDelivered=count, requestedCount=256)
        reject('stopped', lambda: desktop.click(100, 190))
        time.sleep(.15)
        assert len(read_json(STATE)['entry']) == count and not read_json(STATE)['clicks']
        record('no_further_input_after_stop')
        assert desktop.screenshot().size == (1280, 800)
        record('in_memory_screenshot_available_after_stop')
    with Desktop(session['id']) as observer:
        assert observer.screenshot().size == (1280, 800)
        reject('stopped', lambda: observer.press('enter'))
    record('lock_released_but_stop_persists_for_next_controller')
    report['status'] = 'passed'
except Exception as exc:
    report['status'] = 'failed'
    report['error'] = {'type': type(exc).__name__, 'message': str(exc)}
    raise
finally:
    write_json(output / 'report.json', report)
    print('Evidence: ' + str(output), flush=True)
