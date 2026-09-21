#!/usr/bin/env python3
"""Host-only M1-05 integration checks; no oracle enters the interpreter."""

from datetime import datetime, timezone
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import uuid

from lib.builds import retain_builds, verify_running
from lib.capabilities import IDS, selected

from lib.acceptance import ROOT

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument(
    '--acceptance',
    action='store_true',
    help='Run ten alternating clean-reset baselines and seven scenario checks for M1-06',
)
parser.add_argument('--capability', choices=IDS, default='discovered-savings')
args = parser.parse_args()
capability_path, capability, approval = selected(args.capability)
continuation = approval['continuation']
input_count = len(capability['steps']) - 1
account_step = continuation['nextStep']
extract_step = capability['steps'][-1]['id']
search_step = continuation['interruptedStep']
OUTPUT = (
    ROOT
    / 'tmp/replay-checks'
    / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8])
)
OUTPUT.mkdir(parents=True)
oracle = json.loads((ROOT / 'apps/bank-fixture/tests/oracle.json').read_text())
artifact_hash = hashlib.sha256(capability_path.read_bytes()).hexdigest()
cases = [
    ('baseline-a', 'default', 0, None),
    ('baseline-b', 'default', 1, None),
    ('missing', 'default', None, 'member_not_found'),
    ('translated-a', 'translated', 0, None),
    ('translated-b', 'translated', 1, None),
    ('delayed-a', 'delayed', 0, None),
    ('duplicate-a', 'duplicate', 0, 'ambiguous_target'),
    ('unreadable-a', 'unreadable', 0, 'ocr_uncertain'),
    ('blocked-a', 'blocked', 0, 'checkpoint_timeout'),
]
if args.capability == 'discovered-savings':
    cases.extend([('iframe-a', 'iframe', 0, None), ('iframe-b', 'iframe', 1, None)])
if args.acceptance:
    cases = [(f'baseline-{i + 1:02d}', 'default', i % 2, None) for i in range(10)] + cases[2:]
summary = {
    'kind': 'generated-replay'
    if args.capability == 'discovered-savings'
    else ('repeated-manual-replay' if args.acceptance else 'manual-replay'),
    'approvalId': args.capability,
    'status': 'running',
    'capabilitySha256': artifact_hash,
    'oracleSha256': hashlib.sha256(
        (ROOT / 'apps/bank-fixture/tests/oracle.json').read_bytes()
    ).hexdigest(),
    'scope': 'Ten alternating clean-reset baselines plus seven scenarios'
    if args.acceptance
    else 'One pass per integration case',
    'cases': [],
}
sessions = set()
event_keys = {
    'elapsedMs',
    'kind',
    'step',
    'action',
    'status',
    'target',
    'score',
    'candidateCount',
    'box',
    'sequence',
    'durationMs',
    'code',
    'checkpoint',
    'field',
    'confidence',
}


def run(args, **kwargs):
    return subprocess.run(args, cwd=ROOT, timeout=180, **kwargs)


try:
    retain_builds(OUTPUT)
    for name, scenario, index, expected in cases:
        item = {'case': name, 'scenario': scenario, 'status': 'running'}
        summary['cases'].append(item)
        try:
            assert hashlib.sha256(capability_path.read_bytes()).hexdigest() == artifact_hash
            with (OUTPUT / (name + '-startup.log')).open('w') as log:
                run(
                    ['./scripts/desktop', 'reset', 'bank', scenario],
                    stdout=log,
                    stderr=log,
                    check=True,
                )
            verify_running(OUTPUT)
            member_id = (
                oracle['missing']['memberId']
                if index is None
                else oracle['successes'][index]['memberId']
            )
            response = run(
                [
                    './scripts/desktop',
                    'replay',
                    '--capability',
                    args.capability,
                    '--member-id',
                    member_id,
                ],
                capture_output=True,
                text=True,
            )
            (OUTPUT / (name + '-command.log')).write_text(response.stdout + response.stderr)
            response_json = json.loads(response.stdout)
            relative = Path(response_json['evidence']).relative_to('/artifacts')
            directory = ROOT / 'tmp/desktop-artifacts' / relative
            retained = OUTPUT / 'cases' / name
            retained.mkdir(parents=True)
            for filename in ['report.json', 'result.json', 'events.jsonl']:
                shutil.copy2(directory / filename, retained / filename)
            report = json.loads((directory / 'report.json').read_text())
            result = json.loads((directory / 'result.json').read_text())
            events = [
                json.loads(line) for line in (directory / 'events.jsonl').read_text().splitlines()
            ]
            assert all(set(event) <= event_keys for event in events)
            assert not any(
                p.suffix.lower() in ('.png', '.jpg', '.jpeg') for p in directory.iterdir()
            )
            assert report['sessionId'] not in sessions
            sessions.add(report['sessionId'])
            assert report['capabilitySha256'] == artifact_hash
            assert report['modelCalls'] == 0
            assert report['provenance'] == capability['provenance']
            item.update(
                evidence=str(retained.relative_to(OUTPUT)),
                rawEvidence=str(directory.relative_to(ROOT)),
                sessionId=report['sessionId'],
                observedStatus=result['status'],
                code=result.get('code'),
                outcome=result.get('outcome'),
                failedStep=result.get('step'),
                actionsCompleted=report['actionsCompleted'],
                elapsedSeconds=report['elapsedSeconds'],
                sanitizedEvents=len(events),
                screenshotsPersisted=0,
            )
            if expected is None:
                assert response.returncode == 0 and result['status'] == 'success'
                wanted = oracle['successes'][index]
                assert result['output'] == {
                    key: wanted[key]
                    for key in ['memberId', 'memberName', 'accountType', 'currency', 'amountMinor']
                }
                assert report['actionsCompleted'] == input_count
                item['exactOracleMatch'] = True
            elif expected == 'member_not_found':
                assert response.returncode == 0 and result == {
                    'status': 'business_outcome',
                    'outcome': expected,
                }
                assert report['actionsCompleted'] == input_count - 1
                assert not any(e['step'] in (account_step, extract_step) for e in events)
                item['noAccountClickOrExtraction'] = True
            else:
                assert (
                    response.returncode == 1
                    and result['status'] == 'failure'
                    and result['code'] == expected
                )
                assert 'output' not in result and report['actionsCompleted'] == (
                    input_count if scenario == 'unreadable' else input_count - 1
                )
                expected_step = {
                    'duplicate': account_step,
                    'unreadable': extract_step,
                    'blocked': search_step,
                }[scenario]
                assert result['step'] == expected_step and result['expected']
                assert events[-1]['status'] == 'failed' and events[-1]['code'] == expected
                item['noResultOrSubsequentAction'] = True
            item['status'] = 'passed'
        except Exception as exc:
            item.update(status='failed', error=type(exc).__name__)
        finally:
            print(item['status'].upper() + ' ' + name, flush=True)
            (OUTPUT / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    summary['uniqueSessions'] = len(sessions)
    summary['status'] = (
        'passed' if all(c['status'] == 'passed' for c in summary['cases']) else 'failed'
    )
finally:
    (OUTPUT / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print('Evidence: ' + str(OUTPUT), flush=True)
sys.exit(0 if summary['status'] == 'passed' else 1)
