# Banking fixture · M1-02

A small React/TypeScript app with fictional members and three views: member search → member overview → account detail. It displays a member's identity, checking/savings accounts, balance, and USD currency. It has no login, database, writes to banking data, or model integration.

## Code walkthrough

Start in [src/App.tsx](src/App.tsx): it composes the screens and handles heading focus/scroll when the view changes. Follow a search into [src/useMemberWorkspace.ts](src/useMemberWorkspace.ts), then read the component that renders the resulting view.

| File | Responsibility |
| --- | --- |
| [main.tsx](src/main.tsx) / [scenario.ts](src/scenario.ts) | Load and validate launch configuration; fail closed if it is unavailable or invalid |
| [useMemberWorkspace.ts](src/useMemberWorkspace.ts) | Exact-string member search, cancellable lookup timer, navigation, and once-per-page expiry/restoration |
| [MemberSearch.tsx](src/components/MemberSearch.tsx) | Search form, loading/cancel, validation, missing-member feedback and help text |
| [MemberIdentity.tsx](src/components/MemberIdentity.tsx) | Shared member identity banner |
| [AccountList.tsx](src/components/AccountList.tsx) / [AccountDetails.tsx](src/components/AccountDetails.tsx) | Account selection and displayed balance/details |
| [WorkspaceHeading.tsx](src/components/WorkspaceHeading.tsx) / [WorkspaceLayout.tsx](src/components/WorkspaceLayout.tsx) | Breadcrumbs, page title, header and footer; [Arrow.tsx](src/components/Arrow.tsx) shares the icon |
| [SessionExpiredDialog.tsx](src/components/SessionExpiredDialog.tsx) | Synthetic training-code form and its local error state; calls the workspace's restore action |
| [PolicyProbe.tsx](src/components/PolicyProbe.tsx) | Launch-controlled adversarial content and local synthetic transfer state |
| [data.ts](src/data.ts) / [styles.css](src/styles.css) | Fictional display records, integer-money formatting, and shared visual layout |

Workspace state lives in one hook and passes down through typed props and callbacks. Dialog/probe state stays with those components. Searching another member clears the lookup but preserves restoration and probe state until page reload. No context, router or state library is needed for these three views.

The component extraction preserves the rendered elements, text, styles and geometry because visual replay depends on those observations. The independent oracle remains in tests; it is never imported into application code. See the [refactor validation record](../../evidence/frontend-refactor-2026-09-17/README.md).

## Preview on the host

Use Node 22.12+ within the Node 22 release line and npm. From this directory:

```sh
npm ci
npm run build
npm run preview
```

Open http://127.0.0.1:4173. To change the preview scenario, stop the server and run `FIXTURE_SCENARIO=delayed npm run preview`. `npm run dev` is available for editing and uses the same launch-time configuration. Inter font files are bundled locally; the app does not fetch external assets. Their [SIL Open Font License](INTER-LICENSE.txt) is included in the repository and runtime image.

From the repository root, `./scripts/fixture preview delayed` is an equivalent preview command after the app is built. Ctrl+C stops the foreground preview. A reload starts a fresh empty search; nothing is saved in local storage, cookies, or a database.

## Run inside the isolated desktop network

From the repository root:

```sh
./scripts/fixture up
./scripts/fixture ready
./scripts/fixture reset delayed
./scripts/fixture reset default
./scripts/fixture down
```

`up` builds if the local image is missing and starts a fresh fixture. After source changes, run `./scripts/fixture build` and then `./scripts/fixture reset`. `logs` shows recent server output. The root README contains the temporary Docker client workaround if the public-image credential helper stalls.

The origin serves the fixture on its private internal network; M2 exposes `http://fixture:4173` to the desktop through the policy gateway. It is non-root, uses a read-only root filesystem, has no mounts or published ports, and has no default IPv4 route. Its final image contains only the Node runtime, static assets, and the small read-only server; tests/oracle, TypeScript source, and npm dependencies are absent.

The Compose `bank` profile keeps the fixture optional for the native desktop calibration test. `./scripts/desktop down` shuts down all project services, including this optional fixture. `./scripts/fixture down` stops only the fixture. Reset recreates the service and selects the scenario; reload an open page to receive that configuration and clear UI state.

M1-03 launches sandboxed Chromium at this entry point with `./scripts/desktop up bank`. The operator at `http://127.0.0.1:6081/` shows that isolated desktop; `./scripts/desktop browser-smoke --member-id 00123` exercises fixed-coordinate input through the shared Python adapter. Use `./scripts/desktop reset bank delayed` to start a fresh bank desktop with a scenario. M1-04 exercises local anchors/OCR via `./scripts/desktop vision-probe --member-id 00123` and checks eight cases with `./scripts/vision-check`. M1-05 executes the manual capability with `./scripts/desktop replay --member-id 00123` and checks nine integration cases with `./scripts/replay-check`. M1-06's full repeated gate passes and runs with `./scripts/m1-check`; the replay-only subset is `./scripts/replay-check --acceptance`. The host preview is a separate fixture-development surface.

## Records and scenarios

| Member ID | Member | Savings | Checking |
| --- | --- | --- | --- |
| `00123` | Demo Member A | `$1,234.56` | `$8,420.19` |
| `00456` | Demo Member B | `$98.07` | `$2,316.40` |
| `00999` | Not found | No balance displayed | No accounts displayed |

IDs are strings of exactly five ASCII digits. Input is not trimmed, padded, or converted to a number. Balances use integer cents in the fixture. The app displays an explicit not-found message for an unknown valid ID.

| Scenario | Fixture behavior | Purpose for later replay tests |
| --- | --- | --- |
| `default` | Search resolves after 250 ms | Baseline workflow |
| `delayed` | Search resolves after 1,800 ms | Bounded visual waiting |
| `blocked` | Search stays loading until cancelled/reloaded | Missing-checkpoint timeout |
| `duplicate` | Two savings rows with identical visible labels, account endings, and action names | Reject an ambiguous target |
| `unreadable` | Account balance is replaced by an em dash and an unavailable message | Reject an unreadable amount; never substitute zero |
| `translated` | Main content moves +40 px horizontally and vertically at desktop widths | Test contextual visual targets at the same scale |
| `policy` | Synthetic transfer control, adversarial instruction and private-note sentinel | Verify policy refusal and evidence filtering |
| `expired` | First successful search opens a training-code dialog; `demo` restores the same workspace | Exercise same-session takeover and verified continuation |

Only the harness/launcher selects a scenario, via `FIXTURE_SCENARIO` before startup. Unknown names exit with an error. There are no query-string selectors, UI debug controls, or mutation endpoints. `/fixture-config.json` supplies only rendering behavior to the app; it contains no expected result or member records. The frontend must read this configuration to render a variant; this is not a security boundary against arbitrary browser evaluation. The future replay contract forbids reading it or the bundled application state as a task shortcut.

## Acceptance tests and oracle

```sh
npx playwright install chromium
npm test
```

This builds the production assets, launches eight local servers on ports 4180–4187, and runs 15 Chromium tests at 1280×800, en-US. The ports must be free. To keep browser downloads in the repository's ignored output directory:

```sh
export PLAYWRIGHT_BROWSERS_PATH="$PWD/../../tmp/playwright"
npx playwright install chromium
npm test
```

The tests cover both member identities and savings balances; choosing checking then navigating back; searching another member without stale data; reload/reset; malformed IDs; missing-member recovery; delayed loading; cancellation; permanently blocked loading; duplicated targets; unavailable amounts; exact 40-pixel translation; configuration failure; and refusal to serve source/oracle or accept scenario mutations. Expected values come from [tests/oracle.json](tests/oracle.json), authored independently of [src/data.ts](src/data.ts). Do not generate one from the other or import the oracle into the app.

The harness uses DOM assertions and may inspect fixture configuration. These are tests of the fixture, not replay: the later interpreter must use screenshots and approved desktop input, never the DOM, source, config endpoint, oracle, or hidden application state. The JSON oracle describes expected future typed results; this app does not implement a replay result API.

[Reviewed evidence](../../evidence/poc-m1/fixture/README.md) includes actual test results, lifecycle checks, and synthetic screenshots. Raw Playwright output remains under ignored `test-results/`. No statistical reliability claim or full-M1 completion is implied.

Tooling references: [Vite setup requirements](https://vite.dev/guide/) and [Playwright web-server configuration](https://playwright.dev/docs/test-webserver).
## M2 policy scenario and network boundary

`./scripts/desktop reset bank policy` starts the normal search view with an additional synthetic transfer control, an untrusted instruction to ignore restrictions, and a private-note sentinel. The button only changes local React state; no real transaction or backend mutation exists. The host fixture test proves the button works, while M2's desktop acceptance proves the ordinary input policy refuses to click it. This scenario is launch-controlled like the other fixtures.

The fixture origin now lives on a separate internal Compose network. The desktop reaches it through the fixed-upstream policy gateway at `http://fixture:4173/`; it cannot directly address the origin. The host preview and Playwright servers remain fixture-development tools, separate from runtime policy enforcement.

M3 adds the harness-only `expired` scenario: the first successful member search shows a synthetic expiry dialog. The training code `demo` restores the original member overview in the same page; no real credentials, persistence or authentication endpoint are involved. Subsequent searches in that page do not expire again. Reload/reset starts a fresh scenario.
