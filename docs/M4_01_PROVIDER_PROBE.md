# M4-01: provider and guarded transport proof

Implemented 2026-09-20. This tests **one model-selected click**, then a request carrying the resulting screenshot. It also permits one initial screenshot-only request from the model. It does not discover a savings workflow or record a capability. [Genuine OpenAI acceptance passed](../evidence/m4-01-live-provider/README.md) on 2026-09-20; offline results retain separate provenance.

## Run the real proof

Use the existing Docker/Make setup plus [uv](https://docs.astral.sh/uv/getting-started/installation/) on the host. OpenAI 3.16.2 and its transitive dependencies are pinned in `scripts/discovery-probe.lock`. The desktop image contains no provider SDK or key.

1. Copy `.env.example` to ignored `.env` and set `OPENAI_API_KEY` locally. Never paste it into chat or commit it. A host environment variable also works. The loader reads data; it never sources shell commands.
2. Run:

   ```sh
   make start
   make discovery-probe
   ```

   Leave the operator's **Start lookup** alone: the probe needs the fresh search screen. On unchanged images, `make reset` replaces `make start` before another attempt. A separate key file is supported with `uv run --locked --script scripts/discovery-probe --key-file /absolute/path/to/file`.
3. Watch the [operator](http://127.0.0.1:6081/): **Testing model connection**, with Stop available. Success means one native click in the member-ID field and a host `PASSED` result. No ID is typed and no balance is looked up.
4. Inspect `tmp/discovery-probes/<attempt>/report.json`: require `status: passed`, both `guardedClickPassed` and `statelessRoundTripPassed`, two requests/responses, or three when `initialScreenshotRequested` is true, and real response/model identifiers. Matching desktop evidence is `tmp/desktop-artifacts/*-probe-<run-id-prefix>/summary.json`, with one completed action. Reset before a lookup or another probe.

The fixed model is `gpt-5.6-sol`; there is no fallback or automatic retry. Missing credentials, unavailable access/tool, refusal, rate limit, timeout, invalid output or invalid screen end the attempt with a safe code. A timeout may incur usage; the report marks it unknown. The command may make up to three billed requests and does not enforce a dollar cap.

## Code and boundaries

```text
Host: scripts/discovery-probe → scripts/lib/discovery.py → OpenAI Responses
                                 ↕ authenticated localhost:6081/probe/*
Desktop: discovery/http.py → discovery/probe.py → Desktop → native X11 input
                                                   ↑
                                 session, epoch, lock, focus, Stop, policy
```

The host verifies image/source identity, privately obtains a per-session token through a fixed Docker command, then requests an admitted screenshot. The token is absent from panel HTML, URLs, model context and evidence. The subprocess receives no `OPENAI_*` environment variables. API traffic goes to the fixed OpenAI endpoint. HTTP clients ignore environment proxies; the local transport rejects redirects.

Probe routes require exact localhost Host, one separate token, bounded strict JSON, and no browser Origin/fetch-site headers. Panel and discovery credentials are not interchangeable. JSON cannot choose roles, policies, capture sources, destinations or paths. Panel Host/Origin/token/CSP checks remain intact.

One worker holds the actual input lock across all provider requests. It checks session UUID, ownership epoch, focus, application, display and Stop while waiting, before capture and at dispatch. Proposals retain the lease issued before the API request. A proposal is consumed before input; duplicates and uncertain input cannot be retried. Multiple actions in one batch are rejected together. Limits: one click, at most three API requests, 30 seconds/request, 1,200 output tokens/request, 100 seconds total desktop reservation, one queued command, eight-second transport response deadline.

If the first model call asks only for a screenshot, the host rechecks its lease and returns the same admitted initial frame as a tool result. No input has occurred and the desktop reservation remains exclusive. A second screenshot-only request is rejected; this is not an observation loop. Plain clicks may omit `keys` or provide `keys: []`; nonempty modifiers and unknown action fields are rejected. The desktop transport still receives its exact four-field provider click contract and translates it to the guarded native click.

The panel offers Stop during this probe but cannot start a lookup or grant takeover. Shared lifecycle and discovery handoff are M4-02 work. An already-sent API request cannot be recalled; its late answer cannot regain input. Ordinary replay retains its existing policy and zero-model path.

## Decisions and tradeoffs

| Issue | Alternatives | Decision |
| --- | --- | --- |
| Replay's field target is only an 80-pixel aiming region | Give the model coordinates; broaden replay admission; or use a separate policy | A dedicated policy recognizes search/member labels and admits an interior strip of that field. The model sees only screenshot/task; replay admission is unchanged. |
| Policies must share input guards | Duplicate the adapter; mutate it after acquisition; or inject a trusted factory | Python-only `bank_policy_factory`, with `BankPolicy` still default and `SearchPolicy` for this probe. No HTTP/action field exposes the seam. |
| SDK transport changed from older examples | Pin an older release or follow the installed interface | OpenAI 3.16.2 uses `httpx2`; test its actual serialization with mock HTTP. |
| Stateless continuation | Store the provider conversation or retain protocol items in memory | `store: false`, encrypted reasoning requested, previous output retained in memory, matching tool-output call ID, final request with further tools disabled. Live server acceptance passed with the pinned SDK. |
| Initial screenshot-only computer call | Reject it, force a click through prompting, or handle one observation request | Handle one documented screenshot-only call with the admitted initial frame, retain lease checks and cap the exchange at three requests and one click. |

The visual policy supports the fixed synthetic fixture only. Reviewed static anchors authorize the field; the model receives no manual artifact, anchor coordinates, fixture source, hidden state or oracle. The label-relative interior strip excludes the adjacent Search button. Missing/ambiguous screens fail closed. This does not authorize arbitrary pages that imitate the pixels.

## Evidence and validation

[Dated validation record](../evidence/m4-01-provider-transport/README.md): 107 engine tests, 11 host tests with the SDK, five transport cases and the existing M1–M3 gates passed. It preserves exact source hashes and its then-pending live status. The [live follow-up](../evidence/m4-01-live-provider/README.md) records the genuine pass, 15 host tests and six transport checks after the protocol correction.

Host evidence contains request counts, response/model IDs, returned token totals, safe codes and source/image fingerprints. Desktop evidence contains closed native-action metadata and a summary. Screenshots, raw responses, encrypted reasoning, prompts and keys stay out of evidence. The desktop reports `modelCalls: null` because only the host knows provider usage. Simulations explicitly report zero actual calls. `store: false` does not guarantee zero provider retention; see [OpenAI data controls](https://developers.openai.com/api/docs/guides/your-data).

```sh
make quick-check        # Engine/host negatives, schemas, quality and fixture types
make discovery-check    # Fake provider; real HTTP, policy and X11; resets between cases
make policy-check       # Existing policy gate plus full M1 regression
make handoff-check      # Existing same-session takeover regression
```

Run the optional SDK wire test with `uv run --with openai==3.16.2 --python 3.11 python -m unittest discover -s scripts/tests -v`. It uses mock HTTP and no key. Normal host tests skip only this test if the optional SDK is absent. Run desktop gates sequentially with executable source unchanged.

Integration checks cover a native click/tool-output exchange, unrelated control, unsupported typing, duplicate proposals and a response after Stop. Engine tests also cover revoked ownership, stale sessions, lost focus, reservation timeout, input-lock exclusion, token/browser separation and failed evidence writes. These prove transport mechanics, not API access or genuine discovery.

Primary sources checked 2026-09-20: [computer use](https://developers.openai.com/api/docs/guides/tools-computer-use), [caller-managed conversation state](https://developers.openai.com/api/docs/guides/conversation-state), and the installed SDK client/types. The guide specifies `detail: original` on screenshots; the wire test checks that it survives serialization even where the generated SDK screenshot type omits it.
