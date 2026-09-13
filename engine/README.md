# Desktop, local vision, and replay · M1-03/04/05

`interface_ai.desktop.Desktop` is the shared input boundary for the native pad and Chromium in the isolated Linux X11 desktop. It does not implement discovery, visual target recognition, balance extraction, capability artifacts, or human takeover.

M1-04 adds the separate [local vision package](src/interface_ai/vision/README.md): anchor matching, contextual Tesseract OCR, exact amount parsing, and bounded visual predicates. The desktop adapter continues to own every input action. M1-05 adds [strict contracts and the interpreter](src/interface_ai/replay/README.md), driven by the [manual capability](../capabilities/poc/savings-balance/README.md).

The image includes the package source on `PYTHONPATH`; use `python -m interface_ai.cli`. Python 3.11 and the hash-locked desktop dependencies are required. The desktop-only host tests use a fake backend and do not need desktop libraries:

```sh
PYTHONPATH=engine/src python3 -m unittest discover -s engine/tests -p test_desktop.py -v
```

Inside the running desktop, `./scripts/desktop test` runs 47 desktop, vision, contract, and interpreter tests, including actual local OCR with the pinned model and the transient-identity checkpoint regression. The native/browser smoke and visual probe commands exercise the real backend separately. `./scripts/m1-check` combines them with repeated replay, input/artifact rejection, and isolation checks in the M1 acceptance gate.

## API

```python
from interface_ai.desktop import Desktop

with Desktop(session_id="previously-observed-session-id", timeout=45) as desktop:
    image = desktop.screenshot()  # In memory; the adapter never writes captures.
    desktop.click(200, 400)
    desktop.type_text("00123")
    desktop.press("enter")
```

Coordinates in this example illustrate the primitive API, not a reusable banking workflow. Read the current session using `./scripts/desktop ready`. A reset invalidates the previous session ID. A future replay runner must resolve coordinates from declared visual targets and validate its observed result.

All input uses the same `execute()` implementation, with convenience methods for `click`, `move`, `type_text`, `press`, `hotkey`, and `scroll`. Actions reject unsupported fields, out-of-display/non-integer coordinates, unsupported keys, non-printable/non-ASCII or overlong text, and excessive scroll amounts before OS input. Supported text is deliberately limited to printable ASCII in this first adapter.

A context holds an exclusive file lock for its entire input sequence. Every input checks the original session ID, deadline, display dimensions, expected bootstrapped window focus, and stop marker. Typing checks again before each character; hotkeys release any pressed keys even when interrupted. Screenshots remain available after a stop, in memory. X11 framebuffer capture does not use temporary screenshot files.

The CLI requires an explicit session ID for input:

```sh
./scripts/desktop action --session SESSION_ID --json '{"type":"click","x":200,"y":400}'
```

Routine action events retain only action type, sequence, status, duration, and failure code. They omit typed text and raw key sequences. Failures are not automatically retried.

## Limits

Stop is cooperative: a short primitive already dispatched to the OS may finish. This is not the later atomic human ownership/transfer protocol. Window-ID focus checks catch a changed active window; they do not identify safe buttons, enforce browser routes, or establish financial-operation policy. Screenshot export guards apply only to the controlled synthetic fixture, not arbitrary screens.

The current backend is tested only with one 1280×800, 24-bit, little-endian Linux X11 display. PyAutoGUI emits mouse and keyboard events; Xlib/Pillow capture the same framebuffer in memory. Native and browser smoke tests use fixed calibration coordinates and are explicitly not general visual replay. M1-04 supplies local visual targeting and output extraction.
