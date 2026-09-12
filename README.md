# interface-ai

A computer-use automation system in development: model-driven discovery, reusable capabilities, deterministic replay, policy enforcement, and human takeover of the same live session.

**Implemented: M1-01 through M1-04.** An isolated Linux desktop runs either the native calibration pad or the React/TypeScript banking fixture in sandboxed Chromium. Both use the same Python screenshot/input adapter, with session, focus, deadline, exclusive-controller, and stop checks. Local visual anchors and Tesseract OCR now locate controls and extract verified synthetic balances. Capability artifacts/replay, model integration, and human takeover remain later work. No OpenAI key is needed for these steps.

## Run the banking desktop

With Docker Desktop running, from the repository root:

```sh
./scripts/desktop build
./scripts/desktop up bank
./scripts/desktop vision-probe --member-id 00123
```

Open the [read-only desktop viewer](http://127.0.0.1:6080/vnc.html?autoconnect=true&resize=scale&view_only=true). Chromium opens the internal fixture at `http://fixture:4173/` with a fresh disposable profile. The visual probe finds the member field and Savings control from pixels, enters the ID through the desktop adapter, and reads identity, account type, currency, and balance using local OCR. It writes an explicit synthetic `result.json` under the printed evidence directory. This is a manually authored primitive exercise; the capability artifact/interpreter is still M1-05. [Engine API and limits](engine/README.md) · [M1-04 evidence](evidence/poc-m1/vision/README.md).

Repeat with `./scripts/desktop reset bank`, then `./scripts/desktop vision-probe --member-id 00456`. `./scripts/desktop reset bank translated` selects the tested +40 px layout variation. Reload the viewer after resets. Run `./scripts/vision-check` for the eight-case reset-based primitive suite; it finishes on the blocked scenario, so reset bank afterwards.

## Preview the banking fixture

```sh
cd apps/bank-fixture
npm ci
npm run build
npm run preview
```

Open the [banking preview](http://127.0.0.1:4173). Search for `00123` or `00456`, then open Savings; `00999` demonstrates member not found. [Fixture setup, scenario controls, and tests](apps/bank-fixture/README.md) · [M1-02 evidence](evidence/poc-m1/fixture/README.md).

The host preview is a separate development surface. `./scripts/desktop up bank` starts the fixture inside the desktop network and launches Chromium there. `./scripts/fixture up` starts only the internal fixture service.

## Run the native desktop step

Prerequisite: Docker Desktop running with Docker Compose v2. Tested on an Apple Silicon Mac with native Linux ARM64 containers, Docker 28.3.2 and Compose 2.39.1. No host Python or Node installation is required. The first build downloads public Debian and Python packages and needs internet access; subsequent starts reuse the local image. The desktop is limited to 2 CPUs/2 GiB and the viewer relay to 0.5 CPU/128 MiB.

From the repository root:

```sh
./scripts/desktop reset native
./scripts/desktop smoke
```

Open the [read-only desktop viewer](http://127.0.0.1:6080/vnc.html?autoconnect=true&resize=scale&view_only=true). The three targets turn green, synthetic text appears in the input field, and the text panel scrolls. The viewer scales the image; the automation always uses the desktop's 1280×800 coordinates.

| Command | Behavior |
| --- | --- |
| `./scripts/desktop up [native\|bank] [scenario]` | Build if absent, start the selected surface, wait for readiness, print viewer URL; omitted mode preserves the running mode, or defaults to native |
| `./scripts/desktop ready` | Check processes, display, expected window focus, and viewer; print session ID, mode, and stop state |
| `./scripts/desktop smoke` | Run eight bounded checks on a fresh calibration pad; exit nonzero on failure |
| `./scripts/desktop browser-smoke --member-id 00123` | Run eight input/pixel checks in a fresh default banking desktop; also accepts `00456` |
| `./scripts/desktop test` | Run 27 desktop/vision unit tests, including actual local OCR |
| `./scripts/desktop vision-probe --member-id 00123` | Exercise visual targeting, identity checks, and OCR; print the result/evidence location |
| `./scripts/vision-check` | Run eight reset-based baseline, translated, delayed, and rejection cases against the host-only oracle |
| `./scripts/desktop action --session ID --json ACTION_JSON` | Dispatch one validated primitive through the shared adapter; see the engine README |
| `./scripts/desktop screenshot` | Save the known synthetic screen to `tmp/desktop-artifacts/desktop.png` |
| `./scripts/desktop stop-input` | Block subsequent adapter input, including the next character during typing; reset required to run again |
| `./scripts/desktop reset [native\|bank] [scenario]` | Recreate desktop/viewer with a new session; bank also resets the fixture; preserve exported evidence |
| `./scripts/desktop down` | Stop and remove all project services, including the optional fixture; keep images and evidence |
| `./scripts/desktop build` | Explicitly rebuild after changing desktop source/dependencies |
| `./scripts/desktop logs` | Show recent desktop and viewer logs |
| `./scripts/desktop viewer` | Print the local viewer URL |

Run `reset` before each repeated smoke test. `up bank` also creates a fresh desktop; `up native` can reuse it. After editing image contents, run `build`, then `reset`. If port 6080 is occupied, use `DESKTOP_PORT=6081 ./scripts/desktop up bank` and use the same value for later commands. After a reset, reload/reconnect the viewer.

Smoke output is written under `tmp/desktop-artifacts/<run-id>/`: `report.json`, `events.jsonl`, and before/after PNGs. Reports include dependency versions, architecture, display dimensions, session ID, elapsed time, and checks. Failed executions after run initialization also retain a report. Preconditions rejected before initialization print a diagnostic and do not create a run bundle. Raw local output is ignored by Git. Reviewed results live in [desktop evidence](evidence/poc-m1/desktop/README.md).

## What this proves

- Native PyAutoGUI clicks arrive at the exact screenshot coordinates and visibly change all three targets.
- Typing, selection/replacement, Enter, and scrolling reach a native Tk application.
- The visual probe locates targets and extracts both members’ identities, Savings account type, USD currency, and exact balances against an independent oracle. Both default and +40 px layouts pass without changing anchors/settings.
- A delayed search succeeds; duplicate Savings targets, unreadable balances, and blocked loading stop without returning guessed data or dispatching a later action.
- VNC serves pixels from the same X11 display and rejects attempted input at the server, beyond the viewer's client setting.
- Cooperative stop prevents dispatch; reset and shutdown/start produce fresh sessions.
- Live guard checks reject invalid/stale requests and a second controller, interrupt typing, and retain observation access after stop.
- The desktop has no default IPv4 route, and the tested external TCP destinations are unreachable.

The smoke scripts use fixed calibration coordinates. The native state oracle and browser pixel-change checks verify input plumbing, not reusable visual locators or replay. The separate M1-04 visual probe now verifies local recognition and typed results. There are no model calls. Capability replay, cross-OS portability, and human takeover remain unverified.

## Environment and boundaries

`infra/desktop/` packages Xvfb, Openbox, PyAutoGUI, a native Tk test pad, Chromium, x11vnc, and noVNC. The engine captures X11 pixels directly into memory; it does not create temporary screenshot files. Chromium uses its user-namespace sandbox and a [documented seccomp profile](infra/desktop/SECCOMP.md); startup verifies renderer isolation. Tesseract and its English package are version pinned, and the English model hash is checked before OCR. Python dependencies are version/hash locked; the Debian base image is digest pinned. Debian packages are resolved at build time and their exact versions recorded in `/opt/desktop/system-packages.txt`, so a later clean build can receive updated OS packages.

The non-root desktop joins an internal Compose network. Only `tmp/desktop-artifacts` is mounted; no host home, browser profile, credentials, or Docker socket is exposed. A separate fixed-destination TCP relay publishes the viewer at `127.0.0.1:6080`. It joins an ordinary bridge network for Docker Desktop port publishing and the internal network to reach the desktop. The relay forwards only to `desktop:6080`; the desktop itself has no default route. This arrangement was necessary because a published port on an internal-only network was not reachable on the tested host.

The viewer is unauthenticated and read-only, intended for synthetic local data. The stop command is cooperative: an already-dispatched short primitive may finish; it is not an ownership/handoff protocol. `down` terminates the environment. The screenshot guard checks known fixture pixels; it is not general redaction or a reliable sensitive-screen detector. Network probes and container restrictions are a bounded PoC, not comprehensive hostile-code containment. General policy and safe export remain later gates.

## Troubleshooting

- **Docker unavailable:** start Docker Desktop and retry. Logs/readiness errors should identify an unhealthy component.
- **Wrong mode or stale screen:** run `./scripts/desktop reset native` for `smoke`, or `reset bank` for `browser-smoke`.
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

Next is M1-05: a validated manual capability and interpreter, including the known member-not-found branch. The full repeated acceptance suite follows in M1-06. Full M1 is not complete. M1-01, M1-02, and M1-03 were committed and pushed as `c426a49`, `37bbd60`, and `79bf84e` at the user's requests. The completed M1-04 implementation and evidence are included in this revision.

The final assignment also needs genuine discovery/replay evidence, a reusable capability, exceptional runs, human intervention, and `REPORT.md` using the assignment's required headings. The repository is private during preparation; public submission and any push require an explicit user request. The assignment PDF, credentials, and live customer data are not included.
