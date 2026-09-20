# Private candidate capture policy

M4 recording is enabled only for the admitted synthetic bank. Routine run evidence still excludes screenshots, raw OCR, human text and provider transcripts. Full desktop frames remain in memory and are discarded after the run.

The recorder may retain bounded crops of these reviewed static labels in the ignored run's private `candidate/anchors/` directory: Member search, Member ID, Member overview, Savings, View account, and Savings account. The unique template match supplies the crop bounds. It must not retain member identities, account numbers, typed values, balances, dialogs or arbitrary model-selected rectangles. The unobserved Member not found label is copied from the reviewed static environment profile and explicitly attributed as reused, not captured in the successful run.

Each captured crop records its source observation, bounding box and digest in `review.json`. Targets retain anchor-relative geometry; raw desktop coordinates alone are not replay targets. The final extraction uses the existing exact local identity/currency/account and integer-money rules. Reused annotations, inferred checks and the recorded action order are separate fields in the review file.

Candidates are unapproved. Ordinary replay denies them even if the schema validates. Inspect the crop files and derivations, run scoped second-member/translated-layout evaluations, and create a separate reviewed promotion manifest before adding an artifact to the repository. Do not recursively export a candidate directory as routine evidence. An incomplete recording stays incomplete; never insert a missing action from the manual PoC.

Staging is under `tmp/desktop-artifacts/<discovery-run>/candidate`, with private directories/files. Retain failed attempts while investigating; remove private staging only when its owner explicitly chooses cleanup. Historical reviewed evidence and source fingerprints remain immutable.
