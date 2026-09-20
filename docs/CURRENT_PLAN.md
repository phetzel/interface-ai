# Current planning direction

**M4-01 update (2026-09-20):** the host-only OpenAI client, bounded transport, one-click visual policy and offline negative tests are implemented. [Genuine provider acceptance passed](../evidence/m4-01-live-provider/README.md): three OpenAI responses, one native click and a stateless screenshot round trip. [Run and explain the probe](M4_01_PROVIDER_PROBE.md). [Shared lifecycle (M4-02)](M4_02_SHARED_LIFECYCLE.md) is implemented; goal-driven discovery and generated artifacts remain next; a connection probe is not the assignment's discovery demonstration.

Updated 2026-09-19. **M1, bounded M2 and the M3 takeover mechanism are implemented** in the fixed Linux ARM64 environment. The current cleanup addresses the audit's A1–A6 repairs, build provenance, quality checks, readability and documentation. The [root README](../README.md) and [evidence index](../evidence/README.md) are authoritative for current validation; milestone counts below/elsewhere describe their dated source revisions.

**Next:** integrate CLI/panel lifecycle and explicit recognition/checkpoint interfaces alongside real OpenAI discovery, a recorder and an operator-reviewed promotion manifest. Prove a genuinely discovered capability replays for the second member with zero model calls. The real-person handoff is complete; final report and discovery demo packaging remain pending. See the [M4 implementation specification](MILESTONE_4.md) for the next work packages and acceptance gates. Cleanup is not evidence of completed discovery.

**Manual audit update (2026-09-19):** the user completed the member-A takeover and resume flow; its evidence review passed. The user reports the M1–M3 manual checklist fully passed; command/harness checks and agent-operated checks retain their separate provenance. See [manual audit observations](MANUAL_AUDIT_NOTES.md) for the run reference and the deferred human-control click-targeting UX issue.

## Confirmed and open choices

| Area | Confirmed by the user | Still open |
| --- | --- | --- |
| Language | Python engine; TypeScript available for UI | Dependencies pass M1 on Linux ARM64; other environments remain untested |
| UI | React/TypeScript as the initial sample-app direction | Keep operator UI minimal; no polished console yet |
| Models | OpenAI only, using one provider key; GPT-5.6 Sol access and one-click computer-tool exchange verified | Performance on full workflow discovery |
| Automation | Computer use across application surfaces; PyAutoGUI and local visual recognition pass M1 | Broader rendering conditions and model discovery |
| Target | Three-view synthetic banking app; read-only savings lookup passes M1 | M3 expiry is implemented; generic dialogs remain later integration work |
| Schema | Pydantic source, portable JSON, and exported JSON Schema are implemented | Discovery-generated target provenance and broader recovery contracts |
| Repository | No further pushes without an explicit user request | Changes remain local until requested |

Initial directions are accepted. The desktop gate has passed on native and browser calibration fixtures, and manual artifact replay passes the repeated acceptance gate. M2 proves the declared policy/evidence boundary. M3 now provides the handoff mechanism; genuine model discovery remains unimplemented; the witnessed real-person handoff is recorded separately.

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

The tested environment is a non-root Linux ARM64 Docker desktop with one 1280×800 X11 display, fixed scale, and synthetic data. Screenshot/input agreement, read-only viewing, and sandboxed Chromium are verified. M3 adds interactive human ownership and metadata-only event capture through the same adapter. The automation operates the isolated desktop rather than the host desktop.

Playwright can remain useful for testing the sample app or an optional browser adapter later. It is no longer the primary automation abstraction.

## The critical issue: deterministic targeting and extraction

Recording screenshot coordinates is insufficient. A replay target should describe how to rediscover the intended control and verify the surrounding state.

| Strategy | Benefit | Limitation |
| --- | --- | --- |
| Visual anchor/template with relative target location | Works from pixels without DOM access | Theme, scale, repeated controls, and image changes can invalidate matches |
| Local OCR with spatial context | Can locate labels and extract changing text | Reading errors and ambiguous text require strict validation |
| OS accessibility role/name/path | Structured target identity and text where exposed | Coverage and APIs vary by OS/application |
| Absolute coordinates | Simple input execution | Useful only after validating the current target; not the durable locator |

**Validated M1 replay approach:** visual anchors and local OCR within a constrained desktop environment, with explicit screen preconditions and match thresholds. The repeated gate verifies control location and exact extraction for both synthetic members without an LLM. Keep accessibility targeting as an adapter option; broader rendering conditions need separate tests.

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

Screenshots are observations, not an enforcement boundary. A visual agent cannot establish a strong domain/route allowlist just by reading the address bar. Enforce permitted applications and network destinations outside the model; browser-specific route enforcement may require additional instrumentation. Restrict the initial environment to the fixture application and required system components, and state remaining limits. M2 implements this with application identity checks, an operator-owned operation policy, managed browser restrictions, and a fixed-upstream gateway on separate networks; see its specification for limits.

## Next design work

1. Follow [M4](MILESTONE_4.md): prove provider access/action dispatch, then integrate the coordinator and discovery recorder. The M1–M3 manual pass and real-person takeover are complete.
2. Keep recovery scoped to the declared expiry checkpoint; defer generic workflow recovery.
3. Verify OpenAI API access and define allowed outbound model observations; metadata-only evidence export does not authorize raw screenshot transmission.
4. Validate genuine discovery to a reusable artifact, including explicit artifact promotion into the reviewed policy.
5. Integrate the scenario matrix and prepare the final reproducible submission before adding polish or another surface.

At the user’s requests, M1-01 and M1-02 were committed and pushed as `c426a49` and `37bbd60`. M1-03 was subsequently committed and pushed as `79bf84e`. M1-04 was then committed and pushed as `1d89ba8`. M1-05 (`2ea242a`) and the verified M1-06 implementation are committed and pushed at the user's request. Future commits/pushes require an explicit request.
