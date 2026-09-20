# Manual audit observations

## 2026-09-19 — Member A human takeover

The user performed the recovery and resume flow through the operator panel. Their screenshots and report show rejected resume attempts on the wrong screen/member, a return to Demo Member A's overview, and a successful resume to Savings / $1,234.56 USD. This records the member-A flow, not completion of the entire manual checklist.

Read-only inspection of the resulting evidence also passed checklist #27:

- Run: `tmp/desktop-artifacts/20260920T042515Z-handoff-0323f9f2` (local, ignored evidence).
- Session: `d91f69f3-e024-482b-a1c9-beed5480bac9`; `sessionUnchanged: true`.
- Result: `success`, member `00123`, Demo Member A, Savings, USD, `amountMinor: 123456`.
- Zero model calls, five automation actions, 66 human actions and 141 audit events.
- No automation input between the `human` and `resumed` lifecycle events; human sequences increase from 1 through 66.
- Human events contain action metadata without typed text, keys or input coordinates. The audit contains no recognized business values; the run directory contains only `audit.jsonl`, `summary.json` and the separate `result.json`.
- The result file's SHA-256 matches `summary.json`: `65e76ae463ee2c8bd4c0999c03e5929bdc3618feeb55c395157c41946f50eefa`.

The earlier wrong-code rejection, masking and text-field clearing assertions in #24 still depend on the user's observations. The remaining member-B, Stop and failure checks are separate. No checklist selections were changed by this evidence review.

## 2026-09-19 — Agent-operated completion of #28–32

At the user's request, Codex operated the operator panel to validate the remaining Section 6 checks. **All five passed:** member-B same-session recovery to $98.07, panel Stop during pending text input, CLI Stop under human ownership, refusal to resume after arbitrary takeover, and terminal failure diagnostics. Stops remained effective after page reload. The failure audit retained the reviewed step/checkpoint context without input values or screenshots.

These are **agent-operated UI checks**, separate from the user's real-person member-A observations above. No checklist selections were prefilled, no runtime source was changed, and UX-01 remains deferred. The app was left on the final expected `checkpoint_timeout` failure for inspection.

Local records: [results](../tmp/section6-agent-review-20260919/RESULTS.md), [evidence assertions and run references](../tmp/section6-agent-review-20260919/evidence-review.json), [final build verification](../tmp/section6-agent-review-20260919/build-postflight.json). These ignored local files need reviewed packaging before submission.

## 2026-09-19 — Sections 8–9 terminal validation

At the user's request, Codex ran #34–36 sequentially. All passed: 15 fixture tests; the complete M1/M2 gate with 92 engine tests, 17 replay cases and seven rejection cases; and the M3 gate with 92 engine tests and both simulated handoffs. No runtime changes or reruns were needed.

The terminal portion of #37 also passed. Reset/readiness produced session `43f27e2f-ad47-4413-9311-539d0a23ca5c` with `inputStopped: false`; the reopened operator and desktop visibly showed Ready to start and the fresh bank search. Checklist export and accurate reviewer sign-off remain separate closeout work. Section 7 was not independently executed as a checklist step in this pass.

Local [validation report and evidence index](../tmp/sections8-9-review-20260920T052842Z-d74b34a6/RESULTS.md). These are automated results; no human checklist selections were prefilled.

## UX-01 — Clicking targets during human control is difficult

**Status: deferred at the user's request; acceptable for the current audit.**

During the real-person takeover, the user reported difficulty clicking intended targets inside the controlled desktop view, including the recovery controls. They were able to complete the flow, but precise interaction was awkward, especially with the desktop displayed in a narrow panel.

The cause is unconfirmed. Small rendered targets, coordinate scaling, scrolling/focus and interaction latency are possibilities to investigate, not established defects. No runtime change was made in response to this observation.

Follow-up:

1. Reproduce at narrow and wide panel sizes, recording the intended target and where the desktop receives each click.
2. Verify pointer mapping after resizing and scrolling, including the image border and display scale.
3. Evaluate an enlarged/fullscreen desktop view or zoom controls, keeping human input controls easy to reach.
4. Recheck clicking, ownership transfer and Stop after any change; retain the same-session resume guarantees.


## 2026-09-19 — Manual checklist closeout reported

The user subsequently reported that every manual checklist item passed. This is the user's completion report; it does not relabel the individually recorded agent/terminal checks as human actions or claim the separate repository checklist is complete. Preserve the reviewer export for final evidence packaging.

The later operator-only cleanup changes how the desktop is viewed: use 6081 for both observation and controlled input, with no standalone 6080/VNC surface. Checklist IDs and browser storage keys are unchanged, so existing results remain tied to the revision originally tested. UX-01 remains deferred.


## 2026-09-19 — Legacy viewer retired and revalidated

The 6080 viewer, VNC/noVNC processes and packages, viewer relay/service and its unused network were removed. The fixed replacement relay exposes only loopback 6081; the desktop retains its internal network. Native and bank desktops are visible through the operator image. Input continues to require the same server-enforced ownership and adapter checks.

The rebuilt source passed the quick gate (92 engine tests and four host harness tests), the full M1/M2 gate, both M3 handoffs and a browser-operated member-A lookup. New native/runtime checks verify image agreement, rejection of input without human ownership, absence of legacy software and closed 5900/6080 ports. The final app was reset for another run. [Local validation and exact run references](../tmp/operator-only-review-20260920/RESULTS.md).

These are automated/agent-operated regressions of the operator-only revision. Saved checklist results and historical evidence retain their original provenance. [M4](MILESTONE_4.md) is specified, not implemented.
