# M4-02 — Shared replay lifecycle

> Historical design record. Use the [current setup and commands](../DEVELOPMENT.md).

CLI replay now submits its admitted capability and member input to the same in-desktop coordinator used by the operator. The CLI polls for a result; it no longer owns a separate interpreter or desktop input reservation. The private launcher capability authenticates this path, while the browser retains its separate operator token.

The panel can observe and stop a CLI run. An expired workspace pauses at the reviewed continuation; other replay failures preserve their diagnostic and allow inspection under human control, but have no automatic resume. Two simultaneous starts compete for the same idle-state transition. Stop still signals the adapter before acquiring the coordinator mutex.

Pixel observations and exact input/OCR checks now live in `replay/recognition.py`. The sequential interpreter uses that small seam, and discovery can use the same checks without executing or showing the manual artifact's action sequence to the model.

Both entry points write the same replay result, report and sanitized interpreter events. Handoff adds the ownership/action audit and summary. A paused failure has usable diagnostics before any human intervention; completing a recovery replaces that provisional failure with the final result. A terminal Stop cannot be replaced by a worker's late result.

## Limits

The CLI returns a nonzero status when intervention is required; the operator retains the paused run for takeover. It does not hang the shell waiting for a human. A transport failure after submission is explicitly marked as an uncertain dispatch, rather than falsely claiming zero input. Never repeat that command blindly: inspect the operator, then reset for a new run.

This step shares replay lifecycle and recognition. The provider probe still has its deliberately narrow worker reservation; M4-03 adds the goal-driven discovery worker to this coordinator. It is not yet evidence of full discovery.

[Validation record](../../evidence/m4-02-shared-lifecycle/README.md). Reproduce the targeted integration with `./scripts/lifecycle-check`; use `./scripts/m1-check --rejections-only` for the explicitly labeled focused rejection gate.
