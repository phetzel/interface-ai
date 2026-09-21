# Operator workspace

Open `http://127.0.0.1:6081/` after `make assess` or `make up`. Desktop setup automatically starts the local launcher; `make down` stops it. Python 3 is now also required for the offline launcher. No extra user command or API key is required for saved replay.

## Three distinct operations

| Control | What it does | Boundary |
| --- | --- | --- |
| Open app / reset session | Opens the bank, its nested-iframe/shifted/recovery variants, or the native input pad | Fixed local demos; creates a new session; refuses active execution or human ownership |
| Saved workflow → Start lookup | Lists independently admitted approvals, then replays the selected artifact with a five-digit member ID | Zero model calls; selection is an approval ID, never a filesystem path |
| Discover from a goal | Validates the supported savings goal, resets the bank, runs the existing host discovery command and displays its evidence directory | Paid OpenAI use; at most 20 requests/40 inputs/120 seconds; candidate remains unapproved |

Example goal: `Read the current savings account balance for member ID 00456`. This is the same intentionally bounded request grammar as the CLI. It is not arbitrary task understanding. The model chooses actions from screenshots; local typed checks determine success. Operator discovery requires the ignored private `.env` file; environment-variable-only credentials are supported by CLI discovery, not the launcher.

Both `discovered-savings` and the historical `manual-savings` appear because both have independent approvals. The native pad has **Take control**, native clicking, text/key/scroll buttons and Stop, but no bank replay or automatic resume. Native manual evidence is labeled `native-manual-v1`, not bank replay.

## Why a host service

The desktop is deliberately isolated from Docker, the provider key and the SDK. Putting those inside it would expand the execution agent's authority. `scripts/lib/operator_host.py` instead runs on loopback port 6082, accepting only fixed launch operations from the 6081 operator origin with a random token. Host, Origin, fetch-site, JSON size/fields, session and active-state checks apply. No shell command, arbitrary URL/path, key-upload or promotion endpoint exists. The browser never receives the API key.

The existing 6081 desktop HTTP server still owns screenshots, input, replay, ownership and Stop. It independently admits workflow selection at execution. The host service launches the existing `scripts/discover`, including an expected-session binding; it does not implement a second model loop. The provider conversation remains in that bounded child process.

Compared with moving the entire operator to a host proxy, this keeps the existing desktop transport and CLI working when the optional launcher is unavailable. The tradeoff is a second local service/port, automatically managed by the same desktop commands. Use only the 6081 page.

## Cancellation and recovery

Starting a launcher job revokes the old session before reset, so a stale tab cannot launch input during replacement. Only one launcher job runs at a time. The page reconnects with the new server token once reset finishes. Stop signals both the desktop and the host job. A reset already in progress drains, then its new desktop is stopped; it does not proceed to discovery. A provider request already sent may finish, but revoked input cannot execute and discovery checks the lease before another provider request.

The launcher keeps current job status in memory. Ignored local `tmp/operator-jobs/` folders contain command logs; discovery retains its normal source/build/provider report and candidate separately. Restarting the launcher loses its status card, not those files. Terminal commands should not be used concurrently with a UI job against this single shared desktop.

Lookup and recording completion are separate outcomes. If the lookup succeeds but recording is incomplete, its business result is retained, the discovery command exits unsuccessfully with `recording_incomplete`, and the operator reports that no reviewable candidate exists.

`make down` waits for an active launcher job to drain and stop its replacement desktop before tearing down containers. Shutdown rejects new jobs and supervises the worker and its child process group. A stuck child is terminated after the bounded drain period; if cleanup cannot finish, teardown fails explicitly instead of racing an unsupervised reset. Normal Stop remains separate from launcher shutdown.

App switching deliberately resets rather than preserving several running desktops. **Take control / Verify & resume** remains the same-session recovery path. New candidate review and promotion stay explicit terminal operations. After promotion, rebuild and reset the desktop to load the new approval into the saved-workflow list.

## Validation

See [operator workspace evidence](../evidence/operator-workspace/README.md) for automated boundaries, the genuine provider run and agent-operated UI observations. These do not fill in either personal checklist. The native pad and same-origin iframe bank are implemented surfaces; arbitrary cross-origin applications and framesets remain outside demonstrated coverage.
