# Assessment coverage and final review

M5 checks the implementation against the original brief. Source citations below identify where each claim is implemented; the evidence index distinguishes historical revisions and provenance. This is an agent review, not the user's interview or manual-test sign-off.

| Requirement | Implementation / design | Verification |
| --- | --- | --- |
| 3.1 Goal + target and live model loop | [Request admission](../scripts/lib/discovery_request.py), [host loop](../scripts/lib/discovery_flow.py), [guarded worker](../engine/src/interface_ai/discovery/worker.py) | Explicit bounded natural-language goal and allowlisted target; genuine [recorded discovery](../evidence/m4-04-recorded-candidate/README.md); M5 fresh-checkout result below |
| 3.2 Typed reusable artifact | [Contracts](../engine/src/interface_ai/contracts), [recorder](../engine/src/interface_ai/discovery/recorder.py), [generated example](../capabilities/generated/savings-balance/capability.json) | Input binding, exact outputs, checkpoints, recorded/reused derivations and versioned provenance; [promotion evidence](../evidence/m4-05-promotion/README.md) |
| 3.3 Deterministic replay and exceptional states | [Interpreter](../engine/src/interface_ai/replay/interpreter.py), [recognition](../engine/src/interface_ai/replay/recognition.py) | [Generated nine-case matrix](../evidence/m4-06-integration/generated-replay-matrix/summary.json), exact member B, zero model calls, named missing-member outcome and explicit failures |
| 3.4 Configurable allowlist and conservative risky actions | [Admission](../engine/src/interface_ai/policy/admission.py), [operation policy](../engine/src/interface_ai/policy/bank.py), [gateway](../engine/src/interface_ai/policy/gateway.py), [Chromium policy](../infra/desktop/chromium-policy.json) | [Policy gate](../evidence/m4-06-integration/manual-policy-regression/summary.json); configuration is trusted operator-owned source/manifests, not model-writable policy |
| 3.5 Evidence and richer failure signal | [Run evidence](../engine/src/interface_ai/handoff/run_evidence.py), [exporter](../engine/src/interface_ai/policy/evidence.py) | [Failure trace](../evidence/m4-06-integration/generated-replay-matrix/cases/unreadable-a/events.jsonl), closed expected/observed metadata, separate synthetic results, no routine raw screenshots |
| 3.6 Real same-session takeover | [Coordinator](../engine/src/interface_ai/handoff/controller.py), [ownership](../engine/src/interface_ai/desktop/ownership.py), [panel](../engine/src/interface_ai/handoff/operator.js) | [Generated simulated handoffs](../evidence/m4-06-integration/generated-handoff/summary.json), [earlier real-person observation](MANUAL_AUDIT_NOTES.md), Stop during pending input |
| 3.7 Heterogeneity and multi-tenant design | [REPORT](../REPORT.md#heterogeneity--multi-tenant), [adapter protocol](../engine/src/interface_ai/desktop/types.py) | Native input tested independently; new application recognition/tenant bindings are explicitly design-only |
| 6.1 Source and README/demo commands | [README](../README.md), [short demo](DEMO.md) | M5 fresh-checkout rehearsal; no key needed for `make assess` |
| 6.2 Seven-heading write-up | [REPORT.md](../REPORT.md) | All seven exact headings; approximately 1–3 pages of design content, with explicit cuts and boundaries |
| 6.3 Genuine evidence and saved artifact | [Evidence index](../evidence/README.md) | Actual provider IDs, trajectory/candidate lineage, reviewed artifact, replay/error/handoff logs |
| Public repository and submission | [Delivery checklist](SUBMISSION.md) | Prepared; visibility change and submission remain pending user approval |

## M5 improvements and limits

- Closed the goal/target input gap. Accepted request examples are `Find the savings balance for member 00123` and `Read the current savings account balance for member ID 00456`. `find`, `read`, `get` and `look up` are supported; optional `please`, `the`, `current`, `account`, `synthetic bank` and `ID` are allowed. The full request must match the savings intent. Unsupported requests fail before reset/model calls and are not echoed into persisted evidence.
- Added `make assess`: build and replay the approved generated artifact for member B. The manual artifact remains available for historical audits.
- Added **Actual size / Fit to panel**, retaining the same image/input path. It makes small targets larger; no claim is made that every cause of UX-01 has been diagnosed. Human usability confirmation remains pending.
- Kept historical evidence and checklists intact. Current README/report/demo are the assessor entry points; dated design comparisons retain their historical status.

[M5 validation and clean-checkout evidence](../evidence/m5-readiness/README.md) is complete: full regressions, one-command offline setup, new genuine discovery, second-member/translated review, separate agent promotion and ordinary approved replay passed. Executable source is bound to commit `2987382` and the retained manifests. Two intermittent native calibration startup timeouts preceded the successful unchanged full run; their cause is unresolved and their failed records are preserved. The author reported generated takeover #41 complete on September 20; screenshots show the completed lookup. Interview understanding, exported self-reports and public submission remain with the author.

## Current cleanup and awkward-surface coverage

One named check runner replaces milestone commands; generated replay is the consistent default. The operator now keeps the desktop beside compact controls where space permits and places it first in narrow panes. The bank has a nested local-iframe scenario; it adds rendered-frame coverage without duplicating business logic. Same-origin frames are the demonstrated scope. Cross-origin integrations, framesets, new vendor applications and arbitrary goal understanding remain unclaimed. See [cleanup validation](../evidence/assessment-cleanup/README.md).

The operator now exposes that same bounded goal entry and the admitted workflow registry. App selection opens one of the fixed synthetic demos in a new session. The native pad can be manually controlled from the panel; it does not claim native business-workflow discovery. See [operator workspace](OPERATOR_WORKSPACE.md).
