# M5 assessment readiness

Prepared on September 20, 2026. Executable changes are committed as `2987382866f677a7915a8d0103bf03ecbebc092f`; later changes package documentation and evidence. [Build identity](build-preflight.json) binds the desktop and fixture bytes. [The validation summary](summary.json) records the completed agent work. Personal checklist answers and publication are separate from this agent validation.

M5 adds explicit bounded goal/target admission, the one-command `make assess` demo, an actual-size operator view, the required seven-heading report, a brief-to-code coverage map, and an author/interview/submission guide. It retains the original genuine artifact and independent approval.

| Verification | Record |
| --- | --- |
| Fast checks | [Quick gate](quick-summary.json), [127 Linux engine tests](engine-tests.log), [host tests](host-harness-tests.log), [all 24 with the pinned SDK](host-sdk-tests.log), [quality](quality.log) and [fixture typecheck](fixture-typecheck.log). Six published schemas match. Host SDK tests use mock HTTP, not real provider calls. |
| Generated replay and handoff | [Integrated gate](generated-integration/summary.json): nine replay scenarios, both generated handoffs, six simulated transport cases, offline boundary and sanitized export. Automated operators are not real-person attestations. |
| Operator ergonomics | [UI test](operator-ui-summary.json) verifies scaled and actual-size clicks, a narrow viewport with horizontal/vertical scrolling, fit after resize, recovery and completion. This is a tested mitigation for UX-01, pending the author's usability judgment. |
| Stop during typing | [Operator Stop test](operator-stop-summary.json): response in 54 ms, input rejected, same session stopped after reload, disabled controls, no page errors. |
| Checklist/report checks | [Source checks](document-checks.json): both scripts parse, 43/36 unique check IDs, local links resolve and all seven report headings exist. Browser policy prevented local-file preview; no visual checklist-page verification is claimed. Existing self-report selections were not changed. |
| Publication scan | [History and working-tree scan](history-scan.json) found no credential patterns or prohibited historical filenames. This is a bounded pattern scan, not a security certification. The assignment PDF and private key are excluded. |

The [full desktop regression](manual-desktop-regression/summary.json), [policy/export gate](manual-policy-regression/summary.json) and [both manual-artifact handoffs](manual-handoff-regression/summary.json) passed on the same 174 executable files. This includes ten alternating baselines, seven scenario cases and seven preflight/stale/Stop rejections. The [source manifest](source-manifest.json) matches each gate.

The [fresh-checkout offline demo](clean-checkout/offline-summary.json) passed with the documented `make assess` command, exact member-B output, four inputs and zero model calls. No `.env`, host `node_modules` or virtual environment was created; the checkout remained clean. [Initial clone proof](clean-checkout-start.json) and [post-build verification](clean-checkout/build-check.json) are retained. The clone starts at `2987382` with no copied runtime evidence.

The [complete fresh-checkout rehearsal](clean-checkout/summary.json) passed. An explicit savings goal and approved target produced [three real OpenAI responses](clean-checkout/discovery-host/report.json), [four recorded native inputs](clean-checkout/discovery/trajectory.json) and the exact member-A result. I visually inspected all seven static crops and reviewed input binding, click offsets, checkpoint/OCR reuse and the unobserved missing-member branch. [Both candidate evaluations](clean-checkout/candidate-review/evaluation.json) returned exact member-B output before [agent promotion](clean-checkout/promotion/approval.json). After rebuilding, [ordinary approved replay](clean-checkout/promoted-replay/report.json) returned USD `9807` with four inputs and zero model calls.

Candidate and approved bytes share SHA-256 `8ab0c1973e46e9e3af1dfcd0f0901ab7363347387cd6d6bed3c2b52baeda2943`; no action edits were made. The temporary `discovered-rehearsal` approval is retained here as evidence only. The main repository continues to use its original `discovered-savings` approval. Post-promotion source/build identity is separately retained because adding an approval changes image inputs.

## Startup failures retained

Two full-gate attempts hit the native calibration pad's ten-second readiness timeout: [first desktop summary](failed-native-start/desktop-summary.json), [retry summary](failed-native-start/retry/desktop-summary.json) and their adjacent startup logs. The second attempt passed initial startup/native input and failed a later native reset. The container was not OOM-killed. These are actual failures, not passing test results.

Sixteen subsequent diagnostic starts reached native readiness, including direct starts with only Python fault reporting enabled; [diagnostic summary](failed-native-start/diagnostic-summary.json). Instrumentation did not establish a root cause. No timeout was increased, automatic retry added or source repair claimed. This intermittent calibration-startup limitation remains visible even if a subsequent full gate passes. Normal recovery is an explicit fresh reset, not replaying uncertain task input.

## Review boundaries

The fresh clone uses the installed Apple Silicon toolchain and existing package/Docker caches; it is not a new-machine or cache-empty installation claim. Its private provider key is read from the original host's ignored file and is never copied into the clone or evidence. A new promotion made for rehearsal stays separate from the checked-in default approval.

Only sanitized JSON metadata, separate synthetic business results, test output and reviewed static-label crops are packaged. Copied console logs have normalized line endings/trailing blank lines; original local logs remain unchanged. Full desktop captures and raw provider conversations are not included. Prior M1–M4 evidence remains unchanged. See [the requirement map](../../docs/ASSESSMENT_CHECK.md), [REPORT.md](../../REPORT.md) and [the author's remaining steps](../../docs/SUBMISSION.md).

The main demo was restored and [visibly checked](final-demo/visible-check.json): **Lookup complete**, member B, **$98.07**, with the Actual size control available. The [temporary clone was removed](cleanup.json) after curating its evidence; the main images, original approval and earlier records are preserved.
