# Bounded artifact interpreter · M1-05

The loader validates the complete capability and anchor bundle before any desktop acquisition. The interpreter then traverses its finite step list, resolves declared targets afresh from screenshots, dispatches through `Desktop.execute`, verifies postconditions, and returns the strict success/business-outcome/failure union. It imports local vision primitives, not the fixture-specific `BankVision` workflow.

`Observation` caches matches and OCR readings only within one screenshot. Parent anchors define relative regions; every click and extraction therefore starts from newly observed context. A final extraction reads and checks one image, preventing fields from different pages from being combined. Input bindings preserve leading zeroes. Only the artifact's named member-not-found alternative can finish without an output; it must include an exact input-bound identity assertion.

Artifact and input models use [Pydantic strict validation](https://pydantic.dev/docs/validation/latest/concepts/strict_mode/) and forbid extra fields. Actions and result variants use [discriminated unions](https://pydantic.dev/docs/validation/latest/concepts/unions/). [JSON Schema export](https://pydantic.dev/docs/validation/latest/concepts/json_schema/) comes from those models; reference/graph/binding checks remain additional loader semantics.

```sh
# Inside the desktop image:
python -m interface_ai.cli validate-capability
python -m interface_ai.cli replay --member-id 00123
python -m interface_ai.contracts.schema
python -m interface_ai.contracts.schema --output-dir /artifacts/schemas
```

The Docker build regenerates its schema files automatically. To update repository exports, run the schema command in the image and write each named entry to `capabilities/schemas/<name>.schema.json`. Keep the Pydantic dependency pinned when regenerating.

The [manual capability README](../../../../capabilities/poc/savings-balance/README.md) describes the JSON, commands, exact output variants, and supported bounds. The operator command stores sanitized metadata/events and a separate explicit result. It deliberately does not persist screenshots. `capture_sink` is an in-process integration hook only; the artifact cannot configure code or export paths.

Tests cover malformed contracts and inputs, traversal/tampering, artifact-controlled ordering/output binding, early known-outcome termination, failed preconditions, ambiguous checkpoints, missing-postcondition timeouts, stop, no input retry, wrong identity, wrong output type, and preflight before desktop acquisition. `./scripts/desktop test` also runs all prior desktop and vision tests. The host integration harness compares real replay outputs with its separate oracle and checks that every case used the same artifact hash.

This is one deliberately constrained contract, not a general workflow language or a policy engine. The M1-06 repeated acceptance/evidence gate and later model discovery/human ownership work remain pending.
