#!/usr/bin/env python3
"""Live CLI/panel coordination proof; simulated operator, no model calls."""

import json, subprocess, time
from lib.operator import Operator
from pathlib import Path
from lib.acceptance import ROOT as root, attempt, source_hashes
from lib.builds import retain_builds, verify_running

directory = attempt('lifecycle-checks')
retain_builds(directory)
frozen = source_hashes()
(directory / 'source-manifest.json').write_text(json.dumps(frozen, indent=2) + '\n')
base = 'http://127.0.0.1:6081'
checks = []


def reset(scenario):
    subprocess.run(
        ['./scripts/desktop', 'reset', 'bank', scenario], cwd=root, check=True, capture_output=True
    )
    verify_running(directory)
    return Operator()


def get(operator):
    return operator.status()


def post(operator, path, state, extra=None, status=200):
    return operator.post(path, lease=operator.lease(state), expected=status, **(extra or {}))


for scenario in ['expired', 'blocked']:
    h = reset(scenario)
    proc = subprocess.Popen(
        ['./scripts/desktop', 'replay', '--member-id', '00123'],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    deadline = time.monotonic() + 45
    saw_running = False
    while time.monotonic() < deadline:
        s = get(h)
        if s and s['phase'] == 'running':
            saw_running = True
            assert s['runKind'] == 'replay' and s['runId']
            assert post(h, '/start', s, {'memberId': '00456'}, 409)['code'] == 'invalid_transition'
            if scenario == 'blocked':
                stopped = post(h, '/stop', s)
                assert stopped['phase'] == 'stopped'
                break
        if s and s['phase'] == 'awaiting_human':
            break
        time.sleep(0.1)
    assert saw_running
    stdout, stderr = proc.communicate(timeout=30)
    assert proc.returncode == 1, (stdout, stderr)
    reply = json.loads(stdout.splitlines()[-1])
    evidence = root / 'tmp/desktop-artifacts' / Path(reply['evidence']).name
    report = json.loads((evidence / 'report.json').read_text())
    assert report['modelCalls'] == 0 and report['status'] == 'failure'
    if scenario == 'expired':
        assert s['reason'] == 'intervention_required' and s['resumable']
        human = post(h, '/takeover', s)
        assert human['owner'] == 'human'
        assert post(h, '/resume', human, status=409)['code'] == 'resume_rejected'
        post(h, '/stop', human)
    else:
        assert report['code'] == 'stopped'
    checks.append(
        {
            'scenario': scenario,
            'cliVisibleInPanel': True,
            'competingStartRejected': True,
            'panelControlPassed': True,
            'evidence': evidence.name,
        }
    )
assert source_hashes() == frozen
output = directory / 'summary.json'
output.write_text(
    json.dumps(
        {
            'status': 'passed',
            'provenance': 'automated-cli-and-operator-api',
            'realHumanWitnessed': False,
            'checks': checks,
        },
        indent=2,
    )
    + '\n'
)
print('PASS CLI lifecycle')
print('Evidence: ' + str(directory))
