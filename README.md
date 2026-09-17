# interface-ai

A computer-use automation assignment built around a synthetic banking desktop. Python drives OS input and reads pixels; React supplies the sample app. A reviewed manual capability looks up a member's savings balance with local vision/OCR and zero model calls.

**Current:** M1 desktop/replay, M2 bounded policy/evidence and M3 same-session takeover are implemented. The repository cleanup fixes artifact snapshots, terminal handoff evidence and input error classification; adds build verification and a quick quality gate; and separates the React views and operator assets. [Evidence and limitations](evidence/README.md) · [cleanup audit and resolution](docs/CLEANUP_AUDIT_2026-09-17.md).

**Still required:** genuine OpenAI discovery → reviewed generated capability → replay for the second member, a real-person handoff demonstration, and final `REPORT.md`/demo packaging. The existing manual artifact and simulated operator checks do not satisfy those remaining requirements. [Current plan](docs/CURRENT_PLAN.md) · [full roadmap](docs/ROADMAP.md).

## Start the desktop

Prerequisites: Docker Desktop/Compose on the tested Apple Silicon host, with network access for the initial build. Runtime support is Linux ARM64, Python 3.11, one 1280×800 X11 display, fixed scale/fonts and en-US/USD. Docker is the supported distribution; a standalone Python wheel is not validated.

```sh
make build
make up
make validate
make replay MEMBER_ID=00123
```

Open the [read-only viewer](http://127.0.0.1:6080/vnc.html?autoconnect=true&resize=scale&view_only=true). The bank runs inside isolated Chromium at `http://fixture:4173/`. `00123` and `00456` are synthetic members; `00999` exercises the named member-not-found outcome. IDs are strings, including leading zeroes.

```sh
make demo MEMBER_ID=00456 SCENARIO=translated  # Reset, then replay
make reset                                  # Fresh bank search/session
make reset MODE=native                      # Native calibration pad
make stop                                   # Block further input; reset to continue
make down                                   # Stop services; retain evidence/images
```

`make replay` uses the current screen; `make demo` resets first. Starts reuse existing images. After editing image inputs, **build before resetting**. `make build-check` checks both image/source fingerprints and shipped runtime bytes. The live acceptance gates also verify the running containers use those images. `make help` lists all commands; targets run sequentially because they share one desktop.

## Same-session human takeover

```sh
make handoff-demo
make operator
```

Open the [operator panel](http://127.0.0.1:6081/), start a lookup, and choose **Take control** when the synthetic session expires. Click the training-code field, send `demo` through the panel's text controls, and click **Restore workspace** on the desktop. Choose **Verify & resume** on the original member overview. The session stays the same; an invalid return keeps human ownership. Arbitrary interruption has no verified continuation and requires reset.

Stop remains available during pending input. Each started handoff writes a separate `result.json`, sanitized `audit.jsonl`, and terminal `summary.json`, including stopped/expired runs. The summary binds the result digest and records step/checkpoint context and action counts. An already-dispatched primitive may finish; its event updates the count without replacing the terminal outcome. Storage failure revokes input and is visible in panel status. [Lifecycle/evidence details](engine/src/interface_ai/handoff/README.md).

noVNC is server-enforced view-only. The operator panel alone grants human input through the same guarded OS adapter. Automated panel/API tests simulate a human; your demonstration remains a separate acceptance gate.

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
make handoff-check  # Both members; simulated human through the operator API
```

Install Playwright's Chromium once with `cd apps/bank-fixture && npx playwright install chromium`. The two panel browser checks are `scripts/checks/m3_operator_ui.mjs` and `scripts/checks/m3_operator_stop.mjs`; reset with `make handoff-demo` before each, then run it with Node from the repository root. They interact with bank pixels, never its DOM.

[Quality CI](.github/workflows/quality.yml) runs the same quick gate on Linux ARM64. It does not stand in for the live desktop or human gates. Every local quick/live attempt retains logs under `tmp/`. A stale build or schema fails explicitly; checks do not silently rebuild images or rewrite schemas. The schema command is documented in the [replay guide](engine/src/interface_ai/replay/README.md).

For host React work, `make fixture-dev` starts Vite. A built preview uses `npm --prefix apps/bank-fixture run build` and `npm --prefix apps/bank-fixture run preview`, then [127.0.0.1:4173](http://127.0.0.1:4173). This is separate from the isolated desktop fixture.

## Read the repo in this order

| Area | Entry point | What to understand |
| --- | --- | --- |
| Fixture | [App and component guide](apps/bank-fixture/README.md#code-walkthrough) | Screen composition, workflow hook, local UI state and synthetic scenarios |
| Capability | [Manual capability](capabilities/poc/savings-balance/README.md), [Pydantic models](engine/src/interface_ai/contracts/models.py) | Inputs, relative targets, checkpoints, result variants and independent approval |
| Replay | [Loader](engine/src/interface_ai/replay/loader.py), [interpreter](engine/src/interface_ai/replay/interpreter.py) | Bounded verified snapshots; one observation per field set; no uncertain input retry |
| Desktop | [Adapter](engine/src/interface_ai/desktop/adapter.py), [backend protocol](engine/src/interface_ai/desktop/types.py), [ownership](engine/src/interface_ai/desktop/ownership.py) | Input admission, Stop, epochs, lock draining and modifier cleanup |
| Policy | [Bank policy](engine/src/interface_ai/policy/bank.py), [gateway](engine/src/interface_ai/policy/gateway.py), [evidence exporter](engine/src/interface_ai/policy/evidence.py) | Operator authority, allowed surfaces/routes and reconstructive metadata export |
| Handoff | [Controller and evidence guide](engine/src/interface_ai/handoff/README.md) | Transitions, verified continuation, terminal outcomes, HTTP boundary and panel assets |
| Infrastructure | [Compose](compose.yaml), [desktop startup](infra/desktop/start.py) | Isolation, sandboxing, process supervision and same-session viewing |
| Verification | [Quick gate](scripts/quick-check), [build verification](scripts/lib/builds.py), [evidence index](evidence/README.md) | Distinguish test oracle, source identity, shipped image, automation evidence and human observations |

The primitive `BankVision` path is retained for M1 calibration/history; production manual replay reads its targets from the capability. CLI replay and panel execution still have separate lifecycle entry points. Unifying them, exposing a recognition/checkpoint interface, and adding a reviewed promotion manifest are the next discovery/integration work, rather than additional cleanup abstractions.

## Manual review and interview preparation

Open [the M1–M3 manual checklist](docs/manual-acceptance.html) and [the repository/interview checklist](docs/repository-audit.html). On macOS:

```sh
open docs/manual-acceptance.html
open docs/repository-audit.html
```

Both work offline, save independent browser-local notes/statuses, export JSON and print. They execute no commands and prefill no acceptance results. Record the actual commit and dirty state (`git describe --always --dirty`) and use the [evidence index](evidence/README.md) to distinguish historical runs from current validation.

## Boundaries and troubleshooting

The non-root desktop has no default route, host home, credentials, Docker socket or fixture oracle. A fixed-upstream gateway exposes approved fixture routes; managed Chromium policy restricts navigation. The viewer relay alone publishes loopback ports 6080/6081. Runtime observations stay in memory. Explicit synthetic calibration utilities retain debug captures; ordinary replay and safe export suppress images. Export approved replay metadata with `make export RUN=<printed-run-directory>`; business results stay local.

Exact member identity, integer money, ambiguity rejection, bounded waits and typed failure/business outcomes remain deliberate constraints. The trusted host, runtime and fixture are inside the PoC's trust boundary; this is not authorization for arbitrary applications or general screenshot redaction. Base images and Python packages are pinned; most OS packages resolve at build time, with versions retained in evidence. A later rebuild must be validated.

- Docker unavailable: start Docker Desktop; use `make logs` and `make ready` for diagnosis.
- Stale image: `make build`, then `make reset`; acceptance now refuses a stale source/image pair.
- Wrong screen, stopped input or expired ownership: reset the desktop, then reconnect the viewer/panel.
- Port conflict: 6081 is fixed for the panel. Set `DESKTOP_PORT=6082` consistently for viewer commands if 6080 is occupied.
- Public image metadata hangs on macOS: see the documented credential-helper workaround in [desktop setup](docs/DEVELOPMENT.md).

[Development and build provenance](docs/DEVELOPMENT.md) · [M1 history](docs/MILESTONE_1.md) · [M2 design](docs/MILESTONE_2.md) · [M3 design](docs/MILESTONE_3.md) · [initial decisions](docs/DECISIONS.md).
