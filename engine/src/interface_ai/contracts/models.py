from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, model_validator

Name = Annotated[str, Field(pattern=r'^[a-z][a-z0-9-]{0,47}$')]
Digest = Annotated[str, Field(pattern=r'^[0-9a-f]{64}$')]
Code = Annotated[str, Field(pattern=r'^[a-z][a-z0-9_]{0,63}$')]
Seconds = Annotated[float, Field(gt=0, le=10, allow_inf_nan=False)]
Coordinate = Annotated[int, Field(ge=-1600, le=1600)]
Rectangle = Annotated[list[Coordinate], Field(min_length=4, max_length=4)]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)


class MemberInput(StrictModel):
    memberId: Annotated[str, Field(pattern=r'^[0-9]{5}$')]


class SavingsOutput(MemberInput):
    memberName: Annotated[str, Field(pattern=r"^[A-Za-z][A-Za-z .'-]{1,79}$")]
    accountType: Literal['Savings']
    currency: Literal['USD']
    amountMinor: Annotated[int, Field(ge=0, le=99999999999999)]


class Success(StrictModel):
    status: Literal['success'] = 'success'
    output: SavingsOutput


class BusinessOutcome(StrictModel):
    status: Literal['business_outcome'] = 'business_outcome'
    outcome: Literal['member_not_found']


class Failure(StrictModel):
    status: Literal['failure'] = 'failure'
    code: Code
    step: Name | None = None
    expected: list[Name] = Field(default_factory=list, max_length=2)
    observed: Literal['unavailable', 'checkpoint_not_satisfied', 'rejected'] = 'rejected'


RunResult = Annotated[Union[Success, BusinessOutcome, Failure], Field(discriminator='status')]


class Environment(StrictModel):
    platform: Literal['linux-x11']
    width: Literal[1280]
    height: Literal[800]
    locale: Literal['en-US']
    scale: Literal[1]
    ocrModelSha256: Digest
    minimumConfidence: Annotated[float, Field(ge=80, le=100)]
    ocrScale: Literal[3]
    ocrPSM: Literal[7]
    totalTimeoutSeconds: Annotated[float, Field(gt=0, le=60, allow_inf_nan=False)]


class Asset(StrictModel):
    file: Annotated[str, Field(pattern=r'^anchors/[a-z0-9-]+\.png$')]
    sha256: Digest


class Region(StrictModel):
    relativeTo: Name | None = None
    box: Rectangle
    clipToDisplay: bool = False

    @model_validator(mode='after')
    def ordered(self):
        x1, y1, x2, y2 = self.box
        if x1 >= x2 or y1 >= y2:
            raise ValueError('Region must have positive area')
        return self


class Anchor(StrictModel):
    kind: Literal['anchor']
    asset: Name
    region: Region
    threshold: Annotated[float, Field(ge=0.9, le=1, allow_inf_nan=False)]


class Point(StrictModel):
    kind: Literal['relative']
    region: Region


Target = Annotated[Union[Anchor, Point], Field(discriminator='kind')]


class ReadingField(StrictModel):
    region: Region
    parser: Literal['text', 'member_id', 'usd_minor']


class InputAssertion(StrictModel):
    kind: Literal['input_equals']
    field: Name
    input: Literal['memberId']
    prefix: Annotated[str, Field(max_length=80)] = ''
    suffix: Annotated[str, Field(max_length=80)] = ''


class TextAssertion(StrictModel):
    kind: Literal['text_equals']
    field: Name
    text: Annotated[str, Field(min_length=1, max_length=80)]


Assertion = Annotated[Union[InputAssertion, TextAssertion], Field(discriminator='kind')]


class Checkpoint(StrictModel):
    targets: list[Name] = Field(min_length=1, max_length=8)
    assertions: list[Assertion] = Field(default_factory=list, max_length=8)


class Postcondition(StrictModel):
    checkpoint: Name
    outcome: Literal['member_not_found'] | None = None


class StepBase(StrictModel):
    id: Name
    precondition: Name
    timeoutSeconds: Seconds


class ActionStep(StepBase):
    postconditions: list[Postcondition] = Field(min_length=1, max_length=2)


class Click(ActionStep):
    action: Literal['click']
    target: Name


class Type(ActionStep):
    action: Literal['type']
    input: Literal['memberId']


class Press(ActionStep):
    action: Literal['press']
    key: Literal['enter']


class Hotkey(ActionStep):
    action: Literal['hotkey']
    keys: list[Literal['ctrl', 'a']] = Field(min_length=2, max_length=2)

    @model_validator(mode='after')
    def selection_only(self):
        if self.keys != ['ctrl', 'a']:
            raise ValueError('Only select-all is supported in this version')
        return self


class OutputBindings(StrictModel):
    memberId: Name
    memberName: Name
    accountType: Name
    currency: Name
    amountMinor: Name


class Extract(StepBase):
    action: Literal['extract']
    fields: OutputBindings


Step = Annotated[Union[Click, Type, Press, Hotkey, Extract], Field(discriminator='action')]


class Capability(StrictModel):
    schemaVersion: Literal['1.0']
    name: Name
    capabilityVersion: Annotated[str, Field(pattern=r'^[0-9]+\.[0-9]+\.[0-9]+$')]
    provenance: Literal['manually-authored-poc']
    description: Annotated[str, Field(min_length=1, max_length=500)]
    inputSchema: dict = Field(json_schema_extra={'const': MemberInput.model_json_schema()})
    outputSchema: dict = Field(json_schema_extra={'const': SavingsOutput.model_json_schema()})
    environment: Environment
    assets: dict[Name, Asset] = Field(min_length=1, max_length=16)
    targets: dict[Name, Target] = Field(min_length=1, max_length=24)
    fields: dict[Name, ReadingField] = Field(min_length=1, max_length=24)
    checkpoints: dict[Name, Checkpoint] = Field(min_length=1, max_length=16)
    steps: list[Step] = Field(min_length=2, max_length=16)

    @model_validator(mode='after')
    def references(self):
        if (
            self.inputSchema != MemberInput.model_json_schema()
            or self.outputSchema != SavingsOutput.model_json_schema()
        ):
            raise ValueError('This schema version requires the published input/output definitions')

        def region_valid(region):
            if region.relativeTo is not None:
                if region.relativeTo not in self.targets or not isinstance(
                    self.targets[region.relativeTo], Anchor
                ):
                    raise ValueError('Relative regions must reference a declared anchor')
            elif not (
                0 <= region.box[0] < region.box[2] <= 1280
                and 0 <= region.box[1] < region.box[3] <= 800
            ):
                raise ValueError('Root search regions must fit the supported display')

        for name, target in self.targets.items():
            region_valid(target.region)
            if isinstance(target, Anchor) and target.asset not in self.assets:
                raise ValueError('Unknown anchor asset')
            if isinstance(target, Point) and (
                target.region.relativeTo is None or target.region.clipToDisplay
            ):
                raise ValueError('Click regions must be relative, without clipping')
            seen = {name}
            parent = target.region.relativeTo
            while parent is not None:
                if parent not in self.targets or parent in seen or len(seen) >= 8:
                    raise ValueError('Cyclic or excessive target dependencies')
                seen.add(parent)
                parent = self.targets[parent].region.relativeTo
        for field in self.fields.values():
            region_valid(field.region)
            if field.region.relativeTo is None or field.region.clipToDisplay:
                raise ValueError('OCR fields require an anchor-relative, unclipped region')
        for checkpoint in self.checkpoints.values():
            if any(name not in self.targets for name in checkpoint.targets):
                raise ValueError('Unknown checkpoint target')
            for assertion in checkpoint.assertions:
                if assertion.field not in self.fields:
                    raise ValueError('Unknown assertion field')
                if isinstance(assertion, InputAssertion):
                    parser = self.fields[assertion.field].parser
                    if parser not in ('member_id', 'text') or (
                        parser == 'member_id' and (assertion.prefix or assertion.suffix)
                    ):
                        raise ValueError(
                            'Input checks require an exact ID or a declared text context'
                        )
        if len({step.id for step in self.steps}) != len(self.steps):
            raise ValueError('Step identifiers must be unique')
        if not isinstance(self.steps[-1], Extract) or any(
            isinstance(s, Extract) for s in self.steps[:-1]
        ):
            raise ValueError('Exactly one final extraction is required')
        for step in self.steps:
            if step.precondition not in self.checkpoints:
                raise ValueError('Unknown precondition')
            if isinstance(step, Click) and step.target not in self.targets:
                raise ValueError('Unknown click target')
            if isinstance(step, ActionStep):
                if len({p.checkpoint for p in step.postconditions}) != len(step.postconditions):
                    raise ValueError('Duplicate postconditions')
                for post in step.postconditions:
                    if post.checkpoint not in self.checkpoints:
                        raise ValueError('Unknown postcondition')
                    if post.outcome and not any(
                        isinstance(a, InputAssertion)
                        for a in self.checkpoints[post.checkpoint].assertions
                    ):
                        raise ValueError('Business outcomes must verify the requested identity')
            else:
                for key, name in step.fields.model_dump().items():
                    expected = (
                        'usd_minor'
                        if key == 'amountMinor'
                        else 'member_id'
                        if key == 'memberId'
                        else 'text'
                    )
                    if name not in self.fields or self.fields[name].parser != expected:
                        raise ValueError('Invalid output field binding')
        return self
