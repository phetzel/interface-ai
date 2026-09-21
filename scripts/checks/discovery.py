#!/usr/bin/env python3
"""Offline transport integration: fixed fake provider, real HTTP and guarded X11 input."""

import json
import sys
from types import SimpleNamespace

from lib.acceptance import ROOT, attempt, command, source_hashes, write_json
from lib.builds import retain_builds, verify_running
from lib.discovery import ProbeError, Transport, bootstrap, new_report, run_flow

ACTION = {'type': 'click', 'button': 'left', 'x': 400, 'y': 490}


class FakeClient:
    """Coordinates are a test fixture. This is never model/discovery evidence."""

    def __init__(self, *, initial_screenshot=False):
        self.responses = self
        self.count = 0
        self.initial_screenshot = initial_screenshot

    def create(self, **kwargs):
        self.count += 1
        value = {
            'id': 'offline_response_' + str(self.count),
            'model': 'offline-fixture',
            'status': 'completed',
            'output': (
                [{'type': 'computer_call', 'call_id': 'offline_call', 'actions': [ACTION]}]
                if self.count == 1 + int(self.initial_screenshot)
                else [{'type': 'message', 'content': []}]
            ),
        }
        if self.initial_screenshot and self.count == 1:
            value['output'] = [
                {
                    'type': 'computer_call',
                    'call_id': 'offline_screenshot',
                    'actions': [{'type': 'screenshot'}],
                }
            ]
        return SimpleNamespace(model_dump=lambda **_: value)


def main():
    directory = attempt('discovery-checks')
    summary = dict(
        status='running', provenance='simulated-provider-real-desktop', modelCalls=0, checks=[]
    )
    hashes = source_hashes()
    write_json(directory / 'source-manifest.json', hashes)

    def save():
        write_json(directory / 'summary.json', summary)

    def reset(name):
        result = command(
            ['./scripts/desktop', 'reset', 'bank', 'default'],
            directory=directory,
            name=name + '-reset',
        )
        if result.returncode:
            raise ProbeError('reset_failed')
        verify_running(directory)
        return Transport(bootstrap())

    def passed(name):
        summary['checks'].append(name)
        save()
        print('PASS ' + name, flush=True)

    def rejects(name, data, *, before=None, expected):
        transport = reset(name)
        frame = transport.post('start', {'session': transport.session})
        if before:
            before(transport, frame)
        try:
            transport.post('action', dict(lease=frame['lease'], action=data))
        except ProbeError as exc:
            if exc.code not in expected:
                raise
        else:
            raise ProbeError('rejection_missing')
        # The worker's terminal evidence must prove rejected input was not sent.
        records = list(
            (ROOT / 'tmp/desktop-artifacts').glob('*-probe-' + frame['lease']['runId'][:8])
        )
        report = json.loads((records[0] / 'summary.json').read_text())
        expected_actions = 1 if name == 'duplicate-proposal' else 0
        if report['actionsCompleted'] != expected_actions or report['status'] != 'failed':
            raise ProbeError('unexpected_dispatch')
        write_json(directory / (name + '.json'), report)
        passed(name)

    try:
        retain_builds(directory)
        transport = reset('round-trip')
        report = new_report('simulated-provider-real-desktop')
        report['modelCalls'] = 0
        run_flow(
            FakeClient(),
            transport,
            report,
            lambda: write_json(directory / 'round-trip.json', report),
        )
        passed('single-click-and-stateless-tool-output')
        transport = reset('initial-screenshot')
        report = new_report('simulated-provider-real-desktop')
        report['modelCalls'] = 0
        run_flow(
            FakeClient(initial_screenshot=True),
            transport,
            report,
            lambda: write_json(directory / 'initial-screenshot.json', report),
        )
        if report['requestsAttempted'] != 3 or not report['initialScreenshotRequested']:
            raise ProbeError('unexpected_protocol')
        passed('initial-screenshot-then-single-click')
        rejects('unrelated-control', dict(ACTION, x=740), expected={'policy_operation_denied'})
        rejects(
            'unsupported-input',
            {'type': 'type', 'text': 'DO-NOT-DISPATCH'},
            expected={'invalid_action'},
        )
        rejects(
            'duplicate-proposal',
            ACTION,
            before=lambda t, f: t.post('action', {'lease': f['lease'], 'action': ACTION}),
            expected={'ownership_revoked'},
        )

        def stop(_transport, _frame):
            result = command(['./scripts/desktop', 'stop-input'], directory=directory, name='stop')
            if result.returncode:
                raise ProbeError('stop_failed')

        rejects(
            'late-response-after-stop',
            ACTION,
            before=stop,
            expected={'ownership_revoked', 'stopped', 'invalid_transition'},
        )
        if hashes != source_hashes():
            raise ProbeError('source_changed')
        summary['status'] = 'passed'
    except Exception as exc:
        summary.update(
            status='failed', code=exc.code if isinstance(exc, ProbeError) else 'check_failed'
        )
        raise
    finally:
        save()
        print('Evidence: ' + str(directory), flush=True)


if __name__ == '__main__':
    sys.exit(main())
