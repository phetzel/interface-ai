import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from unittest.mock import patch
sys.path.insert(0, 'scripts')
from lib import builds
from lib.acceptance import compare_schemas
root=Path.cwd()
record={}
verified=builds.verify_builds()
with tempfile.TemporaryDirectory(dir=root/'tmp') as directory:
    clone=Path(directory)
    for component, info in verified.items():
        prefix=Path('apps/bank-fixture') if component=='fixture' else Path()
        for name in info['sources']:
            target=clone/prefix/name
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(root/prefix/name,target)
    for label,path in [('editedEngine',clone/'engine/src/interface_ai/replay/loader.py'),('editedFixture',clone/'apps/bank-fixture/src/App.tsx'),('untrackedFixture',clone/'apps/bank-fixture/src/UntrackedProbe.ts')]:
        before=path.read_bytes() if path.exists() else None
        path.write_bytes((before or b'')+b'\n// stale-build probe\n')
        try:
            builds.verify_builds(clone)
            raise AssertionError('Stale source was accepted')
        except ValueError as exc:
            assert 'image is stale' in str(exc),str(exc)
            record[label]={'status':'rejected','reason':str(exc)}
        finally:
            if before is None:path.unlink()
            else:path.write_bytes(before)
    generated=json.loads(builds.output(['docker','run','--rm','--network','none','--entrypoint','python',verified['desktop']['imageId'],'-m','interface_ai.contracts.schema']))
    path=clone/'capabilities/schemas/input-v1.schema.json'
    path.write_text('{"type":"integer"}\n')
    try:compare_schemas(path.parent,generated)
    except ValueError as exc:record['staleSchema']={'status':'rejected','reason':str(exc),'fileUnchanged':path.read_text()=='{"type":"integer"}\n'}
    else:raise AssertionError('Schema accepted')
    shutil.copyfile(root/'capabilities/schemas/input-v1.schema.json',path)
    compiled=next(p for p in verified['fixture']['runtime'] if p.endswith('.js'))
    altered=clone/'changed-asset.js';altered.write_text('// altered compiled output\n')
    original=builds.output
    def mounted(args):
        if args[:2]==['docker','run'] and verified['fixture']['imageId'] in args:
            args=args[:2]+['--mount',f'type=bind,source={altered},target={compiled},readonly']+args[2:]
        return original(args)
    with patch.object(builds,'output',side_effect=mounted):
        try:builds.verify_builds(clone)
        except subprocess.CalledProcessError:record['changedCompiledAsset']={'status':'rejected','asset':compiled}
        else:raise AssertionError('Altered compiled output accepted')
record['restoredSource']={'status':'passed','imageIds':{k:v['imageId'] for k,v in builds.verify_builds().items()}}
(root/'tmp/cleanup-implementation/negative-build-results.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record,indent=2))
