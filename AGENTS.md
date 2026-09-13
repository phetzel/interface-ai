# Repository instructions

## User authorization

- Do not push this repository unless the user explicitly requests a push. The earlier repository-creation request does not authorize subsequent pushes.
- Do not bypass this restriction by uploading repository changes through a GitHub API or another tool. Local edits may be prepared within the user's requested scope.
- M1-01 through M1-06 are complete for the declared Linux ARM64 environment. M1-04 was pushed as `1d89ba8`; M1-05 (`2ea242a`) and M1-06 are committed and pushed at the user's request. M1-06 adds the full acceptance harness and a bounded transient-OCR checkpoint correction, with 47 tests, ten baseline replays, seven scenarios, and seven rejection cases passing. Both the initial failed attempt and corrected passing attempt are retained in `evidence/poc-m1/acceptance/`. Future commits and pushes require another explicit request. Model integration, full policy/evidence enforcement, and human takeover remain later work.

## Current planning constraints

- Use OpenAI only for model access; do not introduce another model-provider key.
- The user accepted the recommended initial direction: Python automation engine; TypeScript/React is the default for the small sample app when a UI is needed. Keep the operator UI minimal.
- Prefer computer use across application surfaces rather than a browser-only automation core.
- Start with a small banking-style sample application and synthetic data.
- Initial choices are OpenAI GPT-5.6 Sol with structured computer actions, PyAutoGUI for desktop input, OpenCV/Tesseract for local visual replay, and Pydantic with portable JSON/JSON Schema. M1 validates the desktop and manual replay stack within its fixed environment; the model choice and discovery pipeline still require their roadmap PoCs.
- Start with one isolated desktop environment and one display. Precise VM/container packaging must pass the environment PoC before it is treated as settled.
- See `docs/CURRENT_PLAN.md` for the active planning direction. `docs/DECISIONS.md` retains the initial comparison for reference.
- See `docs/ROADMAP.md` for proof-of-concept gates and dependencies. A planning discussion does not authorize starting those builds.
