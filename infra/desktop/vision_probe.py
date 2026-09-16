"""Manual M1-04 primitive exercise; not a capability artifact or replay interpreter."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import signal
import sys
import time
import uuid

import cv2
import numpy as np
from interface_ai.desktop import Desktop
from interface_ai.vision.bank import BankVision, ENGLISH_SHA256, THRESHOLD, validate_member_id, wait_for_heading
from bootstrap import assert_known_surface
from common import write_json
from control import ready


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--member-id', required=True)
    args = parser.parse_args()
    validate_member_id(args.member_id)  # Before acquiring a controller or any UI input.
    session = ready()
    if session['mode'] != 'bank' or session['inputStopped']:
        raise RuntimeError('Probe requires a fresh bank desktop with input enabled')
    output = Path('/artifacts') / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-vision-'+uuid.uuid4().hex[:8])
    output.mkdir()
    events = []
    report = {'kind': 'manual-visual-primitives-probe', 'sessionId': session['id'],
              'status': 'running', 'modelCalls': 0, 'display': [1280, 800],
              'recognition': {'opencv': cv2.__version__, 'numpy': np.__version__,
                              'englishModelSha256': ENGLISH_SHA256, 'matchThreshold': THRESHOLD,
                              'ocrMinimumConfidence': 80, 'ocrScale': 3, 'ocrPSM': 7},
              'actionsCompleted': 0}
    started = time.monotonic()

    def action_event(event):
        events.append({'kind': 'action', **event})
        if event['status'] == 'completed':
            report['actionsCompleted'] += 1

    def export(image, name):
        # M2: unredacted observations remain in memory. This legacy probe does
        # not have reviewed public-region capture rules.
        report['screenshots'] = 'suppressed'

    try:
        vision = BankVision(event_sink=events.append)
        with Desktop(session['id'], event_sink=action_event) as desktop:
            screen = wait_for_heading(desktop, vision, 'search')
            export(screen, '01-search.png')
            desktop.click(*vision.search_target(screen))
            desktop.type_text(args.member_id)
            desktop.press('enter')
            screen = wait_for_heading(desktop, vision, 'member', timeout=5)
            export(screen, '02-member.png')
            desktop.click(*vision.savings_target(screen, args.member_id))
            screen = wait_for_heading(desktop, vision, 'account')
            export(screen, '03-account.png')
            result = vision.savings_balance(screen, args.member_id)
            write_json(output / 'result.json', result)  # Explicit synthetic result, separate from routine events.
            report['status'] = 'completed'
    except Exception as exc:
        report.update(status='stopped', code=getattr(exc, 'code', 'probe_failed'))
        # Do not persist raw exception text or partial OCR output.
    finally:
        report['elapsedSeconds'] = round(time.monotonic()-started, 3)
        report['eventsSha256'] = hashlib.sha256(json.dumps(events).encode()).hexdigest()
        write_json(output / 'report.json', report)
        (output / 'events.jsonl').write_text(''.join(json.dumps(event)+'\n' for event in events))
        print(json.dumps({'status': report['status'], 'code': report.get('code'), 'evidence': str(output)}))
    return 0 if report['status'] == 'completed' else 1


def timeout(*_):
    raise TimeoutError('Primitive probe deadline exceeded')


if __name__ == '__main__':
    signal.signal(signal.SIGALRM, timeout)
    signal.alarm(45)
    sys.exit(main())
