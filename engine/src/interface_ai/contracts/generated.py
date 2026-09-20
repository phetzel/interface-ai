"""Version two adds recorded provenance; it does not authorize execution."""

from typing import Annotated, Literal
from pydantic import Field, model_validator
from .models import Capability, Digest, Name, Step, StrictModel, Type

Identifier = Annotated[str, Field(pattern=r'^[A-Za-z0-9_.:-]{1,128}$')]
SessionId = Annotated[
    str, Field(pattern=r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')
]
ActionId = Annotated[str, Field(pattern=r'^action-[0-9]{3}$')]


class InputBinding(StrictModel):
    sourceAction: ActionId
    step: Name
    input: Literal['memberId']


class DiscoveryProvenance(StrictModel):
    kind: Literal['recorded-openai-discovery']
    runId: SessionId
    sessionId: SessionId
    provider: Literal['openai']
    model: Literal['gpt-5.6-sol']
    requests: Annotated[int, Field(ge=1, le=20)]
    responseIds: list[Identifier] = Field(min_length=1, max_length=20)
    executedActions: list[ActionId] = Field(min_length=1, max_length=40)
    inputBindings: list[InputBinding] = Field(min_length=1, max_length=40)
    trajectorySha256: Digest
    observationsSha256: Digest
    runtimeManifestSha256: Digest
    recognitionProfileSha256: Digest
    derivation: Literal['bank-static-label-review-v1']

    @model_validator(mode='after')
    def unique_sources(self):
        if len(set(self.responseIds)) != self.requests or len(self.responseIds) != self.requests:
            raise ValueError('Every accepted provider response must be identified')
        if len(set(self.executedActions)) != len(self.executedActions):
            raise ValueError('Executed action references must be unique')
        return self


class GeneratedCapability(Capability):
    schemaVersion: Literal['2.0']
    provenance: DiscoveryProvenance
    steps: list[Step] = Field(min_length=2, max_length=41)

    @model_validator(mode='after')
    def recorded_path(self):
        if [s.id for s in self.steps[:-1]] != self.provenance.executedActions:
            raise ValueError('Every input step must preserve the recorded action order')
        bindings = self.provenance.inputBindings
        typed = [s.id for s in self.steps if isinstance(s, Type)]
        if [b.step for b in bindings] != typed or any(b.sourceAction != b.step for b in bindings):
            raise ValueError('Bindings must identify each actually recorded typing action')
        return self
