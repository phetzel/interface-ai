# Architecture

Interface AI implements a read-only savings lookup on a synthetic bank. Python owns discovery, policy, native input, vision/OCR and replay; React/TypeScript supplies the fixture. A Linux ARM64 container runs sandboxed Chromium on a 1280×800 X11 desktop. Automation and the operator see the same framebuffer. A native calibration pad separately demonstrates input outside a browser.

CLI and operator accept a bounded savings goal and approved target. Unsupported intents, targets and inconsistent member IDs fail before credentials, reset or model use. OpenAI chooses actions from screenshots; the prompt supplies no ordered UI path. A guarded worker validates each primitive against the visible screen and ownership epoch. Local identity and balance checks determine success. Discovery permits at most 20 requests, 40 inputs and 120 seconds, without implicit provider retries.

Discovery, replay and the panel share one coordinator and OS adapter. The key and SDK remain on the host; replay has neither and cannot reach the provider. A token/Origin-protected loopback service handles fixed demo app resets and goal discovery. The operator is the only page to open, at port 6081. Docker is the tested distribution; other host runtimes remain unproven.

# Artifact schema

A capability declares versions, typed inputs/outputs, ordered actions, targets, extraction fields, checkpoints, environment assumptions and digest-bound assets. IDs are five-character strings; money uses integer minor units plus currency. Results distinguish success, business outcomes and failure. Six Pydantic-generated JSON Schemas are checked for drift.

The recorder converts executed inputs into a version-2 candidate. Actions retain trajectory/observation provenance; the typing action becomes a `memberId` binding and clicks use offsets from visual anchors. The checked-in example has four recorded inputs plus local extraction. Environment, OCR and checkpoint annotations come from a reviewed bank profile; the missing-member branch was reused, not observed during successful discovery. These derivations are explicit.

A separate promotion manifest binds exact candidate/assets, provenance, allowed identifiers and continuation references. Evaluation replays member B on default and shifted layouts before approval. The checked-in promotion is **agent-reviewed**, with unchanged candidate bytes. This is trusted-local admission, not protection from a malicious host. Recording failure retains a verified lookup result but fails discovery completion; it cannot advertise a reviewable candidate.

# Determinism & error handling

Replay uses OpenCV template matching, anchor-relative regions and pinned Tesseract OCR. It checks pre/postconditions and exact member identity before returning a result. Ambiguous targets and invalid amounts fail. Bounded observation waits handle slow transitions and uncertain OCR; wrong identity still fails immediately. Uncertain input is never replayed blindly.

Invalid inputs fail before dispatch. Missing members are named business outcomes. Expiry requests intervention; unknown checkpoints, unreadable output, policy denial and timeout stop with distinct codes and step context. Routine traces record action purpose, target, checkpoint and expected/observed categories without raw OCR, typed values or screenshots. Synthetic business results are separate. The operator shows the live failure screen.

The loader reads bounded regular-file snapshots, verifies their digests and decodes the same bytes, rejecting unsafe paths and symlinks. Build manifests bind executable source to image contents. Test oracles exist only in the host harness. Genuine provider runs, automated operators and reported human observations have separate provenance.

# Heterogeneity & multi-tenant

The adapter separates observe/input primitives from artifact targets and checkpoints. Browser and native surfaces use OS events; bank recognition remains specific to its reviewed profile. Two nested same-origin iframes and a 40-pixel layout translation are demonstrated. Neither establishes arbitrary cross-origin, frameset or new-vendor compatibility. Another application needs its own reviewed recognizer and operation policy.

For tenant reuse, I would separate a vendor/workflow base capability from a versioned tenant binding: approved entry point, application identity, locale, display requirements and restricted anchor/label overrides. Credentials would be session-scoped secrets, never artifact parameters. Each binding needs its own digest, policy review and replay evidence. Overrides may specialize targets but cannot weaken identity checks or broaden authority. Compatibility checks would quarantine drift; revisions require review. Tenant routing, isolated session scheduling and fleet management are design proposals, not implemented features.

# Escalation & handoff

The coordinator exposes the intervention reason, current step/checkpoint and live desktop. An ownership epoch invalidates old automation/model responses. Takeover quiesces input through a lock barrier before granting exclusive human control via the same adapter. Human events exclude typed text and keys. Stop signals cancellation before acquiring the coordinator mutex, so pending typing cannot block it. Terminal results cannot overwrite Stop; evidence-storage failures revoke input.

Resume is restricted to the approved search-completion → original-member overview → open-Savings boundary. It verifies the exact member and screen; rejection leaves human ownership intact. Successful recovery preserves the session UUID and does not repeat completed input. Arbitrary interruptions, including discovery takeover, allow inspection but require reset. Human control is bounded by 15 minutes and an action limit. Launcher shutdown drains active reset/discovery jobs and supervises child processes before container teardown.

# Safety

Trusted configuration and code define approved targets, manifests, operations, visible controls, application identity, gateway routes and Chromium navigation policy. The model and artifact cannot expand them. Transfers, settings and unrelated automation inputs are denied. Human recovery permits broader input inside the isolated synthetic application; this is not a production banking authorization claim.

The non-root desktop has no default network route, host home, Docker socket, provider key or fixture oracle. A narrow gateway serves approved routes. Host/Origin/token and lease checks protect control requests. Raw model conversations and full frames remain in memory; candidate staging retains reviewed static-label crops. Sanitized export reconstructs an allowlisted metadata shape and excludes business values. `store: false` does not promise zero provider retention. A malicious host or an application imitating trusted pixels remains outside the trust boundary.

# Cuts

The implemented scope is one bank workflow, fixed locale/display, a narrow goal grammar and one resume boundary. There is no unrestricted recorder, accessibility backend, credential vault, tenant service, distributed queue or model-assisted replay. The responsive operator provides fit/actual-size viewing and explicit text/key controls, not production co-browsing. Source/image checks do not make OS package builds bit-for-bit reproducible. Native calibration has intermittently timed out at startup; its cause remains unresolved.

The next useful extension is one second vendor/tenant profile, following usability feedback, before adding infrastructure. [Coverage](docs/ASSESSMENT_CHECK.md), [evidence](evidence/README.md) and the [demo](docs/DEMO.md) document what is implemented and how to reproduce it.
