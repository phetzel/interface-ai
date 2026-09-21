# Repository cleanup implementation · September 17, 2026

This record follows the [repository audit](../../docs/history/CLEANUP_AUDIT_2026-09-17.md). The prior React refactor/audit was committed and pushed as `d0a4f21`. Mechanical formatting is separated in `f4f8e99`: all 46 Python syntax trees are unchanged, and fixture typechecking passed. Behavioral cleanup is identified by the source/build manifests and the subsequent implementation commit containing this record.

## Resolution

| Audit item | Implemented change | Proof |
| --- | --- | --- |
| A1 | Shared bounded regular-file reader; hash and decode one anchor snapshot | FIFO capability/asset, malformed/oversized input, replacement snapshot and existing symlink/tamper/preflight regressions |
| A2 | One first-terminal-outcome finalizer; atomic result/summary files; digest/context/counts; fail-closed storage errors | Stop during automation/human input, expiry, repeated Stop, late worker, exception/storage failure and completed outcome regressions; live handoff/panel checks |
| A3 | Expected input errors map to `400 invalid_input`; panel explains five digits/leading zeroes | Real HTTP controller tests and visible invalid-ID panel check |
| A4 | Desktop and fixture build manifests; shipped-byte checks; running-image identity checks; shared preflight in all live harnesses | Edited engine/fixture and untracked source rejected; substituted compiled asset rejected; matching builds accepted |
| A5 | Pinned Ruff/Prettier, quick gate, ARM64 CI definition, readable Python, separate operator assets, backend protocol and shared harness utilities | Quality gate, host/engine/schema/type checks, fixture browser tests and live regressions |
| A6 | One current README/reading route, durable AGENTS rules, current status links, evidence index, corrected subsystem guides | Active documentation/source links checked; older evidence retained unchanged |

The operator server still serves one nonce-protected document, assembling HTML/CSS/JS without new asset routes or tokens in URLs. noVNC remains view-only. Storage failures explicitly stop input and expose missing evidence; they cannot create durable files on unavailable storage. A terminal summary is a last-written commit record for its result, not a cross-file transaction against power loss. See the [handoff guide](../../engine/src/interface_ai/handoff/README.md).

A7–A9 remain the next integration/discovery milestone: shared CLI/panel coordination, explicit recognition/checkpoint interfaces, reviewed promotion and genuine discovery-to-replay evidence. A10 distribution/dependency consolidation remains conditional work. No runtime model SDK, provider key, generalized recovery or standalone-wheel support was introduced.

## Validation

- [Formatting validation](format-validation.json): 46 unchanged Python ASTs between `d0a4f21` and `f4f8e99`.
- [Quick gate](quick-check/summary.json): quality/lint, four host-tool tests, **92 engine tests** in a network-disabled Linux container, four schema matches and fixture typechecking. [Both image/source/runtime manifests](quick-check/build-preflight.json).
- [Fixture browser log](fixture-tests.log): **15/15 passed** after the formatting/build changes.
- [Negative provenance probes](negative-build-results.json): edited engine source, edited fixture source, a new untracked fixture file, stale schema and altered compiled asset all rejected; original files/images preserved. [Reproducer](negative-build-probes.py), run from the repository root after `mkdir -p tmp/cleanup-implementation`; it uses temporary source copies and a disposable read-only asset override.
- [Full M2/M1 gate](m2/summary.json): passed, including [all 11 M1 checks](m1/summary.json), 17 replay cases, seven preflight/stale/Stop rejections, [69 runtime files, four schemas and 24 typed results](m1/final-runtime.json), policy/network checks and safe export. Raw attempts: `tmp/m2-checks/20260917T224227Z-521b8042`, `tmp/m1-checks/20260917T224250Z-616368e4`, `tmp/replay-checks/20260917T224347Z-3b332245`.
- [Both simulated handoff cases](handoff/summary.json): passed with the same session, no repeated automation input, rejected wrong-member/screen returns and exact oracle output. Raw attempt: `tmp/m3-checks/20260917T225214Z-bffd0518`.
- [Visible panel restoration](operator-ui/summary.json) and [Stop during pending input](operator-stop/summary.json): passed, including invalid-ID guidance, scaled desktop clicks, premature-resume rejection, visible diagnostics and same-session completion. Stop returned in 42 ms in this run and interrupted typing; the [actual stopped terminal evidence](stopped-run/summary.json) is retained. This is a measured sample, not a latency guarantee.
- [Frozen acceptance source](m1/source-sha256.json): 125 source, asset and configuration inputs, including the untracked cleanup source, unchanged throughout the gate. Documentation/evidence edits after the run are separate from those inputs.

The initial new snapshot regression [failed](engine-focused.log) because its test hook replaced the search anchor while an earlier, different anchor was decoding. The hook was narrowed to the exact target snapshot; the [corrected 92-test run](engine-focused-2.log) passed. The failure is retained, not presented as a passing attempt.

Automated operator evidence simulates a human. No real-person acceptance or OpenAI discovery run occurred during this cleanup. CI configuration is checked in; local results and the hosted workflow's actual status are separate claims. The user-requested checklist revision follows the cleanup commit/push, with independent fresh review keys and no prefilled human results.
