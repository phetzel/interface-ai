# Repository cleanup audit evidence

See the [full audit and ordered recommendations](../../docs/CLEANUP_AUDIT_2026-09-17.md). Baseline: `a63a143` plus the existing local React refactor; no implementation changes were made by this audit.

| Record | Scope |
| --- | --- |
| [probe.py](probe.py) / [results](probe-results.json) | Temporary capability/anchor FIFO reads, real HTTP invalid member request, and stopped-run files with a simulated worker; no desktop input |
| [asset-probe.py](asset-probe.py) / [results](asset-probe-results.json) | Controlled replacement of one temporary anchor after hashing and before decoding; no desktop input |
| [runtime-check.json](runtime-check.json) | All 30 engine Python source/test files matched the running image |
| [schema-comparison.json](schema-comparison.json) | Four repository schema exports matched verified runtime models |
| [reviewed-source-sha256.json](reviewed-source-sha256.json) | Fingerprint of 92 source/configuration/documentation inputs for review provenance |

The fresh Linux engine suite completed **85 tests in 3.862 seconds: OK**, invoked with `./scripts/desktop test`. This includes the earlier Stop repair regressions. The supplementary probes expose additional gaps; passing existing tests does not resolve those findings.

To repeat the isolated probes against the built desktop image:

```sh
docker compose exec -T desktop python - < evidence/cleanup-audit-2026-09-17/probe.py
docker compose exec -T desktop python - < evidence/cleanup-audit-2026-09-17/asset-probe.py
```

Each probe uses temporary directories, cleans up its child processes and simulates execution instead of sending OS input. The HTTP probe starts a temporary loopback server on an ephemeral port, with the normal Host/Origin/token checks. These are audit reproductions, not new permanent regression tests. The observed FIFO blocking, accepted replaced pixels, `503 execution_failed`, and missing terminal files are failures of the intended boundaries, not successful fixes.

Other fresh audit scratch files remain under ignored `tmp/cleanup-audit-2026-09-17/`. Previous fixture/live validation is referenced separately in [the frontend-refactor evidence](../frontend-refactor-2026-09-17/README.md); it is not represented as newly rerun here.
