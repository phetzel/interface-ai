# M1-03: shared desktop adapter and Chromium bootstrap

Verified 2026-09-12 UTC on the same Apple Silicon / native Linux ARM64 environment as M1-01. M1-02 was committed/pushed as `37bbd60` before this work. This revision includes the completed M1-03 implementation and evidence. This evidence establishes input/observation plumbing across a native application and Chromium, not reusable banking replay or automated balance extraction.

## Recorded checks

| Run | Result | Evidence |
| --- | --- | --- |
| Adapter unit tests in the container | 15 passed | [Output](unit-tests.txt) |
| Native pad through shared adapter | 8 passed, 1 run | [Report](20260912T085752Z-06ff857d/report.json), [capture](20260912T085752Z-06ff857d/after.png) |
| Default bank, synthetic member A | 8 passed, 1 run | [Report](20260912T090530Z-bank-96513eeb/report.json), [account capture](20260912T090530Z-bank-96513eeb/04-account.png) |
| Reset bank, synthetic member B | 8 passed, 1 run | [Report](20260912T090612Z-bank-6c37adef/report.json), [account capture](20260912T090612Z-bank-6c37adef/04-account.png) |
| Live native guard checks | 6 passed, 1 run | [Report](20260912T090728Z-guards/report.json), [harness](live_guard_check.py) |

The native run checks exact pointer coordinates against its independent pad oracle, text replacement/Enter, scroll, VNC pixel agreement and server-side input rejection, network probes, stop, and session preservation. It now uses `interface_ai.desktop.Desktop`; the old smoke-specific input wrappers are removed.

The bank runs use fixed calibration coordinates and bounded pixel-change checks. The executor does not use DOM access, CDP, Playwright, the fixture oracle, app source, or business HTTP requests. Trusted bootstrap uses only `/healthz` and a fixed Chromium launch URL. Both captures were visually reviewed: member `00123` / Demo Member A shows Savings, USD, `$1,234.56`; member `00456` / Demo Member B shows Savings, USD, `$98.07`. This is manual review of synthetic evidence, **not** OCR or a returned/validated typed business result. Each report explicitly has `businessOutputExtracted: false`.

Live guard checks exercised the actual CLI and input backend. Invalid and previously observed session requests caused no pad changes; a separate controller process was rejected while the first held the lock. A second thread requested stop after the first characters arrived: 4 of 256 characters were delivered, subsequent clicks/keys were rejected, and screenshots remained available in memory. The stop persisted after releasing and reacquiring the input lock. Stop is cooperative; short OS operations already dispatched may finish.

The 15 unit tests additionally cover empty explicit session IDs, malformed action variants, focus/display changes, timeout during typing, bounded missing checkpoints, modifier release on stop/backend failure, no automatic retry, and omission of text from routine events. These use a fake backend and do not replace the live checks. Host unit tests also passed during development; the retained output is the container run.

## Environment and startup findings

- Linux ARM64, Python 3.11.2, 1280×800×24 X11 framebuffer, PyAutoGUI 0.9.54, Pillow 11.3.0, python3-xlib 0.15.
- Chromium 152.0.7977.82; [installed OS packages](system-packages.txt), [actual image IDs](images.txt), and [source hashes](source-sha256.json) record this build. Debian packages are not frozen against future repository updates.
- Chromium has a disposable profile and runs as the non-root desktop user, with no remote debugging interface or sandbox-disable flags. Renderer reports show two seccomp filters versus one in the browser process, nested PID namespaces, zero effective capabilities, and no-new-privileges. See the [profile rationale and provenance](../../../infra/desktop/SECCOMP.md).
- The desktop retains its internal-only network, dropped outer capabilities, and existing resource limits. Both browser runs rejected the two selected external TCP probes and found no default IPv4 route. This is a bounded probe, not a comprehensive isolation audit.
- Repeated native/bank resets produced fresh sessions. The [final session](final-session.json) records a healthy bank desktop with input enabled after the deliberately stopped guard run.

Startup attempts before the successful calibration runs exposed and corrected four issues:

1. The default container syscall policy prevented Chromium from creating its sandbox. A versioned Playwright seccomp profile permitted its namespace operations.
2. Chromium still failed its private `chroot`; a documented local syscall allowance fixed it without adding an outer capability or disabling the sandbox.
3. The X11 window title could already be a Python string; startup now accepts the returned string or bytes representation.
4. Chromium rewrites renderer arguments into a space-separated process title. The readiness parser initially missed those renderers; it now handles that representation and verifies their actual process status.

A final review also tightened explicit session validation: an empty ID now rejects instead of selecting the current session. The final image was rebuilt and all 15 unit tests rerun; the earlier image IDs identify the live calibration runs, while the additional final image entry includes this validation fix. The source manifest describes the final source.

These were startup failures, not discarded passing-replay attempts. Their summaries are retained here; raw exploratory logs remain in ignored `tmp/`, and no complete startup-failure trace is claimed in this bundle. All initialized M1-03 native/browser/guard runs are listed above; none failed. Earlier M1-01 failures remain in the separate desktop evidence.

## Reproduce

From the repository root, with Docker Desktop running:

```sh
./scripts/desktop build
./scripts/desktop reset native
./scripts/desktop test
./scripts/desktop smoke
./scripts/desktop reset bank
./scripts/desktop browser-smoke --member-id 00123
./scripts/desktop reset bank
./scripts/desktop browser-smoke --member-id 00456
```

For live guard checks, note the ID printed by `./scripts/desktop ready`, reset with `./scripts/desktop reset native`, then use the old ID:

```sh
docker compose exec -T desktop python - --stale-session OLD_ID < evidence/poc-m1/adapter/live_guard_check.py
./scripts/desktop reset bank
```

Reload the [viewer](http://127.0.0.1:6080/vnc.html?autoconnect=true&resize=scale&view_only=true) after resets. Raw runs include more calibration captures under ignored `tmp/desktop-artifacts`; this bundle retains the reviewed final captures and original reports/events. All retained UI data is fictional. Known-pixel export guards are not general redaction. M1-04 must supply visual locators, contextual OCR, ambiguity handling, and output validation before capability replay can be claimed.
