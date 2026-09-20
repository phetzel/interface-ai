"""Independent admission and review negatives, using simulated recorder fixtures."""

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from interface_ai.contracts.approval import Approval, Continuation
from interface_ai.desktop import DesktopError
from interface_ai.policy.admission import admit, reference_bundle, vocabulary, validate_continuation
from interface_ai.policy.candidate import review_candidate
from interface_ai.policy.evidence import checked_event
from interface_ai.replay.loader import load_bundle, ReplayError
import test_recorder


class ApprovalTests(unittest.TestCase):
    def setUp(self):
        self.fixture = test_recorder.RecorderTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.root = self.fixture.root
        run = self.fixture.recorded
        run.observation_refs += [dict(id='observation-002'), dict(id='observation-003')]
        candidate = self.fixture.recorder.finish(run)
        self.path = self.root / 'candidate/capability.json'
        for name, data in [
            ('trajectory.json', run.trace),
            ('observations.json', run.observation_refs),
            (
                'summary.json',
                dict(
                    status='passed',
                    runId=run.run_id,
                    sessionId=run.run_id,
                    responses=run.responses,
                    candidate=candidate,
                ),
            ),
        ]:
            (self.root / name).write_text(json.dumps(data, indent=2) + '\n')
        self.bundle = load_bundle(self.path)

    def test_review_is_scoped_and_never_ordinary_approval(self):
        _, admission = review_candidate(self.path, root=self.root)
        self.assertEqual(admission.scope, 'candidate-review')
        self.assertIsNone(admission.continuation)
        with self.assertRaises(DesktopError):
            admit(self.bundle)
        with self.assertRaises(DesktopError):
            review_candidate(self.path, root=self.root / 'different')

    def test_trajectory_candidate_or_asset_changes_reject(self):
        path = self.root / 'trajectory.json'
        original = path.read_bytes()
        path.write_bytes(original + b' ')
        with self.assertRaises(DesktopError):
            review_candidate(self.path, root=self.root)
        path.write_bytes(original)
        self.path.write_bytes(self.path.read_bytes() + b' ')
        with self.assertRaises(DesktopError):
            review_candidate(self.path, root=self.root)
        asset = next((self.root / 'candidate/anchors').glob('*.png'))
        asset.write_bytes(asset.read_bytes() + b' ')
        with self.assertRaises(ReplayError):
            load_bundle(self.path)

    def test_symlink_file_and_directory_rejected(self):
        for target in (self.path, self.path.parent):
            link = self.root / 'link'
            link.symlink_to(target)
            with self.assertRaises(ReplayError):
                load_bundle(link if target.is_file() else link / 'capability.json')
            link.unlink()
        asset = next((self.path.parent / 'anchors').glob('*.png'))
        original = asset.rename(self.root / 'original.png')
        asset.symlink_to(original)
        with self.assertRaises(ReplayError):
            load_bundle(self.path)

    def test_continuation_is_named_and_strictly_scoped(self):
        cap = self.bundle.capability
        good = Continuation(
            interruptedStep='action-003', nextStep='action-004', checkpoint='member-ready'
        )
        validate_continuation(cap, good)
        for before, after in [
            ('action-001', 'action-004'),
            ('action-002', 'action-003'),
            ('unknown', 'action-004'),
        ]:
            with self.assertRaises(DesktopError):
                validate_continuation(
                    cap, good.model_copy(update=dict(interruptedStep=before, nextStep=after))
                )
        checked_event(dict(kind='step', step='action-003', status='started'), vocabulary(cap))
        with self.assertRaises(DesktopError):
            checked_event(dict(kind='step', step='unknown', status='started'), vocabulary(cap))

    def test_manifest_must_match_bytes_assets_environment_and_ids(self):
        # A typed trusted manifest is required; candidate fields cannot grant it.
        manual = reference_bundle()
        from interface_ai.policy.admission import approval_for_digest

        approved = approval_for_digest(manual.sha256)
        for field, value in [
            ('assets', {}),
            ('allowedIds', approved.allowedIds.model_copy(update={'step': ['unknown']})),
            ('continuation', approved.continuation.model_copy(update={'nextStep': 'read-balance'})),
        ]:
            with patch(
                'interface_ai.policy.admission.approval_for_digest',
                return_value=approved.model_copy(update={field: value}),
            ):
                with self.assertRaises(DesktopError):
                    admit(manual)
        with tempfile.TemporaryDirectory() as name:
            with patch('interface_ai.policy.admission.APPROVALS', Path(name)):
                with self.assertRaises(DesktopError):
                    admit(manual)
        data = approved.model_dump()
        data['candidateSha256'] = 'f' * 64
        with self.assertRaises(ValueError):
            Approval.model_validate(data)
