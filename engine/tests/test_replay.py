import copy
import hashlib
import os
import subprocess
import sys
import json
from pathlib import Path
import shutil
import tempfile
from types import SimpleNamespace
import unittest
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

from PIL import Image
from pydantic import ValidationError
from interface_ai.contracts.models import Capability, MemberInput
from interface_ai.desktop import DesktopError
from interface_ai.replay.interpreter import Interpreter, Observation
from interface_ai.replay.loader import (
    Bundle,
    ReplayError,
    load_bundle,
    strict_json,
    validate_inputs,
)
from interface_ai.vision import Box, VisionError

BUNDLE_PATH = (
    Path(__file__).resolve().parents[2] / 'capabilities/poc/savings-balance/capability.json'
)


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.raw = json.loads(BUNDLE_PATH.read_text())

    def test_manual_artifact_round_trip_and_bound_assets(self):
        bundle = load_bundle(BUNDLE_PATH)
        self.assertEqual(
            Capability.model_validate(bundle.capability.model_dump()), bundle.capability
        )
        self.assertEqual(len(bundle.templates), 7)

    def test_invalid_structures_versions_references_and_actions(self):
        cases = []

        def change(operation):
            cap = copy.deepcopy(self.raw)
            operation(cap)
            cases.append(cap)

        change(lambda c: c.update(schemaVersion='2.0'))
        change(lambda c: c.update(extra='sentinel'))
        change(lambda c: c['steps'][0].update(action='shell', command='sentinel'))
        change(lambda c: c['steps'][0].update(target='unknown'))
        change(lambda c: c['steps'][0].update(precondition='unknown'))
        change(lambda c: c['steps'][0].update(timeoutSeconds=0))
        change(lambda c: c['steps'][0].update(timeoutSeconds='5'))
        change(lambda c: c['steps'][1].update(id=c['steps'][0]['id']))
        change(lambda c: c['steps'][1].update(keys=['a', 'ctrl']))
        change(lambda c: c['steps'].pop())
        change(lambda c: c['inputSchema'].update(additionalProperties=True))
        change(lambda c: c['outputSchema'].update(type='string'))
        change(lambda c: c['targets']['member-field']['region'].update(relativeTo='unknown'))
        change(lambda c: c['targets']['member-field']['region'].update(relativeTo='member-field'))
        change(lambda c: c['targets']['member-field']['region'].update(relativeTo='member-input'))
        change(lambda c: c['targets']['search-heading']['region'].update(box=[0, 0, 1281, 800]))
        change(lambda c: c['targets']['search-heading']['region'].update(box=[0, 0, True, 800]))
        change(lambda c: c['targets']['search-heading'].update(threshold=0.1))
        change(lambda c: c['fields']['balance']['region'].update(clipToDisplay=True))
        change(lambda c: c['steps'][-1]['fields'].update(amountMinor='member-name'))
        change(lambda c: c['steps'][0]['postconditions'][0].update(outcome='member_not_found'))
        change(lambda c: c['assets']['search-heading'].update(file='../escape.png'))
        for case in cases:
            with self.subTest(case=cases.index(case)):
                with self.assertRaises(ValidationError):
                    Capability.model_validate(case)

    def test_unknown_parent_dependency_rejected_without_keyerror(self):
        self.raw['targets']['search-heading']['region']['relativeTo'] = 'member-field'
        self.raw['targets']['member-field']['region']['relativeTo'] = 'unknown'
        with self.assertRaises(ValidationError):
            Capability.model_validate(self.raw)

    def test_json_duplicates_and_nonfinite_values_rejected(self):
        for text in ['{"x":1,"x":2}', '{"x":NaN}', '{"x":Infinity}']:
            with self.assertRaises(ValueError):
                strict_json(text)

    def test_invalid_inputs_reject_without_coercion_or_raw_value(self):
        for value in [123, None, '', '123', '00123 ', '00123\n', '００１２３', 'sentinel']:
            with self.assertRaises(ReplayError) as error:
                validate_inputs({'memberId': value})
            self.assertEqual(error.exception.code, 'invalid_input')
            self.assertNotIn('sentinel', str(error.exception))
        with self.assertRaises(ReplayError):
            validate_inputs({'memberId': '00340', 'other': True})

    def test_asset_tampering_and_symlink_escape_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / 'bundle'
            shutil.copytree(BUNDLE_PATH.parent, target)
            asset = target / 'anchors/search-heading.png'
            original = asset.read_bytes()
            asset.write_bytes(original + b'changed')
            with self.assertRaises(ReplayError) as error:
                load_bundle(target / 'capability.json')
            self.assertEqual(error.exception.code, 'invalid_asset')
            outside = root / 'outside.png'
            outside.write_bytes(original)
            asset.unlink()
            asset.symlink_to(outside)
            with self.assertRaises(ReplayError):
                load_bundle(target / 'capability.json')

    def test_capability_and_asset_fifos_reject_without_blocking_or_desktop(self):
        child = """
import sys
from types import SimpleNamespace
from unittest.mock import patch
from interface_ai.replay.command import replay
with patch('interface_ai.replay.command.run_coordinated') as desktop:
    args = SimpleNamespace(capability=sys.argv[1], member_id='00123', inputs_json=None, session=None)
    assert replay(args, output_root=__import__('pathlib').Path(sys.argv[2])) == 1
    desktop.assert_not_called()
"""
        for name in ['capability.json', 'anchors/search-heading.png']:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                target = root / 'bundle'
                shutil.copytree(BUNDLE_PATH.parent, target)
                (target / name).unlink()
                os.mkfifo(target / name)
                result = subprocess.run(
                    [sys.executable, '-c', child, str(target / 'capability.json'), str(root)],
                    capture_output=True,
                    text=True,
                    timeout=3,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                report = json.loads(next(root.glob('*-replay-*/report.json')).read_text())
                self.assertEqual(report['actionsCompleted'], 0)
                self.assertEqual(
                    report['code'],
                    'invalid_capability' if name == 'capability.json' else 'invalid_asset',
                )

    def test_image_decoder_uses_verified_snapshot_even_after_path_replacement(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'bundle'
            shutil.copytree(BUNDLE_PATH.parent, target)
            asset = target / 'anchors/search-heading.png'
            original_bytes = asset.read_bytes()
            expected = Image.open(asset).convert('RGB').tobytes()
            original_open = Image.open

            def replace_then_decode(snapshot):
                if snapshot.getvalue() == original_bytes:
                    Image.new('RGB', (20, 20), 'red').save(asset)
                return original_open(snapshot)

            with patch('interface_ai.replay.loader.Image.open', side_effect=replace_then_decode):
                bundle = load_bundle(target / 'capability.json')
            self.assertEqual(bundle.templates['search-heading'].tobytes(), expected)

    def test_oversized_artifacts_and_digest_valid_malformed_png_reject(self):
        for name, size in [('capability.json', 262145), ('anchors/search-heading.png', 131073)]:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                target = Path(directory) / 'bundle'
                shutil.copytree(BUNDLE_PATH.parent, target)
                (target / name).write_bytes(b'x' * size)
                with self.assertRaises(ReplayError):
                    load_bundle(target / 'capability.json')
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'bundle'
            shutil.copytree(BUNDLE_PATH.parent, target)
            (target / 'anchors/search-heading.png').write_bytes(b'not a PNG')
            self.raw['assets']['search-heading']['sha256'] = hashlib.sha256(
                b'not a PNG'
            ).hexdigest()
            (target / 'capability.json').write_text(json.dumps(self.raw))
            with self.assertRaises(ReplayError) as error:
                load_bundle(target / 'capability.json')
            self.assertEqual(error.exception.code, 'invalid_asset')

    def test_preflight_rejects_before_desktop_acquisition(self):
        from interface_ai.replay.command import replay

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            invalid = copy.deepcopy(self.raw)
            invalid['steps'][0]['action'] = 'shell'
            bad = root / 'invalid.json'
            bad.write_text(json.dumps(invalid))
            for capability, member in [(BUNDLE_PATH, '123'), (bad, '00340')]:
                args = SimpleNamespace(
                    capability=str(capability), member_id=member, inputs_json=None, session=None
                )
                with (
                    patch('interface_ai.replay.command.run_coordinated') as desktop,
                    redirect_stdout(StringIO()),
                ):
                    self.assertEqual(replay(args, output_root=root), 1)
                desktop.assert_not_called()
            reports = list(root.glob('*-replay-*/report.json'))
            self.assertEqual(len(reports), 2)
            for path in reports:
                report = json.loads(path.read_text())
                self.assertEqual(report['phase'], 'preflight')
                self.assertEqual(report['actionsCompleted'], 0)


class FakeDesktop:
    def __init__(self, *, missing=False, initial='search', stop_after=None, fail_action=None):
        self.stage, self.missing = initial, missing
        self.actions = []
        self.stop_after = stop_after
        self.fail_action = fail_action

    def screenshot(self):
        return Image.new('RGB', (1280, 800))

    def checkpoint(self):
        if self.stop_after is not None and len(self.actions) >= self.stop_after:
            raise DesktopError('stopped', 'stopped')

    def execute(self, action):
        self.actions.append(action)
        if len(self.actions) == self.fail_action:
            raise DesktopError('input_failed', 'input failed')
        if action['type'] == 'type':
            self.stage = 'entered'
        if action['type'] == 'press':
            self.stage = 'missing' if self.missing else 'member'
        if action['type'] == 'click' and self.stage == 'member':
            self.stage = 'account'


class FakeObservation:
    def __init__(self, runner, image):
        self.runner, self.image = runner, image

    def checkpoint(self, name):
        stage = self.runner.desktop.stage
        return name in {
            'search': ['search-ready'],
            'entered': ['search-ready', 'input-entered'],
            'member': ['member-ready'],
            'account': ['account-ready'],
            'missing': ['member-not-found'],
        }.get(stage, [])

    def target(self, name):
        return Box(100, 100, 120, 120)

    def field(self, name):
        return {
            'account-member-id': self.runner.inputs.memberId,
            'member-name': 'Synthetic Person',
            'account-type': 'Savings',
            'currency': 'USD',
            'balance': 1203,
            'alternate-balance': 4567,
        }[name]


class InterpreterTests(unittest.TestCase):
    def setUp(self):
        self.bundle = load_bundle(BUNDLE_PATH)
        self.events = []

    def run_with(self, desktop, bundle=None, observer=FakeObservation, clock=None):
        options = {} if clock is None else {'clock': clock}
        return Interpreter(
            bundle or self.bundle,
            MemberInput(memberId='00340'),
            desktop,
            event_sink=self.events.append,
            observer_factory=observer,
            ocr=object(),
            **options,
        ).run()

    def test_success_binds_input_and_keeps_values_out_of_events(self):
        desktop = FakeDesktop()
        result = self.run_with(desktop)
        self.assertEqual(result.status, 'success')
        self.assertEqual(result.output.amountMinor, 1203)
        self.assertEqual(desktop.actions[2], {'type': 'type', 'text': '00340'})
        self.assertNotIn('00340', json.dumps(self.events))
        self.assertNotIn('Synthetic Person', json.dumps(self.events))

    def test_artifact_changes_execution_sequence_and_output_binding(self):
        raw = self.bundle.capability.model_dump()
        raw['steps'].pop(1)
        raw['fields']['alternate-balance'] = raw['fields']['balance']
        raw['steps'][-1]['fields']['amountMinor'] = 'alternate-balance'
        bundle = Bundle(Capability.model_validate(raw), 'test', self.bundle.templates)
        desktop = FakeDesktop()
        result = self.run_with(desktop, bundle)
        self.assertEqual(result.output.amountMinor, 4567)
        self.assertEqual([a['type'] for a in desktop.actions], ['click', 'type', 'press', 'click'])

    def test_known_outcome_exits_before_account_click_and_extraction(self):
        desktop = FakeDesktop(missing=True)
        result = self.run_with(desktop)
        self.assertEqual(result.status, 'business_outcome')
        self.assertEqual(result.outcome, 'member_not_found')
        self.assertEqual(len(desktop.actions), 4)
        self.assertFalse(hasattr(result, 'output'))

    def test_precondition_failure_dispatches_nothing(self):
        desktop = FakeDesktop(initial='unknown')
        result = self.run_with(desktop)
        self.assertEqual(result.code, 'precondition_failed')
        self.assertEqual(desktop.actions, [])

    def test_uncertain_input_failure_is_never_retried(self):
        desktop = FakeDesktop(fail_action=3)
        result = self.run_with(desktop)
        self.assertEqual(result.code, 'input_failed')
        self.assertEqual(len(desktop.actions), 3)

    def test_stop_after_dispatch_prevents_any_subsequent_action(self):
        desktop = FakeDesktop(stop_after=3)
        result = self.run_with(desktop)
        self.assertEqual(result.code, 'stopped')
        self.assertEqual(len(desktop.actions), 3)

    def test_output_identity_mismatch_is_not_returned_as_success(self):
        class WrongIdentity(FakeObservation):
            def field(self, name):
                return '00912' if name == 'account-member-id' else super().field(name)

        result = self.run_with(FakeDesktop(), observer=WrongIdentity)
        self.assertEqual(result.code, 'identity_mismatch')
        self.assertFalse(hasattr(result, 'output'))

    def test_wrong_output_type_is_rejected(self):
        class WrongOutput(FakeObservation):
            def field(self, name):
                return '1203' if name == 'balance' else super().field(name)

        self.assertEqual(self.run_with(FakeDesktop(), observer=WrongOutput).code, 'invalid_output')

    def test_multiple_matching_postconditions_are_ambiguous(self):
        class Ambiguous(FakeObservation):
            def checkpoint(self, name):
                return (
                    name == 'member-not-found' and self.runner.desktop.stage == 'member'
                ) or super().checkpoint(name)

        desktop = FakeDesktop()
        result = self.run_with(desktop, observer=Ambiguous)
        self.assertEqual(result.code, 'ambiguous_checkpoint')
        self.assertEqual(len(desktop.actions), 4)

    def test_missing_postcondition_times_out_without_a_later_action(self):
        desktop = FakeDesktop()
        now = [0]

        def clock():
            if desktop.stage == 'member':
                now[0] += 1
            return now[0]

        class Missing(FakeObservation):
            def checkpoint(self, name):
                return False if name == 'member-ready' else super().checkpoint(name)

        result = self.run_with(desktop, observer=Missing, clock=clock)
        self.assertEqual(result.code, 'checkpoint_timeout')
        self.assertEqual(len(desktop.actions), 4)

    def identity_runner(self, readings, clock=None):
        class IdentityObservation(FakeObservation):
            def checkpoint(self, name):
                if name == 'input-entered':
                    return Observation.checkpoint(self, name)
                return super().checkpoint(name)

            def region(self, specification):
                return Box(0, 0, 100, 20)

            def field(self, name):
                if name == 'entered-id':
                    return Observation.field(self, name)
                return super().field(name)

            def __init__(self, runner, image):
                super().__init__(runner, image)
                self.fields = {}

        desktop = FakeDesktop()
        iterator = iter(readings)

        def line(*a, **kw):
            reading = next(iterator)
            if isinstance(reading, Exception):
                raise reading
            return SimpleNamespace(text=reading, confidence=95.0)

        ocr = SimpleNamespace(line=line)
        runner = Interpreter(
            self.bundle,
            MemberInput(memberId='00340'),
            desktop,
            event_sink=self.events.append,
            observer_factory=IdentityObservation,
            ocr=ocr,
            **({} if clock is None else {'clock': clock}),
        )
        return runner, desktop

    def test_uncertain_precondition_reobserves_without_repeating_completed_input(self):
        runner, desktop = self.identity_runner(
            ['00340', VisionError('ocr_uncertain', 'Synthetic transient'), '00340']
        )
        result = runner.run()
        self.assertEqual(result.status, 'success')
        self.assertEqual(
            [a['type'] for a in desktop.actions], ['click', 'hotkey', 'type', 'press', 'click']
        )
        self.assertTrue(any(e.get('code') == 'ocr_uncertain' for e in self.events))

    def test_uncertain_precondition_keeps_deadline_and_stop_guards(self):
        for stop in (False, True):
            with self.subTest(stop=stop):
                now = [0]
                runner, desktop = self.identity_runner(
                    ['00340'] + [VisionError('ocr_uncertain', 'Synthetic transient')] * 100
                )

                def clock():
                    if runner.step is not None and runner.step.id == 'search-member':
                        now[0] += 0.1
                        if stop and any(e.get('code') == 'ocr_uncertain' for e in self.events):
                            desktop.stop_after = 3
                    return now[0]

                runner.clock = clock
                self.events.clear()
                result = runner.run()
                self.assertEqual(result.code, 'stopped' if stop else 'checkpoint_timeout')
                self.assertEqual(result.expected, ['input-entered'])
                self.assertEqual(len(desktop.actions), 3)

    def test_wrong_identity_after_uncertainty_is_not_retried_or_accepted(self):
        runner, desktop = self.identity_runner(
            ['00340', VisionError('ocr_uncertain', 'Synthetic transient'), '00912', '00340']
        )
        result = runner.run()
        self.assertEqual(result.code, 'precondition_failed')
        self.assertEqual(len(desktop.actions), 3)

    def test_transient_malformed_and_wrong_id_wait_for_exact_checkpoint_without_retyping(self):
        runner, desktop = self.identity_runner(['00340|', '00912', '00340', '00340'])
        result = runner.run()
        self.assertEqual(result.status, 'success')
        self.assertEqual(
            [a['type'] for a in desktop.actions], ['click', 'hotkey', 'type', 'press', 'click']
        )
        self.assertTrue(
            any(
                e.get('code') == 'invalid_identity' and e['status'] == 'unsatisfied'
                for e in self.events
            )
        )
        self.assertNotIn('00340|', json.dumps(self.events))

    def test_persistent_malformed_identity_times_out_before_search(self):
        now = [0]

        def clock():
            now[0] += 0.05
            return now[0]

        runner, desktop = self.identity_runner(['00340|'] * 100, clock=clock)
        result = runner.run()
        self.assertEqual(result.code, 'checkpoint_timeout')
        self.assertEqual(result.step, 'enter-member')
        self.assertEqual([a['type'] for a in desktop.actions], ['click', 'hotkey', 'type'])
        self.assertFalse(hasattr(result, 'output'))

    def test_direct_identity_extraction_still_rejects_malformed_reading(self):
        runner, desktop = self.identity_runner(['00340|'])
        runner.step = self.bundle.capability.steps[2]
        runner.step_deadline = runner.clock() + 5
        observation = runner.observer_factory(runner, desktop.screenshot())
        with self.assertRaises(ReplayError) as error:
            observation.field('entered-id')
        self.assertEqual(error.exception.code, 'invalid_identity')
