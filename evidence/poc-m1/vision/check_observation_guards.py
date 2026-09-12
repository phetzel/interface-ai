"""Read-only negative checks using a real capture and the current blocked desktop.

Run after scripts/vision-check (which leaves the blocked scenario visible):
docker compose exec -T desktop python - < this_file.py
Reset bank afterwards: this check deliberately requests stop.
"""
import json
from pathlib import Path
import sys
import threading
import time

from PIL import Image
sys.path.insert(0, '/opt/desktop')
from control import ready
from interface_ai.desktop import Desktop, DesktopError
from interface_ai.desktop.session import request_stop
from interface_ai.vision import VisionError
from interface_ai.vision.bank import BankVision, wait_for_heading

checks = []
captures = sorted(Path('/artifacts').glob('*-vision-*/03-account.png'))
# Find a completed probe using its explicit synthetic result, as harness input only.
source = next(path for path in captures if (path.parent/'result.json').exists())
recorded = json.loads((source.parent/'result.json').read_text())
wrong_id = '00456' if recorded['memberId'] == '00123' else '00123'
vision = BankVision()
with Image.open(source) as screen:
    try:
        vision.savings_balance(screen, wrong_id)
    except VisionError as exc:
        assert exc.code == 'identity_mismatch'
        checks.append({'check': 'wrong_requested_identity_rejected_from_real_capture', 'status': 'passed'})
    else:
        raise AssertionError('Wrong identity was accepted')

session = ready()
assert session['mode'] == 'bank' and not session['inputStopped']
with Desktop(session['id']) as desktop:
    try:
        vision.heading(desktop.screenshot(), 'member')
    except VisionError as exc:
        assert exc.code == 'target_missing'
    else:
        raise AssertionError('Expected the blocked search screen')
    stopper = threading.Timer(.15, request_stop)
    started = time.monotonic()
    stopper.start()
    try:
        try:
            wait_for_heading(desktop, vision, 'member', timeout=5)
        except DesktopError as exc:
            assert exc.code == 'stopped'
        else:
            raise AssertionError('Visual wait ignored stop')
    finally:
        stopper.join(timeout=2)
    elapsed = time.monotonic()-started
    assert elapsed < 1.5
    checks.append({'check': 'operator_stop_interrupts_visual_wait', 'status': 'passed',
                   'elapsedSeconds': round(elapsed, 3)})
print(json.dumps({'status': 'passed', 'actionsDispatched': 0, 'checks': checks}, indent=2))
