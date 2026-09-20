"""The same sanitized replay trace for CLI and operator execution."""

import importlib.metadata
import json
import time

from interface_ai.policy.bank import POLICY_ID
from interface_ai.policy.evidence import checked_event
from .evidence import atomic_write


def write_replay(controller, result):
    bundle = controller.bundle
    events = []
    for entry in controller.audit:
        if entry['kind'] == 'interpreter':
            events.append(checked_event(entry['event'], controller.admission.allowed_ids))
        elif entry['kind'] == 'automation':
            events.append(
                checked_event(
                    {
                        'kind': 'action',
                        **{k: v for k, v in entry.items() if k not in ('kind', 'elapsedMs')},
                    },
                    controller.admission.allowed_ids,
                )
            )
    report = dict(
        runId=controller.directory.name,
        modelCalls=0,
        phase='execution',
        actionsCompleted=sum(
            e.get('kind') == 'action' and e.get('status') == 'completed' for e in events
        ),
        status=result.status,
        policy=POLICY_ID,
        capability=bundle.capability.name,
        capabilityVersion=bundle.capability.capabilityVersion,
        capabilitySha256=bundle.sha256,
        provenance=bundle.capability.model_dump()['provenance'],
        admission=controller.admission.scope,
        approvalId=controller.admission.approval_id,
        environment=bundle.capability.environment.model_dump(),
        sessionId=controller.session['id'],
        elapsedSeconds=round(time.monotonic() - controller.started, 3),
        packages={
            name: importlib.metadata.version(name)
            for name in ['pydantic', 'opencv-python-headless', 'numpy', 'Pillow']
        },
    )
    if result.status == 'failure':
        report.update(code=result.code, failedStep=result.step)
    atomic_write(
        controller.directory / 'events.jsonl',
        ''.join(json.dumps(e) + '\n' for e in events).encode(),
    )
    atomic_write(
        controller.directory / 'result.json', (result.model_dump_json(indent=2) + '\n').encode()
    )
    atomic_write(
        controller.directory / 'report.json', (json.dumps(report, indent=2) + '\n').encode()
    )
