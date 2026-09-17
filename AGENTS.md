# Repository instructions

## User authorization

- Do not push this repository unless the user explicitly requests a push. The earlier repository-creation request does not authorize subsequent pushes.
- Do not bypass this restriction by uploading repository changes through a GitHub API or another tool. Local edits may be prepared within the user's requested scope.
- M1-01 through M1-06 are complete for the declared Linux ARM64 environment. M1-04 was pushed as `1d89ba8`; M1-05 (`2ea242a`) and M1-06 are committed and pushed at the user's request. M1-06 adds the full acceptance harness and a bounded transient-OCR checkpoint correction, with 47 tests, ten baseline replays, seven scenarios, and seven rejection cases passing. Both the initial failed attempt and corrected passing attempt are retained in `evidence/poc-m1/acceptance/`. Future commits and pushes require another explicit request. See the M2 status below for subsequent policy/evidence work; model integration remains later work; see M3 below for human takeover.

## Current planning constraints

- M2-01 through M2-04 (bounded PoC B) are complete locally as of 2026-09-15. See `docs/MILESTONE_2.md` and `evidence/poc-m2/README.md` for researched tradeoffs, failed/passing full attempts, and the final two-file export-reader hardening. Final source passes 63 engine tests and 14 fixture tests; the full M1 regression passes with policy enabled. The final image's 57 runtime files match source. M2 was committed and pushed as `3726347`. M3/PoC D implementation is covered below; OpenAI discovery still needs API access, reviewed outbound observations, and artifact promotion. Do not expand scope or commit/push without a user request.

- Use OpenAI only for model access; do not introduce another model-provider key.
- The user accepted the recommended initial direction: Python automation engine; TypeScript/React is the default for the small sample app when a UI is needed. Keep the operator UI minimal.
- Prefer computer use across application surfaces rather than a browser-only automation core.
- Start with a small banking-style sample application and synthetic data.
- Initial choices are OpenAI GPT-5.6 Sol with structured computer actions, PyAutoGUI for desktop input, OpenCV/Tesseract for local visual replay, and Pydantic with portable JSON/JSON Schema. M1 validates the desktop and manual replay stack within its fixed environment; the model choice and discovery pipeline still require their roadmap PoCs.
- Start with one isolated desktop environment and one display. Precise VM/container packaging must pass the environment PoC before it is treated as settled.
- See `docs/CURRENT_PLAN.md` for the active planning direction. `docs/DECISIONS.md` retains the initial comparison for reference.
- See `docs/ROADMAP.md` for proof-of-concept gates and dependencies. A planning discussion does not authorize starting those builds.

## M3 continuation constraints

- M3 implementation and automated validation are complete for the declared environment: 80 engine tests, 15 fixture tests, both live handoff cases and 63 runtime hashes pass. Full M2/M1 regression passed before the final focused ownership fixes; source deltas and follow-up evidence are retained in `evidence/poc-m3/`. A real-person demonstration remains pending.
- M3 implements same-session human input through a loopback operator panel on fixed port 6081. noVNC remains server-enforced view-only. See `docs/MILESTONE_3.md`. Do not make VNC writable or bypass the desktop ownership adapter.
- Ownership uses epochs plus a quiescence barrier. Future model actions must retain the epoch observed before the model call. The human gateway alone selects the trusted human role; model/action JSON must not expose that override.
- Resume is scoped to the reviewed `search-member` → `open-savings` boundary and validates the original member visually. Arbitrary mid-step interruption requires reset. Do not add blind retries or claim automatic general recovery.
- Automated takeover tests simulate a human and a delayed action; they are not real-person or OpenAI evidence. Keep that provenance explicit. M3 changes are local and must not be committed/pushed without another user request.
