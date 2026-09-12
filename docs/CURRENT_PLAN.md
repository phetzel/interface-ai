# Current planning direction

Updated 2026-09-12. M1-01 through M1-04 are implemented. The isolated Linux ARM64 desktop, banking fixture, shared adapter, and sandboxed Chromium now support local visual target matching and contextual Tesseract OCR. Twenty-seven unit tests and eight reset-based primitive checks pass, including exact outputs for both members, +40 px translation, delayed loading, and deliberate failure cases. See [README](../README.md) and [visual evidence](../evidence/poc-m1/vision/README.md). Capability artifacts/replay, model integration, and human takeover remain later work.

## Confirmed and open choices

| Area | Confirmed by the user | Still open |
| --- | --- | --- |
| Language | Python engine; TypeScript available for UI | Validate the desktop dependencies in the PoC |
| UI | React/TypeScript as the initial sample-app direction | Keep operator UI minimal; no polished console yet |
| Models | OpenAI only, using one provider key; start with GPT-5.6 Sol | Account access and performance on the actual fixture |
| Automation | Computer use across application surfaces; start with PyAutoGUI and local visual recognition | Environment packaging and measured replay reliability |
| Target | Three-view synthetic banking app; read-only savings lookup | Visual targeting and validated output extraction |
| Schema | Pydantic as the source; portable JSON and exported JSON Schema | Exact locator, checkpoint, and outcome definitions |
| Repository | No further pushes without an explicit user request | Changes remain local until requested |

Initial directions are accepted; the implementation assumptions below still need proof. The desktop gate has passed on native and browser calibration fixtures; local recognition primitives now pass their bounded checks; artifact replay, policy, and human handoff remain unverified.

## Revised language comparison

| Option | Why it fits | Trade-off |
| --- | --- | --- |
| Python engine, optional TypeScript/React sample UI | Direct fit for a desktop input backend plus local image processing/OCR; preserves the user's React familiarity | Two toolchains if React is selected |
| TypeScript throughout | One language and shared contracts with React | Must select and validate a desktop input/accessibility backend rather than falling back to browser-only execution |
| Python throughout | One runtime for automation, fixtures, and simple UI serving | Does not take advantage of React familiarity; a richer operator UI is less convenient |

**Accepted initial direction:** Python for the automation engine and React/TypeScript for the small sample app. The engine and sample app do not need the same language: their intended connection is the visible UI. A separate operator interface may eventually need a small typed control API.

PyAutoGUI is one candidate input backend: its documentation covers screenshot capture and mouse/keyboard control on Windows, macOS, and Linux. It does not itself provide OCR or human input recording, and its documented multi-monitor support is limited to the primary monitor. These capabilities need separate decisions. [PyAutoGUI documentation](https://pyautogui.readthedocs.io/en/latest/)

## OpenAI discovery

Use the OpenAI Responses API with a small explicit coordinator. Start with GPT-5.6 Sol and the structured computer tool so each requested mouse/keyboard action can be checked, executed, and recorded. This initial model choice is subject to account access and a bounded evaluation on the fixture.

The model receives screenshots, requests actions, and receives updated observations. Our application owns the desktop session and execution. OpenAI documents both structured computer actions and code-execution integrations; choosing structured actions here is an assignment-specific preference for inspectable action boundaries. [OpenAI computer use](https://developers.openai.com/api/docs/guides/tools-computer-use)

Do not introduce another hosted service for OCR or target matching. Local image/OCR components require no additional provider key. Ordinary replay must not call OpenAI, including for locating controls or interpreting output text.

## Desktop execution and first target

Separate the model-facing computer interface from its OS-specific implementation. Its basic operations are screenshot, pointer input, keyboard input, scroll, and session/control status. Workflow artifacts must not depend on a Playwright Page, CSS selectors, or browser navigation APIs.

The first banking-style application can still run in a browser window. The difference is that the runtime operates the desktop view of that application through the same primitives it could use for a native app. This demonstrates a reusable control mechanism; it does not establish support for every OS, app, or workflow.

The tested environment is a non-root Linux ARM64 Docker desktop with one 1280×800 X11 display, fixed scale, and synthetic data. Screenshot/input agreement, read-only viewing, and sandboxed Chromium are verified. Interactive human control and event capture remain separate gates. The automation operates the isolated desktop rather than the host desktop.

Playwright can remain useful for testing the sample app or an optional browser adapter later. It is no longer the primary automation abstraction.

## The critical issue: deterministic targeting and extraction

Recording screenshot coordinates is insufficient. A replay target should describe how to rediscover the intended control and verify the surrounding state.

| Strategy | Benefit | Limitation |
| --- | --- | --- |
| Visual anchor/template with relative target location | Works from pixels without DOM access | Theme, scale, repeated controls, and image changes can invalidate matches |
| Local OCR with spatial context | Can locate labels and extract changing text | Reading errors and ambiguous text require strict validation |
| OS accessibility role/name/path | Structured target identity and text where exposed | Coverage and APIs vary by OS/application |
| Absolute coordinates | Simple input execution | Useful only after validating the current target; not the durable locator |

**Proposed first replay approach:** visual anchors and local OCR within a constrained desktop environment, with explicit screen preconditions and match thresholds. Keep accessibility targeting as an adapter option. Before committing to this approach, validate that it can locate the chosen controls and extract different synthetic balances without an LLM.

OpenCV provides template matching and Tesseract provides local OCR. These are candidate building blocks, not a claim that robust replay is solved by installing them. [OpenCV template matching](https://docs.opencv.org/4.x/d4/dc6/tutorial_py_template_matching.html), [Tesseract documentation](https://tesseract-ocr.github.io/tessdoc/)

Store stable visual anchors without sensitive member data. Bind changing text such as member IDs to invocation parameters. If multiple targets match, a checkpoint is missing, or OCR cannot establish the expected identity and amount, stop or request intervention. Do not silently choose the best-looking result.

Pin OCR/model assets, preprocessing, matching thresholds, and display assumptions for the demo. Report the supported conditions honestly. Deterministic rules do not imply perfect visual recognition.

The recorder's proposal for an anchor, extraction region, or completion condition must be validated before the capability is promoted for replay. Demonstrate another member and a modest position change to expose accidental reliance on the original coordinates.

## Artifact contract

Use Pydantic as the schema source for the Python engine. Keep portable JSON and a published JSON Schema as the contract. The alternatives below remain useful context if a PoC forces a language change.

- Python engine: Pydantic is a candidate schema source; export JSON Schema.
- TypeScript engine: Zod is a candidate schema source; export JSON Schema.
- Mixed stack: choose one authoritative schema source. Do not independently maintain two hand-written contracts. Generate or validate any operator-client representation against the same published schema.

Retain typed parameters, outputs, schema/capability versions, checkpoints, and distinct outcome/failure results. Add surface-neutral target variants such as visual anchor, OCR text with context, or accessibility target, plus their environment requirements. A supported target variant does not imply every adapter can execute it.

Sources: [Pydantic JSON Schema](https://pydantic.dev/docs/validation/latest/concepts/json_schema/), [Zod JSON Schema](https://zod.dev/json-schema).

## Handoff and safety implications

The human takes control of the same desktop session, not merely the same browser tab. A local desktop viewer or restricted remote-desktop surface is sufficient; a polished operator console remains deferred.

Only one controller may issue input. Quiesce pending automation, transfer control, record allowed human input metadata and sanitized state changes, and verify an explicit checkpoint before resuming. Input capture needs its own desktop/session mechanism; PyAutoGUI alone does not provide it. Do not retain password keystrokes or raw sensitive values.

Screenshots are observations, not an enforcement boundary. A visual agent cannot establish a strong domain/route allowlist just by reading the address bar. Enforce permitted applications and network destinations outside the model; browser-specific route enforcement may require additional instrumentation. Restrict the initial environment to the fixture application and required system components, and state remaining limits. The exact policy mechanism is a required design decision before implementation.

## Next design work

1. Implement M1-05’s validated manual capability and interpreter using the proven visual primitives.
2. Define the visual locator and output-extraction contract before expanding the sample app.
3. Use the implemented banking workflow and failure fixtures to test the locator assumptions.
4. Define desktop ownership, allowlist enforcement, and safe evidence export.
5. Once implementation is requested, validate one real discovery and no-model visual replay before adding polish or a second surface.

At the user’s requests, M1-01 and M1-02 were committed and pushed as `c426a49` and `37bbd60`. M1-03 was subsequently committed and pushed as `79bf84e`. The user clarified that M1-04 was next; that work is now verified and included in this revision. Future pushes require an explicit request.
