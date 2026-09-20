# Delivery and author review

The repository remains private during preparation. The final submission requires a public GitHub repository and an email to `assignments@interface.ai`, sent from the address used to apply, with the repository URL on its own line. Do not send a zip. No visibility change or email is performed by the preparation work.

## Author steps

1. Read [REPORT.md](../REPORT.md). Check that you agree with the tradeoffs and can explain the boundaries, especially reused recognition annotations, agent review, the fixed goal grammar and the single continuation boundary.
2. Follow [the M4 manual supplement](manual-acceptance.html#m4) for generated replay and one real-person takeover. Use **Actual size** if targets are small. Save your observations honestly; generated automated handoffs do not complete this personal review.
3. Work through [the repository/interview checklist](repository-audit.html). Use the route below for a shorter first pass. Export both checklists from the browser where you completed them; their state is browser-local.
4. Review the [assessment coverage](ASSESSMENT_CHECK.md) and [evidence index](../evidence/README.md). Decide whether to record a short demo video; it is optional.
5. After the final push, verify the repository is public before submission. Send the draft below yourself or explicitly authorize its final recipient/body and visibility change.

## Interview route

| Explain | Start here | Be able to answer |
| --- | --- | --- |
| The end-to-end product | [Demo](DEMO.md), [report](../REPORT.md) | Why discover once and replay without a model? |
| Invocation and discovery | [Request](../scripts/lib/discovery_request.py), [loop](../scripts/lib/discovery_flow.py), [worker](../engine/src/interface_ai/discovery/worker.py) | What is model-chosen, and what is enforced locally? |
| Recording and approval | [Recorder](../engine/src/interface_ai/discovery/recorder.py), [capability](../capabilities/generated/savings-balance/capability.json), [approval](../capabilities/approvals/discovered-savings.json) | Which parts were recorded, reused or reviewed? Why can't an artifact approve itself? |
| Replay and recognition | [Interpreter](../engine/src/interface_ai/replay/interpreter.py), [recognition](../engine/src/interface_ai/replay/recognition.py) | How do relative targeting, identity checks, integer money and bounded waits prevent wrong results? |
| Ownership and Stop | [Controller](../engine/src/interface_ai/handoff/controller.py), [ownership](../engine/src/interface_ai/desktop/ownership.py) | What happens to an in-flight action or late model response after takeover? |
| Safety and evidence | [Policy](../engine/src/interface_ai/policy/bank.py), [export](../engine/src/interface_ai/policy/evidence.py), [Compose](../compose.yaml) | What is blocked? What is retained? What remains trusted? |
| Proof and limitations | [Evidence](../evidence/README.md), [build verifier](../scripts/lib/builds.py) | What was genuinely witnessed, simulated or only designed? How would another app/tenant fit? |

## Submission email draft

Subject: Computer-Use Automation System assessment — Phillip

Hi interface.ai team,

Here is my completed Computer-Use Automation System assessment:

https://github.com/phetzel/interface-ai

The README includes a one-command offline demo and the live discovery/replay path. REPORT.md covers the design decisions and limitations, and evidence/ indexes the genuine discovery and replay records.

Thanks,
Phillip

Confirm that this URL is publicly accessible before sending. The draft is not a sent message.
