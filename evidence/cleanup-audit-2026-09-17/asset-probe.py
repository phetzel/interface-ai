"""Controlled file-replacement probe; temporary artifact, no desktop input."""
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
from unittest.mock import patch
from PIL import Image, ImageOps
from interface_ai.replay.loader import load_bundle
from interface_ai.policy.bank import admit

with tempfile.TemporaryDirectory() as directory:
    root=Path(directory)/'bundle'
    shutil.copytree('/opt/capabilities/poc/savings-balance',root)
    raw=json.loads((root/'capability.json').read_text())
    name=next(iter(raw['assets']))
    asset=root/raw['assets'][name]['file']
    with Image.open(asset) as original:
        modified=ImageOps.invert(original.convert('RGB'))
    original_open=Image.open
    replaced=False
    def replace_before_decode(path,*args,**kwargs):
        global replaced
        if Path(path)==asset and not replaced:
            modified.save(asset)
            replaced=True
        return original_open(path,*args,**kwargs)
    with patch('interface_ai.replay.loader.Image.open',replace_before_decode):
        bundle=load_bundle(root/'capability.json')
    admit(bundle)
    print(json.dumps({'replacementBetweenHashAndDecode':replaced,
      'changedFileFailsDeclaredHash':hashlib.sha256(asset.read_bytes()).hexdigest()!=raw['assets'][name]['sha256'],
      'loadedChangedPixels':bundle.templates[name].tobytes()==modified.tobytes(),
      'bundleStillAdmitted':True,'inputActions':0},indent=2))
