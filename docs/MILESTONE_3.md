# M3 — Same-session human takeover

Status: the M3 baseline (`ec2b56e`) and pre-audit Stop/diagnostic repair (`a63a143`) are committed and pushed. The September 17 repository cleanup adds terminal evidence, input error classification, readable panel assets and verified build provenance. Consult the [current evidence index](../evidence/README.md) for current counts and limitations. This document preserves the milestone's design/history; a real-person demonstration remains pending.

## Pre-audit repair, 17 September 2026

An independent audit reproduced a Stop defect in the committed baseline: `Server.service_actions()` waited for the controller mutex on the request-accepting thread while human input held that mutex. The `/stop` handler could therefore be delayed before it had a chance to set the stop flag. The direct-adapter and external-CLI Stop checks did not exercise that HTTP contention.

The local repair uses a nonblocking maintenance lock attempt. A separate timer thread could also avoid blocking acceptance, but would introduce another worker and synchronization lifecycle; retrying maintenance at the next server poll is sufficient for this bounded prototype. Python documents that [`service_actions()` executes in the serving loop](https://docs.python.org/3.11/library/socketserver.html#socketserver.BaseServer.service_actions). Status observations also acquire the mutex nonblockingly and return `503 {"code":"busy"}` during input, so polling does not hold request slots waiting on that lock. The panel retries observations and keeps Stop available; input requests are never automatically retried.

Expiry maintenance retries after the active action releases the mutex, even if the browser is closed. Human actions already have a ten-second adapter deadline, checked between primitives/characters; this is not a promise to forcibly interrupt a blocked OS call. Stop is signaled independently of the controller mutex, subsequent input checks reject it, and held-key cleanup still drains normally.

Handoff now records `kind: interpreter` entries with a nested event validated by the same closed metadata rules as CLI replay. These include reviewed step/target/checkpoint identifiers, confidence and recognition-region boxes, never OCR values, typed text, raw keys or human input coordinates. Input action totals remain separate. The panel displays the current/last observed step, last verified checkpoint, and reason; the last verified checkpoint is historical context, not a claim about the present screen. Resume verification also records satisfied/unsatisfied checkpoint metadata.

See [pre-audit validation](../evidence/pre-audit-2026-09-17/README.md). The checklist now tests panel Stop separately from CLI Stop and inspects an ordinary failed handoff run. It uses a new local-storage version so earlier checklist marks do not silently carry into this revised pass. CLI/coordinator unification, expanded failure routing, artifact promotion and genuine discovery remain subsequent work.

## Scope and acceptance

PoC D adds a real input-transfer path to the existing Linux desktop. A lookup encounters a synthetic expiry screen after submitting member search. The operator takes control, restores the workspace, and explicitly asks to resume. A fresh visual checkpoint must prove that the original member overview is present before the engine continues at `open-savings`. Neither the desktop, Chromium process, nor capability is replaced.

Acceptance covers unchanged session identity, actual OS input from the operator endpoint, exclusion of automation during human control, in-flight input draining, modifier cleanup, stale requests in both directions, duplicate requests, premature/wrong-screen/wrong-member resumption, successful continuation for both members, bounded abandonment, and an audit free of typed values, key sequences and pixels. All automated operator tests must be identified as simulations; they are not evidence that a person completed a handoff or that an OpenAI response was tested.

## Research and choice

| Choice | Benefits | Costs / limitations | Decision |
| --- | --- | --- | --- |
| Writable noVNC | Mature desktop interaction, broad keyboard support | RFB input bypasses the Python adapter; client `viewOnly` alone is not server authorization; recording and epoch rejection require a protocol gateway | Keep x11vnc server-enforced view-only. [noVNC API](https://novnc.com/noVNC/docs/API.html) documents the client flag and input methods. |
| Controlled operator input gateway | Every action crosses the same OS adapter, session/focus/stop checks and ownership epoch; straightforward metadata-only recording | Small UI must explicitly translate display coordinates; initial ASCII text/click/keys only, no drag, IME or clipboard | Use a minimal local panel with memory-only screenshot viewing and structured input. No new framework or provider dependency. |
| Release a lock without versioning | Simple mutual exclusion | A queued action can become valid again after a human returns control | Combine the existing input lock with monotonically increasing ownership epochs. Delayed requests retain their original epoch. |
| Hold the input lock while asking for takeover | Looks atomic | Prevents the active context from draining and can deadlock event recording | Revoke admission under a separate state lock, then wait for input.lock to drain before granting human ownership. [Python flock](https://docs.python.org/3/library/fcntl.html) provides cross-process exclusion and nonblocking acquisition. |
| Restart the entire capability after restoration | Minimal interpreter change | Blindly repeats already executed actions and obscures continuation | Continue at one reviewed boundary; verify original member identity and member overview first. An arbitrary interruption has no continuation and requires reset. |
| Save screenshots and keystrokes for debugging | Rich traces | Would persist sensitive restoration data | Keep live pixels and text in memory; record action kind, status, epoch changes and timing. Results remain separate local data. |

The loopback-published panel uses exact Host/Origin checks and a process-random header token; no CORS allowance, URL token, request logging, or screen persistence. State-changing requests are bounded JSON bodies. Client sequence numbers reject duplicate human requests, and the UI never retries input automatically. These controls follow the custom-header and origin-checking patterns in the [OWASP CSRF guidance](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html). This is a trusted, single-user local prototype, not an authenticated multi-user remote desktop service.

## Ownership and continuation

`automation(epoch n) → quiescing(n+1) → human(n+2) → automation(n+3)`

- The adapter checks owner and epoch at checkpoints, immediately before dispatch and between typed characters/key-down operations. Key-up cleanup remains permitted after revocation.
- Recognizing expiry immediately advances to `quiescing`, revoking queued automation before the operator clicks **Take control**. The button drains input and completes the transfer to `human`; it cannot revive the previous epoch.
- Quiescing is not human ownership. An in-flight primitive can finish before the barrier drains, but no human input starts until the old input context releases its lock. A five-second drain timeout fails closed.
- Human input retains the same session UUID, dimensions, application identity, focus checks, stop switch and network/browser restrictions. Human control is explicit manual authority; the automation-only bank action allowlist is not used for these human actions. Python/shell access remains trusted developer access, unavailable to the model or panel.
- Restoration is synthetic: password-masked training code `demo`, no real credentials or authentication service. The code is cleared after submission. A 15-minute human lease and 100-request cap bound a disconnected/abandoned panel. The panel also reflects the external CLI stop marker. Expiration stops input even without browser polling.
- The engine recognizes the fixed expiry heading from pixels. Recognition is scoped to the `search-member` postcondition. It cannot infer arbitrary recovery procedures or silently treat another failure as recoverable.
- Resume holds input.lock while checking the existing `member-ready` checkpoint, including the invocation's exact member ID. Failure preserves human ownership. Success rotates the epoch and starts a fresh bounded automation segment at step 5. Human waiting does not consume that segment's execution budget.
- Ownership and continuation are volatile. Container/session reset discards them. A supervised gateway crash tears down the desktop; recovery from process restart is deliberately not attempted.

## Work packages

| ID | Work | Gate |
| --- | --- | --- |
| M3-01 | Ownership epochs and drain barrier | In-flight typing/hotkeys stop; stale automation and human requests reject |
| M3-02 | Operator panel and bounded API | Actual desktop input, local request protection, no sensitive recording |
| M3-03 | Expiry scenario and reviewed continuation | Wrong return rejected; correct original-member return completes without repeating search |
| M3-04 | Adversarial/live checks and evidence | Both members, unchanged session, safe audit, previous regressions, honest provenance |

## Validation notes

- The initial HTTP unit-test fixture used a plain mock where the server requires a context-manager mutex. That test setup was corrected to use a real `RLock`; the suite then passed 78 tests. This was a harness failure, not a hidden acceptance success.
- Host fixture tests initially looked in Playwright's default browser cache and could not launch Chromium. Reusing the repository's pinned browser via `PLAYWRIGHT_BROWSERS_PATH="$PWD/tmp/playwright"` passed all 15 tests; no browser upgrade or dependency change was needed.
- The first live expiry recognition and restoration succeeded with the existing OCR model and thresholds. Both members subsequently passed the operator-API acceptance, including wrong-screen and wrong-member rejection, duplicate-input protection and old-epoch rejection.
- The panel itself passed a browser test at a 1000×1200 viewport, mapping smaller displayed image coordinates back to the fixed 1280×800 desktop. Playwright inspected only the operator panel; the banking application remained pixels, with actions emitted through the OS adapter. This is UI verification, not a new browser automation core.
- The complete M2/M1 regression passed before final review tightened immediate pause revocation and synchronized the operator panel with external CLI stop. Final review also made human audit sequences continuous across short input contexts. These changes are revalidated by the full engine suite and both live handoff cases; the retained source manifests distinguish this focused follow-up from the earlier full regression.

## Run it

Build updated images with `make build`, then `make handoff-demo`. Open <http://127.0.0.1:6081/>. Start a lookup; at expiry choose **Take control**. Click the training-code field on the desktop, enter `demo` in the panel's **Text to send**, choose **Send text**, then click **Restore workspace** on the desktop. Choose **Verify & resume** once the original member overview returns. The panel scales clicks to the 1280×800 desktop.

For a negative check, request resume while the expiry dialog is still visible, or navigate to another screen/member before returning. The operator remains in control. `make stop` stops all subsequent input and requires `make handoff-demo` or `make reset` to start again.

The read-only viewer on port 6080 remains available. Only ports 6080 and 6081 are published, both on host loopback, through fixed-destination relays. Model discovery and outbound screenshot review remain the next milestone.
