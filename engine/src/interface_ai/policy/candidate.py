"""Explicit local evaluation of a recorded candidate, never ordinary admission."""

import hashlib
from pathlib import Path
from interface_ai.contracts.generated import GeneratedCapability
from interface_ai.files import read_regular, safe_path
from interface_ai.replay.loader import load_bundle, strict_json
from .admission import Admission, denied, validate_profile, vocabulary


def review_candidate(path, *, root=Path('/artifacts')):
    try:
        path = safe_path(Path(path))
        if not path.is_relative_to(root.resolve()) or path.parts[-2:] != (
            'candidate',
            'capability.json',
        ):
            denied()
        directory = path.parent.parent
        bundle = load_bundle(path)
        cap = bundle.capability
        if not isinstance(cap, GeneratedCapability):
            denied()

        def read(name, limit=262144):
            raw = read_regular(safe_path(directory / name), limit)
            return strict_json(raw), hashlib.sha256(raw).hexdigest()

        review, _ = read('candidate/review.json')
        summary, _ = read('summary.json')
        trajectory, trajectory_hash = read('trajectory.json')
        observations, observation_hash = read('observations.json')
        provenance = cap.provenance
        if (
            review['candidateSha256'] != bundle.sha256
            or review['status'] != 'pending-review'
            or review['reviewEdits'] != []
            or summary['status'] != 'passed'
            or summary['runId'] != provenance.runId
            or summary['sessionId'] != provenance.sessionId
            or summary['responses'] != provenance.responseIds
            or summary['candidate']['sha256'] != bundle.sha256
            or trajectory_hash != provenance.trajectorySha256
            or observation_hash != provenance.observationsSha256
            or len(trajectory) != len(cap.steps) - 1
        ):
            denied()
        validate_profile(bundle)
        obs = {o['id']: o for o in observations}
        for entry, step in zip(trajectory, cap.steps[:-1], strict=True):
            if (
                entry['id'] != step.id
                or entry['action'] != step.action
                or entry['status'] != 'completed'
                or entry['sessionId'] != provenance.sessionId
                or entry['responseId'] not in provenance.responseIds
                or entry['before'] != step.precondition
                or entry['beforeObservation'] not in obs
                or entry['afterObservation'] not in obs
                or not any(
                    p.checkpoint == entry['after'] and p.outcome is None
                    for p in step.postconditions
                )
            ):
                denied()
            if step.action == 'type' and entry.get('inputBinding') != 'memberId':
                denied()
        for name, asset in cap.assets.items():
            if review['assetDerivations'][name]['sha256'] != asset.sha256:
                denied()
        return bundle, Admission('candidate-review', vocabulary(cap), None)
    except (OSError, ValueError, KeyError, TypeError, RecursionError):
        denied()
