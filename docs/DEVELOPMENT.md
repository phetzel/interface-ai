# Development and verification

The [README](../README.md) and [demo](DEMO.md) are the assessor entry points. Historical milestone documents explain earlier decisions; their commands describe those revisions. The supported runtime is Docker/Linux ARM64, not a standalone Python wheel.

## Setup

The offline demo needs Docker Desktop/Compose, Make and Python 3.9+. Development checks also need Node 22 (`.nvmrc` pins the tested version) and `uv`. From the repository root:

```sh
nvm use
make dev-setup
```

This installs fixture dependencies and Playwright Chromium, builds both images, runs the quick checks, and resets/validates a fresh bank desktop. It stops on failure. Playwright is a UI test dependency; the automation engine uses native input and pixels. Select `CAPABILITY=manual-savings` to validate the historical baseline instead.

For React work, `make fixture-dev` starts Vite. `make fixture-preview` builds and serves the standalone fixture on port 4173. This preview is separate from the isolated desktop and is unnecessary for the assessor demo.

## One check runner

```sh
make check SUITE=full
```

| Suite | Coverage |
| --- | --- |
| `quick` (default) | Pinned Ruff/Prettier checks, host tests, Linux engine tests, six schemas and TypeScript |
| `fixture` | Browser UI tests of the sample bank, including nested frames |
| `desktop` | Native/browser input, isolation, session/Stop guards, 17 historical manual replays and rejection cases |
| `policy` | Action and route restrictions, direct-origin denial and safe export |
| `replay` | Generated artifact: both members, translated/nested-iframe layouts, delays and negative outcomes |
| `handoff` | Both generated-artifact same-session recoveries through a simulated operator |
| `discovery` | Offline fake-provider transport, late responses, focus loss and Stop; no real model |
| `lifecycle` | CLI/panel coordination and competing starts |
| `operator` | Responsive panel, fit/actual-size pointer mapping, recovery and pending-input Stop |
| `offline` | No provider SDK/key/egress in replay; generated replay and sanitized export |
| `generated` | `replay`, `handoff`, `discovery`, `offline` |
| `full` | Every suite, plus the historical manual-artifact handoff |

Individual suite options remain available through `scripts/check`, for example:

```sh
./scripts/check --suite handoff --capability manual-savings
./scripts/check --suite desktop --rejections-only
```

The full runner sequences work against the single desktop and links child evidence directories instead of copying entire nested suites. Do not operate the panel or run another suite concurrently. Keep executable source frozen during acceptance. Each attempt retains logs under `tmp/`; failures are preserved. Stale images fail explicitly—checks never silently rebuild, relax assertions or mark human results.

`make quality` checks formatting/basic correctness; `make format` formats active source only. Historical evidence is excluded. CI runs the quick suite on Linux ARM64. `make help-dev` lists lower-level controls; normal demonstrations need only `assess`, `handoff` and `down`.

## Online discovery

`uv` installs the pinned host SDK using `scripts/discover.lock`. The desktop image contains no provider SDK/key. Create a private `.env` in the repository root (it is ignored by Git):

```text
OPENAI_API_KEY=your-key
```

Use your editor rather than putting the key in shell history, then run `chmod 600 .env`. The operator requires this private file. CLI discovery also supports an existing `OPENAI_API_KEY` environment variable; the operator launcher deliberately removes inherited `OPENAI_` variables. Do not put the key in Compose, the fixture, an artifact or evidence.

```sh
make discover GOAL="Read the savings balance for member 00456"
```

`TARGET=synthetic-bank` is implicit. `http://fixture:4173/` is the other accepted spelling. The member ID is derived from the goal; an explicit `MEMBER_ID` must match. Accepted verbs are find/read/get/look up, with the limited variants described by `python3 scripts/discover --help`. Other intents fail before reset/provider use. To validate only:

```sh
python3 scripts/discover --check-request --goal "Find the savings balance for member 00123"
```

Review and promote using the commands in the README. A provider run is paid and sends admitted synthetic observations to OpenAI. `store: false` is not a promise of zero provider retention. The old standalone one-click probe has been retired; its bounded transport diagnostic remains an internal automated test.

## Desktop and build identity

Port 6081 is the sole desktop/operator page. Python 3 starts a loopback-only launcher on 6082 automatically with `up`/`reset`; `make down` stops it. The launcher accepts fixed app resets and bounded goal discovery from the authenticated 6081 UI. It does not expose a shell, arbitrary paths, promotion, or provider credentials. `make reset` creates a new session; `make replay` uses the current screen, while `make demo` resets first. Both select the generated capability by default; `CAPABILITY=manual-savings` explicitly selects the historical artifact. `make reset MODE=native` starts the calibration pad. `make stop` blocks further input until reset; `make down` stops services while retaining evidence.

After runtime changes, run `make build` before reset/checks. `make build-check` compares source fingerprints, immutable image IDs and shipped runtime bytes. Live suites also verify running containers. Schemas are published deliberately, never rewritten by builds; see the [replay guide](../engine/src/interface_ai/replay/README.md).

The desktop has no default route or provider key. The fixed-upstream gateway permits specific fixture routes, including the local nested-frame shell; unknown routes remain denied. Only the operator relay publishes loopback 6081. No VNC/noVNC server remains. Historical viewer evidence describes its original revision.

Build manifests establish tested source/image identity within a trusted host. They are not signatures or bit-for-bit reproducible OS package builds. Preserve image IDs with acceptance results and validate rebuilds.

## Troubleshooting

- Start Docker Desktop if `make ready` cannot reach it; inspect `make logs`.
- For stale builds: `make build`, then reset.
- For wrong screens, stopped input or expired human ownership: reset and refresh the operator.
- Free port 6081 if another local service owns it. Port 6080 is unused.
- Native calibration has historically had intermittent startup timeouts. Preserve a failure record and diagnose it; do not treat a later pass as proof the issue disappeared.

Docker's macOS credential helper has occasionally stalled on public image metadata. This temporary anonymous configuration leaves saved credentials untouched:

```sh
(
  task_docker_host="$(docker context inspect --format '{{.Endpoints.docker.Host}}')"
  task_docker_config="$(mktemp -d)"
  trap 'rm -rf "$task_docker_config"' EXIT
  cat > "$task_docker_config/config.json" <<'JSON'
{"auths":{},"cliPluginsExtraDirs":["/Applications/Docker.app/Contents/Resources/cli-plugins"]}
JSON
  DOCKER_CONFIG="$task_docker_config" DOCKER_HOST="$task_docker_host" make build
)
```

Use it only for these public build images; never bypass build verification.
