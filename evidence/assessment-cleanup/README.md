# Assessment cleanup validation

Completed September 20, 2026, in the working tree based on `7ff4035`. Nothing was committed or pushed by this cleanup. [Final executable hashes](final-source-manifest.json) identify the tested code; the [build record](quick/build-preflight.json) binds source to shipped runtime bytes. Approved capability/asset bytes are unchanged.

## What changed

- One `scripts/check --suite …` entry point replaces milestone launchers. Domain checks remain separate internally; the combined runner links child evidence and avoids repeated nested suites/unit tests.
- `make help` exposes eight assessment commands. The generated artifact is now the default for CLI, panel and demo; historical manual checks select their bundle explicitly.
- Removed the obsolete scripted bank-vision workflow, visual probe, standalone one-click provider command and its SDK lock. Discovery now shares an explicit reservation base with an internal transport diagnostic. Operator HTTP test mechanics are shared; the live guard helper no longer runs out of historical evidence.
- The operator keeps the desktop beside compact controls on wide screens and above them on narrow screens. Fit/actual-size viewing, input ownership and Stop retain their existing contracts.
- The same bank can be wrapped in two nested same-origin iframes. This is a rendered-frame proof, not arbitrary cross-origin/frameset/vendor support.
- Current setup, demo, report and both checklists use the new commands. All 43 acceptance IDs, 36 repository-review IDs and browser storage keys are preserved. No results were prefilled.

## Results

| Check | Result / record |
| --- | --- |
| Quick | [Passed](quick/summary.json): 126 Linux engine tests, 24 host tests with one intentional SDK-dependent skip, six schemas, formatting/lint and fixture types |
| Fixture | 16 browser UI tests passed before and after the wrapper-title fix; [retained first run](fixture.log) includes the nested-frame/CSP checks |
| Desktop foundation | [Passed](desktop/summary.json): native/browser input, isolation, session/Stop/exclusivity, 17 historical replays and seven rejection cases |
| Policy/export | [Passed](policy/summary.json): operation/route boundaries, direct-origin denial and sanitized export |
| Generated replay | [11 cases passed](generated-replay/summary.json), including [iframe member A](generated-replay/cases/iframe-a/result.json) and [iframe member B](generated-replay/cases/iframe-b/result.json); same approved digest, four inputs, zero model calls |
| Generated handoff | [Both members passed](generated-handoff/summary.json), with same-session recovery, exact identity/result, no repeated input and sanitized events |
| Manual handoff | [Both members passed](manual-handoff/summary.json) |
| Provider transport | [Six simulated-provider cases passed](discovery/summary.json); no live provider calls |
| Offline boundary | [Passed](offline/summary.json): provider SDK/key absent, egress blocked, generated replay and safe export |
| CLI/panel lifecycle | [Passed](lifecycle/summary.json): shared run, competing-start rejection, panel control |
| Operator UI | [Passed](operator/summary.json): resized/scrolled pointer mapping, recovery, [Stop during typing](operator/operator_stop.json), 49 ms Stop response in this run |
| Clean source demo | [Passed](clean-source-demo/summary.json): `make assess SCENARIO=iframe`, exact member B / 9807 minor units, four inputs and zero model calls |

The clean rehearsal used an export of the uncommitted source, without `.env`, `node_modules`, virtual environments or prior local run evidence. Its executable hashes matched the main repository. It reused the installed Docker/toolchain and build cache: this is not a fresh-machine claim or a new paid discovery. [Command log](clean-source-demo/command.log) · [result](clean-source-demo/result.json) · [report](clean-source-demo/report.json).

## Retained failures and verification order

The first full run stopped at the previously documented intermittent native-pad readiness timeout. Its [summary](native-startup-failure/summary.json) and [startup log](native-startup-failure/fresh-native-start.log) are retained. The cause remains unresolved; a later successful run does not erase it.

The next full run passed quick, fixture, desktop and policy checks, then [failed at the new iframe startup](iframe-startup-failure/summary.json). The wrapper title lacked `Northstar`, so the existing application-identity guard refused it. The fixture title was corrected; the guard was not weakened. [The source comparison](title-fix-source-diff.json) shows this fixture-server file was the only executable change after the successful desktop/policy suites.

After that correction, quick/fixture were repeated, the complete [generated group passed](generated-suite.json), and manual handoff, lifecycle and both operator checks passed. The clean-source demo then passed. These are suite-level results across the documented sequence; neither earlier failed full invocation is relabeled as successful. No unchanged ten-baseline desktop suite was rerun just for the iframe-specific title correction.

All tests here are automated. The author's earlier reported #41 completion and supplied passing #42 output remain separate [manual observations](../../docs/MANUAL_AUDIT_NOTES.md). Personal comfort with the new operator layout, checklist export, interview understanding and publication/submission remain author work. Historical evidence retains its original provenance.
