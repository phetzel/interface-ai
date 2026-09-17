# React component refactor validation · September 17, 2026

Baseline: pre-audit commit `a63a143a37d8410d4748605fe9bf6cd3848582e7`, committed and pushed before this refactor. The refactor is a local working-tree change. [source-sha256.json](source-sha256.json) identifies the fixture source, shared stylesheet, browser tests and launcher used for this validation. The earlier [pre-audit evidence](../pre-audit-2026-09-17/README.md) describes its own source revision; its manifest is not a claim about these later fixture changes.

## Scope

`App.tsx` now composes components. `useMemberWorkspace.ts` owns lookup/navigation and session restoration; `scenario.ts` validates launch configuration. The recovery form and synthetic policy probe own their local input state. Rendered text/elements/styles, display records and the independent oracle are preserved. No dependency, engine, policy, capability or runtime ownership change is included.

## Checks

| Check | Result |
| --- | --- |
| Host TypeScript and production build | Passed |
| Docker fixture production build | Passed |
| Existing fixture browser suite with stronger state-lifetime assertions | 15 passed; [summary](fixture-tests.json) |
| Before/after host Chromium comparison | 31 states have byte-identical screenshot PNGs and identical rendered app-shell DOM; [hashes](visual-comparison.json) |
| Nine real-desktop replay cases | 9 passed; [summary](replay-summary.json) |
| Both live simulated-operator handoff cases | 2 passed; [summary](handoff-summary.json) |

The browser comparison covers all eight launch scenarios, invalid/missing IDs, both savings identities, checking, blocked cancellation, recovery error/success and the policy probe. It uses 1280×800, en-US and UTC. Its trusted harness can read DOM and supply scenario configuration; this is fixture regression evidence, not computer-use or model-discovery evidence. Raw captures and the one-off comparison harness remain under ignored `tmp/frontend-refactor/`.

The first extended browser-test attempt had 14 passes and one timeout: the new policy-state assertion clicked a lower action covered by the pre-existing policy probe. It now uses the visible Member search breadcrumb. The app was not changed to accommodate this test. That failed attempt is retained in `tmp/frontend-refactor/first-fixture-test/`.

The replay run is retained at `tmp/replay-checks/20260917T205926Z-5e063b3d/`. Its nine fresh sessions cover both identities, missing member, both translated identities, delayed search, ambiguous savings, unreadable balance and blocked search. All actions use the existing screenshot/OCR interpreter and approved OS adapter; model calls remain zero.

The handoff run is retained at `tmp/m3-checks/20260917T210250Z-212ba522/`. Both members complete in the same session; the adversarial case rejects wrong-screen/member continuation, stale ownership and reused human input. This is an automated operator simulation, not a real-person demonstration.

The full M2/M1 acceptance gate and 85 engine tests were validated at the preceding pre-audit revision; they are not being represented here as rerun after this frontend-only change. Human audits and model-driven discovery remain pending. The source manifest and retained summaries are review evidence, not a general reliability claim.
