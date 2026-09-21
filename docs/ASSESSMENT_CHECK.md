# Assessment coverage

This map distinguishes implemented behavior, demonstrated coverage and design proposals. [The evidence index](../evidence/README.md) identifies tested revisions and provenance.

| Requirement | Implementation / design | Verification |
| --- | --- | --- |
| 3.1 Goal, target and live model loop | [Request admission](../scripts/lib/discovery_request.py), [host loop](../scripts/lib/discovery_flow.py), [worker](../engine/src/interface_ai/discovery/worker.py) | Bounded savings goals; [genuine recorded discovery](../evidence/m4-04-recorded-candidate/README.md) |
| 3.2 Typed reusable artifact | [Contracts](../engine/src/interface_ai/contracts), [recorder](../engine/src/interface_ai/discovery/recorder.py), [generated bundle](../capabilities/generated/savings-balance/capability.json) | Explicit input binding, recorded/reused derivations and [independent promotion](../evidence/m4-05-promotion/README.md) |
| 3.3 Deterministic replay and exceptional states | [Interpreter](../engine/src/interface_ai/replay/interpreter.py), [recognition](../engine/src/interface_ai/replay/recognition.py) | [11 generated cases](../evidence/pre-submission-fixes/replay/summary.json): both members, translated/iframe layouts, delays, ambiguity, missing member and failures |
| 3.4 Allowlist and risky-action handling | [Admission](../engine/src/interface_ai/policy/admission.py), [operation policy](../engine/src/interface_ai/policy/bank.py), [gateway](../engine/src/interface_ai/policy/gateway.py) | [Policy gate](../evidence/pre-submission-fixes/policy/summary.json); trusted configuration cannot be expanded by the model |
| 3.5 Evidence and failure diagnostics | [Run evidence](../engine/src/interface_ai/handoff/run_evidence.py), [exporter](../engine/src/interface_ai/policy/evidence.py) | [Unreadable-output trace](../evidence/pre-submission-fixes/replay/cases/unreadable-a/events.jsonl); closed metadata and separate synthetic results |
| 3.6 Same-session human takeover | [Coordinator](../engine/src/interface_ai/handoff/controller.py), [ownership](../engine/src/interface_ai/desktop/ownership.py), [panel](../engine/src/interface_ai/handoff/operator.js) | [Automated generated handoffs](../evidence/pre-submission-fixes/handoff/summary.json), [reported human observations](HUMAN_OBSERVATIONS.md), [pending-input Stop](../evidence/pre-submission-fixes/operator/operator_stop/summary.json) |
| 3.7 Heterogeneity and tenant design | [Report](../REPORT.md#heterogeneity--multi-tenant), [adapter](../engine/src/interface_ai/desktop/types.py) | Native primitives and nested local frames demonstrated; new vendor/tenant bindings are design-only |
| 6.1 Source and reproducible commands | [README](../README.md), [demo](DEMO.md) | [Clean-source rehearsal](../evidence/m5-readiness/clean-checkout/summary.json); [latest one-command demo](../evidence/pre-submission-fixes/assess/summary.json) |
| 6.2 Design write-up | [REPORT.md](../REPORT.md) | Seven required sections, explicit tradeoffs and cuts |
| 6.3 Genuine evidence and saved artifact | [Evidence index](../evidence/README.md) | Provider IDs, recorded trajectory, candidate lineage, reviewed artifact and offline reuse |

## Demonstrated limits

- Goals use a documented savings-intent grammar. Arbitrary natural-language tasks are unsupported.
- Bank recognition is specific to one synthetic application, Linux ARM64/X11, 1280×800 and en-US/USD. Cross-origin applications, framesets and native business workflows are unproven.
- Generated actions are recorded; OCR/checkpoint annotations reuse a reviewed bank profile. The promotion is agent-reviewed.
- Automated tests do not substitute for real-person observations. The later operator's usability remains subject to personal feedback.
- Intermittent native calibration startup timeouts remain unresolved. Successful reruns and earlier failures are both retained.

Current entry points are `make assess`, `make discover`, `make handoff` and `make check`. See [development](DEVELOPMENT.md) for prerequisites and named suites.
