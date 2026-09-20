"""Recorder contracts use synthetic in-memory frames, not model-run evidence."""

import copy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from PIL import Image
from pydantic import ValidationError
from interface_ai.contracts.generated import GeneratedCapability
from interface_ai.contracts.models import SavingsOutput, Success
from interface_ai.desktop import DesktopError
from interface_ai.discovery.recorder import Recorder, STATIC_TARGETS
from interface_ai.policy.bank import REVIEWED_PATH, admit
from interface_ai.replay.loader import load_bundle, ReplayError
from interface_ai.vision import Box


class RecorderTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        runtime = self.root / 'runtime.json'
        runtime.write_text('{}')
        self.bundle = load_bundle(REVIEWED_PATH)
        self.recorder = Recorder(self.bundle, runtime_path=runtime)
        for ref, state in [
            ('observation-001', 'search-ready'),
            ('observation-002', 'member-ready'),
            ('observation-003', 'account-ready'),
        ]:
            image = Image.new('RGB', (1280, 800), 'white')
            boxes = {}
            for i, name in enumerate(STATIC_TARGETS[state]):
                template = self.bundle.templates[self.bundle.capability.targets[name].asset]
                x, y = 100, 230 + i * 160
                image.paste(template, (x, y))
                boxes[name] = Box(x, y, x + template.width, y + template.height)
            view = SimpleNamespace(
                image=image, reference=ref, target=lambda name, boxes=boxes: boxes[name]
            )
            self.recorder.observe(view, state)
        session = '12345678-1234-1234-1234-123456789abc'
        trace = []
        for i, (action, before, after) in enumerate(
            [
                ('click', 'search-ready', 'search-ready'),
                ('type', 'search-ready', 'input-entered'),
                ('press', 'input-entered', 'member-ready'),
                ('click', 'member-ready', 'account-ready'),
            ],
            1,
        ):
            item = dict(
                id=f'action-{i:03d}',
                action=action,
                status='completed',
                before=before,
                after=after,
                beforeObservation='observation-002' if i == 4 else 'observation-001',
                afterObservation='observation-003' if i == 4 else 'observation-002',
                responseId='resp_fixture',
                callId='call_fixture',
                actionIndex=i - 1,
                epoch=0,
                sessionId=session,
            )
            if action == 'click':
                item.update(
                    target='savings-button' if i == 4 else 'member-input',
                    point=[150, 565] if i == 4 else [200, 465],
                )
            if action == 'type':
                item['inputBinding'] = 'memberId'
            trace.append(item)
        self.recorded = SimpleNamespace(
            trace=trace,
            directory=self.root,
            run_id=session,
            controller=SimpleNamespace(session={'id': session}),
            sequence=1,
            responses=['resp_fixture'],
            observation_refs=[
                {'id': 'observation-001', 'checkpoint': 'search-ready', 'sha256': 'a' * 64}
            ],
            result=Success(
                output=SavingsOutput(
                    memberId='00123',
                    memberName='Demo Member A',
                    accountType='Savings',
                    currency='USD',
                    amountMinor=123456,
                )
            ),
        )

    def test_recorded_order_binding_crops_and_reused_annotations_are_explicit(self):
        result = self.recorder.finish(self.recorded)
        cap = load_bundle(self.root / 'candidate/capability.json').capability
        self.assertEqual(result['status'], 'candidate')
        self.assertEqual(
            [s.action for s in cap.steps], ['click', 'type', 'press', 'click', 'extract']
        )
        self.assertEqual(cap.provenance.inputBindings[0].sourceAction, 'action-002')
        review = json.loads((self.root / 'candidate/review.json').read_text())
        self.assertEqual(review['status'], 'pending-review')
        self.assertEqual(
            review['assetDerivations']['not-found-label']['source'], 'reviewed-environment-profile'
        )
        self.assertEqual(
            review['assetDerivations']['search-heading']['source'], 'observed-static-label'
        )
        self.assertFalse(review['fullFramesRetained'])
        self.assertEqual(len(list((self.root / 'candidate/anchors').glob('*.png'))), 7)
        with self.assertRaises(DesktopError):
            admit(load_bundle(self.root / 'candidate/capability.json'))
        data = cap.model_dump()
        data['provenance']['executedActions'].reverse()
        with self.assertRaises(ValidationError):
            GeneratedCapability.model_validate(data)

    def test_incomplete_or_unsupported_path_never_fabricates_missing_steps(self):
        original = copy.deepcopy(self.recorded.trace)
        for change in [{'status': 'uncertain'}, {'action': 'scroll'}]:
            self.recorded.trace = copy.deepcopy(original)
            self.recorded.trace[1].update(change)
            with self.assertRaises(ReplayError):
                self.recorder.finish(self.recorded)
            self.assertFalse((self.root / 'candidate/capability.json').exists())

    def test_absent_success_anchor_prevents_candidate(self):
        del self.recorder.crops['account-heading']
        with self.assertRaises(ReplayError):
            self.recorder.finish(self.recorded)
        self.assertFalse((self.root / 'candidate/capability.json').exists())
