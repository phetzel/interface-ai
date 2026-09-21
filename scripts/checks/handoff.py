#!/usr/bin/env python3
"""Live simulated-operator acceptance. No model, DOM, or hidden app-state reads.

Fixture/reset/oracle access belongs only to this trusted host test harness.
OS actions go through the operator HTTP API; evidence labels that provenance.
"""

from datetime import datetime, timezone
import json
import argparse
import shutil
import time
import uuid

from lib.acceptance import source_hashes, command as run_command
from lib.builds import retain_builds, verify_running
from lib.capabilities import IDS, selected

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--capability', choices=IDS, default='discovered-savings')
args = parser.parse_args()
_, capability, approval = selected(args.capability)
continuation = approval['continuation']
from lib.acceptance import ROOT

BASE = 'http://127.0.0.1:6081'
OUTPUT = (
    ROOT
    / 'tmp/handoff-checks'
    / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8])
)
OUTPUT.mkdir(parents=True)
summary = {
    'status': 'running',
    'approvalId': args.capability,
    'capabilitySha256': approval['capabilitySha256'],
    'operatorProvenance': 'automated-test-through-operator-api',
    'modelCalls': 0,
    'realHumanWitnessed': False,
    'cases': [],
}


def command(name, args, *, stdin=None, expected=0):
    result = run_command(args, script=stdin, directory=OUTPUT, name=name, timeout=240)
    assert result.returncode == expected, name
    return result.stdout


from lib.operator import Operator


def sources():
    return source_hashes()


def scenario(member, negative):
    label = 'member-a-adversarial' if negative else 'member-b'
    command(label + '-reset', ['./scripts/desktop', 'reset', 'bank', 'expired'])
    verify_running(OUTPUT)
    operator = Operator()
    initial = operator.status()
    launch = json.loads(
        command(
            label + '-start',
            [
                './scripts/desktop',
                'replay',
                '--capability',
                args.capability,
                '--member-id',
                member,
                '--pause-for-human',
            ],
        )
    )
    assert launch['phase'] == 'awaiting_human' and launch['code'] == 'intervention_required'
    paused = operator.wait('awaiting_human')
    assert (
        paused['step'] == continuation['interruptedStep']
        and paused['reason'] == 'intervention_required'
    )
    assert paused['session'] == initial['session'] and paused['resumable']
    assert paused['owner'] == 'quiescing' and paused['epoch'] > initial['epoch']
    assert operator.post('/resume', expected=409)['code'] == 'invalid_transition'
    human = operator.post('/takeover')
    assert human['owner'] == 'human' and human['session'] == initial['session']
    human_lease = operator.lease(human)
    assert operator.post('/resume', expected=409)['code'] == 'resume_rejected'
    probe = """import json,sys
from interface_ai.desktop import Desktop,DesktopError
events=[]
try:
 with Desktop(sys.argv[1],epoch=int(sys.argv[2]),event_sink=events.append) as desktop:
  desktop.click(600,390)
except DesktopError as exc:
 assert exc.code=='ownership_revoked',exc.code
else: raise AssertionError('Automation input was accepted')
assert not any(e['status']=='completed' for e in events)
print(json.dumps({'staleAutomationRejected':True,'completedInputs':0}))
"""
    command(
        label + '-late-automation',
        [
            'docker',
            'compose',
            'exec',
            '-T',
            'desktop',
            'python',
            '-',
            initial['session'],
            str(initial['epoch']),
        ],
        stdin=probe,
    )
    operator.click(600, 390)
    if negative:
        seq = operator.status()['sequence']
        operator.type('SECRET-SENTINEL-84729')
        assert (
            operator.post(
                '/action',
                expected=409,
                sequence=seq,
                action={'type': 'type', 'text': 'SECRET-SENTINEL-84729'},
            )['code']
            == 'invalid_transition'
        )
        operator.action({'type': 'hotkey', 'keys': ['ctrl', 'a']})
    operator.type('demo')
    operator.click(640, 450)
    time.sleep(0.4)
    if negative:
        # Human deliberately returns on the search page, then the wrong member.
        operator.click(142, 174)
        assert operator.post('/resume', expected=409)['code'] == 'resume_rejected'
        operator.click(350, 477)
        operator.type('00456')
        operator.press('enter')
        time.sleep(0.4)
        assert operator.post('/resume', expected=409)['code'] == 'resume_rejected'
        operator.click(142, 174)
        operator.click(350, 477)
        operator.type(member)
        operator.press('enter')
        time.sleep(0.4)
    operator.post('/resume')
    assert (
        operator.post(
            '/action',
            expected=409,
            lease=human_lease,
            sequence=operator.status()['sequence'],
            action={'type': 'click', 'x': 600, 'y': 390},
        )['code']
        == 'ownership_revoked'
    )
    final = operator.wait('success')
    assert (
        final['step'] == capability['steps'][-1]['id']
        and final['lastCheckpoint'] == 'account-ready'
    )
    assert final['session'] == initial['session'] and final['epoch'] > human['epoch']
    directory = ROOT / 'tmp/desktop-artifacts' / final['runId']
    result = json.loads((directory / 'result.json').read_text())
    expected = next(
        item
        for item in json.loads((ROOT / 'apps/bank-fixture/tests/oracle.json').read_text())[
            'successes'
        ]
        if item['memberId'] == member
    )
    for field in ('memberId', 'memberName', 'accountType', 'currency', 'amountMinor'):
        assert result['output'][field] == expected[field], field
    audit = (directory / 'audit.jsonl').read_text()
    for prohibited in (
        'SECRET-SENTINEL-84729',
        'demo',
        '00456',
        '00123',
        '"text"',
        '"keys"',
        '"x"',
        '"y"',
    ):
        assert prohibited not in audit, 'Sensitive action data in audit'
    events = [json.loads(line) for line in audit.splitlines()]
    trace = [e['event'] for e in events if e['kind'] == 'interpreter']
    assert {'step', 'target', 'checkpoint', 'reading'} <= {e['kind'] for e in trace}
    assert any(e.get('code') == 'intervention_required' for e in trace)
    assert any(
        e.get('checkpoint') == 'member-ready' and e['status'] == 'unsatisfied' for e in trace
    )
    human_sequences = [e['sequence'] for e in events if e['kind'] == 'human']
    assert human_sequences == list(range(1, len(human_sequences) + 1))
    handoff = next(
        i for i, e in enumerate(events) if e['kind'] == 'lifecycle' and e['status'] == 'human'
    )
    resumed = next(
        i for i, e in enumerate(events) if e['kind'] == 'lifecycle' and e['status'] == 'resumed'
    )
    assert not any(e['kind'] == 'automation' for e in events[handoff + 1 : resumed])
    assert [
        e['action'] for e in events if e['kind'] == 'automation' and e['status'] == 'completed'
    ] == [s['action'] for s in capability['steps'][:-1]]
    safe = OUTPUT / label
    safe.mkdir()
    for name in ('audit.jsonl', 'summary.json', 'events.jsonl', 'report.json', 'result.json'):
        shutil.copyfile(directory / name, safe / name)
    summary['cases'].append(
        {
            'case': label,
            'status': 'passed',
            'sameSession': True,
            'exactOracleMatch': True,
            'noRepeatedAutomationInput': True,
            'noAutomationDuringHuman': True,
            'sanitizedInterpreterTrace': True,
            'operatorStepContext': True,
            'sensitiveValuesAbsent': True,
            'wrongScreenAndMemberRejected': negative,
        }
    )
    print(label + ': passed', flush=True)


try:
    retain_builds(OUTPUT)
    frozen = sources()
    (OUTPUT / 'source-sha256.json').write_text(json.dumps(frozen, indent=2) + '\n')
    scenario('00123', True)
    scenario('00456', False)
    assert sources() == frozen, 'Executable source changed during acceptance'
    summary['status'] = 'passed'
except Exception as exc:
    summary['status'] = 'failed'
    summary['failure'] = str(exc)
    raise
finally:
    (OUTPUT / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print('Evidence: ' + str(OUTPUT), flush=True)
