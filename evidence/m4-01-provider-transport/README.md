# M4-01 provider/transport validation — 2026-09-20

**Offline implementation checks passed. Genuine OpenAI acceptance is pending a local API key.** No actual OpenAI requests were made. This is not discovery-to-artifact evidence.

Based on pushed commit `4646f05` plus the M4-01 working-tree changes. [Executable source hashes](source-sha256.json) identify the exact tested code, including new untracked files; the source stayed unchanged through the live gates. [Validation index](validation.json) contains image IDs, counts and ignored local attempt paths.

| Check | Result and provenance |
| --- | --- |
| [Quick gate](quick-summary.json) | Quality, 107 Linux engine tests, host tests, four schemas and fixture typecheck passed. The ordinary host environment skips the optional SDK wire test. |
| [SDK wire test](sdk-wire.json) | All 11 host tests passed with OpenAI 3.16.2 installed. Mock HTTP separately confirmed both original-resolution image fields, caller-managed history, `store: false` and disabled tools on request two. No network/model calls. Full local log: `tmp/m4-01-host-final.log`. |
| [Desktop transport](transport-summary.json) | Five cases passed against real HTTP/X11: one native click/tool-output exchange, unrelated-control denial, unsupported typing, duplicate proposal and a late response after Stop. Provider responses were simulated. |
| [Visible operator Stop](operator-stop.json) | Agent-operated panel showed “Testing model connection” then “Stopped”; the late proposal was rejected and desktop evidence recorded zero actions. Simulated provider wait; no real-person attestation. |
| [M1](m1-summary.json) and [M2](policy-summary.json) | Native/browser input, sandbox/isolation, ten alternating baselines, seven scenarios, preflight/stale/Stop rejections and safe evidence export passed. |
| [M3](handoff-summary.json) | Both members passed same-session handoff, with wrong-screen/member rejection on member A. Automated operator provenance remains explicit. |
| [Missing-key behavior](missing-key-report.json) | The locked real-probe command failed with `missing_api_key`, zero attempted requests and no desktop probe. This is a configuration check, not a successful live provider run. |

Earlier SDK test attempts are retained in ignored `tmp/m4-01-sdk-tests*.log`: the installed SDK uses `httpx2`, so the older `httpx` import was corrected before the final tests. No screenshot, raw response transcript, API key, private transport token or human input is included here. Existing M1–M3 real-person audit results are unchanged.

Next: supply the key locally and pass `make discovery-probe` on a fresh bank search. Require two real provider responses, one guarded click and a successful stateless screenshot return. Full discovery, recording, review/promotion and second-member generated-artifact replay remain M4-02 through M4-06. [Implementation guide](../../docs/M4_01_PROVIDER_PROBE.md).
