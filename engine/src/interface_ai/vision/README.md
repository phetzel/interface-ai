# Local visual primitives · M1-04

`primitives.py` provides bounded-region template matching and explicit missing/ambiguous outcomes. `ocr.py` reads a declared screenshot region using local Tesseract and parses exact USD text into integer cents. `bank.py` composes those primitives for the small synthetic fixture; it consumes only screenshots and the requested member ID, and emits no input itself.

The operator probe connects recognition to the existing desktop adapter:

```sh
./scripts/desktop build
./scripts/desktop reset bank
./scripts/desktop vision-probe --member-id 00123
./scripts/vision-check
```

The second command starts the default fixture. `reset bank translated` selects the translated variant. `vision-check` runs the eight-case host harness, resetting between cases and checking outputs against the independent fixture oracle. The oracle is never passed to the container probe. These commands exercise a manually authored Python sequence; no capability JSON, interpreter, discovery, or general recovery logic exists yet.

## Matching and geometry

Anchors are reviewed crops containing static UI labels only. Their [manifest](anchors/manifest.json) records source screenshot hashes, crop rectangles, and anchor hashes. They were captured in M1-03 before the M1-04 checks. The initial member-A default probe calibrates recognition; other members, translations, and failure variants are checked with the same settings.

Matching uses grayscale OpenCV `TM_CCOEFF_NORMED` with a fixed 0.92 threshold. Connected groups of above-threshold placements represent candidates; all distinct candidates are retained. Zero matches yields `target_missing`; multiple matches yield `ambiguous_target`, even when one scores higher. Constant/low-variation anchors and out-of-screen regions are rejected. This follows OpenCV's distinction between [single-location and multiple-object matching](https://docs.opencv.org/4.12.0/d4/dc6/tutorial_py_template_matching.html).

Search and account headers establish the current page context. The member input is located relative to its visible field label. The Savings label must be unique within the visible account list, and its View account label is located within that row. Identity and balance extraction boxes are defined relative to the observed page heading. Relative offsets are explicit fixture-layout assumptions; there is no fallback to absolute screenshot coordinates. Templates are checked against their recorded hashes at load time.

Supported conditions are one 1280×800 display, the current bundled fonts/theme, 100% browser scale, and the tested +40 px main-content translation. Chromium's scrollbar may also shift centered content; each page anchor is resolved independently. A header matching does not establish that an arbitrary overlay or operation is safe. Scrolled-off targets, arbitrary reflow, other fonts/themes/scales, and unrelated apps remain unsupported.

## OCR and output checks

The image contains Tesseract 5.3.0, Debian's pinned English data package, OpenCV 4.12.0.88, and NumPy 2.2.6. The English traineddata SHA-256 is checked at runtime. Python distributions are hash locked; OS package versions are recorded with evidence. The English model package version is `1:4.1.0-2`, whose traineddata works with Tesseract 5.3's LSTM engine.

Each bounded crop is converted to grayscale, enlarged 3× with Lanczos, padded by 24 white pixels, and read with LSTM / single-line mode (`--oem 1 --psm 7`). PNG input and TSV output use pipes; captures, recognized text, and TSV are not written to temporary files. An OCR subprocess has a three-second limit and one OpenMP thread. These choices use Tesseract's [TSV and segmentation support](https://tesseract-ocr.github.io/tessdoc/Command-Line-Usage.html) and [image-quality guidance](https://tesseract-ocr.github.io/tessdoc/ImproveQuality.html).

Every recognized word must have confidence at least 80; absent or uncertain readings stop. Confidence is a rejection heuristic, not proof of accuracy. The member ID must equal the exact five-digit input before selecting an account and again on the final page. Account type and currency must read Savings and USD. Amount parsing requires a dollar sign, valid digit grouping, and exactly two decimals; it uses integer arithmetic. It does not substitute OCR characters, infer missing decimals, or treat unavailable output as zero.

Visual heading waits have a five-second limit. Only a missing target is retried; ambiguity and other errors stop immediately. The desktop wait also rechecks stop, session, focus, and deadlines after a predicate completes, so a late successful observation cannot escape the wait deadline. Already-running OCR may finish before stop is observed; no subsequent input bypasses the adapter.

Routine events contain target/field names, boxes, scores, confidences, action types, and failure codes. They omit recognized text and typed values. Explicit synthetic results are written separately to `result.json`. The current primitive probe suppresses captures; separate native/browser calibration utilities can still retain known synthetic screenshots. This is not general sensitive-screen redaction.

M1-05 added the validated manual artifact/interpreter and member-not-found branch; M1-06 added the repeated gate. `BankVision` remains the legacy primitive/calibration path, while capability-driven replay uses the interpreter. Current policy and human ownership are covered by M2/M3; model discovery and a real-person demonstration remain pending. See the [current evidence index](../../../../evidence/README.md).
