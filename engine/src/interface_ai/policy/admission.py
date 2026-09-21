"""Small trusted approval directory; candidate contents never select authority."""

from dataclasses import dataclass
from pathlib import Path
from interface_ai.contracts.approval import Approval, Continuation, POLICY_ID
from interface_ai.contracts.generated import GeneratedCapability
from interface_ai.desktop.adapter import DesktopError
from interface_ai.files import read_regular, safe_path
from interface_ai.replay.loader import strict_json
from .profile import (
    RECOGNITION_PROFILE_ID as RECOGNITION_PROFILE_ID,
    reference_bundle as reference_bundle,
    validate_profile,
)

ROOT = Path(__file__).resolve().parents[4] / 'capabilities'
APPROVALS = ROOT / 'approvals'
DEFAULT_ID = 'discovered-savings'


def denied():
    raise DesktopError(
        'policy_artifact_denied', 'Independent artifact approval is missing or invalid'
    )


def vocabulary(cap):
    return dict(
        step=[s.id for s in cap.steps],
        target=list(cap.targets),
        field=list(cap.fields),
        checkpoint=list(cap.checkpoints),
    )


@dataclass(frozen=True)
class Admission:
    scope: str
    allowed_ids: dict
    continuation: Continuation | None
    approval_id: str | None = None

    def resume_index(self, cap):
        return next(i for i, s in enumerate(cap.steps) if s.id == self.continuation.nextStep)


def read_approval(path):
    try:
        return Approval.model_validate(strict_json(read_regular(safe_path(path), 131072)))
    except (ValueError, OSError, RecursionError):
        denied()


def approvals():
    paths = sorted(APPROVALS.glob('*.json'))
    if not 1 <= len(paths) <= 8:
        denied()
    items = [read_approval(p) for p in paths]
    if len({a.id for a in items}) != len(items) or len({a.capabilitySha256 for a in items}) != len(
        items
    ):
        denied()
    return items


def approval_for_digest(digest):
    matches = [a for a in approvals() if a.capabilitySha256 == digest]
    if len(matches) != 1:
        denied()
    return matches[0]


def capability_path(identifier=DEFAULT_ID):
    matches = [a for a in approvals() if a.id == identifier]
    if len(matches) != 1:
        denied()
    return ROOT / matches[0].capabilityFile


def validate_continuation(cap, continuation):
    if continuation is None:
        return
    steps = {s.id: i for i, s in enumerate(cap.steps)}
    before, after = steps.get(continuation.interruptedStep), steps.get(continuation.nextStep)
    if before is None or after != before + 1:
        denied()
    first, second = cap.steps[before], cap.steps[after]
    if (
        first.precondition != 'input-entered'
        or not any(
            p.checkpoint == 'member-ready' and p.outcome is None for p in first.postconditions
        )
        or second.action != 'click'
        or second.precondition != 'member-ready'
    ):
        denied()
    target = cap.targets[second.target]
    if second.target != 'savings-button' and target.region.relativeTo != 'savings-button':
        denied()


def admit(bundle):
    approved = approval_for_digest(bundle.sha256)
    cap = bundle.capability
    if (
        approved.capabilityVersion != cap.capabilityVersion
        or approved.environment != cap.environment
        or approved.provenance != cap.provenance
        or approved.assets != {k: v.sha256 for k, v in cap.assets.items()}
        or approved.allowedIds.model_dump() != vocabulary(cap)
        or approved.policy != POLICY_ID
    ):
        denied()
    if isinstance(cap, GeneratedCapability):
        validate_profile(bundle)
    validate_continuation(cap, approved.continuation)
    return Admission(
        'approved', approved.allowedIds.model_dump(), approved.continuation, approved.id
    )
