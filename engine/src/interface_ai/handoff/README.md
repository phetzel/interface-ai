# Same-session handoff

Read `controller.py` for the lifecycle, `evidence.py` for atomic terminal files, `server.py` for HTTP admission and `operator.html` / `operator.css` / `operator.js` for the panel. The server assembles these assets into one nonce-protected document: no new public asset endpoints, token URLs or frontend framework.

The operator is the demo's main interface. It shows a plain-language phase and the relevant start/takeover/resume controls beside the live desktop (stacked on narrow windows). Text and key controls appear only during human ownership; Stop remains in the sticky header, including while input is pending. **Run details** holds the raw phase/owner, session UUID and checkpoint diagnostics. The image keeps a constant three-pixel border so scaling matches the desktop-coordinate conversion without a layout shift during takeover. No direct host-keyboard forwarding or new input authority is added. The native calibration pad remains a development/test fixture, visible in this same panel. The standalone VNC/noVNC stack has been removed.

| From | Trigger | Result |
| --- | --- | --- |
| idle | Valid five-digit start | running, automation ownership |
| running | Reviewed expiry during search | awaiting_human, revoked automation epoch |
| running / awaiting_human | Take control | quiescing, then human after input-lock drain |
| human | Exact original-member checkpoint verified | running from reviewed open-savings boundary |
| human | Invalid checkpoint | Remain human; no input replay |
| human | Handoff deadline | stopped with handoff_expired |
| active run | Stop / unexpected worker exception | stopped; input signaled/revoked before evidence writes |
| running | Interpreter terminal result | success, business_outcome or failure |

An arbitrary takeover clears the continuation; only the declared expiry boundary can resume. Stop during pending human input signals the adapter before acquiring the controller mutex. Maintenance/status polling never blocks the accepting thread on that mutex. Input callbacks retain modifier cleanup and the epoch checks.

All terminal paths use `finalize`. The first terminal result wins; late worker results cannot replace Stop. Each file is atomically replaced, and `summary.json` is written last with `resultSha256`, so readers can detect an interrupted two-file write. Late action completion can refresh counts while preserving that outcome and its last step/checkpoint. Stop after a completed run disables further input without rewriting the earlier business result. This is local process evidence, not a transaction across power loss or externally killed containers.

An I/O failure signals Stop, revokes ownership and sets `evidenceStatus=failed`; it never recursively logs the storage exception or exposes its raw text. Missing evidence cannot be made durable on unavailable storage. Reset after investigating it. Raw inputs/OCR/pixels do not enter the routine audit, while explicit business output stays in `result.json`.

Expected HTTP classes remain distinct: `400 invalid_input` for the member contract; `400 invalid_action` for malformed envelopes; `409` for ownership/transition/admission conflicts; `503 busy` for temporary status contention; sanitized `503 execution_failed` for unexpected infrastructure errors. Commands are never automatically retried. Stop remains enabled while a command is pending.

The CLI replay entry point remains separate. Shared coordination/export, a public bounded checkpoint API and reviewed promotion metadata belong with the next discovery milestone. These cleanup changes do not add general recovery or model discovery.
