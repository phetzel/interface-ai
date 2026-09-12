# M1-01 desktop evidence

Measured on 2026-09-12 UTC on an Apple Silicon Mac using Docker Desktop 28.3.2 / Compose 2.39.1. The image ran natively as Linux ARM64 (`aarch64`) at 1280×800. This bundle demonstrates the native desktop calibration PoC only. It is not banking replay or model-discovery evidence.

## Results

| Run | Result | Elapsed | Notes |
| --- | --- | --- | --- |
| [075100 / 8fdf0b5e](runs/20260912T075100Z-8fdf0b5e/report.json) | Failed | 5.675 s | Screenshots, pointer coordinates, and raw VNC check passed; keyboard submission timed out |
| [075621 / d4b36646](runs/20260912T075621Z-d4b36646/report.json) | Passed, 8 checks | 3.154 s | First run after correcting focus and viewer networking |
| [075751 / 2f4ad2b6](runs/20260912T075751Z-2f4ad2b6/report.json) | Passed, 8 checks | 3.213 s | Repeated after reset, with a new session |
| [080017 / 2a8c3c52](runs/20260912T080017Z-2a8c3c52/report.json) | Passed, 8 checks | 3.066 s | Final run following shutdown/start, operator stop, and reset |

These are all smoke attempts that reached run initialization during this implementation. Each has its original report and JSONL check events. Successful timings cover the short smoke sequence, not container build/startup or application replay. Three passing development runs are a feasibility check, not a reliability estimate.

[Lifecycle results](lifecycle.json) record ten checks and their actual command output: shutdown makes the viewer unavailable; readiness rejects a stopped service; cached-image startup succeeds; restart and reset change the session; operator stop rejects a new smoke before any pad input; reset clears that stop; native smoke and standalone screenshot work; the host viewer responds with HTTP 200. The failed command exit codes in this file are expected negative tests. An earlier manual stop/rejected-smoke check also produced the expected result.

A browser inspection confirmed the noVNC page displays the same entered run identifier, green targets, and scrolled content. The raw RFB probe checks dimensions and a known framebuffer pixel and attempts input despite the server's view-only setting. The viewer is not interactive human takeover.

## Issues found and corrected

1. **Docker credential helper stalled on a public pull.** The build was stopped before it progressed, then succeeded with an anonymous temporary Docker client configuration. No global Docker configuration changed. The exact workaround is in the root README.
2. **Native keyboard focus.** The first pad used an override-redirect X11 window: pointer clicks arrived, but keyboard input did not. Letting Openbox manage a fullscreen window fixed focus. The selection test also uses Home/Shift+End, appropriate to the native entry widget, rather than assuming Ctrl+A selects all.
3. **Internal-network port publishing.** The first Compose layout put the published viewer port directly on an internal-only network. The web server was reachable inside the container, but the host connection was refused and Docker had no effective published port. A separate relay now forwards only to `desktop:6080`. The desktop retains its internal network and no default route; the relay publishes `127.0.0.1:6080`.

## Reproduction and provenance

From the repository root, run `./scripts/desktop up`, then `./scripts/desktop reset` and `./scripts/desktop smoke`. See the [setup instructions](../../../README.md) for all lifecycle commands and the first-build workaround. No OpenAI key or model SDK is used.

- [Environment manifest](environment.json): image ID/architecture, container user, dropped capabilities, security options, networks, published ports, and the single project-relative evidence mount.
- [Installed system packages](system-packages.txt): matches `systemPackagesSha256` in the run reports. The Debian base is digest pinned; apt packages can change in future rebuilds.
- [Source hashes](source-sha256.json): exact desktop implementation files used by the final image and lifecycle commands.
- [Before](before.png) and [after](after.png): final run, synthetic native pad only. Other captures remain in ignored local output.

The pad oracle independently records delivered native events for this calibration test. Its state file and fixed coordinates are not an accepted shortcut for banking replay. The desktop has no model credentials or host profile mount. The egress test proves no default IPv4 route and failure of two selected external TCP probes; it does not audit every network protocol. The relay has a normal bridge network for port publishing.

This step does not prove browser bootstrap/sandbox compatibility, local OCR, stable visual locators, general screenshot redaction, application/action policy, or recorded human intervention. Those remain subsequent implementation packages and gates. No commit or push was made for M1-01.
