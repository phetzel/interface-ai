# interface-ai

A computer-use automation system in development: model-driven discovery, reusable capabilities, deterministic replay, policy enforcement, and human takeover of the same live session.

**Implemented: M1-01 (isolated desktop) and M1-02 (banking fixture and oracle).** The native desktop supports real screenshots, mouse/keyboard input, and read-only viewing. The React/TypeScript fixture provides member search, account selection, balances, and controlled failure scenarios. Shared desktop/browser integration, visual replay, model integration, and human takeover remain later work. No OpenAI key is needed for these steps.

## Preview the banking fixture

```sh
cd apps/bank-fixture
npm ci
npm run build
npm run preview
```

Open the [banking preview](http://127.0.0.1:4173). Search for `00123` or `00456`, then open Savings; `00999` demonstrates member not found. [Fixture setup, scenario controls, and tests](apps/bank-fixture/README.md) · [M1-02 evidence](evidence/poc-m1/fixture/README.md).

To run the fixture inside the desktop network, use `./scripts/fixture up` from the root. It serves `http://fixture:4173` internally. The current noVNC desktop still shows the calibration pad; launching and controlling Chromium through the shared adapter is M1-03.

## Run the native desktop step

Prerequisite: Docker Desktop running with Docker Compose v2. Tested on an Apple Silicon Mac with native Linux ARM64 containers, Docker 28.3.2 and Compose 2.39.1. No host Python or Node installation is required. The first build downloads public Debian and Python packages and needs internet access; subsequent starts reuse the local image. The desktop is limited to 2 CPUs/2 GiB and the viewer relay to 0.5 CPU/128 MiB.

From the repository root:

```sh
./scripts/desktop up
./scripts/desktop smoke
```

Open the [read-only desktop viewer](http://127.0.0.1:6080/vnc.html?autoconnect=true&resize=scale&view_only=true). The three targets turn green, synthetic text appears in the input field, and the text panel scrolls. The viewer scales the image; the automation always uses the desktop's 1280×800 coordinates.

| Command | Behavior |
| --- | --- |
| `./scripts/desktop up` | Build if the image is absent, start services, wait for readiness, print viewer URL |
| `./scripts/desktop ready` | Check required processes, native pad, display dimensions, and desktop web endpoint; print session ID |
| `./scripts/desktop smoke` | Run eight bounded checks on a fresh calibration pad; exit nonzero on failure |
| `./scripts/desktop screenshot` | Save the known synthetic screen to `tmp/desktop-artifacts/desktop.png` |
| `./scripts/desktop stop-input` | Prevent the smoke executor's next input dispatch; reset required to run again |
| `./scripts/desktop reset` | Recreate both containers with a fresh session and pad; preserve exported evidence |
| `./scripts/desktop down` | Stop and remove all project services, including the optional fixture; keep images and evidence |
| `./scripts/desktop build` | Explicitly rebuild after changing desktop source/dependencies |
| `./scripts/desktop logs` | Show recent desktop and viewer logs |
| `./scripts/desktop viewer` | Print the local viewer URL |

Run `reset` before each repeated smoke test. After editing image contents, run `build`, then `reset`. If port 6080 is occupied, use `DESKTOP_PORT=6081 ./scripts/desktop up` and use the same value for later commands. After a reset, reload/reconnect the viewer.

Smoke output is written under `tmp/desktop-artifacts/<run-id>/`: `report.json`, `events.jsonl`, and before/after PNGs. Reports include dependency versions, architecture, display dimensions, session ID, elapsed time, and checks. Failed executions after run initialization also retain a report. Preconditions rejected before initialization print a diagnostic and do not create a run bundle. Raw local output is ignored by Git. Reviewed results live in [desktop evidence](evidence/poc-m1/desktop/README.md).

## What this proves

- Native PyAutoGUI clicks arrive at the exact screenshot coordinates and visibly change all three targets.
- Typing, selection/replacement, Enter, and scrolling reach a native Tk application.
- VNC serves pixels from the same X11 display and rejects attempted input at the server, beyond the viewer's client setting.
- Cooperative stop prevents dispatch; reset and shutdown/start produce fresh sessions.
- The desktop has no default IPv4 route, and the tested external TCP destinations are unreachable.

The test pad's fixed coordinates and independent state oracle are calibration fixtures, not reusable visual locators or replay. There are no model calls. This does not yet validate banking lookup, browser bootstrap, OCR, cross-OS portability, or human takeover.

## Environment and boundaries

`infra/desktop/` packages Xvfb, Openbox, PyAutoGUI, a native Tk test pad, Chromium, x11vnc, and noVNC. Chromium is installed for the next step; a browser workflow has not been launched or validated. Python dependencies are version/hash locked; the Debian base image is digest pinned. Debian packages are resolved at build time and their exact versions recorded in `/opt/desktop/system-packages.txt`, so a later clean build can receive updated OS packages.

The non-root desktop joins an internal Compose network. Only `tmp/desktop-artifacts` is mounted; no host home, browser profile, credentials, or Docker socket is exposed. A separate fixed-destination TCP relay publishes the viewer at `127.0.0.1:6080`. It joins an ordinary bridge network for Docker Desktop port publishing and the internal network to reach the desktop. The relay forwards only to `desktop:6080`; the desktop itself has no default route. This arrangement was necessary because a published port on an internal-only network was not reachable on the tested host.

The viewer is unauthenticated and read-only, intended for synthetic local data. The stop command is cooperative: an already-dispatched short primitive may finish; it is not an ownership/handoff protocol. `down` terminates the environment. The screenshot guard checks known fixture pixels; it is not general redaction or a reliable sensitive-screen detector. Network probes and container restrictions are a bounded PoC, not comprehensive hostile-code containment. General policy and safe export remain later gates.

## Troubleshooting

- **Docker unavailable:** start Docker Desktop and retry. Logs/readiness errors should identify an unhealthy component.
- **Fresh-pad error:** run `./scripts/desktop reset`, then `smoke`.
- **Input stopped:** reset clears the stop and creates a new session.
- **Image changes not reflected:** run `build`, then `reset`; ordinary `up` deliberately reuses the image.
- **Build hangs at public base-image metadata:** on the tested Mac, `docker-credential-desktop` stalled during a public pull. An anonymous, temporary client configuration worked without changing global Docker credentials. For that specific issue on macOS, the following builds using the active daemon and public registries:

```sh
(
  task_docker_host="$(docker context inspect --format '{{.Endpoints.docker.Host}}')"
  task_docker_config="$(mktemp -d)"
  trap 'rm -rf "$task_docker_config"' EXIT
  cat > "$task_docker_config/config.json" <<'JSON'
{"auths":{},"cliPluginsExtraDirs":["/Applications/Docker.app/Contents/Resources/cli-plugins"]}
JSON
  DOCKER_CONFIG="$task_docker_config" DOCKER_HOST="$task_docker_host" ./scripts/desktop build
)
./scripts/desktop up
```

## Remaining plan

- [Current direction](docs/CURRENT_PLAN.md)
- [Roadmap and dependencies](docs/ROADMAP.md)
- [Full first milestone](docs/MILESTONE_1.md)
- [Initial options comparison](docs/DECISIONS.md)

M1-02 is implemented and passes its 13 fixture tests. Next is M1-03: promote the proven desktop primitives into a shared adapter and validate Chromium bootstrap against the banking fixture. Visual recognition and the manual replay artifact follow. Full M1 is not complete. M1-01 was committed and pushed as `c426a49` at the user’s request; subsequent M1-02 changes remain local.

The final assignment also needs genuine discovery/replay evidence, a reusable capability, exceptional runs, human intervention, and `REPORT.md` using the assignment's required headings. The repository is private during preparation; public submission and any push require an explicit user request. The assignment PDF, credentials, and live customer data are not included.
