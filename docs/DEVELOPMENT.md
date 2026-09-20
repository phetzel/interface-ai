# Development and verification

The [root README](../README.md) is the current setup/status entry point. The milestone documents preserve decisions and historical evidence. Docker/Linux ARM64 is the supported runtime; package metadata does not imply a tested standalone wheel.

## Quick and live checks

For the short generated-artifact demo, `make assess` only needs Docker/Compose and Make; see the [assessor walkthrough](DEMO.md). For the full internal manual audit, `make audit-setup` installs the host fixture dependencies and Playwright Chromium, builds both images, runs `make quick-check`, and then resets/validates a fresh bank desktop. It stops at the first failed command. The demo and audit startup commands replace the current desktop session. Use `make fixture-preview` in a second terminal for the direct fixture UI checks.

`make quick-check` requires Docker, host Python 3.9+, Node 22 and `uv` (tested with 0.9.18). Run `make fixture-install` and `make build` first. It runs pinned Ruff 0.12.12 and Prettier 3.9.6, host harness tests, Linux engine tests in a disposable network-disabled image, six published-schema comparisons and fixture typechecking. It starts no live desktop and rewrites no artifacts. `make format` covers active source only; no historical evidence is reformatted.

Ruff uses a small correctness/unused-name rule set rather than an expansive style backlog. Prettier is an exact development dependency, as recommended by its [installation guide](https://prettier.io/docs/install); configuration follows [Ruff's configuration reference](https://docs.astral.sh/ruff/configuration/). The Python runtime lock remains separate from development tools. CI pins official actions and uses the [documented ARM64 runner](https://docs.github.com/en/actions/reference/runners/github-hosted-runners).

Live gates remain explicit: `make policy-check` includes the full M1 suite; `make handoff-check` simulates both members through the operator API. Reset to `make handoff-demo` before each panel browser script. No two live suites should manipulate the shared desktop concurrently. Keep executable source frozen during acceptance; the harness records/rechecks it. `make fixture-test` is an independent browser UI gate against the host preview.

## Operator-only desktop

The operator at `http://127.0.0.1:6081/` is the only desktop page. `make operator` prints its URL. The relay forwards only to `desktop:6081`; it keeps the desktop on its internal network. VNC, noVNC, websockify and the old `make viewer`/`DESKTOP_PORT` configuration are removed. Reset prunes the old viewer container automatically; existing evidence is retained. An unused legacy `interface-ai_viewer` network from an earlier checkout can be removed with `docker network rm interface-ai_viewer` after the viewer container is gone.

The native calibration smoke now compares the operator PNG to X11, attempts input without human ownership and asserts ports 5900/6080 are closed. The M1 runtime probe also checks the removed programs/assets are absent, and Compose acceptance permits only loopback 6081 on the operator relay. Historic VNC evidence describes its original revision and remains unchanged.

## Build identity

`infra/desktop/build_manifest.py` enumerates desktop image inputs and records their hashes during Docker build. The image includes `/opt/build-manifest.json` with source fingerprints and shipped runtime hashes. Fixture build inputs are declared in `apps/bank-fixture/package.json`; its build-time generator binds those inputs to compiled assets and server files. Its manifest is outside `dist` and is not a permitted HTTP route. Neither manifest exposes fixture source or test-oracle values to the execution agent.

`scripts/lib/builds.py` compares current source, including untracked files in the declared source trees, with manifests read from immutable image IDs. It verifies shipped bytes in disposable network-disabled containers and checks that Compose actually launched those image IDs. Acceptance retains the manifest in `build-preflight.json`. A stale image fails with a rebuild instruction before desktop input.

These fingerprints establish the relationship between this trusted local build and tested source. They are not signatures, remote build attestations or proof against a malicious host. Base images/Python dependencies are pinned; apt package selection can change on a fresh build. Preserve image IDs/package manifests with acceptance results and validate rebuilds.

Schemas are copied from the repository, not silently regenerated during Docker builds. `make quick-check` compares those exports with runtime Pydantic output. Review an intentional schema change, generate it explicitly using the [replay guide](../engine/src/interface_ai/replay/README.md), rebuild, and rerun checks.

## Public-image credential-helper workaround

On the tested Mac, Docker's credential helper has occasionally stalled while resolving public image metadata. This uses a temporary anonymous client configuration without modifying saved credentials:

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

Use this only for the public images in the current build. A missing runtime image or mismatched fingerprint requires a successful build, not bypassing verification.
