"""Audit-only probes. Temporary files, real HTTP, simulated input; no OS actions."""
import json
import multiprocessing
import os
from pathlib import Path
import shutil
import sys
import tempfile
import threading
from unittest.mock import Mock
from urllib.request import Request, urlopen
from urllib.error import HTTPError

sys.path.insert(0, '/opt/engine/tests')
from interface_ai.replay.loader import load_bundle
from interface_ai.handoff.controller import Controller
from interface_ai.handoff.server import Server, HOST, ORIGIN
from test_handoff import ControllerTests

results = {}

def load(path, begun):
    begun.set()
    load_bundle(path)

with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    main_fifo = root/'main-fifo.json'
    os.mkfifo(main_fifo)
    artifact = root/'artifact'
    shutil.copytree('/opt/capabilities/poc/savings-balance', artifact)
    raw = json.loads((artifact/'capability.json').read_text())
    asset_path = artifact/next(iter(raw['assets'].values()))['file']
    asset_path.unlink()
    os.mkfifo(asset_path)
    for name, path in [('capability_fifo', main_fifo), ('asset_fifo', artifact/'capability.json')]:
        begun = multiprocessing.Event()
        process = multiprocessing.Process(target=load, args=(path,begun))
        process.start()
        assert begun.wait(2)
        process.join(1)
        results[name] = {'stillBlockedAfterSeconds':1,'blocked':process.is_alive(),'exitCodeBeforeTermination':process.exitcode}
        if process.is_alive():
            process.terminate()
        process.join(2)
        assert not process.is_alive()

case = ControllerTests()
case.setUp()
try:
    controller = Controller(output_root=case.root)
    controller.launch = Mock()
    with Server(('127.0.0.1',0),controller) as server:
        thread = threading.Thread(target=server.serve_forever,kwargs={'poll_interval':.01},daemon=True)
        thread.start()
        try:
            request = Request(f'http://127.0.0.1:{server.server_port}/start',
                data=json.dumps({'lease':{'session':'session','epoch':0},'memberId':'123'}).encode(),
                headers={'Host':HOST,'Origin':ORIGIN,'X-Operator-Token':server.token,'Content-Type':'application/json'})
            try: response = urlopen(request,timeout=2)
            except HTTPError as error: response=error
            with response:
                results['invalid_member_http']={'status':response.status,'body':json.load(response),'workerLaunched':controller.launch.called}
        finally:
            server.shutdown(); thread.join(2)
    case.human()
    case.controller.stop()
    results['stopped_run_files']={'phase':case.controller.phase,'files':sorted(p.name for p in case.controller.directory.iterdir()),'resultIsNone':case.controller.result is None}
finally:
    case.doCleanups()

from interface_ai.contracts.schema import schemas
results['published_schemas']={name:json.loads(Path('/opt/capabilities/schemas',name+'.schema.json').read_text())==schema for name,schema in schemas().items()}
print(json.dumps(results,indent=2))
