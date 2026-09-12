# M1-02 fixture evidence

Recorded 2026-09-12 UTC. This is a fixture acceptance bundle, not computer-use replay, model discovery, or completion of full M1. M1-01 was committed/pushed as `c426a49` at the user's request before this work; M1-02 remains local.

## Measured results

- **Build/typecheck:** production Vite build and strict TypeScript checking passed on Node 22.17.1. Package versions and transitive resolutions are locked in the fixture's `package-lock.json`.
- **[Final acceptance run](acceptance.json): 13 passed, zero failures/skips/retries**, 5.374 seconds. Playwright 1.63.0 used isolated macOS ARM64 Chromium 153.0.8010.12, a 1280×800 viewport, en-US locale, and the built production assets. Six separately launched servers supplied the actual scenario configurations.
- **[Container integration](container.json): passed.** Native Linux ARM64 / Node 22.23.2; desktop-to-fixture reachability; startup and readiness; default/delayed/default resets; typo rejection without mutation; complete project shutdown including the optional fixture; no host mounts or published ports; non-root/read-only runtime; no default IPv4 route; test oracle, TypeScript source, and npm dependencies absent from the runtime image.
- **Visual review:** member search, account list, account details, and exception screenshots were inspected. Navigation no longer scrolls the header out of view when it focuses a new screen's heading.

The browser tests cover exact IDs and both savings balances against a separately authored oracle; checking/savings selection; reset and another-member navigation without stale balance; missing-member recovery; all seven malformed ID cases; loading and cancellation; blocked loading; two indistinguishable savings targets; unavailable balance; exact +40 px translation on both axes; unavailable configuration; ignored query-string controls; read-only endpoints; and blocked source/oracle paths.

No external asset requests occurred in either baseline lookup. This is a per-run request check, not a general network-security audit. Container route inspection is similarly a scoped check. The future runner must not access the DOM, fixture config, bundled data, or test oracle to answer a banking task.

## Attempts and corrections

1. [Initial test collection](initial-collection-failure.json) failed before any test ran because Node ESM requires a JSON import attribute for the oracle. The test import was corrected to use `with { type: "json" }`; no app behavior was changed to satisfy collection.
2. [First full run](first-pass.json) passed all 13 tests in 8.631 seconds.
3. Visual review found automatic page scrolling when a new heading received focus. Navigation now resets scroll and focuses without scrolling. The [final run](acceptance.json) passed all 13 tests and records the screen's scroll position in the baseline checks. It also captured the seven PNGs below.

Raw Playwright reports remain in ignored local output; these JSON summaries preserve test outcomes and their original report hashes. There were no model calls or replay attempts. A later packaging-only change included the Inter font license in the image; [final packaging verification](packaging.json) records that final image without rerunning unchanged browser behavior.

## Screens

| Screen | Evidence |
| --- | --- |
| Member search | [search.png](search.png) |
| Member overview | [member.png](member.png) |
| Demo Member A savings | [account-a.png](account-a.png) |
| Demo Member B savings | [account-b.png](account-b.png) |
| Duplicate target | [duplicate.png](duplicate.png) |
| Unavailable balance | [unreadable.png](unreadable.png) |
| Translated account detail | [translated.png](translated.png) |

Screens contain only the fictional fixture. They are full viewport captures, not a demonstration of general redaction.

## Reproduce and continue

See the [fixture README](../../../apps/bank-fixture/README.md) for installation, preview, container commands, scenario controls, and `npm test`. [Source hashes](source-sha256.json) identify the delivered implementation/configuration files; the image and package hashes identify the tested builds. Local source and oracle are distinct files and neither is generated from the other.

Next is M1-03: the shared desktop adapter and trusted Chromium bootstrap. Recognition, deterministic replay, runtime policy enforcement, and human takeover still need implementation. The noVNC desktop remains the native calibration pad; fixture browser tests used a separate local test browser.
