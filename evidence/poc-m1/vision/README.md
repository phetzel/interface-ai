# M1-04: visual targets, local OCR, and bounded predicates

Verified 2026-09-12 after M1-03 was committed and pushed as `79bf84e`. M1-04 is included in this revision. One manually authored Python probe exercises the recognition primitives through real desktop input; no capability artifact, interpreter, model call, DOM/CDP access, fixture-source lookup, or business API is used. Full M1 and the artifact replay gate remain incomplete.

## Actual results

The [eight-case summary](summary.json) records every scenario run. Expected values came from the existing host-only fixture oracle; the runner received only its member-ID parameter. Five successful runs matched member ID/name, Savings account type, USD currency, and integer-cent balance exactly. No anchors, relative regions, thresholds, OCR settings, or code were changed between these cases.

| Case | Observed outcome | Probe time | Evidence |
| --- | --- | --- | --- |
| Default member A | Exact oracle match | 1.207 s | [Report](baseline-a/report.json), [result](baseline-a/result.json), [capture](baseline-a/03-account.png) |
| Default member B | Exact oracle match | 1.419 s | [Report](baseline-b/report.json), [result](baseline-b/result.json) |
| +40 px member A | Exact oracle match | 1.222 s | [Report](translated-a/report.json), [result](translated-a/result.json) |
| +40 px member B | Exact oracle match | 1.318 s | [Report](translated-b/report.json), [result](translated-b/result.json), [capture](translated-b/03-account.png) |
| 1,800 ms delayed search | Exact oracle match | 2.963 s | [Report](delayed-a/report.json), [result](delayed-a/result.json) |
| Duplicate Savings rows | `ambiguous_target`, two candidates; no account click or result | 0.704 s | [Events](duplicate-a/events.jsonl), [capture](duplicate-a/02-member.png) |
| Unavailable balance | `ocr_uncertain`; no result or later action | 1.464 s | [Events](unreadable-a/events.jsonl), [capture](unreadable-a/03-account.png) |
| Permanently blocked search | `checkpoint_timeout`; no account click or result | 5.261 s | [Report](blocked-a/report.json), [events](blocked-a/events.jsonl) |

Times measure the probe, including desktop input and recognition, and exclude container startup. These are individual feasibility checks, not reliability estimates. The translation scenario applies +40 px to main content; scrollbar appearance can additionally change centered page positions, which the fresh anchor matches accommodate.

The earlier [member-A calibration run](calibration/report.json) also completed and returned the expected [typed result](calibration/result.json). Its static label anchors came from the previously captured M1-03 screens; the first M1-04 probe validated the selected settings. There were no unexpected failed probe attempts or post-failure retuning in this package. The three stopped scenario runs above are the expected negative outcomes, not discarded runs.

[Twenty-seven unit tests](unit-tests.txt) pass: 16 desktop tests and 11 vision tests. Vision checks include translation, duplicate matches even with unequal scores, scoped matching, invalid regions/anchors/thresholds, exact decimal parsing, leading-zero input validation, pinned-model verification, real OCR via memory pipes, blank/low-confidence rejection, and OCR timeout handling. The added desktop test rejects a predicate that finishes successfully after its wait deadline.

Two additional [observation guard checks](observation-guards.json) pass with zero input actions: a real account capture is rejected for the wrong requested member, and operator stop interrupts a live visual wait. Their [reproducible harness](check_observation_guards.py) operates only on synthetic test data. The final reset restores a [healthy bank session](final-session.json) with input enabled.

## Reproduce and inspect

```sh
./scripts/desktop build
./scripts/desktop reset bank
./scripts/desktop test
./scripts/vision-check
# The suite ends on the deliberately blocked search.
docker compose exec -T desktop python - < evidence/poc-m1/vision/check_observation_guards.py
./scripts/desktop reset bank
```

For an individual probe: `./scripts/desktop reset bank translated`, then `./scripts/desktop vision-probe --member-id 00456`. The printed directory contains reports/events, known-fixture screenshots, and a separate `result.json` only if extraction completed. The probe exits nonzero on rejection; the host suite passes a negative case only when its exact expected failure and absence of later action/result are verified.

Raw runs remain in ignored `tmp/desktop-artifacts` and `tmp/vision-checks`. This bundle retains original reports/events/results for all nine probes and four reviewed representative captures. The source manifest records the final implementation; its [hashes](source-sha256.json), [image IDs](images.txt), and [installed packages](system-packages.txt) identify the tested build. The report's `eventsSha256` hashes the ordered event array serialized with Python `json.dumps`, rather than the JSONL file bytes.

## Recognition settings and limits

Linux ARM64 / 1280×800 X11, Chromium 152.0.7977.82, OpenCV Python 4.12.0.88, NumPy 2.2.6, Tesseract 5.3.0, English data package `1:4.1.0-2`, and English model SHA-256 `7d4322bd2a7749724879683fc3912cb542f19906c83bcc1a52132556427170b2`. Matching uses a fixed 0.92 threshold with explicit multiple-candidate rejection. OCR uses grayscale, 3× Lanczos scaling, a white border, single-line mode, and minimum word confidence 80. See the [vision package](../../../engine/src/interface_ai/vision/README.md) and [anchor provenance](../../../engine/src/interface_ai/vision/anchors/manifest.json).

Confidence is only a rejection heuristic. Exact comparison to the independent oracle establishes correctness for these synthetic cases. OCR text is not repaired or coerced into zero. Routine events omit typed values and recognized member/balance text; explicit results and reviewed screenshots contain fictional fixture data. Crops and OCR output use memory pipes before deliberate synthetic export. This does not provide general sensitive-screen redaction or operation authorization.

Supported bounds remain the current fonts/theme, 100% scale, visible targets, and the tested translation. Unknown overlays, arbitrary responsive changes, scale/theme changes, and off-screen targets are unsupported. The missing-member business branch, schema/interpreter, and ten clean-reset artifact replays remain M1-05/06. OpenAI discovery and human takeover remain later milestones.
