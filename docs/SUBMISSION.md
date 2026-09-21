# Delivery and author review

The repository remains private during preparation. The final submission requires a public GitHub repository and an email to `assignments@interface.ai`, sent from the address used to apply, with the repository URL on its own line. Do not send a zip. No visibility change or email is performed by the preparation work.

## Author steps

1. Read [REPORT.md](../REPORT.md). Check that you agree with the tradeoffs and can explain the boundaries, especially reused recognition annotations, agent review, the fixed goal grammar and the single continuation boundary.
2. Preserve the completed generated-artifact takeover reported for [manual check #41](manual-acceptance.html#m4). Give feedback on the newer compact operator layout; automated checks cannot establish personal comfort.
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

## Repeating the takeover if needed

The author reported #41 complete and supplied a passing terminal result for #42 on September 20. Keep those results. Export the checklists (#43), finish the repository/interview review, and assess the newer responsive operator layout. The sequence below is a reference if you choose to repeat takeover; a new paid discovery is unnecessary.

From `/Users/phillip/interview/interface-ai`, open the checklists in the same browser you used before:

```sh
open -a "Google Chrome" docs/manual-acceptance.html docs/repository-audit.html
make handoff
```

For check 41, finish the following in one session, within 15 minutes of taking control. Do not reset between these steps:

1. Refresh [the operator](http://127.0.0.1:6081/). The command already started the lookup. At **Your help is needed**, record the UUID from **Run details** and choose **Take control**.
2. While the expiry dialog remains open, choose **Verify & resume**. Expect rejection, with human control retained.
3. Choose **Actual size** if the image is too small. Click the training-code field inside the desktop. Use the panel's **Text to send → Send text** to send `demo`, then its **Enter** button. Expect Demo Member A's overview.
4. Click **Member search** inside the desktop and choose **Verify & resume**. Expect rejection because this is the wrong screen.
5. Focus the desktop member-ID field. Use the panel's **Select all**, send `00456`, then **Enter**. On member B's overview, choose **Verify & resume**; expect rejection because this is the wrong member.
6. Return through **Member search**, focus the ID field, **Select all**, send `00123`, then **Enter**. On member A's overview, choose **Verify & resume**. Expect **Lookup complete**, Savings **$1,234.56 USD**, and the original UUID.
7. Record whether Actual size and viewport scrolling made clicking comfortable. Export the manual checklist after your observations; export the repository checklist after the interview route above. Keep any unperformed personal checks unverified.

If the control window expires, run the handoff command again and start a new session. When finished, `make down` stops the local services while retaining evidence.
