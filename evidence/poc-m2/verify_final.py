#!/usr/bin/env python3
"""Verify the reviewed two-file follow-up to the full M2 acceptance run.

Requires the final built desktop image and Docker. Resets the synthetic desktop,
replays one member, checks deployed hashes, and exports metadata. Each invocation
retains its own attempt under tmp/m2-final-checks.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import uuid

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'evidence/poc-m2/attempts/20260915T221535Z-f59cfad5/m1-regression'
OUTPUT=ROOT/'tmp/m2-final-checks'/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8])
OUTPUT.mkdir(parents=True)
report={'status':'running','fullGate':'20260915T221535Z-f59cfad5','checks':[]}


def run(name,args,script=None):
    with (OUTPUT/(name+'.log')).open('w') as out:
        result=subprocess.run(args,cwd=ROOT,input=script,text=True,stdout=out,stderr=subprocess.STDOUT,timeout=180)
    assert result.returncode==0,name
    report['checks'].append(name)
    return (OUTPUT/(name+'.log')).read_text()


try:
    before=json.loads((BASE/'source-sha256.json').read_text())
    current={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in before}
    changed=[name for name in before if before[name]!=current[name]]
    assert set(changed)=={'engine/src/interface_ai/policy/evidence.py','engine/tests/test_policy.py'},changed
    report['changesSinceFullGate']={name:{'before':before[name],'after':current[name]} for name in changed}
    (OUTPUT/'source-sha256.json').write_text(json.dumps(current,indent=2)+'\n')
    units=(ROOT/'tmp/m2-builds/final-unit-tests.log').read_text()
    assert 'Ran 63 tests' in units and units.rstrip().endswith('OK')
    shutil.copy2(ROOT/'tmp/m2-builds/final-unit-tests.log',OUTPUT/'unit-tests.log')
    report['unitTests']=63
    report['unitExecution']='Final source mounted read-only in the dependency image; final deployed image separately hash-checked'
    run('reset',['./scripts/desktop','reset','bank'])
    response=json.loads(run('replay',['./scripts/desktop','replay','--member-id','00456']))
    assert response['status']=='success'
    name=Path(response['evidence']).name
    original=ROOT/'tmp/desktop-artifacts'/name
    result=json.loads((original/'result.json').read_text())
    oracle=json.loads((ROOT/'apps/bank-fixture/tests/oracle.json').read_text())['successes'][1]
    assert result['output']=={key:oracle[key] for key in ['memberId','memberName','accountType','currency','amountMinor']}
    report['exactOracleMatch']=True
    runtime={}
    for path,digest in current.items():
        if path.startswith(('engine/','capabilities/')):
            runtime['/opt/'+path]=digest
        elif path.startswith('infra/desktop/') and (path.endswith('.py') or path.endswith('requirements.lock')):
            runtime['/opt/desktop/'+Path(path).name]=digest
        elif path=='infra/desktop/chromium-policy.json':
            runtime['/etc/chromium/policies/managed/interface-ai.json']=digest
    manifest=ROOT/'tmp/desktop-artifacts/m2-final-manifest.json'
    manifest.write_text(json.dumps({'runtimeFiles':runtime,'results':[response['evidence']+'/result.json']}))
    data=run('runtime',['docker','compose','exec','-T','desktop','python','-','--manifest','/artifacts/'+manifest.name],
             (ROOT/'scripts/checks/m1_runtime.py').read_text())
    (OUTPUT/'runtime.json').write_text(data)
    report['runtimeFilesChecked']=len(runtime)
    response=json.loads(run('export',['./scripts/desktop','export-evidence','--run',name]))
    safe=ROOT/'tmp/desktop-artifacts'/Path(response['evidence']).relative_to('/artifacts')
    assert {p.name for p in safe.iterdir()}=={'summary.json','events.jsonl','manifest.json'}
    for file in safe.iterdir():
        assert not any(marker in file.read_text() for marker in ['SECRET-SENTINEL-84729','00456','Demo Member B'])
    shutil.copytree(safe,OUTPUT/'safe-export')
    run('final-reset',['./scripts/desktop','reset','bank'])
    (OUTPUT/'images.jsonl').write_text(run('images',['docker','image','inspect','interface-ai-desktop:local','interface-ai-bank-fixture:local',
         '--format','{"id":{{json .Id}},"architecture":{{json .Architecture}}}']))
    assert all(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest for name,digest in current.items())
    report['status']='passed'
finally:
    if report['status']!='passed':report['status']='failed'
    (OUTPUT/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Evidence: '+str(OUTPUT))
