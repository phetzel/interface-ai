# Short assessment walkthrough

This now demonstrates a capability recorded from a real OpenAI desktop run, reviewed locally, and replayed without a model. The checked-in promotion is labeled **agent review**. The earlier real-person manual-artifact takeover remains separate evidence; the generated-artifact acceptance harness uses a simulated operator.

## 1. Build and replay for a different member

Start Docker Desktop. From the repository root:

```sh
make assess
```

Open [the operator](http://127.0.0.1:6081/). Expect **Lookup complete**, Demo Member B / `00456`, Savings, **$98.07 USD**. The printed evidence directory contains the separate exact result and a report with `modelCalls: 0`, four completed inputs and the promoted capability digest. Docker/Compose and Make are sufficient for this offline demonstration; no host SDK or key is needed.

To show relative targeting, run `make assess SCENARIO=translated`. The result remains exact while the content moves 40 pixels on both axes. `make assess SCENARIO=iframe` wraps the same bank in two nested local iframes; replay still uses pixels/native input. This is bounded same-origin coverage, not proof of arbitrary legacy applications.

## 2. Explain where the artifact came from

Open [the genuine recorder evidence](../evidence/m4-04-recorded-candidate/README.md), [generated capability](../capabilities/generated/savings-balance/capability.json), [recording review](../capabilities/generated/savings-balance/recording-review.json) and [independent approval](../capabilities/approvals/discovered-savings.json).

Three actual OpenAI responses produced four native inputs. The artifact preserves those input steps, binds the recorded typing action to `memberId`, and adds verified local extraction. Explain the reused environment/OCR/checkpoint annotations and the unobserved, reused missing-member branch. The seven reviewed crops contain static labels only. Review replay for member B and translated layout preceded promotion; the candidate and approved digests are identical.

A new online discovery is optional for this walkthrough and requires `uv` plus the private host key configured in [development setup](DEVELOPMENT.md#online-discovery):

```sh
make discover GOAL="Find the savings balance for member 00123"
make review RUN=<the-printed-host-discovery-folder-name>
```

Discovery resets the desktop and sends only admitted synthetic desktop observations to OpenAI. It incurs provider usage. `store: false` does not promise zero provider retention. The key and SDK remain on the host; neither enters the isolated desktop or replay. A new run remains a candidate until explicitly reviewed and promoted. `make promote RUN=... PROMOTION_ID=discovered-rehearsal` approves a reviewed new run under a separate ID. Then rebuild and use `CAPABILITY=discovered-rehearsal` for replay/handoff. The default checked-in promotion is preserved. This is a bounded savings-workflow demonstration, not a general revision registry.

## 3. Take over the same desktop and resume

```sh
make handoff
```

The command starts the lookup and pauses at **Session expired**. Refresh the operator page after reset, note the session UUID, then:

1. Choose **Take control** and wait for **You have control**.
2. Choose **Verify & resume** while still expired: expect rejection and retained human ownership.
3. Click the training-code field in the desktop image. Send `demo` through **Text to send → Send text**; use the panel’s **Enter** button or click **Restore workspace** inside the desktop.
4. On Demo Member A / `00123`’s overview, choose **Verify & resume**.
5. Expect **$1,234.56 USD**, **Lookup complete**, and the same session UUID.

Finish within the 15-minute human-control window. Wrong screen or wrong member cannot resume. Arbitrary interruption has no declared continuation and requires reset. Choose **Actual size** above the image when targets are small, then scroll inside that viewport. **Fit to panel** restores the compact view. The explicit Enter button avoids aiming at a small submit button. The responsive panel puts controls beside the desktop on wide screens and below it in narrow panes. Personal comfort with that new arrangement still needs author feedback.

## Evidence and cleanup

`make check SUITE=generated` runs generated replay scenarios, simulated takeover, offline provider transport and export checks. `make check SUITE=full` runs all automated coverage once, including the historical manual baseline. Neither calls OpenAI or attests a real human test. See the [suite table](DEVELOPMENT.md#one-check-runner) and [evidence index](../evidence/README.md).

Use `make down` when finished. The [manual acceptance checklist](manual-acceptance.html) and [repository/interview checklist](repository-audit.html) are optional internal reviews. Read [REPORT.md](../REPORT.md) and [assessment coverage](ASSESSMENT_CHECK.md); [author review and delivery](SUBMISSION.md) lists the remaining personal steps.
