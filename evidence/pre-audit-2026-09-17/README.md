# Pre-audit repair validation — 17 September 2026

The pre-audit repair passes the focused checks and complete policy/replay regression for local changes on top of `ec2b56e`. Nothing in this repair has been committed or pushed. The desktop is left on a fresh default bank search screen with input enabled; see [final readiness](final-ready.json).

The repair keeps the operator request-accepting loop nonblocking during human input, makes status polls return a temporary busy response, retains the existing sanitized interpreter events in handoff audits, and displays the current step, last verified checkpoint, and reason in the panel.

These checks use simulated input or an automated operator. They do not constitute a real-person demonstration or model discovery. The revised manual checklist starts with all checks unmarked.

## Focused checks

| Check | Evidence | Result |
| --- | --- | --- |
| New HTTP regression against baseline maintenance behavior | [Expected failure](stop-regression-before-fix.log) | Reproduces Stop waiting behind human input; fake backend, no OS input |
| Real HTTP/controller/adapter concurrency and diagnostics | [Focused test log](handoff-unit.log) | 22 tests pass; Stop interrupts typing, releases held modifiers, survives status polling; maintenance retries expiry without browser polling |
| Complete Linux engine suite and both handoff cases | [API acceptance](operator-api/summary.json), [engine log](operator-api/unit-tests.log) | 85 tests pass; both exact outputs, same sessions, restricted resume and sanitized interpreter trace pass |
| Scaled operator controls and visible step/reason | [Panel result](operator-ui/summary.json) | Takeover, rejected premature resume and completion pass at 1000 × 1200 |
| Panel Stop during a pending text request | [Final result](operator-stop/summary.json), [first result](operator-stop-first-summary.json) | Input rejected as stopped, same session, controls disabled after reload; observed HTTP response 42 ms, not a latency guarantee |
| Failed panel run and retained context | [Failure UI result](failure-ui/summary.json), [trace](failure-ui/audit.jsonl) | Actual blocked-search run shows search-member / checkpoint_timeout; safe trace retained and unsupported continuation remains disabled |
| Standalone manual checklist | [Browser checks](checklist-ui.log) | 35 initially unmarked checks; persistence, export, attestation, command validation, filtering and desktop/mobile layout pass |
| Repository/interview checklist | [Browser checks](repository-checklist-ui.log) | 31 initially unreviewed topics, interview prompts, independent storage, export, printing and responsive layout pass |
| Complete M2 policy gate and M1 regression | [Policy summary](policy-summary.json), [M1 summary](m1-summary.json), [replay cases](replay-summary.json) | Ten baseline replays, seven scenarios, seven rejection cases, native/browser input, isolation and safe export pass |
| Exact runtime and source | [Runtime](final-runtime.json), [source manifest](source-sha256.json), [final comparison](final-source-verification.json), [image IDs](images.jsonl) | All 63 runtime files, four schemas and 97 executable-source hashes match; replay uses zero model calls |

The first panel Stop screenshot was taken before the live frame finished loading after reload. Its behavioral result above is retained; the final Stop test rerun waits for the frame and also passes. A test-only wait added for that capture changed the source after the first full regression had frozen its manifest. That partial attempt was deliberately interrupted and is retained under [aborted-attempt](aborted-attempt/reason.json); its running/partial summaries are not passing acceptance evidence. The restarted regression passed with fixed source. The earlier handoff API run differs only by that [test-only screenshot wait](test-only-delta.json); its runtime and API harness match final source.

Full local attempts remain at `tmp/m2-checks/20260917T202056Z-04c71c44`, `tmp/m1-checks/20260917T202118Z-29e66b61`, `tmp/m3-checks/20260917T201423Z-ffa70f36`, and `tmp/pre-audit-2026-09-17/`. Per-case paths inside generated summaries refer to those original local folders. This index retains compact summaries and metadata rather than duplicating every calibration file. The fixture source was unchanged; the independent audit's 15 browser-test passes are not relabeled as a new fixture run here.

## Reproduce

Run `make build`, then `make handoff-check` and `make policy-check` sequentially. Each changes the same synthetic desktop. For the browser checks, use Node 22 and the repository Playwright cache:

```sh
make handoff-demo
PLAYWRIGHT_BROWSERS_PATH="$PWD/tmp/playwright" node scripts/checks/m3_operator_ui.mjs
make handoff-demo
PLAYWRIGHT_BROWSERS_PATH="$PWD/tmp/playwright" node scripts/checks/m3_operator_stop.mjs
make reset MODE=bank SCENARIO=default
```

The UI screenshots are explicit synthetic acceptance captures made by the trusted host test. The runtime still does not persist screenshots, typed text, raw keys or OCR business values. Handoff trace geometry is recognition-region metadata, not a recording of human input coordinates. This development evidence directory is distinct from M2's reconstructive safe-export output.

The manual audit remains pending. Discovery, generated-artifact promotion, unified CLI/panel coordination and broader failure escalation remain subsequent work.
