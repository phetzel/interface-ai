# M4-06 integrated acceptance

Passed 2026-09-20 on the working tree after `b18b0a5`. [The validation index](validation-index.json) identifies the records below. [The source manifest](source-manifest.json) hashes 172 executable/configuration/artifact files; those bytes match the full desktop, manual-handoff and generated-handoff gates. Documentation and evidence packaging are outside that executable manifest. [Build identity](build-preflight.json) binds the tested desktop and fixture images.

The same artifact recorded from the [genuine M4-04 OpenAI run](../m4-04-recorded-candidate/README.md), then [evaluated and independently promoted in M4-05](../m4-05-promotion/README.md), now passes the integrated checks. Its candidate and approved digest remains `a3e6acd5dfd97d7e420bf9a9287ff60f62b2ea66d4a7b930db8ab9bfa6ca25ca`. It preserves four model-selected inputs, explicit `memberId` binding and local extraction. Reused recognition annotations and the unobserved missing-member branch remain labeled; review did not rewrite the input sequence.

| Gate | Result and retained record |
| --- | --- |
| Generated integration | [`make m4-check`](summary.json) passed, including provider SDK/key absence and blocked provider egress in the replay desktop. It makes no genuine provider requests. |
| Generated replay | [Nine cases](generated-replay-matrix/summary.json): A/B baseline, missing member, translated A/B, delayed readiness, ambiguous target, unreadable balance and blocked screen. Exact successes, distinct business outcome and expected failures all passed. |
| Generated same-session handoff | [Both members passed](generated-handoff/summary.json). Member A includes wrong-screen/member resume rejection; ownership, original session, no repeated automation input and sanitized traces are checked. These are simulated operators, not real-person observations. |
| Provider transport negatives | [Six simulated cases](simulated-provider-transport/summary.json), including unsupported input, unrelated control, duplicate proposal and a late response after Stop. Separate from the genuine discovery evidence. |
| Offline second-member replay/export | [Exact result](member-b-result.json), [report](member-b-report.json), [events](member-b-events.jsonl) and [sanitized export](safe-export/manifest.json). Member B / `00456`, Savings, USD `9807`, four inputs and zero model calls. Export excludes business values. |
| Full M2/M1 regression | [Policy gate](manual-policy-regression/summary.json) and [full desktop gate](manual-desktop-regression/summary.json) passed. Native/browser input, sandbox/isolation, ten alternating baselines plus seven scenarios, and seven preflight/stale/Stop rejections passed. This is the full successful rerun following M4-02's separately retained failed attempts. |
| Manual-artifact handoff | [Both members passed](manual-handoff-regression/summary.json), preserving earlier behavior through the shared coordinator and independent approval changes. |
| Operator UI | [Recovery UI](operator-ui-summary.json) and [Stop during pending typing](operator-stop-summary.json) passed. Stop returned in 51 ms; input was rejected, the same session remained stopped after reload, and controls stayed disabled. No page errors. |
| Fast checks | [Quick gate](quick-summary.json): 127 Linux engine tests, six published schemas, formatting/lint, fixture typecheck and host tests. System Python ran 20 host tests with the optional SDK test skipped; the [cached SDK run](host-sdk-tests.log) passed all 20 using mock HTTP, with no key or provider call. |
| Fixture browser tests | [All 15 passed](fixture-tests.log); fixture executable source was unchanged through the final gates. |
| Final visible demo | [Final result](final-demo/result.json) and [report](final-demo/report.json) confirm approved B replay. The existing operator page was reloaded and visibly showed **Lookup complete**. |

Local gate folders are `tmp/m4-checks/20260920T103713Z-bb7c2e78`, `tmp/m2-checks/20260920T104354Z-9e56a521`, `tmp/m1-checks/20260920T104416Z-cd742ab0` and `tmp/m3-checks/20260920T105306Z-d5f4267d`. The final demo is `tmp/desktop-artifacts/20260920T105722Z-replay-1aed277e`. Curated regression records retain JSON metadata and separate synthetic results; raw calibration images and UI debug screenshots remain ignored locally.

## Failed attempt and scope

The [first M4-06 launch attempt](failed-launch-attempt.json) passed generated replay and handoff, then failed because the harness directly launched the non-executable Python transport script. Calling it through `python3` fixed the launcher. The complete combined gate was rerun and passed; the failed summary is preserved.

Both HTML checklist sources now include unverified M4 supplements. Their JavaScript syntax, unique IDs and local source links were checked. Browser policy blocked the local-file preview, so no visual checklist-page verification is claimed. Existing reviewer results were not changed. The earlier real-person manual-artifact takeover remains distinct from these automated checks and the artifact's explicit agent review.

M4 is complete for the fixed Linux ARM64, 1280×800, en-US/USD savings workflow. Scaled operator click difficulty remains UX-01. Final assessment work still includes `REPORT.md`, a clean-clone rehearsal, preserving the user's checklist export and the repository/interview walkthrough. Use the [short demo](../../docs/DEMO.md) for the next review.
