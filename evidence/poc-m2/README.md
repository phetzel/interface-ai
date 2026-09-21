# M2 acceptance: policy and safe evidence

M2 is complete for the declared synthetic Linux ARM64 desktop. The [full gate](attempts/20260915T221535Z-f59cfad5/summary.json) passed on 2026-09-15, including all eleven M1 regression groups. A subsequent two-file evidence-reader hardening change passed [final verification](final-verification/summary.json): 63 engine tests, 57 deployed file hashes, a fresh exact-result replay, and safe export. The desktop was reset to the default bank search screen. Changes remain local and uncommitted.

## Measured coverage

| Boundary | Result |
| --- | --- |
| Network routes | Allowed fixture resources load; five live forbidden method/path/query cases return structured denials. Unit tests also cover Host ambiguity, encoded paths, request bodies, absolute URLs and redirects. |
| Origin isolation | Desktop and fixture origin share no network; the gateway joins both. Origin DNS does not resolve from the desktop, and a connection to the host-observed origin IP fails. |
| Browser policy | The deployed Chromium visibly blocks an external HTTP destination and a local-file destination. Tests wait for a new active window; raw screen pixels/OCR remain in memory. |
| Operation policy | A functional synthetic transfer button, an instruction to ignore restrictions, arbitrary typing and a browser shortcut do not grant input permission. Four requests reject with zero completed input actions and unchanged transfer status. |
| Application identity | The ordinary bank adapter checks the bootstrapped window, window class, approved executable and process ancestry. A real second application taking focus causes rejection with zero input. |
| Capture/export | Ordinary raw screenshot saving rejects before persistence. Safe export includes only `summary.json`, `events.jsonl`, and `manifest.json`; results, images and arbitrary extra files are excluded. Sensitive-string injections and symlink/non-regular input rejection have regression tests. |
| Artifact trust | A schema-valid artifact with an unapproved digest rejects before desktop acquisition and before its metadata enters logs. The reviewed M1 artifact and its anchors remain unchanged. |
| Existing behavior | Ten baseline replays, seven scenario replays, seven zero-input rejection cases, plus native/browser/session/viewer/isolation checks pass. |

The [live policy report](attempts/20260915T221535Z-f59cfad5/live-policy.json) records ten checks; [network membership](attempts/20260915T221535Z-f59cfad5/networks.json) and the [literal-IP probe](attempts/20260915T221535Z-f59cfad5/origin-ip-bypass.log) separately establish the origin boundary. The [M1 regression summary](attempts/20260915T221535Z-f59cfad5/m1-regression/summary.json) contains the full result mapping. Baseline replay time was 3.486–4.015 seconds, median 3.598, excluding resets; these are feasibility measurements, not a reliability estimate.

The fixture's [14 Playwright tests passed](fixture-tests.json), including proof that the synthetic transfer control actually changes local state when clicked directly by the fixture harness. That is fixture validation, not desktop task automation or model-discovery evidence.

## Failures and follow-up

The [first full attempt](attempts/20260915T221304Z-2231c138/summary.json) failed when gateway startup re-resolved its fixture dependency with the default scenario. The [startup log](attempts/20260915T221304Z-2231c138/policy-reset.log) retains both fixture recreations. The startup script now uses `--no-deps` after the fixture's own health-checked scenario setup, and the live test explicitly checks the selected scenario before testing its UI. The next full attempt passed. No failed runs were discarded or silently retried.

Development also included an inconclusive headless-browser timeout and an initial visible-screen assertion expecting different wording. The [development probe summary](development-probes.json) labels these as development observations; the repeatable live test verifies the actual visible organization-block message without weakening browser restrictions.

After the full gate, final review identified that opening a FIFO could block before the regular-file check. The reader now uses a nonblocking, no-follow open and checks the actual descriptor. Only `engine/src/interface_ai/policy/evidence.py` and its test changed relative to the full-gate source manifest. [Final verification](final-verification/summary.json) records the before/after hashes, [63 passing tests](final-verification/unit-tests.log), [57 matching deployed files](final-verification/runtime.json), and an additional real replay/export. The full repeated desktop suite ran before this isolated export-reader fix; it was not represented as having run again afterward. The final source was tested through a read-only mount in the dependency image, then the rebuilt deployed image was independently hash-checked.

## Reproduction and provenance

```sh
make build
make policy-check
# From the replay command's printed directory name:
make export RUN=YYYYMMDDTHHMMSSZ-replay-xxxxxxxx
```

`make policy-check` resets the synthetic desktop, exercises the live policy, runs the full M1 regression, exports a real replay, and leaves a fresh search screen. Each new attempt is retained under `tmp/m2-checks/`. [verify_final.py](verify_final.py) reproduces the focused two-file follow-up against this recorded full-gate snapshot; it also resets the desktop.

Images were built from the local checkout with the repository's build-context exclusions and Docker layer caching, using the existing dependency locks. This was not a clean-clone submission rehearsal. [Initial build](build.log), [final build](final-build.log), [final image identities](final-verification/images.jsonl), and [source hashes](final-verification/source-sha256.json) are retained. Replay uses the unchanged manual capability digest `94d37e09907c839e3c04bd1662003ae6529d087e137952e4e844a673d32d9c17` and zero model calls.

The [final archive audit](audit.json) matched 88 source hashes, parsed 75 JSON files and 1,275 JSONL records, checked 53 existing local links, scanned retained text evidence for the private-note sentinel, and checked each safe export's three-file allowlist. The audit itself and this added audit link were written after those counts were measured.

## Evidence categories and limits

The [final safe export](final-verification/safe-export/manifest.json) is metadata-only. The surrounding acceptance archive additionally retains explicit synthetic results and M1 calibration images for engineering review; it is not itself a safe-export bundle. Policy-scenario screen pixels and private-note sentinel values are not persisted in the live policy report.

The policy trusts the reviewed fixture, application/runtime code and host. It does not prevent a malicious application from imitating pixels or a privileged operator from changing the runtime. Calibration overrides are trusted test code, unavailable in structured action JSON. General screenshot redaction, arbitrary app authorization, a model's outbound observation policy, real discovery, and same-session human takeover remain outside this milestone. Research and tradeoffs are in [MILESTONE_2.md](../../docs/history/MILESTONE_2.md).
