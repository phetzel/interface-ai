# M1-06 · Repeated acceptance and reproducibility

**M1 is complete for its declared environment.** The corrected [acceptance run](attempts/20260913T015743Z-cf9ae83c/summary.json) passed all eleven gate groups on 2026-09-12 Pacific time (2026-09-13 UTC): 47 unit tests, ten alternating-member clean-reset baselines, seven scenario replays, seven zero-action rejection cases, lifecycle/input/viewer checks, and isolation/source/evidence verification. The [attempt index](attempts.json) retains the original failed run too.

## Definition-of-done coverage

| M1 criterion | Measured result and evidence |
| --- | --- |
| 1. Environment | Shutdown removes all project services; fresh start works; repeated native start preserves the session; resets create new sessions. [Gate summary](attempts/20260913T015743Z-cf9ae83c/summary.json). |
| 2. Input and viewer | Eight native and eight browser calibration checks passed; six live guard checks passed, including stale-session rejection, exclusive ownership, stop during typing, and no later input. Raw VNC pixels match the display and server-side input is rejected. [Native](attempts/20260913T015743Z-cf9ae83c/native-smoke/report.json), [browser](attempts/20260913T015743Z-cf9ae83c/browser-smoke/report.json), [guards](attempts/20260913T015743Z-cf9ae83c/native-guards/report.json). |
| 3. Baseline | Ten of ten fresh-session runs alternate `00123` / `00456` and exactly match the independent oracle. Replay time: 2.769–3.150 seconds, median 3.034; excludes container resets. [Results](RESULTS.md). |
| 4. Translation | Both members pass with +40 px translation on both axes and the same artifact. [Results](RESULTS.md). |
| 5. Waiting | The 1,800 ms delay succeeds; blocked loading returns `checkpoint_timeout` at `search-member`, with no later input. [Results](RESULTS.md). |
| 6. Known outcome | Missing member returns `member_not_found`, after four actions and before any account click or extraction. [Result](attempts/20260913T015743Z-cf9ae83c/replay/cases/missing/result.json). |
| 7. Ambiguity / unreadable output | Duplicate targets reject at `open-savings`; unreadable balance rejects at `read-balance`; neither returns success output. [Results](RESULTS.md). |
| 8. Validation | Numeric, short, and extra-field inputs; unsupported schema/action; stale session; and stopped replay all reject with zero input actions. Malformed inputs/artifacts reject before session acquisition. [Gate summary](attempts/20260913T015743Z-cf9ae83c/summary.json). |
| 9. Model independence | No OpenAI configuration or model SDK in the runtime; zero model calls; fixture reachable; selected external IPv4/IPv6 connections fail; model hostname resolution fails. [Runtime checks](attempts/20260913T015743Z-cf9ae83c/final-runtime.json), [container boundaries](attempts/20260913T015743Z-cf9ae83c/container-boundaries.json). |
| 10. Evidence | Both attempts retained; 2,294 replay events checked for allowed metadata fields and absence of synthetic input/output values; no replay screenshots persisted. [Independent audit](evidence-validation.json). |
| 11. Reproducibility | Both images build from clean source exports; 51 runtime files match source hashes; four schema exports match their models; dependency/image versions recorded. All 24 results in the accepted attempt validate, as do all 41 results across both attempts. [Final runtime](attempts/20260913T015743Z-cf9ae83c/final-runtime.json), [source hashes](attempts/20260913T015743Z-cf9ae83c/source-sha256.json), [image IDs](attempts/20260913T015743Z-cf9ae83c/images.json), [system packages](attempts/20260913T015743Z-cf9ae83c/system-packages.txt). |

The accepted run leaves [a fresh bank search session](attempts/20260913T015743Z-cf9ae83c/final-session.json) with input enabled. Reload the local viewer after the resets.

## Commands and scope

From the repository root, with Docker Desktop running and Python 3.9+ on the host:

```sh
./scripts/desktop build
./scripts/fixture build
./scripts/m1-check
```

The [acceptance command](../../../scripts/m1-check) combines lifecycle, native/browser calibration, view-only verification, live input guards, unit tests, runtime/source checks, network probes, repeated replay, and seven rejection cases. The [replay subset](../../../scripts/replay-check) is also available as `./scripts/replay-check --acceptance`; it performs ten alternating-member baseline runs and seven fixture scenarios. Neither harness supplies the oracle to the replay process. The oracle is used only by the host to compare explicit results.

All replays use the same [manual artifact](../../../capabilities/poc/savings-balance/capability.json), SHA-256 `94d37e09907c839e3c04bd1662003ae6529d087e137952e4e844a673d32d9c17`, with unchanged templates, OCR preprocessing, confidence threshold, and deadlines. The supported environment is native ARM64 Linux X11, one 1280×800 display, en-US/USD, fixed fonts, and 100% scale. Translation checks move content by 40 pixels on both axes. These small feasibility tests do not establish production reliability, general app support, or automatic discovery.

## First attempt and bounded correction

[Attempt 20260913T015032Z-96ec03b2](attempts/20260913T015032Z-96ec03b2/summary.json) failed the repeated-replay gate: nine of ten baselines passed and all seven scenario cases passed. [Baseline 08](attempts/20260913T015032Z-96ec03b2/replay/cases/baseline-08/result.json) returned `invalid_identity` at `enter-member`, after three input actions and before search submission. It produced no output. Its original report and event log are retained alongside the result.

The interpreter immediately rejected a malformed OCR identity during checkpoint evaluation, whereas a well-formed but incorrect identity already left the checkpoint unsatisfied. The correction makes malformed identity behave as an unsatisfied checkpoint too. Postcondition polling can observe again within the existing deadline and must eventually read the exact requested ID. It never retries typing, substitutes characters, lowers confidence, or extends deadlines. Preconditions and final extraction remain strict.

The failed replay did not persist a screenshot or raw OCR text, so the precise pixel-level cause is unknown. A blinking caret or intermediate rendering could explain it; neither is claimed as proven. The regression covers the observed error category: malformed reading, wrong valid ID, eventual exact ID, persistent malformed-reading timeout, and direct extraction rejection. [The rebuilt image passed all 47 tests](builds/regression-tests.log).

The corrected acceptance run encountered the same error category in four real replays: baselines 03, 05, and 07, plus translated A. All observed a later exact identity and returned the correct output without retyping. [Recovery observations](transient-recovery.json). No artifact or recognition settings changed between the two attempts or between members.

## Build provenance

The first images were built from a clean `git archive` of M1-05 commit `2ea242a`. The corrected build used that clean export plus the explicit local M1-06 changes. No host `node_modules`, virtual environment, or other ignored dependency directory entered either build context. Docker layer caching was allowed; this was not a cache-free installation or the final clean-clone submission rehearsal.

Both builds used the anonymous temporary Docker client configuration documented in the root README, without modifying global credentials. See [initial source metadata](builds/initial-source.json), [initial build log](builds/initial.log), [corrected source metadata](builds/corrected-source.json), [corrected build log](builds/corrected.log), and [tracked patch](builds/tracked-changes.patch). Each acceptance attempt records its own image identities and source hashes; new harness files are covered by those manifests.

## Evidence handling and limits

Each attempt retains every completed check and attempted replay, including failures. Routine replay events use an allowlist of metadata keys and contain no typed input or OCR values. Explicit synthetic results are separate files. Replay creates no image files. The native and browser calibration checks export only their known synthetic fixture screens; the native after-screen and browser account-screen were visually reviewed. These captures are calibration evidence, not model-discovery traces.

The independent [audit script](verify_evidence.py) validates the portable JSON Schemas, all 41 retained results, current source hashes, and replay event fields. Run it with `uv run --no-project --cache-dir tmp/uv-cache --with jsonschema==4.25.1 python evidence/poc-m1/acceptance/verify_evidence.py`. Its first launch hit a macOS system-configuration error in the restricted `uv` process before executing validation; rerunning with normal local process access passed. This tool-launch issue is separate from the two desktop acceptance attempts.

Network checks verify fixture health while attempting external IPv4, IPv6, and OpenAI endpoint connections. A DNS failure is recorded as a DNS failure, not a successful TCP blocking test. Container configuration checks cover non-root execution, dropped capabilities, no privileged mode, the single designated artifact mount, internal desktop networking, and loopback-only viewer publication. These are bounded checks of this local environment, not general policy enforcement or sensitive-screen redaction.

M1-05 (`2ea242a`) and M1-06 are committed and pushed at the user's request. Genuine model discovery, full policy/evidence enforcement, and human takeover remain later work.
