# M4 — Discover, record, review, and replay

Status: M4-01 provider/transport code and [genuine OpenAI acceptance](../evidence/m4-01-live-provider/README.md) passed 2026-09-20. M4-02 through M4-06 remain specified. [M4-01 setup, decisions and limits](M4_01_PROVIDER_PROBE.md). This specification was prepared 2026-09-19 after the M1–M3 manual acceptance pass.

## Outcome

Given the goal “Find the savings balance for member 00123” and the running synthetic bank desktop, OpenAI chooses and performs the UI actions through our guarded desktop adapter. A recorder produces a candidate capability from the actions actually executed. After explicit local review and promotion, that capability retrieves member 00456’s balance using only local vision/OCR, with zero model calls.

This is the largest remaining assessment requirement: genuine goal-driven discovery and an artifact demonstrably derived from it. M1–M3 already establish desktop input, manual-artifact replay, policy/evidence controls and same-session takeover. The real-person member-A recovery has now been witnessed; preserve that evidence rather than treating another simulated run as its replacement.

M4 is one complete savings-lookup workflow on the current Linux ARM64 desktop. It includes the lifecycle and artifact-admission changes needed to support that workflow. Cross-platform support, arbitrary workflow recovery, another provider, a workflow editor and operator click-targeting polish remain outside this milestone. The reported click difficulty remains tracked as UX-01 in [manual audit notes](MANUAL_AUDIT_NOTES.md).

## Research and decisions

Official documentation checked on 2026-09-19:

- OpenAI supports structured `computer` actions as well as code execution/custom UI tools. The current computer-tool examples use `gpt-5.6-sol` with Responses, can return multiple actions per call, and receive a screenshot in the corresponding tool output. This means our adapter must account for action batches and correlate tool calls with observations. [Computer use guide](https://developers.openai.com/api/docs/guides/tools-computer-use)
- `store: false` does not establish zero retention across all provider systems; abuse monitoring and other documented data controls remain relevant. Our local evidence policy and permission to transmit screenshots are separate boundaries. [OpenAI data controls](https://developers.openai.com/api/docs/guides/your-data)

- Responses also supports caller-managed conversation history with `store: false`; preserve replayable output/tool items rather than relying on stored response IDs. Test the exact computer-tool conversation with the pinned SDK. [Conversation state](https://developers.openai.com/api/docs/guides/conversation-state)

The choices below are our engineering recommendations, not claims that OpenAI supplies the recorder, policy enforcement or deterministic replay.

| Decision | Options and tradeoffs | Recommendation |
| --- | --- | --- |
| Model/action interface | Structured computer actions fit the existing adapter and expose each operation for checking. Custom functions could carry target annotations, but require another model-facing action protocol. Generated Python offers flexibility but expands execution authority and complicates recording. | Start with Responses + `computer` + GPT-5.6 Sol, subject to an actual account-access probe. Do not introduce generated code execution. Keep the model configurable and record the returned identifier. |
| Where the API key lives | Adding internet/key access to the desktop is simple but weakens our strongest isolation claim. A separate provider container adds packaging. A host client keeps provider access outside the desktop at the cost of a small transport boundary. | A pinned Python host client owns OpenAI requests. The desktop retains no key, model SDK or external route. |
| Runtime coordination | Keeping CLI and panel paths separate is quick but produces different takeover/status behavior. A large orchestration framework is unnecessary. | Extract one session coordinator and inject the admitted bundle/run mode. CLI, operator and discovery use its lifecycle; only one active run exists. |
| Durable targets | Coordinates are easy to record but fail when layout shifts. Asking a model to emit an entire workflow can invent steps or checks. Local anchors/OCR are already proven, but need reviewable annotations. | Record executed actions, build candidate targets from their observed frames, and require review of anchors, input bindings, extraction regions and checkpoints. Never promote raw coordinates alone. |
| Approval | Another hard-coded digest works for one artifact but spreads special cases. Trusting a candidate’s own “approved” field grants it authority. | A small operator-owned promotion manifest binds the exact reviewed bundle and continuation boundary. No general capability registry. |
| Diagnostics | Saving every screenshot makes investigation easy but changes retention substantially. Metadata alone needs enough context to explain failure. | Shared sanitized execution trace and a structured failure diagnostic. Keep candidate anchor crops in private synthetic staging under an explicit capture policy; export them only after review. Keep routine run evidence image-free. |

## Architecture and trust boundaries

```text
Host: make discover → Python provider client → OpenAI Responses
                            ↕ bounded authenticated messages
Isolated desktop: session coordinator ← operator UI on 6081
                    ↓                     (human owns input only after takeover)
               policy + epoch checks
                    ↓
               guarded OS adapter → X11 pixels / native input
                    ↓
               execution recorder → candidate bundle

Host review → approved manifest → same coordinator + local replay interpreter
                                  (no provider client needed)
```

The host client is trusted application code, not a model-controlled shell. It uses a fixed localhost destination and a separate per-run discovery capability provisioned through a fixed local launcher. The capability is absent from the operator HTML, model context and logs. The server chooses the trusted automation role; request JSON cannot choose human authority. Retain existing Host/Origin/token checks for the panel. Do not publish another port or place a Docker socket in the desktop.

Define only bounded start/observe/propose/status/stop operations for discovery. Bind every observation and proposal to run ID, desktop UUID, ownership epoch and a monotonically increasing sequence. Duplicate, late, foreign-session or consumed proposals are rejected. Validate message size, action count, coordinates, keys and text before dispatch. The host cannot silently use the human input endpoint as the model’s executor.

Extract a small recognition/checkpoint interface from the existing interpreter. Keep its strict identity, ambiguity and integer-money rules. This is a practical seam for discovery/recording and replay, not a replacement visual framework.

### Observation and execution policy

- Discovery is explicitly enabled only for the synthetic bank in the admitted image/session. Send the goal, typed synthetic member input and approved desktop pixels. Never send the host screen, environment variables, credentials, fixture source, hidden state or test oracle.
- Model suggestions remain untrusted. A separate discovery policy limits application identity, routes, allowed input primitives and visible read-only bank controls. It does not prescribe the workflow’s action order or feed the reviewed manual artifact to the model. Unknown or risky controls pause before input; the model cannot broaden the policy.
- Record an epoch before each model call; recheck it and the current screen before every primitive in an action batch. Stop/takeover discards the remaining batch. An uncertain dispatched input is never retried. Do not report an unexecuted batch as successful tool output.
- No model observation is captured or transmitted while the human owns the session. Drop queued unsent images on takeover. A request already sent cannot be recalled; discard its response after the epoch changes. After verified release, start from a fresh observation.
- Use foreground requests with `store: false`; retain required conversation/tool items in bounded memory rather than persisting a raw transcript. Implement and test the supported stateless conversation form before depending on it. Document provider retention separately.
- Proposed limits: 20 model requests, 40 input primitives, 5 minutes of active discovery, a 30-second request timeout and bounded output tokens per request. Pause on three repeated no-progress observations. Stop still interrupts locally without waiting for the provider. Human control retains its separate existing deadline. These are runtime safety limits, not a project schedule.
- Disable implicit SDK retries initially, so request counts and failures remain explainable. Track requests attempted, completed responses and billed usage when returned. A timeout may have incurred provider usage; mark it unknown. Any estimated spend guard is checked between requests and is not a provider-enforced dollar cap.
- Provider warnings/refusals, unexpected tool types, unavailable access and invalid output produce explicit outcomes. Never automatically acknowledge a provider safety challenge.

## From an executed run to a reusable artifact

The first recorder is intentionally narrow. The existing typed member input, savings output and Pydantic-derived JSON schemas remain the foundation. Schema 1.0 currently permits only manually authored provenance and click/type/Enter/select-all/extract steps, with at most 16 steps. Define a versioned generated-provenance contract; normalize provider key names before admission. If a genuine trajectory needs scrolling or additional steps, explicitly extend and test the contract or reject it as unsupported. Never silently omit an action to make recording fit.

1. Record ordered, admitted and actually dispatched primitives with call/action IDs, sequence, session/epoch and before/after observation references. An API proposal alone is not an executed step. Capture observations in memory around state changes.
2. Associate the typed member entry with the declared `memberId` input; do not replace every incidental occurrence of `00123` in the recording. Each binding has an explicit source action and reviewer-visible explanation.
3. Generate candidate label/anchor crops and relative target/extraction regions from the observed successful path. Keep only static synthetic labels; exclude member details, typed values and balances from retained anchors. Staging is a bounded, local development exception with its own capture policy and cleanup; full frames remain in memory. Never auto-export an unreviewed candidate image. Reject ambiguous or missing anchors.
4. Generate typed steps and draft pre/postconditions from that path. Unsupported operations or missing semantic annotations yield an incomplete candidate, not a silently substituted manual capability.
5. Present a file-based review summary: which parts were recorded, inferred, reused as environment rules, or edited by the reviewer. Human annotations of target/field/checkpoint semantics are allowed and must be attributed. The recorder still produces the ordered executed path; review cannot fabricate an absent discovery run.
6. Require local dry validation, candidate replay and explicit promotion. Preserve the pre-review candidate digest and a review delta alongside the promoted version. Discovery success and replay readiness are separate states.

Candidate replay is available only through an explicitly scoped local review command with the same desktop policy, input guards and zero-model boundary. It is not a general bypass of artifact admission. The ordinary demo loads approved bundles only.

Publish a new contract version with generated provenance and a separate promotion manifest; version 1.0 explicitly permits only the manual PoC. At minimum bind: discovery run ID and source/image fingerprints; provider/model identity and request count; candidate digest; reviewed capability version/digest and all anchor digests; policy version; reviewer decision and edits; environment requirements; allowed step/target/checkpoint IDs; and the declared continuation step/checkpoint. The approval file is operator-owned and read as a bounded regular-file snapshot. A bundle cannot approve itself.

Replace the manual digest/path, fixed event-ID vocabulary and numeric resume index with values validated against this admitted manifest. Allocate structural IDs in the recorder, not in model prose or user input, and admit only the reviewed manifest’s IDs. Do not weaken ID validation into free-form model text. Preserve manual provenance for the current PoC artifact. The generated artifact gets its own identity and path.

For M4, the only replay continuation remains the verified original-member overview before opening Savings. Resolve it by a declared checkpoint/step reference, not “step index 5.” Every other interruption can offer same-session human control, but resume is rejected without an admitted continuation. A changed member, stale UUID or ambiguous checkpoint cannot resume.

## Implementation sequence and blockers

| Step | Deliverable | Done when | Depends on |
| --- | --- | --- | --- |
| M4-01: Provider/transport PoC | Pinned optional host SDK, bounded protocol, synthetic observation policy and provider probe | A real model sees the admitted desktop and one proposed action reaches the guarded adapter; unsupported/late actions are rejected. Access failure is diagnosed without leaking a key. | Existing desktop; API key/access needed only for the real call |
| M4-02: Shared lifecycle | CLI, operator and discovery share one coordinator; recognition/checkpoint seam | CLI run is visible in the panel, can stop/escalate there, and cannot race another run. Existing replay/handoff tests still pass. | Can be developed with fake provider responses alongside M4-01 |
| M4-03: Bounded discovery | Goal → observe → model → validate → act → verify loop | Genuine member-A lookup succeeds from the search screen without feeding the known path; local visual checks validate the exact identity/output. Budget, stale response and stuck cases are demonstrated. | M4-01 + M4-02 |
| M4-04: Recorder PoC | Executed trajectory → candidate typed artifact and reviewed visual assets | Candidate is derived from that real run, carries input binding/provenance and validates without copying the manual sequence. Review edits are explicit. | M4-03; contract fixtures may be designed earlier |
| M4-05: Review and promotion | Independent manifest and generated-bundle admission | Editing any approved bytes fails closed. Second-member and translated-layout replay pass before promotion. Fixed path/digest/resume-index dependencies are removed. | M4-04; manifest/schema work can start after M4-01 |
| M4-06: Integrated evidence | Reproducible discovery, replay and takeover commands with sanitized evidence | The same promoted artifact replays offline for member B and recovers the expiry scenario in the original desktop session. Negative cases and model-call accounting are preserved. | M4-02 through M4-05 |

Start with the small provider/action PoC, then lifecycle integration. Do not invest in a general recorder before we have an actual model-produced trajectory. API access blocks the genuine model evidence, but not fake-provider tests, schema work or coordinator integration. Recorder viability and second-member replay block milestone completion; UI polish does not.

## Acceptance and evidence

| Check | Required observation |
| --- | --- |
| Genuine discovery | Live UI, real OpenAI response IDs/model usage, at least one model-chosen action, exact member-A result, and a successful bounded run. No scripted trajectory mislabeled as discovery. |
| Traceable artifact | Each recorded action maps to dispatched evidence; parameter/target/checkpoint derivations and review edits are inspectable. Bundle and promotion digests agree. |
| Offline reuse | Promoted artifact runs for `00456` with no provider client/key available and no desktop egress; output matches the separate host oracle. `modelCalls: 0` is supported by architecture and evidence. |
| Robust targeting | Same promoted artifact handles the existing translated-layout scenario; ambiguous or missing targets stop instead of guessing. |
| Distinct outcomes | Missing member remains a business outcome; wrong identity, blocked screen, policy rejection and timeout remain distinct failures/escalations. |
| Handoff | Generated artifact’s expiry run pauses, transfers input exclusively, rejects wrong-screen/member resume, and completes after verified recovery with unchanged session UUID. |
| Late responses / Stop | Delayed response after Stop/takeover/reset cannot dispatch; duplicate sequences and partial batches cannot replay input. |
| Artifact authority | Modified artifact/anchor, missing approval, unknown IDs, unsafe paths and undeclared continuation all fail before input. |
| Evidence/privacy | Shared replay/handoff trace retains safe step/target/checkpoint context and bounded failure diagnostics; no raw prompts, human text, OCR, API key or routine screenshots are exported. |
| Regression | Build identity, quick checks, fixture suite, M1/M2 policy gate and M3 handoff gate pass on the final source. Fake-provider tests are labeled separately from genuine discovery. |

Keep discovery metadata, reviewed candidate/provenance, approval manifest, second-member replay, one failure and generated-artifact handoff evidence in an indexed export. Explicit synthetic business results stay separate from routine metadata. Preserve failed attempts honestly. Use bounded, reviewed reason codes with human-readable explanations of action purpose and admission decisions; do not persist raw model reasoning. A short execution trace with checkpoints, selected targets, policy decisions and the failed expectation supplies the richer failure diagnostic; screenshots are not required for every failure.

Proposed commands below are an interface goal, **not available yet**:

```sh
make discover MEMBER_ID=00123    # Explicit online run; key supplied through host environment
make review RUN=<discovery-run>  # Validate candidate and show review/dry-run instructions
make promote RUN=<discovery-run> # Explicitly approve the exact reviewed bundle
make demo CAPABILITY=<approved-id> MEMBER_ID=00456
make handoff-demo CAPABILITY=<approved-id>
```

Reuse the current `make start` offline demo and operator at 6081. Keep setup concise; `make discover` should invoke the pinned host environment rather than require users to install SDK packages by hand. Never request a key in chat or commit an environment file containing one.

## Questions to settle through the first PoCs

| Question | Default / how we resolve it |
| --- | --- |
| Is GPT-5.6 Sol with the computer tool available on this API account? | Keep the accepted model choice. Verify with the first small real request; report access/tool incompatibility before changing models. |
| Can the recorder infer useful targets from these screenshots? | Attempt automatic static-label crops plus existing local recognition. Permit documented reviewer annotations. If most of the path must be rewritten, stop and revisit the recorder rather than calling the manual artifact generated. |
| Is stateless multi-turn computer use supported as configured? | Validate two consecutive tool turns with `store: false` and the pinned SDK. Keep protocol items in memory; do not quietly enable storage to make the PoC pass. |
| How strict can discovery’s action policy be without scripting the task? | Permit observed read-only controls/declared input while allowing the model to choose their order. A test must show unsafe controls denied and legitimate model-selected navigation accepted. Review any policy change independently of the model. |
| How much additional human demonstration is needed? | Existing manual-artifact handoff remains valid evidence. Add one concise generated-artifact handoff after integration, because its admission and resume references have changed. |

## After M4

Finish submission packaging: `REPORT.md` (roughly 1–3 pages with Architecture; Artifact schema; Determinism & error handling; Heterogeneity & multi-tenant; Escalation & handoff; Safety; Cuts), final evidence index, and a clean-clone rehearsal of the exact discovery/replay/handoff commands. Complete the separate repository/interview walkthrough. Fix UX-01 only if it materially improves the final demonstration without obscuring the core proof. Publication, pushes and submission remain subject to the user’s explicit request.
