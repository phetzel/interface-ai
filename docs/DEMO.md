# Assessor walkthrough

Run commands from the repository root. Start Docker Desktop first; Docker/Compose and Make on Apple Silicon are the tested prerequisites. The initial build needs network access. No host Node/Python setup or API key is needed for this demo.

This demonstrates desktop automation, parameterized replay and human takeover using a **manually authored capability**. Genuine OpenAI discovery and generated capability promotion are still pending. Replay makes zero model calls. [Current evidence and remaining work](../evidence/README.md).

## 1. Start and watch a lookup

```sh
make start
```

This builds both images, starts a fresh healthy bank desktop and validates the capability. Open **[the operator panel](http://127.0.0.1:6081/)**. Leave member `00123` selected and click **Start lookup**. The panel shows the same desktop the automation controls; expect Demo Member A's savings balance of **$1,234.56 USD** and a successful lookup.

## 2. Replay for a different member

```sh
make demo MEMBER_ID=00456
```

This resets the desktop and replays the same capability for Demo Member B. The terminal prints a success status and evidence directory. Reload the operator panel to reconnect to the new session and see **$98.07 USD** on the savings page. The run's `result.json` records the typed business result, and `report.json` records `modelCalls: 0`. This run uses the CLI; the panel's run status does not track CLI replay.

## 3. Restore an expired session and resume

```sh
make handoff-demo
```

Reload the operator panel, keep member `00123`, and click **Start lookup**. When the desktop shows an expired workspace:

1. Click the panel's **Take control** button.
2. Click the training-code field **inside the desktop image**.
3. Type `demo` in the panel's **Text to send** field and click **Send text**.
4. Click **Restore workspace** inside the desktop image.
5. Once Demo Member A's overview returns, click **Verify & resume** in the panel.

The lookup completes with **$1,234.56 USD**. Open **Run details** to compare the session UUID throughout takeover and resumption. Text and key controls appear only while you own the desktop. The **Stop** button stays at the top and stops further input; starting again afterward requires a reset. The operator panel is the only desktop page; the legacy 6080 viewer has been removed.

## 4. Finish

```sh
make down
```

Services stop; images and local evidence remain. Each run has its own timestamped folder directly under `tmp/desktop-artifacts/`, with `-replay-` or `-handoff-` in the name. A printed container path `/artifacts/<run>` corresponds to `tmp/desktop-artifacts/<run>` on the host. Each run keeps its own result and sanitized execution evidence. [Evidence format and limitations](../evidence/README.md).

For a failed startup, use `make logs` and `make ready`; [build troubleshooting](DEVELOPMENT.md#public-image-credential-helper-workaround) covers the known Docker credential-helper issue. Re-running `make start` rebuilds as needed and replaces the desktop session.

The [full manual checklist](manual-acceptance.html) covers failure cases and regression checks. The [repository checklist](repository-audit.html) is for the author's code review and interview preparation; neither is required to walk through this demo.
