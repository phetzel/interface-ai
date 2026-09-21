# M1-05 · Manual capability and replay evidence

M1-05 passed on the isolated ARM64 Linux desktop on 2026-09-12. The same manually authored capability executed both members and the supported layout variant, returned the named missing-member outcome, and stopped safely on ambiguous targets, unreadable output, and blocked loading. This is one pass per integration case; M1-06's repeated acceptance gate remains pending.

The [capability](../../../capabilities/poc/savings-balance/capability.json) has SHA-256 `94d37e09907c839e3c04bd1662003ae6529d087e137952e4e844a673d32d9c17`, version `0.1.0`, and provenance `manually-authored-poc`. All eleven retained runs used that artifact and made zero model calls. The interpreter reads its actions, targets, regions, input bindings, checkpoints, and output bindings from JSON. Automatic discovery is later work.

## Real desktop integration

The [host-only harness](https://github.com/phetzel/interface-ai/blob/613ee9cec4868be03dacd606de89e5e88dce5e4e/scripts/replay-check) compared success outputs with the fixture's separate oracle. The oracle is not available to the replay command. [summary.json](summary.json) preserves run IDs, timings, and assertions; each directory below contains its original report, sanitized event log, and typed result.

| Case | Result | Completed input actions | Seconds |
| --- | --- | ---: | ---: |
| [Baseline A](baseline-a/result.json) | Exact output: member `00123`, USD `123456` minor units | 5 | 3.047 |
| [Baseline B](baseline-b/result.json) | Exact output: member `00456`, USD `9807` minor units | 5 | 2.929 |
| [Missing member](missing/result.json) | `member_not_found`; no account click or extraction | 4 | 1.483 |
| [Translated A](translated-a/result.json) | Exact output after a 40 px layout translation | 5 | 3.161 |
| [Translated B](translated-b/result.json) | Exact output after a 40 px layout translation | 5 | 3.032 |
| [Delayed loading](delayed-a/result.json) | Exact output after 1,800 ms loading delay | 5 | 4.918 |
| [Duplicate Savings targets](duplicate-a/result.json) | `ambiguous_target` at `open-savings` | 4 | 2.411 |
| [Unreadable balance](unreadable-a/result.json) | `ocr_uncertain` at `read-balance` | 5 | 3.374 |
| [Blocked loading](blocked-a/result.json) | `checkpoint_timeout` at `search-member` | 4 | 6.475 |

Failure cases returned no success output and dispatched no later input action. The blocked case's elapsed time includes earlier steps; its search step has a five-second budget. Template-not-found and uncertain OCR events during polling are expected intermediate observations, not successful checkpoints.

Two earlier successful development probes are also retained: [first-success](first-success/report.json) and [first-missing](first-missing/report.json). These preceded final schema-export and failure-reporting refinements; the nine-case suite above ran with the final implementation. No unexpected failed runtime attempts were discarded.

## Contract and interpreter checks

[unit-tests.txt](unit-tests.txt) records **44 passing tests**, including 17 new contract/interpreter tests. They cover invalid artifacts and inputs before desktop acquisition, duplicate JSON keys, unsupported versions/actions, bad references and cycles, tampered assets and symlink escapes, artifact-controlled ordering/output binding, early business outcomes, stop, failed preconditions, ambiguous checkpoints, bounded waits, no input retry, and invalid or mismatched output identity. Interpreter unit tests use explicit fakes; the table above supplies the real screenshot/input/OCR evidence.

An independent Draft 2020-12 validator checked all four exported schemas, the manual artifact, and all eleven retained result documents. It also rejected three invalid documents. See [schema-validation.json](schema-validation.json) and the reproducible [validation script](validate_schemas.py). Reference graphs and other semantic constraints are additionally enforced by the loader.

Replay screenshots remain in memory; the operator command did not persist any. Routine events contain step names, action types, timing, boxes, scores, and confidence, without typed input or OCR values. Explicit results contain the synthetic member output separately.

## Reproduce

From the repository root with Docker Desktop running:

```sh
./scripts/desktop build
./scripts/desktop test
./scripts/desktop validate-capability
./scripts/desktop reset bank
./scripts/desktop replay --member-id 00123
./scripts/desktop reset bank
./scripts/desktop replay --member-id 00456
./scripts/replay-check
uv run --no-project --cache-dir tmp/uv-cache --with jsonschema==4.25.1 python evidence/poc-m1/replay/validate_schemas.py
```

Raw integration logs are under the ignored `tmp/replay-checks/20260912T180808Z-64fc7ea3` directory; raw run evidence is under `tmp/desktop-artifacts`. The curated copies here are sufficient to inspect results without those directories. On this host the image build used an anonymous Docker client config at `tmp/docker-client` and Docker Desktop's socket to avoid a local credential-helper issue.

See [source-sha256.json](source-sha256.json), [image IDs](images.txt), [system packages](system-packages.txt), and the [final fresh desktop session](final-session.json) for provenance. The source manifest covers executable source, schemas, templates, and build configuration, excluding explanatory documentation edited after the image build. [Runtime verification](runtime-validation.json) matched 51 container files to the host manifest and all four schema exports to the running models. [Source verification](source-validation.json) checked syntax, local documentation links, the unchanged artifact across eleven runs, and the allowed metadata fields across 726 events. The final session has input enabled and the bank fixture reset to its search screen.

M1-04 was committed and pushed as `1d89ba8`. M1-05 is committed locally at the user's request and has not been pushed. M1-06 repeated acceptance, model-driven discovery, and human takeover remain later work.
