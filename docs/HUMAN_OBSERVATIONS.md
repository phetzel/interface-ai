# Human takeover observations

These are reported real-person observations, not automated test attestations. The public repository does not include personal review forms or their browser-local answers.

## Manual workflow — September 19, 2026

The author operated recovery for member A. Supplied screenshots and the completion report showed wrong-screen/member resume rejection, restoration of member A's overview and successful continuation to Savings / $1,234.56 USD.

Read-only inspection of local run `20260920T042515Z-handoff-0323f9f2` confirmed:

- Session `d91f69f3-e024-482b-a1c9-beed5480bac9` was preserved.
- Result: member `00123`, Savings, USD, `amountMinor: 123456`; zero model calls.
- Five automation actions and 66 human actions were recorded; no automation input occurred during human ownership.
- Human audit events excluded typed values, keys and coordinates. The separately stored result matched its recorded digest.

The raw run is local and not packaged here. These statements record the earlier inspection; the public automated handoff evidence is linked separately below.

## Generated workflow — September 20, 2026

The author reported successful generated-workflow takeover. Screenshots showed premature-resume rejection, recovery to member A, return to search, and final **Lookup complete** / $1,234.56 with view-only mode. The completion report covers the prescribed rejection and same-session checks; screenshots alone do not prove every intermediate assertion.

## Usability and automated evidence

The author reported difficulty clicking small targets in a narrow desktop view. Actual-size viewing and responsive controls were added; automated coordinate tests pass. Personal comfort with that later layout has not been independently established.

[Generated handoff tests](../evidence/pre-submission-fixes/handoff/summary.json) and [operator UI tests](../evidence/pre-submission-fixes/operator/summary.json) are automated. [Operator workspace observations](../evidence/operator-workspace/README.md) are agent-operated. Neither is relabeled as a real-person demonstration.
