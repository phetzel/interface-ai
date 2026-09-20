# interface-ai

A computer-use automation assignment built around a synthetic banking desktop. Python drives OS input and reads pixels; React supplies the sample app. OpenAI discovers a savings lookup, a recorder captures the executed path, and an independently reviewed capability replays it for another member with local vision/OCR and zero model calls.

**Current:** M1–M3 desktop, policy and same-session takeover are implemented. M4 is complete: genuine discovery, recording, reviewed promotion and offline second-member replay have passed integrated acceptance and the full M1–M3 regressions. [Evidence and limitations](evidence/README.md) · [M4 design](docs/MILESTONE_4.md).

**Submission preparation:** [REPORT.md](REPORT.md) and the [requirements review](docs/ASSESSMENT_CHECK.md) are written. M5 validation and clean-checkout rehearsal are in progress; your manual review and interview walkthrough remain. The earlier real-person handoff is preserved in [manual audit observations](docs/MANUAL_AUDIT_NOTES.md). Generated promotion is labeled agent review, and automated takeover checks remain simulated-operator evidence. [Current plan](docs/CURRENT_PLAN.md) · [full roadmap](docs/ROADMAP.md) · [author review and delivery](docs/SUBMISSION.md).

## Try the demo

Prerequisites: Docker Desktop/Compose and Make on the tested Apple Silicon host, with network access for the initial build. From the repository root:

```sh
make assess
```

Open the [operator panel](http://127.0.0.1:6081/). Expect Demo Member B’s Savings balance, **$98.07 USD**, and **Lookup complete**. This uses the checked-in artifact from a genuine discovery, with no host SDK or key. Follow the [short assessor walkthrough](docs/DEMO.md) for provenance, translated layout and takeover.

For a new online run (after the build), provide a goal and approved target:

```sh
make discover GOAL="Find the savings balance for member 00123" TARGET=synthetic-bank MEMBER_ID=00123
```

This uses the pinned host OpenAI environment and resets the synthetic bank only after request/key/build validation. The supported goal grammar accepts find/read/get/look up a savings balance for a five-digit member; other intents or targets fail before execution. See `python3 scripts/discover --help` or validate without a key/desktop using `--check-request --goal "Find the savings balance for member 00123" --target synthetic-bank`. The key stays in the host’s private `.env`. [Provider setup](docs/M4_01_PROVIDER_PROBE.md) · [discovery limits](docs/M4_03_DISCOVERY.md) · [recording evidence](evidence/m4-04-recorded-candidate/README.md) · [review and promotion](docs/M4_05_PROMOTION.md). `make review RUN=<host-discovery-folder>` evaluates an unapproved candidate; promotion is explicit and refuses to overwrite an existing approval.

`make start` remains the one-command build/start entry for the historical manual capability and the original M1–M3 checklist. Choose **Start lookup** in the panel for member `00123`. This manual artifact has its own provenance and approval. Reset/start commands replace the desktop session; Docker reuses unchanged build layers.

Runtime support is Linux ARM64, Python 3.11, one 1280×800 X11 display, fixed scale/fonts and en-US/USD. Docker is the supported distribution; a standalone Python wheel is not validated. The bank runs inside isolated Chromium at `http://fixture:4173/`. `00123` and `00456` are synthetic members; `00999` exercises the named member-not-found outcome. IDs are strings, including leading zeroes. Watch the same desktop in the operator panel; the legacy 6080 viewer has been removed.

The demo has one entry point: the operator panel. The other surfaces serve development and verification:

| Surface | Purpose | Needed for the demo? |
| --- | --- | --- |
| Operator, port 6081 | Start a lookup, watch the desktop, take control and resume | Yes |
| Host bank preview, port 4173 | Develop and manually test the synthetic sample app outside the isolated desktop | No |
| Native calibration pad | Prove OS clicks, typing and scrolling work outside a browser | No; keep for desktop regression tests |

The operator shows controls for the current phase, keeps Stop available during pending input, and puts the session UUID and step/reason in **Run details**. Choose **Actual size** for larger targets and scroll within the desktop viewport; **Fit to panel** restores the scaled view. Human text input uses **Text to send → Send text** after clicking a field in the desktop image.

```sh
make demo CAPABILITY=discovered-savings MEMBER_ID=00456 SCENARIO=translated  # Reset, then replay
make reset                                  # Fresh bank search/session
make reset MODE=native                      # Native calibration pad
make stop                                   # Block further input; reset to continue
make down                                   # Stop services; retain evidence/images
```

`make replay` uses the same coordinator as the operator, so CLI runs are visible there and can be stopped or taken over. [Shared lifecycle](docs/M4_02_SHARED_LIFECYCLE.md). It uses the current screen; `make demo` resets first. Starts reuse existing images. After editing image inputs, **build before resetting**. `make build-check` checks both image/source fingerprints and shipped runtime bytes. The live acceptance gates also verify the running containers use those images. `make help` lists all commands; targets run sequentially because they share one desktop.

## Same-session human takeover

```sh
make handoff-demo CAPABILITY=discovered-savings MEMBER_ID=00123
make operator
```

Refresh the [operator panel](http://127.0.0.1:6081/) after reset and choose **Take control** at the paused synthetic expiry. The command already started the generated lookup. Click the training-code field, send `demo` through the panel's text controls, and click **Restore workspace** on the desktop. Choose **Verify & resume** on the original member overview. The session stays the same; an invalid return keeps human ownership. Arbitrary interruption has no verified continuation and requires reset.

Stop remains available during pending input. Each started handoff writes a separate `result.json`, sanitized `audit.jsonl`, and terminal `summary.json`, including stopped/expired runs. The summary binds the result digest and records step/checkpoint context and action counts. An already-dispatched primitive may finish; its event updates the count without replacing the terminal outcome. Storage failure revokes input and is visible in panel status. [Lifecycle/evidence details](engine/src/interface_ai/handoff/README.md).

The operator image is observation only. Input requires human ownership and goes through the guarded OS adapter; there is no separate VNC server. Automated panel/API tests and the completed real-person demonstration have distinct evidence provenance.

## Development and checks

Host development/checks need Python 3.9+, Node 22 (`.nvmrc` pins the tested version), and `uv` for pinned Ruff. The runtime dependencies remain separately hash-locked inside Docker. Prettier is an exact fixture development dependency; neither formatting tool enters replay's Python runtime.

```sh
make fixture-install
make quality        # Formatting and basic correctness lint
make format         # Format active source; historical evidence is excluded
make build
make quick-check    # No live desktop: build identity, unit tests, schemas, types
make fixture-test   # React build + 15 Playwright browser tests
make policy-check   # M2 policy/export plus full M1 lifecycle/replay regression
make handoff-check  # Manual artifact, both members; simulated operator
make m4-check       # Generated matrix/handoff, offline boundary and safe export
```

Install Playwright's Chromium once with `cd apps/bank-fixture && npx playwright install chromium`. The two panel browser checks are `scripts/checks/m3_operator_ui.mjs` and `scripts/checks/m3_operator_stop.mjs`; reset with `make handoff-demo` before each, then run it with Node from the repository root. They interact with bank pixels, never its DOM.

[Quality CI](.github/workflows/quality.yml) runs the same quick gate on Linux ARM64. It does not stand in for the live desktop or human gates. Every local quick/live attempt retains logs under `tmp/`. A stale build or schema fails explicitly; checks do not silently rebuild images or rewrite schemas. The schema command is documented in the [replay guide](engine/src/interface_ai/replay/README.md).

For host React work, `make fixture-dev` starts Vite. After dependency installation, `make fixture-preview` builds and serves the preview at [127.0.0.1:4173](http://127.0.0.1:4173). This is separate from the isolated desktop fixture.

## Read the repo in this order

| Area | Entry point | What to understand |
| --- | --- | --- |
| Fixture | [App and component guide](apps/bank-fixture/README.md#code-walkthrough) | Screen composition, workflow hook, local UI state and synthetic scenarios |
| Capability | [Manual capability](capabilities/poc/savings-balance/README.md), [Pydantic models](engine/src/interface_ai/contracts/models.py) | Inputs, relative targets, checkpoints, result variants and independent approval |
| Discovery/promotion | [Host loop](scripts/lib/discovery_flow.py), [worker](engine/src/interface_ai/discovery/worker.py), [recorder](engine/src/interface_ai/discovery/recorder.py), [admission](engine/src/interface_ai/policy/admission.py) | Model-selected inputs, recorded derivations, private crops and independent authority |
| Replay | [Loader](engine/src/interface_ai/replay/loader.py), [interpreter](engine/src/interface_ai/replay/interpreter.py) | Bounded verified snapshots; one observation per field set; no uncertain input retry |
| Desktop | [Adapter](engine/src/interface_ai/desktop/adapter.py), [backend protocol](engine/src/interface_ai/desktop/types.py), [ownership](engine/src/interface_ai/desktop/ownership.py) | Input admission, Stop, epochs, lock draining and modifier cleanup |
| Policy | [Bank policy](engine/src/interface_ai/policy/bank.py), [gateway](engine/src/interface_ai/policy/gateway.py), [evidence exporter](engine/src/interface_ai/policy/evidence.py) | Operator authority, allowed surfaces/routes and reconstructive metadata export |
| Handoff | [Controller and evidence guide](engine/src/interface_ai/handoff/README.md) | Transitions, verified continuation, terminal outcomes, HTTP boundary and panel assets |
| Infrastructure | [Compose](compose.yaml), [desktop startup](infra/desktop/start.py) | Isolation, sandboxing, process supervision and same-session viewing |
| Verification | [Quick gate](scripts/quick-check), [build verification](scripts/lib/builds.py), [evidence index](evidence/README.md) | Distinguish test oracle, source identity, shipped image, automation evidence and human observations |

The primitive `BankVision` path remains for M1 calibration/history. Production replay reads the admitted capability; CLI and panel share one coordinator. Discovery reuses recognition and guarded input but chooses actions through the model. The recorder preserves executed inputs; independent approval supplies authority and the sole continuation boundary.

## Manual review and interview preparation

Start with [the manual checklist and M4 supplement](docs/manual-acceptance.html) to test behavior. Then use [the repository/interview checklist](docs/repository-audit.html) to explain the code and its tradeoffs. These are our detailed internal reviews; assessors can use the [short demo guide](docs/DEMO.md).

With the development prerequisites above installed, run this once from the repository root:

```sh
make audit-setup
```

This installs fixture dependencies and Playwright Chromium, builds both images, runs the quick gate, and starts a fresh validated bank desktop. Review its output for the checklist's setup checks; no results are marked automatically. Then run `make fixture-preview` in a second terminal for the banking UI section. Open the checklists on macOS:

```sh
open docs/manual-acceptance.html
open docs/repository-audit.html
```

Both work offline, save independent browser-local notes/statuses, export JSON and print. They require no name, revision or date form. They execute no commands and prefill no acceptance results. The acceptance harnesses record source provenance; include `git describe --always --dirty` output in issue notes when useful. Use the [evidence index](evidence/README.md) to distinguish historical runs from current validation.

## Boundaries and troubleshooting

The non-root desktop has no default route, host home, credentials, Docker socket or fixture oracle. A fixed-upstream gateway exposes approved fixture routes; managed Chromium policy restricts navigation. The fixed operator relay alone publishes loopback port 6081; the desktop still has no default route. Runtime observations stay in memory. Explicit synthetic calibration utilities retain debug captures; ordinary replay and safe export suppress images. Export approved replay metadata with `make export RUN=<printed-run-directory>`; business results stay local.

Exact member identity, integer money, ambiguity rejection, bounded waits and typed failure/business outcomes remain deliberate constraints. The trusted host, runtime and fixture are inside the PoC's trust boundary; this is not authorization for arbitrary applications or general screenshot redaction. Base images and Python packages are pinned; most OS packages resolve at build time, with versions retained in evidence. A later rebuild must be validated.

- Docker unavailable: start Docker Desktop; use `make logs` and `make ready` for diagnosis.
- Stale image: `make build`, then `make reset`; acceptance now refuses a stale source/image pair.
- Wrong screen, stopped input or expired ownership: reset the desktop, then reload the operator panel.
- Port conflict: free loopback port 6081 before starting the operator. Port 6080 is no longer used.
- Public image metadata hangs on macOS: see the documented credential-helper workaround in [desktop setup](docs/DEVELOPMENT.md).

[Development and build provenance](docs/DEVELOPMENT.md) · [M1 history](docs/MILESTONE_1.md) · [M2 design](docs/MILESTONE_2.md) · [M3 design](docs/MILESTONE_3.md) · [initial decisions](docs/DECISIONS.md).
