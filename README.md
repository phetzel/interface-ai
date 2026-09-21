# interface-ai

Discover a savings lookup with OpenAI, review the recorded workflow, then replay it for another member with **zero model calls**. Python operates a Linux desktop through native input and pixels/OCR. A synthetic React bank supplies the test application. Human takeover shares the same desktop and verifies the original member before resuming.

## Try it

Start Docker Desktop. With Docker Compose, Make and Python 3 installed, run from the repository root:

```sh
make assess
```

Open [the operator](http://127.0.0.1:6081/). Expect **Lookup complete**, Demo Member B / `00456`, Savings, **$98.07 USD**. This uses the approved generated workflow; no API key or host SDK is required. Initial builds need network access. Linux ARM64 on Apple Silicon is the tested environment.

```sh
make assess SCENARIO=translated  # Same workflow after a 40px layout shift
make assess SCENARIO=iframe      # Same bank inside two nested local iframes
make handoff                    # Pause member A's lookup for human recovery
make down                       # Stop services; retain images and evidence
```

For takeover, refresh the operator, choose **Take control**, click the desktop's training-code field, send `demo` through **Text to send → Send text**, then press the panel's **Enter**. On member A's overview, choose **Verify & resume**. Expect **$1,234.56 USD** and the same session UUID. Finish within 15 minutes; Stop remains available. [Demo details](docs/DEMO.md).

## Discover and save a new workflow

Install `uv` and configure the private host key using [development setup](docs/DEVELOPMENT.md#online-discovery). Then use **Discover from a goal** in the operator, or:

```sh
make discover GOAL="Find the savings balance for member 00123"
make review RUN=<printed-discovery-folder-name>
# Inspect the candidate, crops, derivations and evaluation before approving:
make promote RUN=<same-folder-name> PROMOTION_ID=discovered-rehearsal
make assess CAPABILITY=discovered-rehearsal
```

Discovery incurs OpenAI usage. The model chooses native actions from screenshots; local checks determine success. Goals are limited to savings lookup on the approved synthetic bank. A new candidate requires review and promotion before it appears as a saved workflow. The key and SDK stay on the host.

The checked-in example came from three genuine provider responses and four executed inputs. Its recognition/checkpoint annotations reuse a reviewed bank profile, and its promotion is explicitly **agent review**. [Recording evidence](evidence/m4-04-recorded-candidate/README.md) · [approval](capabilities/approvals/discovered-savings.json).

## Operator and verification

**Apps & workflows** switches between bank variants and the native input pad, or selects an approved workflow for offline replay. App switching creates a fresh session; takeover preserves one. These are fixed synthetic demos, not access to the host computer's applications. **Actual size** enlarges small desktop targets.

```sh
make check                  # Formatting, unit tests, schemas and types
make check SUITE=generated  # Replay, simulated handoff, transport and offline proof
make check SUITE=full       # All suites against the shared desktop
```

Checks require the [development prerequisites](docs/DEVELOPMENT.md). Playwright tests fixture/operator UI; runtime automation uses pixels and native input. Automated checks never call a live provider.

| Read next | Purpose |
| --- | --- |
| [REPORT.md](REPORT.md) | Architecture, tradeoffs and limitations |
| [Demo](docs/DEMO.md) | End-to-end walkthrough and expected results |
| [Coverage](docs/ASSESSMENT_CHECK.md) | Requirements mapped to code and evidence |
| [Development](docs/DEVELOPMENT.md) | Setup, tests and troubleshooting |
| [Evidence](evidence/README.md) | Discovery provenance and validation results |

## Scope

One read-only workflow, one synthetic application, one 1280×800 X11 display and en-US/USD. Exact string IDs, integer money, independent approval, bounded waits and exclusive input ownership are enforced. Nested same-origin iframes and shifted layouts are demonstrated. Arbitrary goals, cross-origin applications, framesets, native business workflows and multi-tenant orchestration remain outside demonstrated coverage.

The [documentation index](docs/README.md) separates current guides from historical design notes.
