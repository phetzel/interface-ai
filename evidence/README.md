# Evidence index

Use this index to distinguish a claim from the exact source and environment that support it. Failed attempts are retained alongside corrections. Historical counts are not current test totals. Raw local attempts live under ignored `tmp/`; reviewed records below are committed.

| Claim / revision | Reviewed record | What it establishes | Limit |
| --- | --- | --- | --- |
| September 17 repository cleanup, after `d0a4f21`; formatting separated as `f4f8e99` | [Cleanup implementation](cleanup-implementation-2026-09-17/README.md) | Loader/terminal/HTTP repairs, build/source verification, quality gate and affected regressions; exact source manifest included | Read the run results for the tested source, not just the parent commit |
| React component refactor, pushed as `d0a4f21` | [Frontend refactor](frontend-refactor-2026-09-17/README.md) | 15 browser tests, 31 exact visual/DOM comparisons, nine replay cases and two simulated handoffs | Comparisons describe the pre-formatting React revision |
| Repository audit at `a63a143` plus React changes | [Audit reproductions](cleanup-audit-2026-09-17/README.md) | 85 tests, 30 runtime source matches, four schema matches and reproduced defects | Baseline findings; fixes are in the newer cleanup record |
| Pre-audit Stop repair `a63a143` | [Pre-audit record](pre-audit-2026-09-17/README.md) | Full M2/M1 gate, 85 tests, HTTP/visible Stop and diagnostics, simulated handoffs | Exact recorded source; no real-person attestation |
| M3 baseline `ec2b56e` | [M3 record](poc-m3/README.md) | Ownership epochs, same-session input, quiescence, restricted verified continuation | Simulated operators; follow-up corrections are separately documented |
| M2 baseline `3726347` | [M2 record](poc-m2/README.md) | Bounded policy, isolation, safe export and M1 regression | Synthetic fixed environment; no general redaction or arbitrary-page authorization |
| Original M1 gate | [M1 acceptance](poc-m1/acceptance/README.md) | Native/browser desktop primitives, manual capability, OCR, repeated replay and rejections | Manually authored capability, fixed Linux ARM64 environment |

## Latest local validation (not yet packaged for submission)

The user reports the M1–M3 manual checklist passed, including a real-person member-A takeover. [Manual audit observations](../docs/MANUAL_AUDIT_NOTES.md) separate that observation from agent-operated UI checks and terminal/harness results, and link the ignored local evidence. Preserve the exported reviewer checklist and review these files before publishing. This does not complete the separate repository/interview review or genuine discovery.

The [M4 specification](../docs/MILESTONE_4.md) defines the remaining discovery-to-replay proof.

## Pending evidence

- A real OpenAI discovery run with reviewed outbound observations and an artifact recorder.
- An operator-reviewed generated capability replayed for the second member with zero model calls.
- Final packaging of the witnessed real-person handoff and reviewer checklist export.
- Final assignment report and end-to-end demo/evidence packaging.

The [manual checklist](../docs/manual-acceptance.html) and [repository review](../docs/repository-audit.html) hold separate reviewer self-reports. Automated testing of those pages does not complete either review. Routine run metadata omits typed values, OCR text and screenshots; explicit synthetic results/debug calibration records have their own documented retention boundaries.
