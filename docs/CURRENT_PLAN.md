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

## Remaining after M4

1. Write the required `REPORT.md` with architecture, schema, determinism/error handling, heterogeneity/multi-tenant scope, escalation, safety and cuts.
2. Rehearse [the short demo](DEMO.md) from a clean clone, including setup and optional online discovery.
3. Complete the repository/interview checklist and explain the code in the user’s own words.
4. Decide whether to improve the scaled operator click targets (UX-01) before the final demonstration. It remains documented, not silently marked fixed.

The M4 supplement in the manual checklist and the new repository topics begin unverified. Existing saved checklist results refer to their original revision. Final publication/submission and further pushes require the user’s explicit request.

[Full roadmap and original comparisons](ROADMAP.md) · [M4 specification and tradeoffs](MILESTONE_4.md) · [review/promotion design](M4_05_PROMOTION.md) · [manual audit observations](MANUAL_AUDIT_NOTES.md).
