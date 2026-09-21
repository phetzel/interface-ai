"""Closed routine events and a reconstructive export, never recursive copying."""

import json
import math
from pathlib import Path

from interface_ai.desktop.adapter import DesktopError
from interface_ai.files import read_regular
from interface_ai.replay.loader import strict_json
from .admission import approval_for_digest, read_approval, APPROVALS, RECOGNITION_PROFILE_ID
from interface_ai.contracts.approval import POLICY_ID

CODES = frozenset(
    """busy checkpoint_timeout deadline display_changed input_failed
invalid_action invalid_deadline not_acquired session_unavailable stale_session
stopped unexpected_focus policy_application_denied policy_artifact_denied
policy_operation_denied policy_surface_denied policy_capture_denied ambiguous_checkpoint identity_mismatch
invalid_identity precondition_failed unsupported_environment invalid_asset
invalid_capability invalid_input invalid_amount invalid_anchor invalid_region
invalid_threshold target_missing ambiguous_target ocr_environment ocr_failed
ocr_timeout ocr_unavailable ocr_uncertain invalid_output execution_failed
missing_completion preflight_failed evidence_rejected ownership_revoked
discovery_budget discovery_stuck quiesce_timeout intervention_required resume_rejected invalid_transition handoff_expired""".split()
)
ENUMS = {
    'kind': {'action', 'step', 'target', 'reading', 'checkpoint'},
    'status': {'started', 'completed', 'rejected', 'failed', 'matched', 'satisfied', 'unsatisfied'},
    'action': {'click', 'move', 'type', 'press', 'hotkey', 'scroll', 'extract'},
    'code': CODES,
}
NUMBERS = {
    'elapsedMs': 120000,
    'durationMs': 120000,
    'score': 1,
    'confidence': 100,
    'candidateCount': 10000,
    'sequence': 1000,
}


def reject():
    raise DesktopError('evidence_rejected', 'Evidence contains unsupported fields or values')


def safe_code(value):
    return value if isinstance(value, str) and value in CODES else 'execution_failed'


def checked_event(event, allowed_ids=None):
    enums = ENUMS | (
        allowed_ids
        if allowed_ids is not None
        else read_approval(APPROVALS / (RECOGNITION_PROFILE_ID + '.json')).allowedIds.model_dump()
    )
    if (
        not isinstance(event, dict)
        or not event
        or set(event) - (enums.keys() | NUMBERS.keys() | {'box'})
    ):
        reject()
    for key, value in event.items():
        if key in enums:
            if value is None and key in ('step', 'action'):
                continue
            if not isinstance(value, str) or value not in enums[key]:
                reject()
        elif key in NUMBERS:
            if (
                type(value) not in (int, float)
                or not math.isfinite(value)
                or not 0 <= value <= NUMBERS[key]
            ):
                reject()
            if key in ('sequence', 'candidateCount') and type(value) is not int:
                reject()
        elif (
            not isinstance(value, list)
            or len(value) != 4
            or any(
                type(v) is not int or not 0 <= v <= (1280 if i % 2 == 0 else 800)
                for i, v in enumerate(value)
            )
        ):
            reject()
    # Copy only after validation; later caller mutation cannot alter the record.
    return json.loads(json.dumps(event, allow_nan=False))


def _read(path, maximum):
    if any(p.is_symlink() for p in (path, *path.parents)):
        reject()
    try:
        return read_regular(path, maximum)
    except (OSError, ValueError):
        reject()


def export_bundle(source, destination):
    """Export only approved replay metadata; business results/images stay local."""
    source, destination = Path(source).absolute(), Path(destination).absolute()
    if (
        source.is_symlink()
        or not source.is_dir()
        or destination.exists()
        or any(p.is_symlink() for p in (destination, *destination.parents))
    ):
        reject()
    try:
        report = strict_json(_read(source / 'report.json', 65536))
        if not isinstance(report, dict):
            reject()
        approval = (
            approval_for_digest(report.get('capabilitySha256'))
            if report.get('phase') == 'execution'
            else None
        )
        allowed_ids = approval.allowedIds.model_dump() if approval else None
        events = [
            checked_event(strict_json(line), allowed_ids)
            for line in _read(source / 'events.jsonl', 4 * 1024 * 1024).splitlines()
        ]
        if (
            not isinstance(report, dict)
            or report.get('status') not in ('success', 'failure', 'business_outcome')
            or report.get('phase') not in ('preflight', 'execution')
            or type(report.get('modelCalls')) is not int
            or report['modelCalls'] != 0
            or type(report.get('actionsCompleted')) is not int
            or not 0
            <= report['actionsCompleted']
            <= (len(approval.allowedIds.step) - 1 if approval else 0)
        ):
            reject()
        if report['phase'] == 'execution' and (
            report.get('policy') != POLICY_ID or report.get('admission', 'approved') != 'approved'
        ):
            reject()
        if report['phase'] == 'preflight' and (
            report['status'] != 'failure' or report['actionsCompleted'] != 0
        ):
            reject()
        summary = {
            key: report[key] for key in ('status', 'phase', 'modelCalls', 'actionsCompleted')
        }
        if report['status'] == 'failure':
            if report.get('code') not in CODES:
                reject()
            summary['code'] = report['code']
        if report['phase'] == 'execution':
            summary.update(policy=POLICY_ID, capabilitySha256=approval.capabilitySha256)
    except (ValueError, TypeError, KeyError, RecursionError, DesktopError):
        reject()
    # All data is validated before creating an output directory. No source
    # filenames, run labels, raw exceptions, results, or pixels are copied.
    destination.mkdir(mode=0o700)
    (destination / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    (destination / 'events.jsonl').write_text(''.join(json.dumps(event) + '\n' for event in events))
    (destination / 'manifest.json').write_text(
        json.dumps(
            {
                'format': 'safe-evidence-v1',
                'screenshots': 'suppressed',
                'businessResults': 'excluded',
                'sourceMetadata': 'not-copied',
                'files': ['summary.json', 'events.jsonl', 'manifest.json'],
            },
            indent=2,
        )
        + '\n'
    )
    return destination
