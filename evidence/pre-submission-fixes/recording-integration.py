"""Recorder fault through worker, host CLI and launcher; simulated OS/provider only."""
from contextlib import nullcontext
import json
from pathlib import Path
import runpy
import sys
import uuid
from types import SimpleNamespace
from unittest.mock import Mock, patch
sys.path[:0] = ['/opt/engine/tests', '/audit/scripts']
from test_discovery_loop import DiscoveryLoopTests, CLICK
from interface_ai.replay.loader import ReplayError
from lib.discovery import MODEL
from lib import operator_host as host

case = DiscoveryLoopTests()
case.setUp()
try:
    frame = case.start()
    case.discovery.recorder = SimpleNamespace(observe=lambda *_: None,
        finish=Mock(side_effect=ReplayError('recording_incomplete', 'Synthetic recording failure')))
    frame = case.send(frame, [CLICK, {'type':'type','text':'00123'}, {'type':'keypress','keys':['ENTER']}])
    frame = case.send(frame, [dict(CLICK,x=900,y=600)])
    case.discovery.worker.join(2)
    assert case.discovery.summary()['status'] == 'failed'
    assert case.discovery.summary()['code'] == 'recording_incomplete'
    assert not (case.discovery.directory/'candidate/capability.json').exists()
    class Transport:
        session = 'synthetic-session'
        def __init__(self,*a,**kw): pass
        def post(self,operation,data):
            if operation=='propose': return frame
            return dict(lease={'runId':'synthetic-run'},directory='synthetic-run',actionsCompleted=0,
                        width=1280,height=800,png='iVBORw0KGgo=')
    client = Mock()
    client.responses.create.return_value.model_dump.return_value = dict(
        id='resp_synthetic',model=MODEL,status='completed',output=[dict(type='computer_call',
        call_id='call_synthetic',actions=[{'type':'screenshot'}])])
    root = Path('/audit/evidence/recording-integration') / uuid.uuid4().hex
    directory=root/'tmp/discovery-runs/incomplete'
    directory.mkdir(parents=True,exist_ok=True)
    main=runpy.run_path('/audit/scripts/discover')['main']
    main.__globals__.update(attempt=lambda _:directory,load_key=lambda _: 'synthetic-test',
        source_hashes=lambda:{},retain_builds=lambda _:None,verify_running=lambda _:None,
        bootstrap=lambda:{'session':Transport.session},Transport=Transport)
    with patch.dict(sys.modules, {'openai':SimpleNamespace(OpenAI=lambda **kw:nullcontext(client)),
            'httpx2':SimpleNamespace(Client=lambda **kw:None)}), \
            patch.object(sys,'argv',['discover','--member-id','00123']):
        exit_code=main()
    report=json.loads((directory/'report.json').read_text())
    result=json.loads((directory/'result.json').read_text())
    assert exit_code==1 and report['status']=='failed' and report['code']=='recording_incomplete'
    assert result['status']=='success' and result['output']['amountMinor']==123456
    jobs=host.Jobs(); jobs.active=True
    jobs.job=dict(id='incomplete',kind='discover',status='running')
    def execute(args,log,timeout):
        if args[0]=='./scripts/desktop': return 0
        log.write_text('Evidence: '+str(directory)+'\n')
        return exit_code
    with patch.object(host,'ROOT',root),patch.object(host,'Operator') as operator, \
            patch.object(jobs,'execute',side_effect=execute):
        operator.return_value.status.return_value={'session':'synthetic-session'}
        jobs.run(dict(kind='discover',goal='Find the savings balance for member 00123'))
    assert jobs.job['status']=='failed' and not jobs.job['candidate']
    assert 'recording incomplete' in jobs.job['stage']
    summary=dict(provenance='simulated-provider-and-OS-recorder-fault',modelCalls=0,
        desktopStatus=case.discovery.summary()['status'],lookupStatus=result['status'],
        candidateFileExists=False,cliExitCode=exit_code,hostStatus=report['status'],
        code=report['code'],launcherStatus=jobs.job['status'],launcherStage=jobs.job['stage'],
        reviewableCandidate=jobs.job['candidate'])
    Path('/audit/evidence/recording-integration.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary))
finally:
    case.doCleanups()
