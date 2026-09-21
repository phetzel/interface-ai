"""Reviewed bank recognition shared by discovery, policy and generated admission.

The source is the original approved manual bundle. Keep its bytes and digest:
existing recorded provenance explicitly names them. Selecting the default demo
capability must never change this recognition/identity contract.
"""

from interface_ai.contracts.generated import GeneratedCapability
from interface_ai.replay.loader import load_bundle

RECOGNITION_PROFILE_ID = 'manual-savings'


def reference_bundle():
    from .admission import capability_path, admit

    bundle = load_bundle(capability_path(RECOGNITION_PROFILE_ID))
    admit(bundle)
    return bundle


def validate_profile(bundle):
    """This recorder reuses these semantics; review cannot silently weaken them."""
    from .admission import denied

    if not isinstance(bundle.capability, GeneratedCapability):
        denied()
    cap = bundle.capability
    reference = reference_bundle()
    if cap.provenance.recognitionProfileSha256 != reference.sha256:
        denied()
    for key in ('environment', 'inputSchema', 'outputSchema', 'fields', 'checkpoints'):
        if cap.model_dump()[key] != reference.capability.model_dump()[key]:
            denied()
    for name, target in reference.capability.targets.items():
        if name == 'member-input':
            continue
        if cap.targets.get(name) != target:
            denied()
