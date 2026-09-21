# interface-ai

Discover a savings lookup through a real OpenAI computer-use run, review the recorded capability, then replay it for another member with **zero model calls**. Python drives native Linux input and reads pixels/OCR; React supplies a synthetic bank. Human takeover uses the same desktop and verifies the original member before resuming.

## Try it

Start Docker Desktop. From this directory, with Docker Compose, Make and Python 3 installed:

```sh
make assess
```

Open [the operator](http://127.0.0.1:6081/). Expect **Lookup complete**, Demo Member B / `00456`, Savings, **$98.07 USD**. The approved generated artifact is the default everywhere. No API key or host SDK is needed for replay. Initial builds require network access; Linux ARM64 on Apple Silicon is the tested environment.

```sh
make assess SCENARIO=translated  # The same workflow after a 40px layout shift
make assess SCENARIO=iframe      # The same bank inside two nested local iframes
make handoff                    # Pause member A's lookup for human recovery
make down                       # Stop services; retain images and evidence
```

For takeover, refresh the operator, choose **Take control**, click the training-code field in the desktop image, send `demo` using **Text to send → Send text**, then press the panel's **Enter**. On member A's overview, choose **Verify & resume**. Expect **$1,234.56 USD** and the same session UUID. Wrong screen/member cannot resume. Complete recovery within 15 minutes; Stop remains available.

The desktop sits beside compact controls on wide screens and above them in narrow panes. **Actual size** enlarges small targets; scroll inside the desktop viewport. Input goes through the guarded adapter. The image itself is not a separate VNC connection. [Detailed demo and expected results](docs/DEMO.md).

## Run a new discovery

With `uv` installed and a private host key configured as described in [development setup](docs/DEVELOPMENT.md#online-discovery):

```sh
make discover GOAL="Find the savings balance for member 00123"
make review RUN=<printed-discovery-folder-name>
# Inspect the candidate, static crops, derivations and evaluation before approving:
make promote RUN=<same-folder-name> PROMOTION_ID=discovered-rehearsal
make assess CAPABILITY=discovered-rehearsal
```

The terminal accepts a **bounded savings goal**, not arbitrary tasks. The model chooses native actions from screenshots; local checks establish success. `synthetic-bank` is the default approved target. Unsupported intents/targets fail before reset or provider use. In the operator, expand **Discover from a goal**, enter that same goal and click **Start discovery**. **Start lookup** separately replays the selected approved workflow without a model.

A new online run incurs provider usage. Its candidate remains unapproved until review/promotion; promotion refuses to overwrite an existing approval. The key/SDK stay on the host. The checked-in example came from three genuine provider responses and four executed inputs. Its static recognition/checkpoint annotations were reused from a reviewed bank profile, and its promotion is explicitly **agent review**. [Original discovery and recording](evidence/m4-04-recorded-candidate/README.md) · [approval](capabilities/approvals/discovered-savings.json).

## Use the operator

At [localhost:6081](http://127.0.0.1:6081/), **Apps & workflows** lets you:

- Open/reset Northstar bank, its nested-iframe/shifted/recovery variants, or the native input pad. Switching starts a new session; Stop an active run or human control first.
- Select an approved saved workflow, enter a member ID and choose **Start lookup**. The generated workflow and historical manual baseline are listed separately.
- Enter a supported savings goal under **Discover from a goal**. This starts a fresh bank desktop, incurs OpenAI usage, and displays the resulting evidence folder. New candidates require terminal review/promotion before becoming approved workflows.

The native pad supports **Take control**, clicking in the image, and the panel's text/key/scroll controls. It is an input demonstration, not a native banking workflow. App selection is a fixed demo launcher, not access to your Mac's applications.

The local launcher starts automatically with desktop setup and stops with `make down`. The only page to open is port 6081; an authenticated loopback-only control service on 6082 keeps Docker and the provider key on the host. See [operator design and validation](docs/OPERATOR_WORKSPACE.md).

## Understand and verify it

| Start here | Purpose |
| --- | --- |
| [REPORT.md](REPORT.md) | Required design write-up, boundaries and tradeoffs |
| [Demo](docs/DEMO.md) | Short assessor walkthrough |
| [Coverage](docs/ASSESSMENT_CHECK.md) | Original requirements mapped to implementation/evidence |
| [Development](docs/DEVELOPMENT.md) | Setup, named checks, advanced commands and troubleshooting |
| [Evidence index](evidence/README.md) | Genuine discovery, replay, simulated operators and human observations |
| [Repository checklist](docs/repository-audit.html) | Guided code walkthrough and interview questions |
| [Manual checklist](docs/manual-acceptance.html) | Detailed internal acceptance, with browser-local results |
| [Delivery](docs/SUBMISSION.md) | Remaining personal review and unsent submission draft |

`make help` lists eight assessment commands. All automated validation uses one entry point:

```sh
make check                  # Fast: formatting, unit tests, schemas and types
make check SUITE=generated  # Generated replay, simulated handoff, transport and offline proof
make check SUITE=full       # All suites, sequenced against the shared desktop
```

Checks need the development prerequisites and built images described in [development setup](docs/DEVELOPMENT.md). Playwright verifies fixture/operator UI only; runtime execution uses screenshots and native OS input. Checks retain logs, reject stale images, and never mark human checklist results or call a live provider.

## Scope

One read-only workflow, one synthetic application, one 1280×800 Linux X11 display, fixed fonts/scale and en-US/USD. IDs preserve leading zeroes; money uses integer minor units. Exact identity, ambiguity rejection, deadlines, independent approval, ownership epochs and sanitized evidence are enforced.

The nested-iframe scenario is the same application on the same approved origin. It proves this rendered surface can be replayed without traversing a DOM. Arbitrary cross-origin applications, framesets, new layouts, native business workflows, tenant orchestration and unrestricted natural-language tasks remain outside demonstrated coverage. A native calibration pad separately verifies OS input.

The original manual bundle stays as a historical regression baseline and the recognition profile referenced by recorded provenance. The obsolete scripted vision workflow and standalone one-click provider command have been removed. Dated milestone documents and evidence remain history; use [the current plan](docs/CURRENT_PLAN.md) for status. Commits, publication and submission remain explicit author actions.
