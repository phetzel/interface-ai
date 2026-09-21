# Current planning direction

Updated 2026-09-20. M1–M3 are implemented, and the user completed their manual acceptance pass. M4 now has genuine discovery, a recorder, independent promotion and approved offline replay. M4-06 integrated acceptance and the full M1–M3 regressions passed; the [root README](../README.md) and [evidence index](../evidence/README.md) identify the final validation record.

## What is implemented

| Milestone | Result |
| --- | --- |
| M1 | Linux ARM64 desktop input across native/browser fixtures; relative visual targeting, local OCR and typed zero-model replay |
| M2 | Independent operation/artifact policy, isolated fixture gateway, closed evidence and sanitized export |
| M3 | One desktop session with Stop, ownership epochs, exclusive human control, verified original-member continuation and terminal evidence |
| M4-01 | Real OpenAI computer-tool transport, host-only key/SDK and stateless screenshot exchange |
| M4-02 | One coordinator for CLI, panel and discovery reservations; shared recognition and sanitized trace |
| M4-03 | Real goal-driven member-A discovery; bounded requests/actions/time; no scripted input sequence |
| M4-04 | Executed actions recorded as a typed candidate, explicit input binding and static-label crops |
| M4-05 | Unchanged member-B/translated evaluation, agent-reviewed promotion manifest and approved offline replay |
| M4-06 | Generated replay/handoff/negative evidence, offline/export proof, full regressions and operator UI checks passed |

The generated artifact preserves four model-selected inputs, rather than the manual artifact’s five-input sequence. It reuses reviewed bank environment/OCR/checkpoint annotations, including an explicitly unobserved missing-member branch. Agent review, simulated operator checks and the earlier real-person manual-artifact takeover are distinct claims.

## Accepted choices and limits

Python owns computer control and recognition; React/TypeScript supplies the synthetic bank. OpenAI is the only provider, with a private host key. The fixed environment is one 1280×800 Linux ARM64 X11 display, en-US/USD, pinned fonts/OCR and sandboxed Chromium. Native input and pixels are the runtime interface; DOM, fixture state and host test oracles are not runtime shortcuts.

The separate approval manifest binds exact bundle/asset digests and closed structural IDs. Only search completion → verified original-member overview → open Savings has automatic continuation. Other interruptions may transfer control but cannot invent a resume path. Candidate recording and review support the first savings workflow; arbitrary apps, general workflow editing and a revision registry remain outside scope.

Discovery uses at most 20 requests, 40 inputs, four batch items and 120 seconds. No-progress and uncertain-input handling fail closed. The host retains provider conversation items in bounded memory with `store: false`; local retention and provider data controls remain distinct. Offline replay has no provider SDK/key/route and makes zero model calls.

## M5 — Assessment readiness

The core M1–M4 implementation is complete. M5 closes the goal/target input gap, adds actual-size desktop viewing, writes the required report, rehearses setup from a fresh checkout and prepares submission evidence. See [M5 status](MILESTONE_5.md), [assessment coverage](ASSESSMENT_CHECK.md) and [REPORT.md](../REPORT.md).

[M5 validation and clean-checkout rehearsal passed](../evidence/m5-readiness/README.md) on executable source commit `2987382`. The fresh clone completed offline setup and a new real discovery → evaluated candidate → agent promotion → offline replay. The report, coverage map, submission draft and interview route are ready. Two intermittent native calibration startup timeouts are retained as an unresolved limitation; a subsequent full gate passed unchanged. No personal checklist results were completed by automation.

## Remaining author work

1. Read the report and verify that its explanations match your understanding.
2. The author reported generated-artifact takeover #41 complete on September 20. Preserve that observation and give feedback on the subsequent responsive operator layout; it does not require repeating all earlier tests.
3. Complete the repository/interview checklist and export both checklists from your browser.
4. Review the publication-ready repository, approve public visibility and send the submission email from your application address.

The [author review and delivery guide](SUBMISSION.md) provides the route and an unsent email draft. A new app, production orchestration and tenant infrastructure remain outside scope. UX-01 now has a tested actual-size mitigation, with personal usability acceptance pending.

[Full roadmap and original comparisons](ROADMAP.md) · [M4 specification](MILESTONE_4.md) · [M5 readiness](MILESTONE_5.md) · [manual audit observations](MANUAL_AUDIT_NOTES.md).

## Assessment cleanup

The public command surface is now eight commands; one named-suite runner replaces milestone-specific launchers and duplicate nested gates. The generated capability is the default. The historical manual bundle remains unchanged as the recognition/provenance baseline. Obsolete scripted bank vision and the standalone provider probe were removed; shared discovery reservation and internal transport diagnostics are separate. A nested same-origin iframe scenario exercises the existing bank without introducing a second business application. See [current development commands](DEVELOPMENT.md) and [cleanup validation](../evidence/assessment-cleanup/README.md).

## Operator workspace

The operator now starts bounded goal discovery, lists independently admitted saved workflows, and switches between the existing synthetic bank variants and native input pad. A local host service starts/stops with the existing desktop commands; SDK/key/Docker access remain outside the isolated runtime. App switching replaces the session, while takeover preserves it. See [operator design and validation](OPERATOR_WORKSPACE.md).
