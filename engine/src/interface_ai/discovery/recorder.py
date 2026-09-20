"""Narrow recorder: executed actions plus explicitly attributed visual annotations.

Only crops of reviewed static labels are retained, never full frames or member
values. The candidate is private staging, not an approval or executable policy.
"""

import hashlib
from io import BytesIO
import json
from pathlib import Path

from interface_ai.contracts.generated import GeneratedCapability
from interface_ai.contracts.models import Anchor
from interface_ai.files import read_regular
from interface_ai.handoff.evidence import atomic_write
from interface_ai.replay.loader import ReplayError, load_bundle
from interface_ai.vision import VisionError
from .policy import OUTPUT_FIELDS

STATIC_TARGETS = {
    'search-ready': ('search-heading', 'member-field'),
    'input-entered': ('search-heading', 'member-field'),
    'member-ready': ('member-heading', 'savings-label', 'savings-button'),
    'account-ready': ('account-heading',),
    'member-not-found': ('search-heading', 'member-field', 'not-found'),
}
PARENTS = {
    'member-input': 'member-field',
    'search-button': 'member-field',
    'savings-button': 'savings-button',
}


def encoded(value):
    return (json.dumps(value, indent=2) + '\n').encode()


def digest(value):
    return hashlib.sha256(value).hexdigest()


def png(image):
    stream = BytesIO()
    image.save(stream, format='PNG')
    return stream.getvalue()


class Recorder:
    def __init__(self, bundle, *, runtime_path=Path('/opt/build-manifest.json')):
        self.bundle = bundle
        self.runtime_digest = digest(read_regular(runtime_path, 262144))
        self.crops = {}
        self.boxes = {}
        self.incomplete = False

    def observe(self, view, checkpoint):
        boxes = {}
        try:
            for name in STATIC_TARGETS[checkpoint]:
                box = view.target(name)
                boxes[name] = list(box.tuple())
                target = self.bundle.capability.targets[name]
                if not isinstance(target, Anchor):
                    raise ValueError('Static label must be an anchor')
                if target.asset not in self.crops:
                    crop = png(view.image.crop(box.tuple()))
                    if len(crop) > 131072:
                        raise ValueError('Static crop too large')
                    self.crops[target.asset] = (
                        crop,
                        dict(
                            source='observed-static-label',
                            observation=view.reference,
                            target=name,
                            box=list(box.tuple()),
                            sha256=digest(crop),
                        ),
                    )
        except (VisionError, KeyError, ValueError):
            self.incomplete = True
        self.boxes[view.reference] = boxes

    def finish(self, run):
        if self.incomplete or not run.trace or any(e['status'] != 'completed' for e in run.trace):
            raise ReplayError(
                'recording_incomplete', 'Only a complete observed path can become a candidate'
            )
        if run.trace[-1]['after'] != 'account-ready' or run.result.status != 'success':
            raise ReplayError('recording_incomplete', 'A verified account result is required')
        # Reuse named visual/OCR definitions, never the manual action sequence.
        profile = self.bundle.capability.model_dump()
        cap = {
            key: profile[key]
            for key in (
                'inputSchema',
                'outputSchema',
                'environment',
                'assets',
                'targets',
                'fields',
                'checkpoints',
            )
        }
        cap['targets'].pop('member-input', None)
        steps, bindings, derivations = [], [], []
        for entry in run.trace:
            step = dict(
                id=entry['id'],
                action=entry['action'],
                precondition=entry['before'],
                timeoutSeconds=5.0,
                postconditions=[{'checkpoint': entry['after']}],
            )
            if entry['action'] == 'click':
                parent = PARENTS[entry['target']]
                box = self.boxes[entry['beforeObservation']][parent]
                x, y = entry['point'][0] - box[0], entry['point'][1] - box[1]
                name = 'target-' + entry['id']
                cap['targets'][name] = dict(
                    kind='relative',
                    region=dict(
                        relativeTo=parent, box=[x - 2, y - 2, x + 2, y + 2], clipToDisplay=False
                    ),
                )
                step['target'] = name
            elif entry['action'] == 'type' and entry.get('inputBinding') == 'memberId':
                step['input'] = 'memberId'
                bindings.append(dict(sourceAction=entry['id'], step=entry['id'], input='memberId'))
            elif entry['action'] == 'press':
                step['key'] = 'enter'  # The admitted provider normalizer only permits Enter.
            elif entry['action'] == 'hotkey':
                step['keys'] = ['ctrl', 'a']
            else:
                raise ReplayError('recording_incomplete', 'Unsupported executed operation')
            # This branch is a reviewed environment annotation. It was NOT
            # observed in the successful discovery and is identified as such.
            if entry['before'] == 'input-entered' and entry['after'] == 'member-ready':
                step['postconditions'].append(
                    dict(checkpoint='member-not-found', outcome='member_not_found')
                )
            steps.append(step)
            derivations.append(
                dict(
                    step=step['id'],
                    sourceAction=entry['id'],
                    beforeObservation=entry['beforeObservation'],
                    afterObservation=entry['afterObservation'],
                    targetMethod='recorded-point-relative-to-observed-label'
                    if entry['action'] == 'click'
                    else 'admitted-native-primitive',
                )
            )
        steps.append(
            dict(
                id='extract-result',
                action='extract',
                precondition='account-ready',
                timeoutSeconds=5.0,
                fields=OUTPUT_FIELDS,
            )
        )
        asset_sources = {}
        for name, asset in cap['assets'].items():
            if name in self.crops:
                crop, source = self.crops[name]
            else:
                # The missing-member label does not occur on a successful path.
                # Its optional outcome branch reuses the reviewed static profile.
                if name != 'not-found-label':
                    raise ReplayError(
                        'recording_incomplete', 'Required successful-path anchor was not observed'
                    )
                crop = png(self.bundle.templates[name])
                source = dict(source='reviewed-environment-profile', sha256=digest(crop))
            asset['sha256'] = digest(crop)
            asset_sources[name] = source
        cap.update(
            schemaVersion='2.0',
            name='savings-balance-discovered',
            capabilityVersion='0.1.0',
            description='Candidate recorded from executed OpenAI computer actions; visual/OCR annotations require explicit local review.',
            steps=steps,
            provenance=dict(
                kind='recorded-openai-discovery',
                runId=run.run_id,
                sessionId=run.controller.session['id'],
                provider='openai',
                model='gpt-5.6-sol',
                requests=run.sequence,
                responseIds=run.responses,
                executedActions=[e['id'] for e in run.trace],
                inputBindings=bindings,
                trajectorySha256=digest(encoded(run.trace)),
                observationsSha256=digest(encoded(run.observation_refs)),
                runtimeManifestSha256=self.runtime_digest,
                recognitionProfileSha256=self.bundle.sha256,
                derivation='bank-static-label-review-v1',
            ),
        )
        validated = GeneratedCapability.model_validate(cap)
        candidate = run.directory / 'candidate'
        candidate.mkdir(mode=0o700)
        (candidate / 'anchors').mkdir(mode=0o700)
        for name, asset in validated.assets.items():
            crop = self.crops[name][0] if name in self.crops else png(self.bundle.templates[name])
            atomic_write(candidate / asset.file, crop)
        raw = encoded(validated.model_dump())
        atomic_write(candidate / 'capability.json', raw)
        # Decode and digest the staged bytes through the same bounded replay loader.
        loaded = load_bundle(candidate / 'capability.json')
        review = dict(
            format='candidate-review-v1',
            status='pending-review',
            candidateSha256=loaded.sha256,
            capturePolicy='static-synthetic-labels-only-v1',
            fullFramesRetained=False,
            actionDerivations=derivations,
            assetDerivations=asset_sources,
            reusedAnnotations=[
                'environment',
                'input/output schemas',
                'anchor search regions',
                'OCR fields',
                'exact identity/account checkpoints',
                'missing-member outcome',
            ],
            inferredAnnotations=[
                'relative click regions from executed points',
                'pre/postconditions from observed states',
                'final extraction using local verified result',
            ],
            reviewEdits=[],
        )
        atomic_write(candidate / 'review.json', encoded(review))
        atomic_write(
            candidate / 'REVIEW.md',
            (
                '# Candidate — not approved\n\n'
                'The ordered input steps come only from completed native dispatches. Each step maps to its source action and before/after observation. Screenshot/wait items are observations, not replay input steps.\n\n'
                'Review `review.json`: captured assets are static labels from the run; the absent missing-member label and its alternative outcome reuse the reviewed environment profile. OCR regions, exact identity/account checks and schema definitions are reused annotations. Final extraction is the locally validated result, not model prose.\n\n'
                'Verify the input binding, each relative click region, candidate digest and asset crops. Then run scoped second-member and translated-layout evaluations before promotion. No human approval or edits have been claimed. Full frames remain memory-only. This private staging directory is not an evidence export.\n'
            ).encode(),
        )
        return dict(status='candidate', directory=candidate.name, sha256=loaded.sha256)
