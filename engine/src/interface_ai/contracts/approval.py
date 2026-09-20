"""Operator-owned authorization, separate from the proposed capability."""

from typing import Annotated, Literal
from pydantic import Field, model_validator
from .models import StrictModel, Digest, Name, Environment
from .generated import DiscoveryProvenance

POLICY_ID = 'bank-read-only-v2'


class Vocabulary(StrictModel):
    step: list[Name] = Field(min_length=2, max_length=41)
    target: list[Name] = Field(min_length=1, max_length=64)
    field: list[Name] = Field(min_length=1, max_length=24)
    checkpoint: list[Name] = Field(min_length=1, max_length=16)

    @model_validator(mode='after')
    def unique(self):
        if any(len(v) != len(set(v)) for v in self.model_dump().values()):
            raise ValueError('Duplicate authorized identifier')
        return self


class Continuation(StrictModel):
    interruptedStep: Name
    nextStep: Name
    checkpoint: Literal['member-ready']


class DiscoverySource(StrictModel):
    sourceManifestSha256: Digest
    buildEvidenceSha256: Digest
    desktopImage: Annotated[str, Field(pattern=r'^sha256:[a-f0-9]{64}$')]
    fixtureImage: Annotated[str, Field(pattern=r'^sha256:[a-f0-9]{64}$')]
    reviewEvidenceSha256: Digest


class Approval(StrictModel):
    format: Literal['promotion-v1']
    id: Name
    capabilityFile: Annotated[str, Field(pattern=r'^[a-z0-9/-]+/capability\.json$', max_length=160)]
    candidateSha256: Digest
    capabilitySha256: Digest
    capabilityVersion: Annotated[str, Field(pattern=r'^\d+\.\d+\.\d+$')]
    assets: dict[Name, Digest] = Field(min_length=1, max_length=16)
    policy: Literal['bank-read-only-v2']
    decision: Literal['approved']
    reviewer: Literal['historical-manual-review', 'agent-review', 'user-review']
    reviewEdits: list[Name] = Field(max_length=40)
    provenance: Literal['manually-authored-poc'] | DiscoveryProvenance
    source: DiscoverySource | None
    environment: Environment
    allowedIds: Vocabulary
    continuation: Continuation | None

    @model_validator(mode='after')
    def source_and_delta(self):
        if self.capabilityFile.startswith('/') or '//' in self.capabilityFile:
            raise ValueError('Relative bundle path required')
        if not self.reviewEdits and self.candidateSha256 != self.capabilitySha256:
            raise ValueError('Changed candidate needs an explicit review delta')
        if isinstance(self.provenance, DiscoveryProvenance) and self.source is None:
            raise ValueError('Generated approval needs source and evaluation evidence')
        return self
