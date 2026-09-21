# M5 — Assessment readiness

Scope: finish the work that can be validated independently, then hand the author a short personal review. No new provider, application surface, workflow framework or multi-tenant infrastructure is introduced.

| Step | Deliverable | Status |
| --- | --- | --- |
| M5-01 | Brief-to-code review; explicit bounded goal/target input; cleanup | Implemented; [coverage map](ASSESSMENT_CHECK.md), request tests and operator actual-size checks pass |
| M5-02 | Seven-heading, approximately 1–3 page `REPORT.md` | Written; author must agree with and explain its claims |
| M5-03 | Generated-artifact personal review and takeover | Automated coverage passes; the author reported #41 complete September 20. Checklist export remains with the user |
| M5-04 | Fresh checkout, offline setup, genuine discovery/review/new promotion/replay rehearsal | Passed on `2987382`; [complete rehearsal](../evidence/m5-readiness/clean-checkout/summary.json) |
| M5-05 | Curated evidence and concise assessor path | [One-command demo](DEMO.md), requirement map and [final evidence](../evidence/m5-readiness/README.md) complete |
| M5-06 | Interview route and repository checklist | [Route prepared](SUBMISSION.md#interview-route); personal understanding cannot be completed by an agent |
| M5-07 | Private push, public-readiness check and submission draft | History/working-tree scan passed; Private delivery is tracked in Git history. Public visibility and sending the submission remain user actions |

## Validation boundaries

Executable source stays unchanged during each live gate. Full generated and M1–M3 regressions cover the final source, with separate operator fit/actual-size and pending-input Stop checks. A fresh Git clone must start without copied `.env`, `tmp`, `node_modules` or virtual environments. It may reuse the installed toolchain, package cache and Docker build cache; this is a clean checkout on the tested machine, not a new-machine claim.

The new online rehearsal uses the existing private host key through `--key-file`, with a bounded real provider run and no key copied into the clone. A new candidate is evaluated on default/translated member B, inspected and explicitly labeled agent-reviewed before promotion under a separate ID. The original approved artifact and historical records are preserved.

Only metadata, separate synthetic results and reviewed static crops may enter the evidence package. Raw screenshots and browser-local human checklist selections are not exported automatically. The repository remains private until the author approves publication; no email is sent by this milestone.

## Author finish

Read [the report](../REPORT.md), preserve the reported section-10 takeover result in [the manual checklist](manual-acceptance.html#m4), give feedback on the newer operator layout, work through [the repository checklist](repository-audit.html), and export both self-reports. [Delivery instructions and email draft](SUBMISSION.md) finish the process.
