# M4-02 shared lifecycle validation

Validated 2026-09-20 after `e52c206`, with source hashes retained. All operator actions in this record are automated API checks, not a real-person attestation. There were no model calls.

- Final quick gate: formatting/lint, host tests, 109 Linux engine tests, schemas and fixture typecheck passed.
- Ten alternating baselines and seven scenario replays passed on the preceding source. The later change only restores stale-session reporting to preflight; it does not change execution.
- CLI runs were visible through operator status, rejected competing starts, offered expiry takeover, rejected premature resume, and stopped through the operator.
- Both adversarial member-A and member-B same-session handoff cases passed.
- Final focused gate passed all seven malformed-input/artifact, stale-session and Stop rejections, verified shipped sources/results and reset to a clean search.
- Bounded policy/isolation checks and the final sanitized export passed.

Two full gate attempts failed and remain in ignored local evidence: `tmp/m2-checks/20260920T093036Z-3f3da9dc` (missing step context in OS-action events) and `tmp/m2-checks/20260920T094219Z-d72f60e9` (stale-session report phase). Their corrections were verified as above. This record does not relabel either full attempt as passed. The complete combined regression will run on final M4 source.

The matrix/handoff/lifecycle records carry their own source manifests in their original local run directories; `source-sha256.json` here identifies the final focused rejection revision. The generated-discovery work is not included in this claim.
