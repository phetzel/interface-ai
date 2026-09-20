"""Trusted acceptance-harness selection, never imported by the runtime."""

import json
from .acceptance import ROOT

IDS = ('manual-savings', 'discovered-savings')


def selected(identifier):
    if identifier not in IDS:
        raise ValueError('Choose an explicit supported capability')
    approval = json.loads((ROOT / 'capabilities/approvals' / (identifier + '.json')).read_text())
    path = ROOT / 'capabilities' / approval['capabilityFile']
    cap = json.loads(path.read_text())
    return path, cap, approval
