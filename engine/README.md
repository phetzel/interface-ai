# Engine

Python owns the native desktop adapter, local vision, capability contracts, replay, policy, discovery worker and same-session handoff. The host-side provider loop lives in `scripts/lib/discovery_flow.py`; the optional provider SDK/key never enters this runtime.

Read the code in this order: [contracts](src/interface_ai/contracts/models.py), [replay](src/interface_ai/replay/README.md), [recognition](src/interface_ai/replay/recognition.py), [desktop adapter](src/interface_ai/desktop/adapter.py), [policy](src/interface_ai/policy/admission.py), [discovery worker](src/interface_ai/discovery/worker.py), then [handoff](src/interface_ai/handoff/README.md). The generated capability is the default. The original manual bundle remains the reviewed recognition profile named by recorded provenance.

`make check` runs the complete Linux unit/OCR suite in a disposable network-disabled image. `make check SUITE=full` adds live native/browser, replay, policy, discovery-transport and operator checks. See [development commands](../docs/DEVELOPMENT.md). The image places the package on `PYTHONPATH`; `python -m interface_ai.cli` is the internal CLI. A standalone wheel is not the supported distribution.

## API

```python
from interface_ai.desktop import Desktop

with Desktop(session_id="previously-observed-session-id", timeout=45) as desktop:
    image = desktop.screenshot()  # In memory; the adapter never writes captures.
    desktop.click(200, 400)
    desktop.type_text("00123")
    desktop.press("enter")
```

Coordinates in this example illustrate the primitive API, not a reusable banking workflow. Read the current session using `./scripts/desktop ready`. A reset invalidates the previous session ID. The replay interpreter resolves coordinates from declared visual targets and validates its observed result.

All input uses the same `execute()` implementation, with convenience methods for `click`, `move`, `type_text`, `press`, `hotkey`, and `scroll`. Actions reject unsupported fields, out-of-display/non-integer coordinates, unsupported keys, non-printable/non-ASCII or overlong text, and excessive scroll amounts before OS input. Supported text is deliberately limited to printable ASCII in this first adapter.

A context holds an exclusive file lock for its entire input sequence. Every input checks the original session ID, deadline, display dimensions, expected bootstrapped window focus, and stop marker. Typing checks again before each character; hotkeys release any pressed keys even when interrupted. Screenshots remain available after a stop, in memory. X11 framebuffer capture does not use temporary screenshot files.

The CLI requires an explicit session ID for input:

```sh
./scripts/desktop action --session SESSION_ID --json '{"type":"click","x":200,"y":400}'
```

Routine action events retain only action type, sequence, status, duration, and failure code. They omit typed text and raw key sequences. Failures are not automatically retried.

## Limits

Stop is cooperative: a short primitive already dispatched to the OS may finish. M3 adds epoch revocation and an input-lock drain barrier before human ownership is granted. Window-ID focus checks alone catch a changed active window. M2 adds the separate operation/application and route boundaries described below. Ordinary raw screenshot persistence is now denied.

The current backend is tested only with one 1280×800, 24-bit, little-endian Linux X11 display. PyAutoGUI emits mouse and keyboard events; Xlib/Pillow capture the same framebuffer in memory. Native and browser smoke tests use fixed calibration coordinates and are explicitly not general visual replay. Capability-driven recognition supplies local visual targeting and output extraction.
## M2 policy boundary

Bank automation defaults to `interface_ai.policy.bank.BankPolicy` in the shared desktop adapter immediately before dispatch. Its targets come from the operator-reviewed bundle, not the calling artifact. It permits a member-field click, a five-digit ID, Ctrl+A, Enter after entry, and the unique Savings button. Off-target clicks, arbitrary typing, scrolling and other shortcuts are denied. Focus, application process/class, session, stop and deadline checks still apply.

Discovery supplies a separately reviewed policy through the Python-only `bank_policy_factory` seam. The shared reservation controls ownership and bounded requests. The one-action transport diagnostic remains only for automated tests; normal discovery chooses its own actions. Action JSON cannot select policies or bypass adapter guards.

The CLI admits only independently approved bundle/asset digests before desktop acquisition. Candidate evaluation uses an explicit trusted review path; promotion binds the reviewed bytes and permitted continuation. Generic interpreter unit tests do not authorize unapproved artifacts.

Keyboard permission belongs to the current acquired `Desktop` object. Separate single-action CLI processes do not share that permission. Native calibration and the fixed browser smoke harness are trusted developer tests; their calibration override is not exposed in action JSON or the CLI.

Routine replay events pass a closed vocabulary before persistence. `export-evidence --run RUN_ID` reconstructs a small metadata export, excluding raw screenshots, business results, arbitrary source metadata, and additional files. Ordinary screenshot persistence is denied. See [M2 design and limits](../docs/history/MILESTONE_2.md).

## Same-session ownership

`Desktop(..., epoch=observed_epoch)` pins queued actions to the ownership generation observed when they were proposed. The constructor captures the current epoch if omitted; a future model caller must capture before the model request, not when a delayed response arrives. Every input and checkpoint checks owner/epoch. Only the trusted operator gateway constructs `role="human"` contexts; the action CLI and future model tool have no role override. Human input keeps session/focus/application/stop guards and destination restrictions, with explicit manual authority instead of the automation-only bank action allowlist.

The coordinator exposes one reviewed continuation after synthetic member-search expiry. It releases the old automation context, transfers ownership after quiescence, verifies `member-ready` against the original typed input, and resumes at the approval's declared next step in the same session. Generic mid-step recovery is rejected. See [M3 scope, research and limits](../docs/history/MILESTONE_3.md).
