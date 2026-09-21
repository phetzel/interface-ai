# Pre-submission audit fixes

September 21, 2026. Working-tree changes after `5ef8f68`; the [source manifest](source-manifest.json) identifies executable/configuration bytes. The original independent audit and its failed reproductions remain unchanged. No paid provider calls, capability promotion, personal checklist changes, publication, commit or push are claimed by this record.

## Corrections

- **F1 — Recording completion:** a successful business lookup no longer implies a successful discovery recording. The worker records `recording_incomplete`; the host requires an explicit candidate status, directory reference and SHA-256 before success. The CLI preserves the typed lookup result but exits 1. The launcher says that recording is incomplete and no reviewable candidate exists. [The isolated worker → CLI → launcher reproduction](recording-integration.json) uses simulated provider/OS input and the real failure path. [Reproduction source](recording-integration.py) is retained; it runs in a network-disabled desktop image with the host scripts/build-manifest module mounted read-only.
- **F2 — Launcher shutdown:** non-daemon worker ownership and a retained process-group handle let shutdown drain the current job before the HTTP server exits. Cancellation prevents discovery after reset and stops the replacement desktop. Forced termination reaches shell/uv descendants and reaps the parent. New jobs are rejected while closing. Desktop teardown waits for actual listener closure; incomplete cleanup fails explicitly. Closing an idle launcher does not stop a new CLI-created desktop. Real HTTP/synthetic-process tests cover drain, forced descendant cleanup, child timeout, and refusal after shutdown.
- **F3 — Transient OCR:** preconditions re-observe only `ocr_uncertain`, within the original step/desktop deadlines and ownership/Stop guards. Missing targets, wrong identity and malformed identity remain rejected. No input is repeated and no confidence threshold or approved artifact changes. Tests cover recovery from uncertainty, persistent uncertainty, Stop while waiting, and wrong identity after uncertainty.
- **F4 — Setup documentation:** the operator requires the private ignored `.env` file; environment-variable-only credentials are supported by CLI discovery. Docker and desktop subprocesses still receive no provider key.

## Validation

[The quick gate](quick/summary.json) passed 133 Linux engine tests, 36 host tests (one intentional optional-SDK skip), six schema comparisons, formatting/lint and fixture typechecking. The detailed engine/host logs and build identity are alongside its summary. A separate run with the cached pinned SDK passed [all 36 host tests without skips](host-sdk-tests.log), using mocked provider transport. Host regressions use temporary loopback servers and synthetic child processes; engine regressions use simulated input/recognition.

The first live policy attempt failed while replacing the old launcher: macOS reset a connection before refusing subsequent connections. The corrected lifecycle loop continues observing a reset and waits for refusal before proceeding. [The failed attempt](launcher-restart-failure/summary.json), its log/source manifest, and its build record are preserved. A new host regression covers that sequence. Two standalone integration-harness attempts needed corrections: the initial invocation omitted the CLI build-manifest import mount, and a repeat reused an existing synthetic job directory. The retained reproduction now creates a unique directory for every attempt. These were harness setup errors, not product defects; their logs remain under local `tmp/pre-submission-fixes/`. The final network-disabled reproduction passed.

[All eight affected live suites passed](live-gates.json) on the frozen source bytes:

| Suite | Result |
| --- | --- |
| [Policy](policy/summary.json) | Admission, isolation, origin-IP rejection and safe export passed |
| [Generated replay](replay/summary.json) | 11 cases, including nested frames and shifted layouts |
| [Manual replay](manual-replay/summary.json) | 9 cases, including both members and shifted layouts |
| [Generated handoff](handoff/summary.json) | 2 cases, including wrong-screen/member rejection |
| [Manual handoff](manual-handoff/summary.json) | 2 cases, including wrong-screen/member rejection |
| [Simulated discovery](discovery/summary.json) | 6 real-desktop transport cases; no real model calls |
| [CLI/panel lifecycle](lifecycle/summary.json) | Expiry and blocked-policy cases |
| [Operator UI](operator/summary.json) | Responsive coordinates, completion and Stop during pending input; Stop responded in 69 ms |

Sanitized replay/handoff traces and separate synthetic results are retained alongside their summaries. Screenshots are not copied into this correction record. These are affected regressions, not a rerun of every historical acceptance test.

The agent also selected `manual-savings` in the browser, entered member B, and observed `Lookup complete` and `$98.07`. It then started a real app switch in the operator while a terminal observer waited for an active job before invoking `make down`. [The shutdown record](live-shutdown.json) confirms the job was active, teardown returned 0 after 20.32 seconds, ports 6081/6082 were closed, and all project containers remained absent immediately and eight seconds later. [The observer source](live-shutdown.py) and [command log](live-shutdown.log) are retained. This is agent-operated testing, not a real-person attestation.

Finally, [the one-command assessment demo](assess/summary.json) rebuilt/restored the project and replayed the generated workflow successfully for member B. The agent observed the correct balance in the operator, left it open, and confirmed [current image/source identity](assess/build-check.json).

No new live-provider cancellation was exercised. Existing intermittent native-startup behavior remains an acknowledged limitation; this focused follow-up does not claim to fix it. Supported goals, applications and automatic resume boundaries are unchanged.
