# M4-04 recorded candidate

Passed 2026-09-20 on the retained source manifest. A genuine OpenAI discovery made three requests and four native inputs. The recorder produced schema-2 capability `a3e6acd5dfd97d7e420bf9a9287ff60f62b2ea66d4a7b930db8ab9bfa6ca25ca`: four input steps, then local extraction. It did not insert the manual artifact’s select-all step. Each action maps to the recorded trajectory and before/after observations. The typing action is explicitly bound to `memberId`.

The candidate reuses reviewed environment, OCR and checkpoint annotations. Six label crops came from verified frames; the missing-member label/branch was reused from the environment profile and was not observed on this successful path. `candidate-review.json` distinguishes recorded, inferred and reused material. No review edits or approval are claimed here.

Candidate anchors remain private under `tmp/desktop-artifacts/20260920T100843Z-discovery-e746dd79/candidate`; this export intentionally contains no candidate images. Full frames, prompts and raw OCR are not retained. The separate synthetic result is member A, Savings, USD, 123456 minor units. The host report contains actual response IDs and usage, not simulated provider results.

The quick gate passed with 122 Linux engine tests. Recorder tests reject incomplete trajectories, missing anchors, reordered provenance and ordinary admission of an unapproved candidate. Candidate/provenance and asset hashes were independently checked. M4-05 must evaluate member B and translated layout before promotion; recording success is not replay approval.
