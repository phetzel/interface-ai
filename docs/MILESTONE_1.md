# Milestone 1: Isolated desktop and model-free banking replay

Status: M1-01 through M1-04 implemented and verified on 2026-09-12. The Linux ARM64 desktop, banking fixture/oracle, shared adapter, sandboxed Chromium, and local visual/OCR primitives are available. M1-04 passes 27 unit tests and eight scenario checks; see [visual evidence](../evidence/poc-m1/vision/README.md). M1-05/06 remain planned, and full M1 is not complete. M1-01 through M1-03 were pushed at the user’s explicit requests (`c426a49`, `37bbd60`, `79bf84e`). M1-04 is included in this revision; no model calls have been made.

## Outcome

From a documented local command, start an isolated desktop showing a small banking application, run a manually authored capability for a synthetic member, and return the correct savings balance using desktop input and local visual recognition only. A live viewer shows that same desktop. Repeat for another member and demonstrate deliberate handling of ambiguity, delayed rendering, and failed checkpoints.

This milestone validates the desktop and deterministic replay assumptions. The manual artifact must be labeled as a PoC fixture; it is not evidence of LLM discovery. Genuine discovery, artifact generation, and full human takeover follow in later milestones.

## Environment findings

- Host reports macOS (`Darwin`) on `arm64`.
- Docker CLI 28.3.2 is installed and selects the `desktop-linux` context.
- After the user opened Docker Desktop, the daemon was verified reachable: client/server 28.3.2, Linux architecture `aarch64`, 10 CPUs, and 8,218,034,176 bytes of memory allocated (approximately 7.65 GiB). The earlier daemon-readiness blocker is resolved.
- Node/npm, system Python, and uv are on PATH. Host Tesseract was not found on PATH; it can be packaged in the desktop image instead.
- M1-01 built and ran a native ARM64 Debian desktop with PyAutoGUI/Pillow and a native Tk calibration pad. Desktop input, viewing, and lifecycle checks passed. M1-03 now validates the same adapter in sandboxed Chromium against both synthetic members; M1-04 now verifies visual anchors and local OCR on the baseline, translated, delayed, duplicate, unreadable, and blocked cases.

The desktop image now builds and runs natively for ARM64, without x86 emulation. Recheck daemon readiness at startup. Chromium desktop input now passes its calibration checks. OpenCV/Tesseract primitives now pass the bounded fixture checks; capability replay and the full repeated acceptance gate remain later work. The fixture itself builds and runs natively on ARM64; its browser acceptance tests ran in isolated host Chromium. Docker documents native architecture selection and the possible cost of emulation. [Docker multi-platform builds](https://docs.docker.com/build/building/multi-platform/)

## Initial environment design

The target milestone adds a fixture service to the implemented desktop and viewer relay:

1. **fixture:** the built React/TypeScript banking app, served as static assets with bundled synthetic data.
2. **desktop:** Linux X11 virtual display, a lightweight window manager, Chromium, VNC/noVNC viewing, and the Python runner with PyAutoGUI, OpenCV, Tesseract, and Pydantic. PyAutoGUI/Pillow, the shared adapter, OpenCV, and Tesseract are installed through M1-04; Pydantic and the interpreter remain M1-05.
3. **viewer:** a fixed-destination relay that publishes a loopback port while the desktop retains its internal-only network. See the implementation evidence for the measured Docker Desktop networking issue.

The runner executes inside the desktop environment so screenshot and input coordinates refer to the same display. The tested baseline is a 1280×800 display, one monitor, browser zoom 100%, en-US locale, USD currency, and fixed font assets. Both native and bank calibration screens fit these verified dimensions. Host Retina scaling and viewer zoom must not change the runner's coordinate space.

Expose the viewer on an available loopback-only port, initially proposed as 6080. Start it view-only during replay to avoid manual input races. Full operator control and human-action capture are deferred. noVNC is a browser-based VNC client, not an automation or ownership system. [noVNC](https://novnc.com/info.html)

Connect fixture and desktop on a private Compose network. After build/dependency installation, the replay environment should have no external network access and no model credentials. Publish only the viewer to the host loopback address; verify actual isolation rather than treating configuration as proof. Do not mount the host home directory, Docker socket, credentials, or personal browser profile. Export only to the project's designated PoC output directory. [Compose networks](https://docs.docker.com/reference/compose-file/networks/), [Docker port publishing](https://docs.docker.com/engine/network/port-publishing/)

Containerization provides the selected demo boundary; do not claim general hostile-code containment or production financial-data compliance. M1 executes a fixed validated action vocabulary and a trusted manual artifact, not arbitrary model-generated code.

## Scope

### Included

- Repeatable desktop startup, readiness checks, reset, shutdown, screenshot, and stop behavior.
- Tiny banking fixture, one read-only workflow, two successful members, one missing member.
- Desktop adapter with screenshot, click, keyboard input, scroll, display metadata, and stop checks.
- Local visual anchor resolution, contextual OCR, bounded visual waiting, and output validation.
- Small Pydantic-validated manual artifact and interpreter; no general-purpose workflow language.
- Structured events, a synthetic-data-only evidence bundle, and an automated acceptance harness.
- One minimal native text-entry smoke test for the input adapter to check that basic control is not tied to Chromium. This is not a second full capability or proof of cross-OS support.

### Deferred

- OpenAI calls, discovery prompts, recorder/compiler, and automatic capability generation.
- Full human intervention routing, input capture, and resume semantics.
- Session-expiry recovery, permission workflows, irreversible actions, and writes to banking data.
- General sensitive-screen redaction and arbitrary-app policy enforcement.
- Accessibility adapter, arbitrary themes/scales, multi-monitor and multi-OS support.
- Polished operator UI, backend database, real login, deployments, capability catalog, or queues.

Deferral applies only to M1; these remain required later where the assignment demands them.

## Fixture and workflow

Use three small views:

1. **Member search:** member ID field, Search button, and a loading state.
2. **Member detail:** visible member identity and an account list containing both checking and savings.
3. **Account detail:** visible member identity, account type, balance, currency, and a route back to search.

Implemented fixtures (expected results belong to the harness):

| Input | Visible savings balance | Expected typed result |
| --- | --- | --- |
| `00123` | `$1,234.56` | `amountMinor: 123456`, `currency: USD` |
| `00456` | `$98.07` | `amountMinor: 9807`, `currency: USD` |
| `00999` | Explicit member-not-found message | Business outcome `member_not_found` |

Use visibly synthetic labels such as Demo Member A/B. Preserve leading zeroes in IDs. Keep the fixture readable and ordinary: no automation-only test IDs, invisible automation markers, or required UI knowledge embedded in the runtime.

The app does not require a backend in M1. Scenario configuration and data reset belong to the test harness, not the replay action contract. The harness may read expected values and configure failure scenarios; the runner may not obtain results from fixture source, app state, DOM, browser evaluation, an HTTP API, or hidden metadata. The interpreter sees only declared inputs, its artifact, screenshots, and local recognition results.

Implemented variants: default (250 ms search), delayed (1,800 ms), permanently blocked search, duplicated savings target in the same account list, unreadable balance, and +40 px main-content translation on both axes at desktop widths. Controls are launch-time environment settings, not UI or query-string options. The app and expected-result oracle are tested independently of the future replay engine; see [fixture README](../apps/bank-fixture/README.md).

## Minimal contracts

Do not create a framework before the PoC. Define only the types needed to run this workflow:

- **Desktop session:** session identifier, display dimensions, current run/stop state, screenshot and input operations.
- **Target descriptor:** static anchor reference, scoped search region relative to a stable landmark, optional OCR text/input reference, relative click point, match threshold and ambiguity rule.
- **Step:** identifier, action, target/input reference, precondition, expected postcondition, timeout. Allow only bounded known branches and waits.
- **Capability:** schema version, capability name/version, input/output definitions, supported environment, ordered steps, known business outcomes, and completion checks.
- **Result:** success with typed output; named business outcome; or failure with step, expected/observed summaries, and safe evidence references.
- **Event:** run/step identifiers, action type, target-resolution metadata, elapsed time, outcome, and error code. Omit raw typed input and extracted account data from routine logs.

Validate IDs and action arguments before UI input. Validate member and account identity at the final screen before returning a balance. Parse currency using decimal-safe conversion into integer minor units. Reject malformed or uncertain readings; do not silently substitute OCR characters or coerce unreadable text into zero.

Thresholds and OCR preprocessing are calibrated against development screenshots and then fixed for acceptance runs. Use distinct acceptance variations. Keep match candidates and ambiguity rules explicit; taking the single highest image score is not sufficient evidence of a unique target.

An OCR confidence threshold is a rejection heuristic, not proof of accuracy. Exact comparisons against an independent synthetic oracle establish correctness only for the tested scenarios.

## Implementation work packages

| Order | Package | Concrete deliverable | Depends on |
| --- | --- | --- | --- |
| M1-01 (done) | Environment and readiness | Compose definition, desktop image, viewer, ready/reset/stop commands, native ARM64 smoke check | Reachable Docker daemon |
| M1-02 (done) | Fixture and oracle | Three views, synthetic records, harness-only scenario controls, expected results | Agreed workflow; can proceed while environment is prepared |
| M1-03 (done) | Desktop adapter | Pixel/input agreement, trusted app bootstrap, stop checks, native text-entry smoke | M1-01 |
| M1-04 (done) | Visual primitives | Anchor matching, OCR extraction, bounded visual predicates, ambiguity detection | M1-02 and M1-03 |
| M1-05 | Manual artifact and interpreter | Validated JSON capability, input bindings, typed outputs, known not-found branch | M1-04; draft types can be written earlier |
| M1-06 | Acceptance and evidence | Reset-based scenario suite, safe events/crops, measured results, README commands | M1-05 |

Within each package, build the smallest working path and add its failure check before proceeding. Keep all input dispatch in one executor so later model actions and ownership enforcement can use the same boundary.

Draft types and fixture UI are independent of Docker availability. The final target schema depends on actual visual matching behavior. Evidence collection starts with the first execution; M1-06 packages and verifies it.

## Proposed repository layout

The engine desktop and vision packages, CLI, banking fixture, infrastructure, helpers, and four evidence bundles now exist. Contracts, replay, and capability paths below remain planned:

```text
apps/bank-fixture/                 React/TypeScript app and fixture scenarios
engine/pyproject.toml              Python dependencies and CLI entry point
engine/src/interface_ai/desktop/   OS-specific input and screenshot adapter
engine/src/interface_ai/vision/    Target matching, OCR, visual predicates
engine/src/interface_ai/contracts/ Pydantic types and JSON Schema export
engine/src/interface_ai/replay/    Small interpreter and structured results
engine/src/interface_ai/cli.py     Operator-facing PoC commands
engine/tests/                     Contract, vision, executor, integration tests
infra/desktop/                    Desktop image and startup scripts
compose.yaml                      Local fixture and desktop services
capabilities/poc/                 Clearly labeled manual artifact and safe anchors
evidence/poc-m1/                  Reviewed synthetic-data-only run evidence
```

Use one Python package and one small frontend package; no generic plugin architecture. Do not add real credentials or an OpenAI dependency to M1.

## Command experience to implement

Provide one documented command for each of: start the environment, check readiness, open the viewer, replay for a specified member, run the acceptance suite, reset the fixture/session, stop a run, and stop the environment.

Exact names are an implementation detail, but commands must work from the repository root and fail with actionable errors when Docker is unavailable. Readiness must wait for actual display/fixture readiness rather than fixed startup sleeps. Invalid input must fail before mutation. Every run must have a bounded total deadline and per-step deadline.

The reset helper may relaunch the trusted fixture entry point and choose a scenario. Once a replay starts, business-task actions and result verification use the desktop interface only.

## Definition of done

All criteria below are required for declaring M1 complete. Suggested counts are engineering gates, not assignment requirements or statistical reliability claims.

1. **Environment:** a fresh start opens the fixture in the isolated desktop; the viewer shows the same session; readiness, reset, shutdown, and repeated start work.
2. **Input:** screenshot/input coordinates agree; a native text-entry smoke and the browser fixture use the same low-level adapter; a stop request prevents subsequent actions.
3. **Baseline:** ten clean-reset replays alternating the two valid IDs return exactly the expected identity, account type, amount, and currency. No post-hoc edits to the artifact between members.
4. **Translation:** the same artifact succeeds on an explicit modest translation, initially proposed as 40 pixels, while scale and theme remain fixed. Declare the tested bounds.
5. **Waiting:** a bounded injected load delay succeeds; an indefinitely missing checkpoint times out with structured evidence and no subsequent action.
6. **Known outcome:** the missing member returns `member_not_found`, never a fabricated zero balance or generic crash.
7. **Ambiguity and unreadable output:** duplicate indistinguishable targets and invalid/unreadable numeric output produce a deliberate failure. No arbitrary best-match click or guessed amount.
8. **Validation:** malformed inputs and unsupported artifact actions/versions are rejected before input execution.
9. **Model independence:** no model credentials, SDK calls, or endpoint access are required; the environment can reach only its intended local resources during replay. Test prohibited egress rather than asserting it from config alone.
10. **Evidence:** replay logs identify the step and expected/observed state without raw member/balance fields. Persist only known synthetic fixture captures or allowlisted safe crops. Unknown desktop captures are kept in memory and discarded. Exported anchors contain no dynamic member data.
11. **Reproducibility:** record dependency/image/recognition versions, environment dimensions, scenario configuration, and all attempted acceptance outcomes, including failures. README separates commands that actually work from future features.

Image exports are limited to this synthetic fixture. M1 must not claim that this is a general financial-PII redaction solution. Full screenshot/trace sanitization is a later gate before broader use.

## Failure decisions

| Failure | Next action | Do not do |
| --- | --- | --- |
| Docker unavailable | Start/check the existing engine during implementation and re-run readiness; investigate the reported failure | Replace it with an unplanned paid cloud environment |
| Required package lacks ARM64 support | Verify a compatible backend/package or explicitly evaluate emulation with measured results | Silently report emulated performance as native |
| Viewer and screenshot coordinates differ | Normalize and validate display/viewer scaling | Scatter unexplained coordinate offsets into workflow steps |
| Visual matching is unstable | Improve contextual anchors and ambiguity checks; document supported rendering bounds | Fall back to permanent raw coordinates or hidden DOM selectors |
| OCR misreads identity or balance | Improve regions/preprocessing and strict checks; reconsider accessibility where available if necessary | Call an LLM during replay or guess character substitutions |
| Fixture only works because it is tailored to the artifact | Add independent translated/duplicate/delayed cases and inspect assumptions | Add invisible target markers solely to pass the demo |

If one bounded correction and rerun does not resolve a major recognition failure, report the evidence and propose a revised approach before expanding scope. A failed PoC is useful if it changes the decision early; do not call the milestone complete with a narrowed gate that was never disclosed.

## Questions and assumptions

| Question | Default/answer | Blocking? |
| --- | --- | --- |
| Is there a time budget or demo date? | User confirmed neither needs to constrain the milestone; use the acceptance gates above | No |
| Which execution environment? | Existing Docker Desktop on this ARM64 Mac; isolated Linux desktop now verified | Native/browser input and visual primitive checks passed; artifact replay remains untested |
| Does M1 need an OpenAI key? | No; genuine discovery follows later | No |
| Must it work on Windows or native macOS now? | No; one tested Linux environment with surface-neutral interfaces | No additional user decision needed |
| Must the viewer support full human takeover now? | No; same-session observation and stop are included, ownership/capture/resume follow later | Does not block M1; remains mandatory for the final system |
| Is read-only balance lookup sufficient? | Yes for this first milestone; add a blocked-risk demonstration later | No |
| Should we publish or push the result? | No, unless the user explicitly requests a push/publication | No; all work can remain local |

The next milestone should add early real human-control capture and policy checks, followed by genuine OpenAI discovery and conversion into the validated artifact. Passing M1 alone does not complete the assignment.
