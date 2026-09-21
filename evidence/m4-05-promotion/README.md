# M4-05 reviewed promotion

Passed 2026-09-20. The same candidate digest `a3e6acd5dfd97d7e420bf9a9287ff60f62b2ea66d4a7b930db8ab9bfa6ca25ca` replayed for member B on default and translated layouts before approval. Both returned the exact synthetic USD balance, 9807 minor units, with zero model calls and four inputs. `evaluation.json` binds the source, image IDs and retained evaluation files.

Codex inspected all seven static crops and the recorded/reused/inferred annotations. They contain static labels only. The local promotion is explicitly `agent-review`, with no edits to the candidate. It is not a user review or a real-person takeover attestation. See [the separate approval](../../capabilities/approvals/discovered-savings.json), [generated bundle](../../capabilities/generated/savings-balance/capability.json) and [review documentation](../../docs/history/M4_05_PROMOTION.md).

After promotion and rebuilding, ordinary approved replay for member B also passed (`approved-member-b`). Result files here contain explicit synthetic business values; routine reports/events remain metadata-only. The final quick gate passed 127 Linux engine tests and 20 host tests (one intentional skip), all six schema comparisons and fixture typechecking. New negatives cover unapproved candidates, altered recorded evidence/assets, unsafe symlinks, missing/mismatched approval, unknown event IDs and invalid continuation references.

Full combined regression and generated-artifact takeover are M4-06; this record does not claim those gates yet. The final recorded quick gate is authoritative for this step.
