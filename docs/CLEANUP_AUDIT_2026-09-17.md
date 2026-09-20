# Repository cleanup and improvement audit

September 17, 2026 · `a63a143` plus the local React refactor

**Implementation follow-up:** A1–A6 are addressed by the subsequent repository cleanup; see the [resolution and validation record](../evidence/cleanup-implementation-2026-09-17/README.md). The findings and reproductions below describe the original audited baseline and are preserved as history. A7–A9 were subsequently addressed by M4 ([shared lifecycle](../evidence/m4-02-shared-lifecycle/README.md) and [independent promotion](../evidence/m4-05-promotion/README.md)); A10 remains conditional distribution work.

The repository has sensible subsystem boundaries and meaningful defensive tests. It needs a focused cleanup pass, particularly around artifact loading, run lifecycle, evidence, test provenance and documentation. A framework rewrite would add work without resolving those problems. The largest remaining product requirement is still genuine discovery → reviewed artifact → model-free replay.

This audit covers the Python engine, contracts, recognition, replay, policy, handoff/API/operator UI, Docker/bootstrap/networking, launchers, acceptance harnesses, React fixture, documentation and evidence organization. The existing local React changes are included. No implementation files were changed by this audit, and nothing was committed or pushed. Findings below distinguish reproduced defects, source-confirmed gaps and maintainability recommendations.

## Priorities

“Now” means the next bounded repair/cleanup pass. “Next” belongs with discovery/integration. “Later” is useful only when its stated need arises. Size estimates describe relative scope, not a time commitment.

| ID | Priority | Finding | Evidence | Size |
| --- | --- | --- | --- | --- |
| A1 | Now | Artifact reads can block, and decoded anchor bytes can differ from verified bytes | Reproduced | Small |
| A2 | Now | Stopped handoff runs lack terminal result/summary files | Reproduced | Small–medium |
| A3 | Now | Invalid member input is reported as a server failure | Reproduced through HTTP | Small |
| A4 | Now | Acceptance provenance does not consistently bind source to the images actually tested | Source-confirmed gap | Medium |
| A5 | Now | No quick, enforced quality gate; dense code and duplicated test utilities make changes harder to review | Source review | Small–medium |
| A6 | Now | Current documentation contradicts itself and mixes active behavior with historical milestones | Verified examples | Small |
| A7 | Next | CLI replay and panel handoff need one run lifecycle and evidence contract | Existing integration gap, reconfirmed | Medium–large |
| A8 | Next | Recognition and continuation depend on interpreter internals | Source review | Medium |
| A9 | Next | Capability approval, event identifiers and resume position are scattered | Existing design constraint, reconfirmed | Medium |
| A10 | Later | Distribution, dependency ownership and OS rebuild reproducibility need an explicit contract | Source review; package installation not tested | Small–medium |

## A1 — Read and decode one bounded, verified artifact snapshot

At [loader.py:37](../engine/src/interface_ai/replay/loader.py#L37), the loader checks file size and calls `read_bytes()`. Neither the capability nor its anchors must be regular files. A named pipe reports a small size but its read waits for a writer; the desktop execution timeout has not started yet. Both capability and anchor FIFOs stayed blocked in isolated child processes and had to be terminated.

The same loader hashes an anchor's bytes at line 52, then reopens its path with `Image.open()` at line 54. A controlled replacement between these operations made it load different pixels while `admit(bundle)` still accepted the unchanged capability digest. This requires a concurrent writer to the bundle; it is a file-integrity defect, not evidence of a remote attack against the fixed local fixture.

**Suggested change:** introduce a small bounded regular-file reader, checking the opened descriptor with `fstat`, rejecting special files without blocking, and enforcing a limit on bytes actually read. Decode the verified bytes through `BytesIO` so the hash and image describe the same snapshot. Preserve the existing path-confinement and error-code rules. The evidence exporter already has a relevant bounded descriptor-reading pattern in [evidence.py:65](../engine/src/interface_ai/policy/evidence.py#L65); share only the low-level mechanics if doing so keeps dependencies simple.

**Validation:** FIFO capability/asset, oversized file, changed file, malformed PNG, symlink escape and valid bundle; assert bounded completion and zero desktop acquisition/input for rejected bundles. A replacement after hashing must either have no effect on decoded bytes or be rejected. Retain the current asset-tampering tests.

Reproductions: [file/HTTP/lifecycle probe](../evidence/cleanup-audit-2026-09-17/probe.py), [results](../evidence/cleanup-audit-2026-09-17/probe-results.json), [anchor replacement probe](../evidence/cleanup-audit-2026-09-17/asset-probe.py), [results](../evidence/cleanup-audit-2026-09-17/asset-probe-results.json).

## A2 — Finalize stopped and abandoned runs consistently

[Controller.stop()](../engine/src/interface_ai/handoff/controller.py#L85) revokes ownership and appends a lifecycle event. It does not set a terminal result or write the summary. The worker returns early when another transition supersedes it at [line 135](../engine/src/interface_ai/handoff/controller.py#L135), so it cannot supply those files afterwards. The probe stopped an active handoff and found only `audit.jsonl`; `controller.result` remained `None`.

This does not mean Stop failed to stop input. It means evidence consumers must infer termination from an event log, and stopped/expired/exceptional runs have a different artifact shape from completed runs.

**Suggested change:** one idempotent terminal-finalization path that records outcome, reason, last step/checkpoint, session, capability digest and counts. Keep lifecycle status separate from business-result status where necessary. Use atomic final-file replacement. Signal/revoke input immediately; evidence writing must not delay the Stop signal or introduce a new lock ordering. Define what happens when evidence storage fails, without logging request bodies or raw OCR values.

**Validation:** Stop during automation and human input, handoff expiry, repeated Stop, worker exception and successful completion. Each started run gets one coherent terminal record, no late success overwrites Stop, and the existing HTTP Stop/modifier-cleanup regressions still pass.

## A3 — Map domain errors at the HTTP boundary

[Controller.start()](../engine/src/interface_ai/handoff/controller.py#L92) calls `validate_inputs`, which raises `ReplayError('invalid_input')`. [The HTTP handler](../engine/src/interface_ai/handoff/server.py#L114) catches `DesktopError` and malformed JSON exceptions but not `ReplayError`. Submitting member ID `123` with a valid lease returned `503 {"code":"execution_failed"}`. No worker launched, so validation itself is effective; its public error classification is wrong.

**Suggested change:** explicitly translate expected domain validation failures into a stable client response, such as `400 invalid_input`. Keep malformed action, stale lease/ownership conflict, temporary busy state and infrastructure failure distinct. The panel should display a clear five-digit-ID message and preserve leading zeroes. Avoid consolidating every exception into one generic class merely to simplify the handler.

**Validation:** real HTTP requests for short/numeric/extra-field IDs, malformed JSON and stale leases. Verify status/code, no worker/input, and no echo of arbitrary submitted values. Retain a generic sanitized response for genuinely unexpected failures.

## A4 — Make acceptance prove which build it exercised

[m3-check](../scripts/m3-check#L175) hashes the host source before and after its run, but runs unit tests and desktop actions against an existing `interface-ai-desktop:local` image. An unchanged source tree is not proof that image contains that tree. [m1-check](../scripts/m1-check#L107) does compare many engine/infra/capability runtime files, but its mapping excludes the compiled React fixture. Recording a fixture image ID beside source hashes does not establish the relationship between them. The launcher intentionally reuses existing images; this is documented, but easy to miss while editing.

**Suggested change:** add one shared preflight that checks embedded build/source fingerprints for both desktop and fixture images and rejects a stale build before starting acceptance. For the fixture, generate a build manifest from reviewed source inputs and bind it to compiled asset hashes. For M3, reuse the existing engine runtime comparison instead of just recording host hashes. Do not expose these manifests to the task agent as fixture-data shortcuts.

**Validation:** intentionally change one source file without rebuilding and verify the gate refuses to label old-image execution as validation of that source; rebuild and verify it passes. Include untracked source files and compiled fixture output. Keep each attempt's source/build identity and failures.

For this audit specifically, all **30 engine Python source/test files were independently matched to the running image** before attributing the 85 passing tests to the working tree. [Runtime comparison](../evidence/cleanup-audit-2026-09-17/runtime-check.json).

## A5 — Add a small quality gate and make the busiest code readable

The repository has strong scenario tests, but no checked-in CI workflow, formatter/linter configuration, or quick aggregate check for typechecking, unit tests and schema drift. `make test` depends on a running desktop. The M3 harness already demonstrates that the Python suite can run in an isolated image without a live X11 session.

**Suggested sequence:**

1. Add a quick local target: verify the build fingerprint, run engine unit tests in a disposable network-disabled container, compare all four schema exports without overwriting them, and typecheck the fixture. Keep browser and full desktop acceptance as explicit additional gates.
2. Choose pinned formatting/lint tools and apply them to active source only. Start with useful unused-import and correctness rules; avoid a large style-rule backlog. Wire the same checks into CI when the repository is ready. Do not reformat captured patches, logs or historical evidence.
3. Reformat [controller.py](../engine/src/interface_ai/handoff/controller.py), [operator.html](../engine/src/interface_ai/handoff/operator.html), and the compact host harnesses in a mechanical change, separate from behavior changes. The small line counts currently hide dense multi-statement lines.
4. Extract only repeated harness infrastructure: bounded command execution/log retention, run-directory creation, source/runtime fingerprints and summary writing. Keep case assertions explicit and each oracle outside the runtime. The two operator-browser checks also repeat polling and scaled-coordinate handling.

For the operator panel, separate request handling, state rendering and desktop-coordinate conversion into named functions/modules, and move styles out of compressed lines. There is no need to convert it to React just for consistency. External assets would require deliberate server routing, package inclusion and CSP handling; keep the process token out of URLs and preserve the special Stop-during-input behavior.

Add lightweight types where they protect real boundaries: a desktop-backend protocol, ownership/phase literals or enums, an operator snapshot/request contract, and a small run-evidence interface. Avoid annotating every test helper or introducing a general orchestration framework.

**Validation:** the existing 85 engine tests, fixture tests and schema comparison for mechanical/type changes; both actual panel tests for operator changes; all affected live suites for shared harness changes. A quick gate should fail on an intentionally stale schema and should not regenerate it silently.

## A6 — Establish one current entry point and keep history clearly historical

Specific contradictions make the repo harder to explain in an interview:

- [MILESTONE_3.md:3](MILESTONE_3.md#L3) says the pre-audit repair is uncommitted/unpushed, although it is in `a63a143` on `origin/main`.
- [CURRENT_PLAN.md:3](CURRENT_PLAN.md#L3) still describes the M3 baseline's 80 engine tests, while current validation has 85. Historical counts are useful, but should not look like the current status.
- [vision/README.md:36](../engine/src/interface_ai/vision/README.md#L36) says the primitive probe retains captures; its current export function suppresses them. It also describes M1-05/M1-06 as future work.
- [replay/README.md:25](../engine/src/interface_ai/replay/README.md#L25) and the [capability README](../capabilities/poc/savings-balance/README.md#L45) still describe policy/human ownership as future work without clearly separating the historical milestone from current integrations.

**Suggested change:** use the root README for current setup/status and a short architecture/reading route. Keep milestones as dated design/history records with explicit supersession links. Make `AGENTS.md` primarily durable working rules plus links; avoid duplicating a long rolling validation narrative. Add a compact evidence index mapping claim → test/run → source revision → limitation. There are **719 tracked evidence files, about 4.5 MB**: navigation is the issue, not disk usage. Retain failed attempts and exact provenance; do not delete them to make the repo appear smaller.

The two audit HTML pages share presentation/storage mechanics but deliberately use independent progress keys. A small generation/template step is worth considering only if another checklist is added or repeated edits become painful; preserve standalone offline use and separate reviewer results. Their application logic does not need to become part of the runtime app.

**Validation:** follow setup from a clean checkout, verify commands and source links, and check that “implemented,” “automated test passed,” “human witnessed” and “model discovered” remain separate claims. Updating documentation must not prefill human audit results.

## A7 — Unify run lifecycle before adding discovery-driven recovery

[CLI replay](../engine/src/interface_ai/replay/command.py#L53) constructs an interpreter directly. [Panel execution](../engine/src/interface_ai/handoff/controller.py#L125) constructs another with expiry detection, ownership transitions and a different evidence shape. The CLI run is not the panel's run. The panel escalates only the known expiry at `search-member`; other failures become terminal states that reject takeover. The safe exporter accepts replay directories, not the handoff event envelope.

**Suggested change:** one coordinator owns run identity, lifecycle, deadlines, ownership, continuation and evidence. CLI and HTTP are adapters to that coordinator. Give exceptional outcomes explicit choices: reviewed continuation, human inspection/manual completion, or abort/reset. Share the sanitized event schema and provide a reviewed export path for handoff runs. Keep business results separate from shareable diagnostics.

A controller cleanup should expose a small transition table and a terminal finalizer, rather than spreading lock acquisition across many new classes. Retain epochs, the input-lock drain barrier and the current verified original-member boundary. Generic mid-step resume would be a new feature with a new proof burden.

**Validation:** start the same workflow through either entry point and observe/control the same run; identical result/event semantics; tested ownership/Stop races; correct handling of expiry, ambiguity, timeout, business outcome and arbitrary interruption. No automatic repeat of an uncertain action.

This is an integration milestone, not a prerequisite for formatting or the three small repairs above. It should accompany the next discovery-to-replay work rather than becoming an open-ended cleanup project.

## A8 — Give recognition and checkpoint verification explicit interfaces

[Observation](../engine/src/interface_ai/replay/interpreter.py#L12) receives the whole interpreter and reaches into its bundle, guards, deadline, clock, OCR, inputs and event sink. [BankPolicy](../engine/src/interface_ai/policy/bank.py#L34) fabricates a partial interpreter with `SimpleNamespace` just to locate approved targets. [Resume](../engine/src/interface_ai/handoff/controller.py#L205) mutates `runner.step` and `runner.step_deadline` to verify a checkpoint. These are useful seams obscured by implicit dependencies.

**Suggested change:** separate screenshot recognition/checkpoint evaluation from sequence execution. Pass the small set of dependencies explicitly, or through a typed observation context, and expose a public bounded checkpoint-verification operation. Keep target/OCR caching scoped to one screenshot. Policy should retain its independently approved bundle, even if it shares the pure recognition implementation.

Treat [BankVision](../engine/src/interface_ai/vision/bank.py) and its duplicated calibration anchors as a legacy primitive/calibration path. Label and test that role clearly; avoid evolving two competing production workflow implementations. Consolidate shared primitives, not independent fixture oracles or policy authority.

**Validation:** fake backend/clock tests for deadlines and errors, checkpoint identity checks, policy targeting, then replay and handoff live suites. Never combine fields read from different screenshots, leak OCR values into routine events, or make policy trust caller-selected targets.

## A9 — Keep reviewed capability configuration together

The capability's scope is deliberately narrow, but introducing a generated artifact currently requires edits in several places: [provenance/business shapes](../engine/src/interface_ai/contracts/models.py#L179), [approved digest/path](../engine/src/interface_ai/policy/bank.py#L14), [safe identifier vocabulary](../engine/src/interface_ai/policy/evidence.py#L22), and [resume index 4/checkpoint](../engine/src/interface_ai/handoff/controller.py#L142).

**Suggested change:** one small operator-reviewed promotion manifest binds the candidate artifact's digest, provenance, allowed metadata identifiers, policy profile and named continuation boundary. Resolve the continuation by reviewed step/checkpoint names and validate the relationship at load time. Keep numeric limits and operation permissions under runtime/operator authority. Do not let model-authored content extend its own allowlist.

The `frozen=True` model setting also does not make nested lists/dictionaries immutable. There is no demonstrated exploit in the trusted runtime, but internal code should not mutate a loaded approved capability; either make that ownership rule explicit or create an immutable execution representation during promotion.

**Validation:** reviewed artifact accepted; altered/unreviewed digest, invalid vocabulary, nonexistent continuation and unsafe override rejected. Prove a genuinely discovered run replays for the other member with zero model calls. Keep the independent result oracle unchanged.

## A10 — Clarify the supported build/distribution contract

The current Docker path is credible and tested. The repository also has Python package metadata and an entry point, but the image imports a copied tree through `PYTHONPATH` rather than installing that package. [Package data](../engine/pyproject.toml#L18) explicitly lists vision anchors, not `handoff/operator.html`; [REVIEWED_PATH](../engine/src/interface_ai/policy/bank.py#L16) assumes the current source-tree/`/opt` layout. A standalone wheel is therefore not an established supported distribution. No wheel-install test was performed in this audit.

**Suggested change:** keep Docker as the documented submission path. If a wheel is later required, package resources deliberately, resolve them through a resource API/configured reviewed bundle location, and test installation from outside the source checkout. Do not add package-distribution work to the immediate assignment milestone without that need.

Related small improvements:

- Choose one authoritative direct-dependency list; [pyproject.toml](../engine/pyproject.toml) and [requirements.in](../infra/desktop/requirements.in) currently repeat it. Preserve the hash-locked runtime and keep future model credentials/SDKs outside model-free replay where required.
- The [desktop base image](../infra/desktop/Dockerfile#L11) is digest-pinned and Tesseract is version-pinned, but most apt packages, including Chromium and fonts, are selected from the current repository at build time. Preserve a validated image identity and environment manifest, and validate controlled rebuilds. A base digest alone does not freeze those later packages.
- Consolidate runtime-path ownership: [bootstrap helpers](../infra/desktop/common.py#L8) hard-code `/tmp/interface-ai`, while [engine session code](../engine/src/interface_ai/desktop/session.py#L6) supports an override. Avoid implying that a partial override relocates the whole desktop.
- Keep supported architecture/display/locale explicit. Broader OS, screen scaling and locale support are feature work, not cleanup.

## What should remain intact

- Exact string identity checks and integer minor-unit money values.
- Separate success, business outcome and failure results.
- One guarded input adapter; fail-closed ambiguity and bounded observation waits.
- Independent policy authority, application/focus checks and restricted routes.
- Epoch revocation, quiescence and modifier cleanup. The earlier HTTP Stop acceptance-loop bug is fixed and its current regression tests pass.
- Per-screenshot recognition caches, strict artifact validation and separate fixture oracles.
- Honest provenance: manual capability, simulated operator, real person and real model run are different evidence categories.
- The recent React component split. Its shared CSS and three-view state hook are reasonable at this size; adding a router/global store/design system would not address the findings here.

## Suggested implementation sequence

| Change set | Scope | Completion gate |
| --- | --- | --- |
| 1. Correctness repairs | A1 loader snapshot/bounds, A3 HTTP error mapping, A2 terminal finalization; separate small commits | Focused regressions plus existing engine/Stop tests; live handoff after finalizer changes |
| 2. Build and review confidence | A4 image/source preflight, A5 quick check and mechanical formatting, A6 current docs/index | Deliberately stale images/schemas rejected; existing gates still pass; interview reading path works |
| 3. Execution integration | A7 shared coordinator and evidence contract; A8 explicit recognition/checkpoint seam | Both entry points, exceptional runs and handoff behave consistently |
| 4. Assignment completion | A9 reviewed promotion alongside real discovery, second-member replay, real-person audit, demo/report | Actual model evidence, zero-model replay evidence, witnessed intervention and required deliverables |

Keep formatting, source moves and behavior changes reviewable separately. Do not delay the real discovery milestone to finish optional packaging or generalized architecture. `REPORT.md`, end-to-end discovery commands and the pending human demonstration remain deliverables, not defects that a refactor can close.

## Validation and limits

Fresh in this audit: **85/85 engine tests** in the declared Linux image, including the current HTTP Stop regressions and Linux OCR tests; **30/30 engine Python files** matched between working tree and image; **4/4 repository schemas** matched the verified runtime models; the isolated file-loading, hash/decode, terminal-evidence and real-HTTP validation probes above.

The preceding frontend-refactor validation remains applicable because this audit changed no implementation: **15 fixture tests, 31 exact before/after visual/DOM comparisons, nine desktop replay cases and two simulated-operator handoff cases**. Those runs were not repeated as part of this audit. See [their separate record](../evidence/frontend-refactor-2026-09-17/README.md).

The full M2/M1 acceptance gate was not rerun here. The earlier pre-audit record retains it against its own source revision. This review did not run a new real-person audit, model discovery, dependency vulnerability scan or standalone package-install test. Source review findings are not claims that every possible race or deployment environment was exercised.

Audit evidence: [index](../evidence/cleanup-audit-2026-09-17/README.md) · [source fingerprint](../evidence/cleanup-audit-2026-09-17/reviewed-source-sha256.json).
