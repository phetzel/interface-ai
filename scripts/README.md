# Host commands and checks

The public interface is `make help`; `make help-dev` lists development controls. These scripts are trusted host tooling, separate from the desktop execution agent.

| Entry | Responsibility |
| --- | --- |
| `desktop`, `fixture` | Compose lifecycle and fixed container commands |
| `operator-host` | Automatically managed local UI launcher; fixed app resets and the existing discovery command, no extra user setup |
| `discover` | Explicit paid discovery, pinned host SDK/key, bounded goal admission |
| `review-capability` | Candidate evaluation and deliberate independent promotion |
| `check` | One named-suite runner; `checks/` contains domain assertions |
| `quality`, `build-check` | Formatting/lint and source/image verification |
| `lib/` | Shared subprocess, build, operator-client, discovery and review mechanics |
| `tests/` | Host-only tests of those mechanics |

`check --suite full` sequences the suites against one desktop. It keeps each run's evidence and links those records from one summary. Helpers do not relax case assertions, retry uncertain input, call a real provider or overwrite historical evidence. The `discovery` suite uses a fake provider against real guarded input and labels that provenance explicitly.

Milestone-specific launchers, the old visual workflow probe and the standalone one-click provider command were removed. The native/browser calibration checks remain because they verify input independently of bank recognition. Historical milestone commands are documented in dated records; current commands are in [development](../docs/DEVELOPMENT.md).
