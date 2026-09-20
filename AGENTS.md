# Repository working rules

## Authorization and scope

- Commit/push only when the user explicitly requests it. Never bypass this with an upload/API. Local edits may proceed within the requested scope.
- Keep the repository private during preparation. Do not include the assignment PDF, credentials, real customer data or raw unreviewed captures.
- Python owns automation; TypeScript/React owns the synthetic banking fixture. Use OpenAI only for future discovery, with one provider key. Keep the operator UI minimal.
- Use computer input/observations across surfaces. The runtime must not use fixture DOM, hidden state, host acceptance oracles or browser automation as execution shortcuts.
- Docker on Linux ARM64, one 1280×800 X11 display, fixed fonts/scale and en-US/USD is the supported environment. Other environments and standalone wheel distribution remain unproven.

## Invariants to preserve

- One guarded OS adapter: exact session, focus/application, display, deadline, Stop and input-lock checks. Keep exact string IDs, integer minor-unit amounts, distinct result variants, ambiguity rejection and bounded observation waits. Never retry uncertain input.
- Artifact loading must use bounded regular-file snapshots and decode the same bytes whose digest was checked. A capability cannot authorize itself; preserve independent policy admission.
- Ownership uses epochs and an input-lock quiescence barrier. Future model actions retain the epoch observed before the model call. JSON cannot select the trusted human role.
- The loopback operator is the only desktop observation/control surface; no standalone VNC server. Its image endpoint never grants input. Human input uses the panel and the same guarded adapter. Keep Host/Origin/token/CSP boundaries and Stop available during pending input.
- Resume is only the independently approved search-completion → open-Savings boundary, resolved from manifest step/checkpoint references after visual verification of the original member. Arbitrary interruption requires reset.
- Routine evidence contains closed metadata, never input text, keys, raw OCR or screenshots. Explicit business results remain separate. Storage failure must stop input; terminal worker results cannot overwrite Stop.
- Manual capability, simulated operator, real-person observation and genuine model discovery are different claims. Never prefill human checklist results or relabel automated evidence.
- Preserve historical evidence, failures, captured patches and source manifests unchanged. Format active source only.

## Working and verification

Start with [README](README.md), [current plan](docs/CURRENT_PLAN.md), [evidence index](evidence/README.md) and the [cleanup audit](docs/CLEANUP_AUDIT_2026-09-17.md). The milestone documents preserve design/history; the README and latest evidence record describe current behavior.

- `make quality` checks pinned formatting and Python correctness rules; `make format` formats active source.
- After image input changes, `make build`; `make build-check` rejects stale images and verifies shipped bytes, including compiled fixture assets.
- `make quick-check` runs formatting/lint, host harness tests, Linux engine tests, schema drift checks and fixture typechecking without a live desktop.
- For fixture changes run `make fixture-test`. For execution/policy/ownership/harness changes run the affected live gates (`make policy-check`, `make handoff-check`) and panel checks. Keep one live desktop suite at a time; do not edit executable source while a gate freezes its source manifest.
- Both HTML checklists are standalone, independent reviewer self-reports. Update their source links/instructions when behavior changes; do not confuse testing the pages with completing either human audit.
