"""Preflight locally, then submit replay to the session's single coordinator."""

from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import time
import uuid

from interface_ai.contracts.models import Failure
from interface_ai.desktop.session import STOP, read_session
from interface_ai.handoff.client import replay as run_coordinated
from interface_ai.policy.bank import admit, POLICY_ID
from interface_ai.policy.evidence import safe_code
from .loader import ReplayError, load_bundle, strict_json, validate_inputs

DEFAULT_CAPABILITY = '/opt/capabilities/poc/savings-balance/capability.json'


def replay(args, *, output_root=Path('/artifacts')):
    run_id = (
        datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-replay-' + uuid.uuid4().hex[:8]
    )
    directory = output_root / run_id
    started = time.monotonic()
    report = dict(runId=run_id, modelCalls=0, actionsCompleted=0, phase='preflight')
    try:
        bundle = load_bundle(args.capability)
        try:
            data = (
                strict_json(args.inputs_json)
                if args.inputs_json is not None
                else {'memberId': args.member_id}
            )
        except (ValueError, RecursionError):
            raise ReplayError('invalid_input', 'Input JSON is invalid') from None
        inputs = validate_inputs(data)
        admit(bundle)
        report.update(
            policy=POLICY_ID,
            capability=bundle.capability.name,
            capabilityVersion=bundle.capability.capabilityVersion,
            capabilitySha256=bundle.sha256,
            provenance=bundle.capability.provenance,
            environment=bundle.capability.environment.model_dump(),
        )
        session = read_session()
        if platform.system() != 'Linux' or session['mode'] != 'bank':
            raise ReplayError(
                'unsupported_environment', 'Replay requires the isolated bank desktop'
            )
        report['sessionId'] = session['id']
        if args.session is not None and args.session != session['id']:
            raise ReplayError('stale_session', 'Reset invalidated the requested session')
        report['phase'] = 'execution'
        if STOP.exists():
            raise ReplayError('stopped', 'Reset the desktop before replay')
        # An uncertain transport failure cannot be labeled as zero dispatched input.
        report.update(phase='dispatch', actionsCompleted=None)
        state = run_coordinated(args.capability, inputs.memberId, session['id'])
        result = state['result']
        if not result:
            raise ReplayError('execution_failed', 'Coordinator returned no run outcome')
        print(
            json.dumps(
                dict(
                    status=result['status'],
                    code=result.get('code'),
                    outcome=result.get('outcome'),
                    phase=state['phase'],
                    evidence=str(output_root / state['runId']),
                )
            )
        )
        return 1 if result['status'] == 'failure' else 0
    except Exception as exc:
        result = Failure(code=safe_code(getattr(exc, 'code', 'preflight_failed')))
    report.update(
        status=result.status,
        code=result.code,
        failedStep=result.step,
        elapsedSeconds=round(time.monotonic() - started, 3),
    )
    directory.mkdir(mode=0o700)
    (directory / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    (directory / 'result.json').write_text(result.model_dump_json(indent=2) + '\n')
    (directory / 'events.jsonl').write_text('')
    print(
        json.dumps(
            dict(status=result.status, code=result.code, outcome=None, evidence=str(directory))
        )
    )
    return 1
