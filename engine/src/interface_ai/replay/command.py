"""Operator command: preflight before desktop acquisition; data-free routine events."""

from datetime import datetime, timezone
import importlib.metadata
import json
from pathlib import Path
import platform
import time
import uuid

from interface_ai.contracts.models import Failure
from interface_ai.desktop import Desktop
from interface_ai.desktop.session import read_session
from interface_ai.policy.bank import admit, POLICY_ID
from interface_ai.policy.evidence import checked_event, safe_code
from .interpreter import Interpreter
from .loader import ReplayError, load_bundle, strict_json, validate_inputs

DEFAULT_CAPABILITY = '/opt/capabilities/poc/savings-balance/capability.json'


def replay(args, *, output_root=Path('/artifacts')):
    run_id = (
        datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-replay-' + uuid.uuid4().hex[:8]
    )
    directory = output_root / run_id
    directory.mkdir()
    events = []
    started = time.monotonic()
    report = {
        'runId': run_id,
        'modelCalls': 0,
        'actionsCompleted': 0,
        'phase': 'preflight',
        'packages': {
            name: importlib.metadata.version(name)
            for name in ['pydantic', 'opencv-python-headless', 'numpy', 'Pillow']
        },
    }
    interpreter = None

    def record(event):
        events.append(
            checked_event({'elapsedMs': round((time.monotonic() - started) * 1000, 3), **event})
        )

    def action_event(event):
        record(
            {
                'kind': 'action',
                'step': interpreter.step.id if interpreter and interpreter.step else None,
                **event,
            }
        )
        if event['status'] == 'completed':
            report['actionsCompleted'] += 1

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
        admit(bundle)  # A valid schema does not authorize its instructions or metadata.
        report['policy'] = POLICY_ID
        report.update(
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
        with Desktop(
            args.session if args.session is not None else session['id'],
            timeout=bundle.capability.environment.totalTimeoutSeconds,
            event_sink=action_event,
        ) as desktop:
            interpreter = Interpreter(bundle, inputs, desktop, event_sink=record)
            report['phase'] = 'execution'
            result = interpreter.run()
    except Exception as exc:
        result = Failure(code=safe_code(getattr(exc, 'code', 'preflight_failed')))
    report.update(status=result.status, elapsedSeconds=round(time.monotonic() - started, 3))
    if isinstance(result, Failure):
        report.update(code=result.code, failedStep=result.step)
    (directory / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    (directory / 'result.json').write_text(result.model_dump_json(indent=2) + '\n')
    (directory / 'events.jsonl').write_text(''.join(json.dumps(event) + '\n' for event in events))
    print(
        json.dumps(
            {
                'status': result.status,
                'code': getattr(result, 'code', None),
                'outcome': getattr(result, 'outcome', None),
                'evidence': str(directory),
            }
        )
    )
    return 1 if isinstance(result, Failure) else 0
