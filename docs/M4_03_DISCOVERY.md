# M4-03 — Bounded goal-driven discovery

From a built workspace with the host key in `.env`, run `make discover MEMBER_ID=00123`. This resets the synthetic bank and invokes the pinned host Python/OpenAI environment. The desktop keeps no provider key, SDK, or external network route. The operator at port 6081 shows the run and retains Stop/takeover.

The host sends the goal and a permitted screenshot to Responses with `store: false`. It retains required encrypted reasoning/tool items only in bounded process memory. A native computer-tool response can contain up to four primitives. The desktop normalizes supported actions, consumes the observation lease, checks current ownership and the visible control before each input, and verifies its effect from pixels. Provider prose never supplies the business result.

The local policy permits the requested synthetic ID, field selection, Enter, and clicks on the visible read-only lookup/Savings controls. Static bank label geometry and exact identity/OCR rules are reused as environment annotations, independently of the model. No sequence of UI actions is fed to the model or executed as a fallback. Unknown controls, other text, navigation shortcuts and unsupported tool types are rejected.

## Limits and tradeoffs

We retain the existing adapter's 120-second reservation instead of expanding it to the proposed five minutes. The host and desktop also bound requests (20), native inputs (40), batch size (4), observations (512) and repeated unchanged states (three repetitions). Requests use a 30-second timeout with SDK retries disabled. Stop and takeover revoke the old epoch while the provider is pending; a late answer cannot dispatch or obtain another model observation. Arbitrary discovery takeover has no automatic continuation.

The actual provider returned click/type/Enter batches and trailing waits. A wait/screenshot is an observation operation, so it may follow locally verified completion; another input may not. Every item has a sanitized disposition. The trajectory contains only dispatched action structure and before/after observation references. A failed or uncertain batch is never acknowledged as fully executed, and is never retried.

A strict visual allowlist limits flexibility but gives an inspectable boundary for this first workflow. The alternative—accepting arbitrary coordinates or generated code—would make the recorder and safety proof harder to explain. This is a fixed-environment demonstration, not a general computer agent.

[Validation and genuine provider evidence](../evidence/m4-03-goal-discovery/README.md). Full generated artifacts, promotion and offline reuse are subsequent M4 steps. Provider data controls remain separate from local retention: `store: false` is not a promise of zero provider retention.
