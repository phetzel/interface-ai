# Desktop, local vision, and replay · M1-03/04/05

`interface_ai.desktop.Desktop` is the shared input boundary for the native pad and Chromium in the isolated Linux X11 desktop. It does not implement discovery, visual target recognition, balance extraction, capability artifacts, or the handoff workflow itself. M3 adds the separate `interface_ai.handoff` coordinator and operator gateway.

M1-04 adds the separate [local vision package](src/interface_ai/vision/README.md): anchor matching, contextual Tesseract OCR, exact amount parsing, and bounded visual predicates. The desktop adapter continues to own every input action. M1-05 adds [strict contracts and the interpreter](src/interface_ai/replay/README.md), driven by the [manual capability](../capabilities/poc/savings-balance/README.md).

The image includes the package source on `PYTHONPATH`; use `python -m interface_ai.cli`. Python 3.11 and the hash-locked desktop dependencies are required. The desktop-only host tests use a fake backend and do not need desktop libraries:

```sh
PYTHONPATH=engine/src python3 -m unittest discover -s engine/tests -p test_desktop.py -v
```

Inside the running desktop, `./scripts/desktop test` runs the complete desktop, vision, contract, policy, replay and ownership test suite, including actual local OCR with the pinned model and the transient-identity checkpoint regression. The native/browser smoke and visual probe commands exercise the real backend separately. `./scripts/m1-check` combines them with repeated replay, input/artifact rejection, and isolation checks in the M1 acceptance gate.

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

The current backend is tested only with one 1280×800, 24-bit, little-endian Linux X11 display. PyAutoGUI emits mouse and keyboard events; Xlib/Pillow capture the same framebuffer in memory. Native and browser smoke tests use fixed calibration coordinates and are explicitly not general visual replay. M1-04 supplies local visual targeting and output extraction.
## M2 policy boundary

Bank automation defaults to `interface_ai.policy.bank.BankPolicy` in the shared desktop adapter immediately before dispatch. Its targets come from the operator-reviewed bundle, not the calling artifact. It permits a member-field click, a five-digit ID, Ctrl+A, Enter after entry, and the unique Savings button. Off-target clicks, arbitrary typing, scrolling and other shortcuts are denied. Focus, application process/class, session, stop and deadline checks still apply.

M4-01 supplies a separate `SearchPolicy` through the Python-only `bank_policy_factory` seam. It permits one probe's click within the visually recognized member field; the probe coordinator enforces the one-action budget. No action JSON or HTTP field can select this policy or bypass adapter guards. The host owns the pinned OpenAI SDK/key; `discovery/` contains only the bounded desktop transport and policy. [Provider probe guide](../docs/M4_01_PROVIDER_PROBE.md).

The CLI admits only the reviewed artifact digest before desktop acquisition or metadata logging. Low-level interpreter unit tests still exercise generic artifacts; that does not grant those artifacts permission to run through the operator CLI. A future promotion mechanism must explicitly review new artifacts and update the policy.

Keyboard permission belongs to the current acquired `Desktop` object. Separate single-action CLI processes do not share that permission. Native calibration and the fixed browser smoke harness are trusted developer tests; their calibration override is not exposed in action JSON or the CLI.

Routine replay events pass a closed vocabulary before persistence. `export-evidence --run RUN_ID` reconstructs a small metadata export, excluding raw screenshots, business results, arbitrary source metadata, and additional files. Ordinary screenshot persistence is denied. See [M2 design and limits](../docs/MILESTONE_2.md).

## Same-session ownership

`Desktop(..., epoch=observed_epoch)` pins queued actions to the ownership generation observed when they were proposed. The constructor captures the current epoch if omitted; a future model caller must capture before the model request, not when a delayed response arrives. Every input and checkpoint checks owner/epoch. Only the trusted operator gateway constructs `role="human"` contexts; the action CLI and future model tool have no role override. Human input keeps session/focus/application/stop guards and destination restrictions, with explicit manual authority instead of the automation-only bank action allowlist.

The coordinator exposes one reviewed continuation after synthetic member-search expiry. It releases the old automation context, transfers ownership after quiescence, verifies `member-ready` against the original typed input, and resumes at `open-savings` in the same session. Generic mid-step recovery is rejected. See [M3 scope, research and limits](../docs/MILESTONE_3.md).
