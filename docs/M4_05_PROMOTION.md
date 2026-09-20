# M4-05 — Review and promotion

The recorder writes an unapproved candidate under its private desktop run. `make review RUN=<host-discovery-folder>` cross-checks real provider metadata, candidate/trajectory digests and the discovery image fingerprint. It then uses an explicitly scoped review route to replay the exact candidate for member B on default and translated layouts. This route uses the ordinary coordinator, desktop policy, ownership epochs and interpreter, without a provider client. It grants no ordinary approval or resumable takeover.

After inspecting `candidate/REVIEW.md`, `review.json`, the static anchor images and the evaluation results, `make promote RUN=<host-discovery-folder>` makes the local approval decision. It preserves the candidate bytes and records an empty review delta when no edits were needed. The checked-in first promotion uses `agent-review`: Codex inspected the crops and annotations. That is distinct from a real person witnessing takeover or reviewing the code. The command defaults to `user-review` when the user explicitly performs this review and promotion themselves.

Promotion checks that both evaluations passed with unchanged candidate/source bytes and unchanged evidence. It copies only the typed capability, declared static anchors and review records into `capabilities/generated/savings-balance`, then writes authority separately to `capabilities/approvals/discovered-savings.json`. It refuses to overwrite an existing promotion. A later run can be promoted under a new ID, for example `make promote RUN=... PROMOTION_ID=discovered-rehearsal`. The ID selects a separate bundle and manifest; existing approval bytes are never overwritten. The demo bounds this directory to eight approvals, without a general revision registry.

The manifest binds candidate and approved digests, all asset hashes, version, provider/model provenance, original source/image fingerprints, review evidence, environment, policy version, allowed structural event IDs and continuation references. Schema 1 retains manual provenance. Both JSON schemas come from their Pydantic models; the promotion contract has its own published schema.

## Replay and continuation

After promotion, rebuild the image, then run:

```sh
make build
make demo CAPABILITY=discovered-savings MEMBER_ID=00456
make handoff-demo CAPABILITY=discovered-savings MEMBER_ID=00123
```

The first command pair performs offline replay. The handoff command launches the expiry scenario and stops at the approved pause; open `http://127.0.0.1:6081/` to take control. The existing default manual handoff command still opens an idle expiry demo for the original checklist.

Admission reads bounded regular-file approval snapshots and compares them with the loaded bundle, including its closed event vocabulary. Modified JSON or asset bytes, symlink paths, missing approval, mismatched identifiers and invalid continuation references fail before input. Model prose never supplies event identifiers. Candidate evaluation cannot write approval into its own bundle.

The only resumable boundary remains search completion followed by opening Savings. The manifest identifies those steps by ID and requires the original member’s `member-ready` checkpoint. There is no numeric resume index in policy and no generic “continue from wherever the human stopped.” Arbitrary takeover still requires reset.

## Deliberate limits and review decisions

The generated action order comes from the actual discovery; the recognition profile supplies environment, OCR, identity checks and the optional missing-member branch. The latter is explicitly labeled reused, since the successful discovery did not encounter a missing member. The local policy now permits the visible field/button interiors, rather than the manual artifact’s tiny aiming region, so model-selected points remain valid when converted to relative targets. Both discovery and replay share those independently reviewed control bounds (`bank-read-only-v2`).

The first promotion preserves the candidate exactly and supports this one bank workflow. There is no general registry, graphical workflow editor, automatic provider approval, or claim of general discovery across arbitrary applications. Full frames remain memory-only; only reviewed static synthetic labels enter the repository. Routine execution evidence remains image-free.

The host and operator-owned approval directory are trusted in this demonstration. Digests bind the bytes reviewed and executed; they are not a cryptographic signature or protection against an administrator replacing both the bundle and its authority. Review/promotion is a local foreground workflow: do not edit a candidate while evaluating or promoting it. The desktop image’s read-only filesystem and build/source checks preserve the packaged runtime boundary.
