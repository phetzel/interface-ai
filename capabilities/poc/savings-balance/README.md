# Savings balance · manual PoC capability 0.1.0

[capability.json](capability.json) is deliberately **manually authored**, using the M1-04 visual calibration. It is not the result of model discovery. The bundle includes all seven static label anchors, their hashes, supported environment, input/output definitions, visual checkpoints, ordered steps, and the known member-not-found outcome. [Anchor provenance](anchor-provenance.json) distinguishes the earlier M1-03 label crops from the M1-05 missing-member label; none contains a dynamic member ID or balance.

From the repository root:

```sh
./scripts/desktop build
./scripts/desktop reset bank
./scripts/desktop validate-capability
./scripts/desktop replay --member-id 00123
```

Use a fresh `reset bank` for each invocation. `00456` exercises a different member and balance; `00999` returns `member_not_found`. To test the unchanged artifact with translated content, use `reset bank translated` before replay. `./scripts/replay-check` runs the nine integration cases; `./scripts/replay-check --acceptance` runs ten baselines plus seven scenarios. The full M1-06 gate passes and is reproducible with `./scripts/m1-check`; see [acceptance evidence](../../../evidence/poc-m1/acceptance/README.md).

The image contains this bundle at `/opt/capabilities/poc/savings-balance/`. `--capability PATH` selects another operator-supplied bundle inside the container. All references are relative to its JSON file, so moving the whole directory preserves it. No member data, fixture oracle, host paths, executable expressions, or model credentials belong in the artifact. The optional `--inputs-json '{"memberId":"00123"}'` invocation uses the same strict input contract. `--session ID` can bind to an explicitly observed session; otherwise the command observes the current session immediately before acquisition.

## Sequence and outcomes

1. Require the search page and click the input resolved from its label.
2. Select existing input through the shared desktop adapter.
3. Type the bound member ID and verify the displayed field equals it.
4. Press Enter and wait for either the matching member page or the known not-found message containing the exact queried ID.
5. Require the matching member, resolve a unique Savings row and its button, then verify the account identity, type, and currency.
6. Extract all output fields from a single new screenshot and validate the output before returning success.

The file supplies this sequence and every target/field region; the interpreter does not call `BankVision` or the M1-04 probe. The current schema supports only click, select-all, bound member typing, Enter, and final extraction. It has no arbitrary loops, jumps, code, shell actions, browser navigation, or callback names. The sole declared branch terminates with the named business outcome.

An invocation returns one of the published [result schema](../../schemas/result-v1.schema.json) variants:

- `success` with `memberId`, `memberName`, `accountType`, `currency`, and integer `amountMinor`.
- `business_outcome` with `outcome: member_not_found` and no fabricated output.
- `failure` with a code, failed step, expected checkpoint/output summary, and observed-state category. No partial OCR values are returned.

The printed evidence directory contains `report.json`, `events.jsonl`, and `result.json`. Explicit output values live only in the result file; routine events omit typed text, recognized identities/balances, and raw key sequences. This command retains no screenshots: observations and OCR crops stay in memory. The operator’s live image still shows the same desktop. CLI replay status comes from its terminal/result files until lifecycle integration in M4. These are synthetic local results, not a general financial-data retention policy.

## Validation and supported bounds

The [Pydantic models](../../../engine/src/interface_ai/contracts/models.py) are authoritative. They generate the [capability](../../schemas/capability-v1.schema.json), [input](../../schemas/input-v1.schema.json), [output](../../schemas/output-v1.schema.json), and result schemas. The portable JSON Schemas describe structural constraints; the loader additionally checks references, anchor dependency cycles/depth, output bindings, a final extraction, and branch identity checks. A plain JSON Schema check alone is not sufficient to authorize execution.

Loading rejects unsupported versions/actions, unknown fields/references, duplicate JSON keys, non-finite values, invalid regions, altered assets, and paths escaping the bundle. Artifact/input/asset checks finish before desktop acquisition or input. Capability and PNG reads reject special files, bound bytes read, and decode the exact verified anchor snapshot. No automatic retry repeats an input whose result is uncertain.

Every input has a precondition and bounded postcondition; only observations are polled. A step has a five-second budget in this artifact, and the entire desktop execution has a 45-second budget. Session/focus/display/stop checks run around observations and again before dispatch. OCR uses a bounded subprocess with the remaining step budget. Multiple matching postconditions or targets fail instead of selecting the highest score.

The supported environment is the existing isolated Linux X11 desktop, 1280×800, current fonts/theme, en-US/USD, and the tested 100% scale/+40 px translation. OCR/model assets and settings remain the M1-04 calibration. Locale and browser scale are established by trusted bootstrap; the artifact declaration does not independently detect arbitrary runtime scale/theme changes. M2 enforces a bounded route/operation policy; M3 adds same-session human takeover at the reviewed continuation. Generated-capability promotion, discovery and general recovery remain later work. [Current evidence](../../../evidence/README.md).

The schema version (`1.0`) describes the contract; the capability version (`0.1.0`) identifies this manual workflow. Each run records the exact JSON SHA-256 and capability version. Anchor hashes bind the associated visual assets. JSON changes require a new reviewed capability revision before broader use.
