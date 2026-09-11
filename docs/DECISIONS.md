# Options and recommended decisions

Prepared 2026-09-11. Planning only; nothing described here is implemented or measured. Recommendations assume similar familiarity with TypeScript and Python. Account-level model access remains unverified.

The assignment's Section 4 leaves seven areas open: language/runtime/frameworks; model and agent loop; computer-use technology; target application; artifact/schema storage; deterministic execution; and architecture. This document compares those choices and adds the preparation decisions that remain.

## Recommended baseline

Use TypeScript on a supported Node.js LTS release, Playwright with a visible Chromium session, Zod-backed JSON artifacts, and a small explicit orchestration loop. Start with one OpenAI provider adapter and GPT-5.6 Sol, subject to a bounded evaluation when implementation begins. Run against a local sample banking application with synthetic records and controllable failures. Keep one automation process and file-based persistence. Human intervention uses the existing browser window and an explicit local resume command.

This is a recommendation for this assignment, not a claim that these tools outperform every alternative. The highest-value work is the capability contract, replay semantics, and control transfer.

## 1. Language, runtime, and frameworks

| Option | Why choose it | Cost for this project | Recommendation |
| --- | --- | --- | --- |
| TypeScript + Node.js + Playwright + Zod | One language across browser tooling, core contracts, and a minimal operator surface | Runtime validation is still required; static types do not validate model output | Preferred baseline |
| Python + Playwright + Pydantic | Equally credible browser automation; convenient if Python is your strongest language or desktop/vision work is central | A richer web operator interface could introduce a second language | Choose this if materially more familiar |
| C#/.NET or Java | Credible enterprise choices, especially with existing expertise | Additional setup without a clear benefit for this one-browser slice | Use only if already your strongest stack |

Playwright documents shared core browser capabilities across these bindings; TypeScript is an integration preference, not a claim that Python cannot do the job. [Playwright languages](https://playwright.dev/docs/languages)

For the sample application's framework, plain server-rendered HTML with a small HTTP server is sufficient. Express is a reasonable convenience if routing starts to distract us. A React/Next.js application makes sense only if its UI is part of what we want to demonstrate. I would avoid spending this assignment's time on a component system, database ORM, or deployment stack.

Use Playwright Test for browser scenarios and the runtime's built-in test runner for pure policy/schema/state-transition tests. Pin exact runtime and package versions when implementation starts and commit the lockfile.

## 2. Model provider, model, prompting, and loop

### Model comparison

| Candidate | Fit | Trade-off | Suggested use |
| --- | --- | --- | --- |
| OpenAI GPT-5.6 Sol | The current computer-use guide includes this model in its native computer-tool examples | Need to own tool execution, recording, safety, and verification | Initial default for a focused discovery flow |
| OpenAI GPT-6 Astra | Current guidance describes computer use, structured outputs, and multistep workflows | No assignment-specific evaluation yet establishes that the larger model is necessary | Try if the baseline repeatedly fails a legitimate workflow |
| Anthropic Claude Sonnet 5 | Current docs list image/tool use and computer-tool compatibility | Different API and tool protocol; no reason to implement two providers initially | Strong alternative if Claude access or familiarity is better |
| Anthropic Claude Opus 5 | Current model guidance recommends it broadly for demanding work | Extra capability may not change the outcome on a narrow fixture | Escalation candidate within an Anthropic-first implementation |
| Google Gemini 3.8 Flash | Google's current recommended computer-use model | Another execution protocol and safety response format to integrate | Credible alternative if Google is the preferred provider |

These are documented capabilities, not a cross-provider benchmark. Availability and exact pricing must be checked for the actual account before a paid run. Pin an immutable model version where the provider exposes one; otherwise record the model identifier and run date and acknowledge possible backend changes.

Sources: [OpenAI computer use](https://developers.openai.com/api/docs/guides/tools-computer-use), [GPT-5.6 Sol](https://developers.openai.com/api/docs/models/gpt-5.6-sol), [OpenAI model guidance](https://developers.openai.com/api/docs/guides/latest-model), [Claude model overview](https://platform.claude.com/docs/en/models/overview), [Claude computer use](https://platform.claude.com/docs/en/agents-and-tools/tool-use/computer-use-tool), [Gemini computer use](https://ai.google.dev/gemini-api/docs/computer-use).

### Loop comparison

- **Small custom loop with typed tools — recommended.** Expose observations and narrow actions such as click, fill, select, read, and request intervention. Each tool maps to the same policy-checked execution layer used by replay. Keep the loop explicit enough to inspect in an interview.
- **Provider-native computer-use protocol.** Particularly suitable for screenshot-first discovery. The recorder must still convert provider-specific actions into our own capability format; native tool output is not a reusable contract by itself.
- **Higher-level agent SDK/framework.** Useful when orchestration complexity justifies it. For this slice, we still need custom artifact, failure, and ownership semantics, so a framework may save less work than expected.

The proposed prompt gives the goal, target, typed invocation inputs, allowed actions, success criteria, and stop conditions. It treats page content as untrusted task data. Request one state-changing action per observation cycle and a concise action rationale, not hidden chain-of-thought. Cap steps, elapsed time, repeated unsuccessful actions, and spending. The model can propose completion; deterministic checks decide whether the goal was met.

Keep discovery inputs explicit alongside the natural-language goal. For example, the member ID is a named input binding, not a literal to be guessed out of a transcript later. Do not provide the model with a prewritten click sequence and call that discovery.

## 3. Computer-use technology and observation strategy

| Option | Strength | Main limitation for this assignment | Verdict |
| --- | --- | --- | --- |
| Playwright with semantic/contextual locators | Direct control over actions, waiting, and verification | Browser-only; poorly labeled controls need another targeting strategy | Preferred execution foundation |
| Puppeteer | Direct browser automation if already familiar | Does not remove the need to design recording, replay, or handoff | Reasonable, no decisive advantage here |
| Selenium | Suitable if existing WebDriver knowledge or infrastructure is useful | This project does not need an existing grid or extensive browser matrix | Acceptable but not the default |
| Stagehand | Higher-level natural-language browser operations and documented caching | Cached model results are not the complete typed capability and error contract | Consider as a discovery helper, not the authoritative replay design |
| Browser Use | Existing browser-agent loop and provider integrations | Need to expose action boundaries and preserve session/control semantics | Good Python-first shortcut if kept behind our interfaces |
| Screenshot + mouse/keyboard | Closer to surfaces with no useful DOM, including desktop | Coordinate normalization, target identity, output extraction, and deterministic replay become harder | Useful discovery mode; avoid raw-coordinate replay as the whole solution |
| OS accessibility/native automation | Credible desktop approach | Platform setup and adapters compete with core implementation time | Describe the extension; defer implementation |

Primary references: [Playwright locators](https://playwright.dev/docs/locators), [Puppeteer](https://pptr.dev/), [Selenium overview](https://www.selenium.dev/documentation/overview/), [Stagehand act and caching](https://docs.stagehand.dev/v4/basics/act), [Browser Use quickstart](https://docs.browser-use.com/open-source/quickstart).

**Recommended observation strategy:** screenshots plus a compact description of visible controls, text, roles, and context; execute through Playwright. Support useful existing labels and scoped table/frame context without relying on automation-only test IDs.

Snapshot control IDs are temporary handles. Before recording a step, resolve the selected control to a persistent target description that can be validated on a fresh observation. If screenshot discovery selects coordinates, associate the visible hit target with that description where possible. An unresolved or ambiguous target blocks promotion into an unattended capability; it is not silently replaced by a guessed selector.

A screenshot-only discovery mode with semantic recording would be a stronger optional demonstration of the legacy constraint, but it adds recorder complexity. For genuine DOM-less surfaces, describe a separate accessibility or deterministic visual-target adapter. Do not claim that a browser implementation already supports native desktops.

## 4. Target application and workflow

| Target | Benefits | Costs/risks | Recommendation |
| --- | --- | --- | --- |
| Public sandbox/demo | Little app-building effort; an independently built UI | Resets, uptime, rate limits, and failure injection may be outside our control | Acceptable fallback |
| Small local sample app | Repeatable data, deliberate failures, easy reviewer setup | Must avoid making the target artificially easy or spending too long on it | Preferred |
| Local app with modest legacy characteristics | Can demonstrate repeated labels, tables, and a frame | Additional locator and observation complexity | Add one or two characteristics to the local target |
| Native desktop sample | Directly demonstrates heterogeneity | Environment and manual-control setup add significant work | Defer |

Choose one primary capability: `get_savings_balance(memberId)`.

Flow: search member → open matching member → select savings account → verify member/account identity → extract amount and currency. Return an integer minor-unit amount plus currency, with member IDs represented as strings to preserve leading zeroes. Set one locale and currency for the initial fixture.

Use several synthetic members with distinct balances, a missing member, and deterministic switches for delayed loading, session expiry, permission denial, and an unexpected dialog. Keep fixture setup/reset separate from the automation surface. The model and replay runner must not use hidden fixture state or application APIs to complete the business task. An independent test harness may use fixture truth to verify results.

A risky sample control can demonstrate a denied action without implementing a second banking workflow. Block irreversible actions in the initial policy.

## 5. Artifact schema and storage

| Option | Advantage | Problem | Recommendation |
| --- | --- | --- | --- |
| JSON + runtime validation | Portable, reviewable, easy to validate and diff | Less friendly for handwritten commentary | Canonical artifact |
| YAML + validation | Convenient for manual authoring | Another parser and input representation | Optional authoring format later |
| Generated TypeScript/Python | Directly executable | Arbitrary code is harder to constrain, review, and adapt to new surfaces | Optional output later, not the canonical artifact |
| SQLite/database | Useful for querying many capabilities and runs | Schema migrations and storage work before scale exists | Defer |

Recommend Zod as the TypeScript schema source, exporting a JSON Schema restricted to representable constructs. Python's Pydantic is an equally valid counterpart. [Zod JSON Schema](https://zod.dev/json-schema), [Pydantic JSON Schema](https://pydantic.dev/docs/validation/latest/concepts/json_schema/)

The proposed artifact separates:

- `schemaVersion`: the format understood by the interpreter.
- Capability name and `capabilityVersion`: behavior reviewed for use.
- Input/output schemas and explicit input references.
- Required surface features, vendor/app identity, and compatible app versions.
- Ordered typed steps with target descriptors, preconditions, postconditions, and bounded recovery.
- Known business outcomes and final output extraction/checks.
- References to policy and sanitized discovery evidence.

Store one formatted JSON file per capability version and separate JSONL events per run. Artifact-requested permissions cannot widen the independently configured execution policy. Treat every loaded artifact as untrusted input: reject unsupported versions/actions and arbitrary executable expressions.

For future tenant reuse, keep the base capability separate from validated tenant configuration: entry URL, allowed label/locator overrides, and declared app version. Reject incompatible versions rather than applying an unbounded fallback. Do not embed credentials or member values in the reusable artifact.

Discovery supplies successful action evidence; reviewed engine rules or explicit capability annotations supply exception behavior that was never observed. Describe that provenance honestly.

## 6. Deterministic replay, targeting, and recovery

| Strategy | Trade-off | Decision |
| --- | --- | --- |
| Repeat raw clicks and fixed sleeps | Simple recording; weak identity and timing guarantees | Reject as the core |
| Interpret typed steps with explicit predicates | More design work; auditable decisions and outputs | Recommended |
| Ordered locator fallbacks | Useful if each fallback preserves target meaning | Allow a small validated list; stop on ambiguity |
| LLM self-healing | May rescue discovery but introduces new decisions | Keep out of ordinary replay; optional separately labeled assisted mode later |

Prefer role/name or label where meaningful; otherwise use scoped visible text and stable table/frame context. Re-resolve targets at each step. Wait for declared state transitions within deadlines, rather than treating a click completing as proof of success. Playwright provides actionability checks, but business-state verification is ours. [Playwright auto-waiting](https://playwright.dev/docs/actionability)

Define terminal results as success with outputs, a named business outcome, or failure with step/expected/observed details. Track waiting for intervention as a run lifecycle state with an intervention ID; resumption yields the eventual terminal result.

Examples:

- Missing member: return `member_not_found`.
- Slow load: wait within a bounded deadline; retry only safe operations.
- Known benign dialog: handle with an explicit rule.
- Session expiry: request human restoration of the same session, then verify the restart checkpoint.
- Permission denial or policy denial: stop with a clear classification; do not work around permissions.
- Unknown dialog or ambiguous target: pause or stop with evidence.
- Timeout after a consequential action: reconcile the visible result before retrying; otherwise escalate.

Replay has no dependency on the model adapter and can run without model credentials. Determinism means fixed decision rules for observed conditions, not that changing application data must produce an unchanged balance.

## 7. Architecture and boundaries

| Architecture | Benefit | Cost | Verdict |
| --- | --- | --- | --- |
| One automation process with explicit modules | Easy setup, state ownership, debugging | No distributed crash recovery | Recommended |
| Local HTTP service | Useful for a separate operator UI or an agent-facing endpoint | Authentication and lifecycle work | Add only a minimal loopback control surface if needed |
| Queue + workers + database | Scaling and durable jobs | Infrastructure the brief explicitly does not reward | Design later |
| General agent graph/orchestration framework | Helpful for complicated workflows | Extra semantics to explain for a small loop | Not required |

The sample app may be a separate local process; "one process" refers to automation orchestration.

Conceptual modules: model adapter → discovery coordinator → validated action executor → surface adapter. A recorder produces the capability. A separate replay interpreter uses the same executor and surface adapter. Policy, session ownership, and sanitized events are shared enforcement points.

The surface adapter observes, resolves targets, acts, and extracts visible data. Workflow logic never needs a raw browser page object. Implement only the browser adapter; explain accessibility/visual adapter requirements and unsupported features.

CLI commands are sufficient for discovery, replay, inspection, intervention, and resume. Preserve the live session in memory through a handoff. Process crash recovery and distributed ownership remain explicit cuts.

## 8. Acceptance criteria and evidence plan

Earlier preparation decision 2 was not covered by Section 4. Compare an informal happy-path demo with a small repeatable scenario matrix: the latter demonstrates the rubric much more convincingly.

| Scenario | What we must prove |
| --- | --- |
| Real discovery | Actual model requests cause actual UI actions and reach a verified goal |
| Parameterized replay | Same saved artifact handles another member with a different expected balance |
| No model during replay | No credentials required and zero model calls recorded |
| Missing member | Structured business outcome, not a crash |
| Invalid input | Rejected before any UI mutation |
| Delayed response | Bounded wait or safe recovery, never a blind continuation |
| Permission denial | Clear stop without a bypass |
| Human intervention | Same live session; automation pauses; human acts; resume revalidates state |
| Policy denial | Forbidden route or action is refused before execution |
| Failed checkpoint | Step, expected state, observed state, and sanitized richer evidence are available |
| Sensitive-data sentinel | Known synthetic secret/PII marker is absent from exported artifacts and logs |

Prioritize tests of meaningful boundaries: ambiguous locators, ownership transitions, policy enforcement, data redaction, and duplicate-action risk. Avoid tests that only mirror trivial implementation details.

Optional stretch choices: replay a declared scenario mix repeatedly and report successes/failures, then demonstrate one base capability on a second app variant. Do not present an untested confidence score as reliability evidence.

## 9. Session ownership, human actions, and safety

Earlier preparation decision 5 crosses architecture and replay but needs its own concrete plan.

| Handoff approach | Benefit | Cost | Recommendation |
| --- | --- | --- | --- |
| Existing local browser + CLI resume | Smallest real same-session takeover | Reviewer must be on the same machine; manual action capture still required | Preferred initial demo |
| Minimal local operator page | Clear intervention context and buttons | Extra UI/control channel | Useful if CLI workflow is confusing |
| Remote desktop/co-browsing | Remote operator can act | Streaming, access control, and deployment complexity | Defer |

Use explicit states: automation running → pausing → human control → validating resume → automation running or terminal stop. Finish/cancel in-flight automation before granting control. Recheck ownership before executing each action, including actions returned by a pending model request. A human resume signal is not evidence that the page is correct.

Capture observable human clicks, field-change metadata, navigation, and checkpoint changes while omitting sensitive field values. Combine this with an intervention reason and sanitized before/after evidence; a freeform note alone does not prove what happened. If handoff changes the workflow, rejoin only at a declared checkpoint, otherwise stop or mark the completion as human-assisted. Do not automatically incorporate unreviewed human steps into the capability.

Use a separate disposable browser profile, exact allowed origins/routes, allowed action types, and capability-level operation restrictions. Check destinations and popups before allowing automated navigation. No arbitrary JavaScript/shell tools in the agent contract. Return sensitive outputs only to the authorized caller; logs should record output shape/status rather than raw values.

The demo's human control covers benign recovery with synthetic data. Direct manual browser control is not fully mediated by the automation policy; document this limit rather than claiming that a browser allowlist constrains everything an operator can do. No permission bypass or irreversible transaction demo is needed.

## 10. Preparation, time budget, and submission

Earlier preparation decision 1 maps to Section 4's target choice, decision 3 to the artifact, and decision 4 to the computer-use approach. Decisions 2, 5, and 6 are covered here in Sections 8–10.

Before implementation:

1. Confirm the chosen language reflects actual familiarity and select one provider account with API access. Keep keys outside Git; no key is needed to review this planning document.
2. Fix the first capability, synthetic fixtures, locale, and controlled failure scenarios.
3. Review the artifact, result contract, targeting rules, and control-transfer states together.
4. Write the small acceptance matrix before building the loop.
5. Set a step/time/spend cap for live discovery. Do not assume a subscription to a coding assistant grants application API credit.
6. Establish sanitized logging before the first live run. Default rich capture to safe export, not automatic persistence of full browser traces.
7. Make the local reset and human-control experience reproducible. A cloud browser introduces another account/network boundary and is unnecessary initially.
8. Reserve time for a clean-clone rehearsal, evidence review, and the short report.

Suggested effort allocation, not a delivery estimate: 15% contracts and target, 25% discovery and recorder, 25% replay and failure handling, 20% handoff and safety integration, 15% evidence and documentation. Rebalance based on what fails; do not omit a core requirement to polish another.

The first implementation milestone should be one real discovery followed by parameterized replay, with recording and policy checks present from the start. The next completes failures and real takeover. Optional extensions come only after all mandatory scenarios work.

The final root `REPORT.md` must use exactly these headings: Architecture; Artifact schema; Determinism & error handling; Heterogeneity & multi-tenant; Escalation & handoff; Safety; Cuts. Keep this longer planning comparison separate from that 1–3 page submission report.

The final `evidence/` must contain genuine discovery/replay logs and a saved capability. A simulated provider may help offline tests but does not replace real discovery evidence. The repository must become public before submission; changing visibility and emailing the submission are later actions.
