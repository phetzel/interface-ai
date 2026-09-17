# M3 — Same-session takeover evidence

The implementation uses actual OS input in the existing isolated Linux ARM64 desktop. **The operator in these checks is an automated test, not a person. No model response or model call is represented by this evidence.** A real-person demonstration remains pending.

The September 17 audit subsequently found an HTTP Stop accept-loop defect that these historical checks did not cover. Use the [pre-audit repair validation](../pre-audit-2026-09-17/README.md) for the current local revision; this original record remains unchanged below.

## Final verification

[Final operator-API acceptance](final-operator-api/summary.json) passes for both members; its [engine log](final-operator-api/unit-tests.log) passes all **80 tests**. [Runtime verification](final-runtime.json) matches all **63 runtime files** to the final source, validates four exported schemas, and confirms the declared model-free/network properties. [Final image IDs](final-images.jsonl) identify the rebuilt images.

The regression directory retains selected summaries, logs and provenance; per-case paths inside the generated summaries refer to the original local attempts `tmp/m2-checks/20260916T013703Z-47faee86` and `tmp/m1-checks/20260916T013726Z-0f07a150`. Those full local attempts remain available; they are not duplicated wholesale into this archive.

The full prior [M2 policy gate](regression/policy-summary.json) and [M1 regression](regression/m1-summary.json) passed: ten baselines, seven scenarios and seven rejection cases, alongside native/browser/input/isolation checks. That full gate preceded the final ownership review. The [exact four-file delta](final-review-delta.json) comprises two runtime modules, their tests and the handoff harness: immediate revocation on expiry, external-stop visibility, and continuous human action numbering. The final engine suite and both live handoff cases recheck these changes; the 17-replay gate was not repeated after this focused update.

The [final panel test](final-operator-ui/summary.json) also passes at the smaller viewport. A separate [live external-stop check](external-stop.json) confirms `make stop` is reflected by the panel and invalidates its old lease without changing sessions.

## Initial recorded checks

| Check | Evidence | Result |
| --- | --- | --- |
| Two members, same-session restoration and exact final output | [Operator API acceptance](operator-api/summary.json) | Both pass against the host-only oracle; session UUID unchanged |
| Premature resume, wrong screen, wrong member | [Adversarial audit](operator-api/member-a-adversarial/audit.jsonl) | Rejected; human ownership retained |
| Automation exclusion and stale action | [Live delayed-action probe](operator-api/member-a-adversarial-late-automation.log) | Ownership rejection with zero completed inputs |
| No repeated search input | [Adversarial summary](operator-api/member-a-adversarial/summary.json), [second member](operator-api/member-b/summary.json) | Five automation actions per run; only the final account click occurs after resumption |
| In-flight drain, key release, stale epochs, duplicate requests, abandonment, HTTP protections | [Engine tests](operator-api/unit-tests.log) | Initial implementation: 78 tests pass |
| Real panel controls at a smaller viewport | [Operator UI test](operator-ui/summary.json) | 1000×1200 host viewport; scaled desktop clicks, rejected premature resume and successful completion; no page errors |
| Synthetic expiry fixture and prior fixture behavior | [Fixture tests](fixture-tests.json) | 15 tests pass |

The in-flight race uses real file locks with a fake input backend so the exact release ordering is deterministic. Live operator acceptance separately verifies the real OS input path. The delayed-action probe is a stale queued-action simulation, not an OpenAI test.

Each human action records its kind/status/duration/sequence, never its text, keys or coordinates. The negative test types a private sentinel into the password-masked synthetic field, clears it, and confirms it is absent from the audit. Live screenshots are memory-only. Final business outputs stay in ignored local run directories; this archive retains exact-oracle-match assertions rather than those result files.

## Reproduce

Build images, then run `make handoff-check`. It resets the synthetic desktop twice and leaves the second successful lookup visible. Every attempt, including failure, stays under `tmp/m3-checks/`. Run the panel test after another `make handoff-demo`:

```sh
PLAYWRIGHT_BROWSERS_PATH="$PWD/tmp/playwright" node scripts/checks/m3_operator_ui.mjs
```

Node 22 and the fixture's installed Playwright browser are required only for that UI test. The engine tests run inside the pinned desktop image. `make policy-check` reruns the preceding M2/M1 gates. `make handoff-demo` prepares the real-person demonstration.

## Development failures and scope

[Development notes](development/notes.json) retain the initial HTTP-test double error and missing host-browser-cache failure. The corrected checks reuse the existing dependency versions and browser installation. These were not silently treated as passing runs.

This entire archive is a development/acceptance record, not an output from M2's `export-evidence` command. Handoff `audit.jsonl` and `summary.json` are deliberately limited metadata; development logs contain test diagnostics and local environment paths. M2's reconstructive export remains limited to admitted replay bundles. There is no claim of arbitrary screenshot redaction, multi-user operator authentication, general UI recovery, or tested model discovery.
