# Bounded artifact interpreter · M1-05

The loader validates the complete capability and anchor bundle before any desktop acquisition. The interpreter then traverses its finite step list, resolves declared targets afresh from screenshots, dispatches through `Desktop.execute`, verifies postconditions, and returns the strict success/business-outcome/failure union. It imports local vision primitives, not the fixture-specific `BankVision` workflow.

`Observation` caches matches and OCR readings only within one screenshot. Parent anchors define relative regions; every click and extraction therefore starts from newly observed context. A final extraction reads and checks one image, preventing fields from different pages from being combined. Input bindings preserve leading zeroes. Only the artifact's named member-not-found alternative can finish without an output; it must include an exact input-bound identity assertion.

M1-06 found an intermittent malformed OCR identity immediately after typing. A malformed reading now leaves the checkpoint unsatisfied, just like a well-formed but incorrect ID. Postcondition polling can observe again within the existing deadline; it never retries input or repairs characters. Preconditions still reject unsatisfied screens, and direct extraction still rejects malformed identity. Three regression tests cover eventual exact matching, persistent-error timeout before search, and strict extraction.

Artifact and input models use [Pydantic strict validation](https://pydantic.dev/docs/validation/latest/concepts/strict_mode/) and forbid extra fields. Actions and result variants use [discriminated unions](https://pydantic.dev/docs/validation/latest/concepts/unions/). [JSON Schema export](https://pydantic.dev/docs/validation/latest/concepts/json_schema/) comes from those models; reference/graph/binding checks remain additional loader semantics.

```sh
# Inside the desktop image:
python -m interface_ai.cli validate-capability
python -m interface_ai.cli replay --member-id 00123
python -m interface_ai.contracts.schema
python -m interface_ai.contracts.schema --output-dir /artifacts/schemas
```

The Docker build copies reviewed schema exports; `make quick-check` fails on drift from the runtime models without rewriting them. To update repository exports, run the schema command in the image and write each named entry to `capabilities/schemas/<name>.schema.json`. Keep the Pydantic dependency pinned when regenerating.

The [manual capability README](../../../../capabilities/poc/savings-balance/README.md) describes the JSON, commands, exact output variants, and supported bounds. The operator command stores sanitized metadata/events and a separate explicit result. It deliberately does not persist screenshots. `capture_sink` is an in-process integration hook only; the artifact cannot configure code or export paths.

Tests cover malformed contracts and inputs, traversal/tampering, artifact-controlled ordering/output binding, early known-outcome termination, failed preconditions, ambiguous checkpoints, missing-postcondition timeouts, stop, no input retry, wrong identity, wrong output type, and preflight before desktop acquisition. `./scripts/desktop test` also runs all prior desktop and vision tests. The host integration harness compares real replay outputs with its separate oracle and checks that every case used the same artifact hash.

This is one deliberately constrained contract, not a general workflow language or a policy engine. The M1-06 repeated acceptance/evidence gate passes; see [acceptance evidence](../../../../evidence/poc-m1/acceptance/README.md). M2 enforces the bounded banking policy; CLI and panel now share one M4 coordinator with M3 ownership. Schema 1 preserves the manual artifact; schema 2 adds recorded discovery provenance. Independent promotion manifests bind the loaded bytes, asset hashes, closed identifiers and named continuation. Candidate evaluation has a separate local review scope and never approves itself. [Current evidence](../../../../evidence/README.md).

## M4 entry points

`Recognition` owns shared visual/OCR checks; `Interpreter` traverses the admitted steps. `replay.command` performs preflight, then the private coordinator client submits a single run. The server revalidates admission and refuses competing starts. `policy.admission` reads operator-owned manifests, while `policy.candidate` handles explicitly scoped evaluation of recorded candidates. Both use the guarded adapter and no provider SDK.

Use `make demo CAPABILITY=discovered-savings MEMBER_ID=00456` for the checked-in generated artifact. Its four recorded inputs are followed by one local extraction. Routine reports serialize structured generated provenance and retain modelCalls 0; source/provider IDs are provenance of discovery, not replay calls. [Review details](../../../../docs/M4_05_PROMOTION.md).
