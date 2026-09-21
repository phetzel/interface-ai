# Operator workspace validation

September 20, 2026 local time (September 21 UTC). Uncommitted source; manifests identify the tested bytes. Historical evidence and approved capability bundles were not rewritten. These observations are **agent-operated UI checks**, not a new real-person attestation.

## Observed through the visible operator

| Check | Observation |
| --- | --- |
| Saved workflow selection | Selected `manual-savings`, ran member B and observed $98.07. Report records the selected manual approval and zero model calls. |
| Native app | Switched from the operator, took control, clicked all three targets green, submitted synthetic text, scrolled rows, and stopped. Separate `native-manual-v1` evidence contains no bank capability claim. |
| Nested local iframes | Switched to the iframe bank and ran `discovered-savings` for member A. Observed $1,234.56 and successful zero-model replay. |
| Shifted layout | On the final source, selected the shifted bank and replayed member B. Observed $98.07; [report](shifted-generated-b/report.json) confirms four inputs and zero model calls. |
| Default selection and native controls | On the final source, a CLI-configured manual workflow appeared selected. Switching to native retained its app label, offered Take control without bank resume, and Stop revoked input. |
| Stop during desktop launch | Requested a shifted-layout desktop, then Stop while reset was underway. The new desktop finished in `stopped`/view-only state. |
| Unsupported goal | Entered a money-transfer request. The panel explained the supported savings goal; no launcher job, desktop reset or model request was started. |
| Actual goal discovery | Entered `Read the current savings account balance for member ID 00456`. Three genuine OpenAI requests/four inputs produced $98.07 and a recorded candidate. The panel displayed the evidence folder and review-required status. The candidate did not enter the approved workflow list. |
| Same-session recovery | Launched the recovery variant. Premature, wrong-screen and wrong-member resumes were rejected. Restored member A and completed at $1,234.56 in session `1676d254-d618-4d88-a3f2-8d3449371dd4`. Audit confirms three rejections, eleven human inputs and four automation inputs. |
| Actual-size interaction | Used Actual size in the narrow operator pane, clicked the member-search breadcrumb, returned to Fit to panel and completed recovery. |
| Second discovery and Stop | A member-A run also completed in three requests/four inputs. It finished before the attempted interruption; Stop then disabled input and preserved the successful result. This does **not** attest to manually stopping an in-flight provider response. |

The first manual selection/native/iframe checks preceded the small selector-display correction. The member-B and member-A discovery runs, recovery and approval behavior used identical host/runtime bytes to the final implementation except for the subsequent operator JavaScript startup fix and formatter file inclusion; [the explicit digest delta](post-discovery-changes.json) records that change. Final automated checks validate the corrected panel.

## Failures found and corrected

The app selector initially reverted visually to Northstar after a successful native/variant launch. It now retains the selected app when reconnecting. A subsequent automated operator check failed at member-validation startup. The panel could enable Start before loading the workflow registry, and an older completed host job could unnecessarily reload a page after a CLI reset. Start now waits for the registry, and automatic reconnection only follows a replacement job observed by that page. The failed attempt is retained in [operator-startup-failure](operator-startup-failure/summary.json).

## Automated checks

- [Final quick gate](quick-final/summary.json): 129 Linux engine tests; 29 host tests (one intentional optional-SDK skip); six schema comparisons; fixture types and formatting/lint.
- [Final operator gate](operator-final/summary.json): invalid input, recovery, fit/actual-size/narrow/scrolled coordinates, and Stop during pending typing. Separate [Stop measurements](operator-final/operator_stop.json) retain the latency and stopped state.
- Host tests reject wrong Host/Origin/token, oversized/duplicate JSON, unknown apps/unsupported goals, stale sessions and active input. A blocked reset test proves Stop prevents subsequent discovery and stops the replacement desktop.
- [Generated group](generated/summary.json) passed: eleven replay cases, two same-session handoffs, six simulated-provider transport cases and SDK/key/egress absence plus safe export. No model calls occurred in this group.

## Evidence and scope

`discovery-member-b/` and `discovery-member-a-before-stop/` preserve actual provider response IDs, request counts, typed results, source fingerprints and image identities. Their new candidates remain local/unapproved. The previously reviewed generated capability digest is unchanged. Other folders retain synthetic replay/native/recovery metadata and explicit business results; no credentials or raw screenshots are published here.

The local same-origin iframe bank and native pad are implemented surfaces. Cross-origin vendor apps, framesets, arbitrary goals, native business-workflow discovery, concurrent desktops and production/multi-tenant operation remain unclaimed. Existing intermittent native-startup failures remain historical limitations; this manual native launch passed. Personal interview understanding, checklist attestations, public visibility and submission remain with the author.

## Final verification order

The generated group passed before the final panel default-selection initialization and inclusion of the launcher entry point in the formatter configuration. [The exact source delta from its retained handoff manifest](post-generated-changes.json) is operator.js and ruff.toml only. Engine/host job/provider/replay behavior was unchanged. The final quick gate, operator gate and clean-source rehearsal then passed on the final bytes. Earlier gate evidence is retained alongside the final gate files.

[Clean-source rehearsal](clean-source/setup.json): make assess passed from an exported working tree with no .env, node_modules, virtual environment or previous tmp files. It reused the installed toolchain and Docker build cache. The operator then rejected a valid discovery goal with a helpful missing-key message, without resetting the completed lookup. This is a clean source export of uncommitted work, not a new-machine or fresh-commit claim.

The launcher was then stopped in that disposable checkout. A fresh desktop still offered saved workflows while explaining that launcher functions were unavailable. Agent-operated member-B replay completed at $98.07, without a key or launcher service.
