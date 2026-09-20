# M4-01 live OpenAI acceptance — 2026-09-20

**Passed.** A genuine `gpt-5.6-sol` exchange selected one click in the synthetic member-ID field, the guarded native adapter executed it, and OpenAI accepted the resulting screenshot with caller-managed history and `store: false`.

| Evidence | Result |
| --- | --- |
| [Provider report](provider-report.json) | Three requests and three responses: initial screenshot request, click proposal, then acknowledgment. Both acceptance flags passed; returned token usage is recorded. |
| [Desktop summary](desktop-summary.json) and [events](desktop-events.jsonl) | Exactly one completed native click, two admitted captures, matching run/session IDs; 7.866 seconds in the desktop reservation. |
| [Transport checks](transport-summary.json) | Six simulated-provider cases passed against real HTTP/X11, including initial screenshot continuation, unsupported input, unrelated target, duplicate proposal and late response after Stop. Actual model calls in this suite: zero. |
| [Host tests](host-tests.log) and [quality](quality.log) | 15 tests passed with the pinned SDK, plus formatting/lint. Tests cover bounded screenshot continuation, Stop, modifier rejection and stateless serialization. |
| [Validation](validation.json) and [source hashes](source-sha256.json) | Live and transport runs used identical executable source. Only three host protocol/harness/test files differ from the earlier offline record; desktop and fixture image identities are unchanged. |

The operator visibly displayed **Model action test complete**. No bank lookup was started and no member ID was entered. This proves M4-01 provider/transport integration; goal-driven discovery, capability recording, promotion and generated-artifact replay remain M4-02 through M4-06.

## Corrections and preserved failures

[Four earlier failed attempts](failed-attempts.json) remain recorded. One connection failure had no returned response and unknown provider usage. A subsequent authenticated model-access read succeeded without a network/TLS configuration change. Three later attempts received a response but rejected its proposed action before native input. The diagnostic retained only shape/type flags, never raw model output.

The initial implementation expected the first computer call to be a click. [OpenAI's guide](https://developers.openai.com/api/docs/guides/tools-computer-use) permits an initial screenshot-only call. The corrected host returns its admitted initial frame after rechecking the lease; no input has occurred under the exclusive reservation. It permits this once and rejects repetition. The successful run exercised this path. The pinned SDK also permits an empty `keys` list on a plain click; the host normalizes that optional field while rejecting nonempty modifiers and unknown fields. Empty-modifier support alone did not resolve the earlier rejection.

Limits remain one click, at most three provider requests, 30 seconds per request and a 100-second desktop reservation. No SDK retry, model fallback, broader native policy or additional desktop route was added. Across all five live attempts there were seven Responses requests attempted and six completed responses; the first attempt's usage remains unknown. The separate model-access diagnostic was a read, not a generation request.

The [earlier offline M1–M3 regression record](../m4-01-provider-transport/README.md) is preserved as dated evidence; its pending-key status describes that earlier run. This follow-up reran the affected host/transport checks. Screenshots, prompts, raw responses, keys and transport credentials are excluded from this record.
