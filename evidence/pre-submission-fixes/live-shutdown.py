import json
import socket
import subprocess
import sys
import time
from pathlib import Path

root = Path.cwd()
sys.path.insert(0, str(root / 'scripts'))
from lib.operator import Operator
from lib.operator_host import local_request

out = root / 'tmp/pre-submission-fixes'
prior = Operator().status()
record = {'provenance': 'agent-operated-browser-and-real-Docker-shutdown', 'realHumanWitnessed': False, 'modelCalls': 0, 'manualReplay': {k: prior.get(k) for k in ('session', 'phase', 'step', 'result')}}
assert prior['phase'] == 'success', prior['phase']
print('Waiting for an operator app-switch job.', flush=True)
deadline = time.monotonic() + 90
while time.monotonic() < deadline:
    status = local_request()
    if status['active'] and status['job']['kind'] == 'switch':
        record['jobBeforeShutdown'] = status['job']
        record['activeBeforeShutdown'] = True
        break
    time.sleep(0.1)
else:
    raise RuntimeError('No active app switch observed; shutdown test not executed')
started = time.monotonic()
with (out / 'live-shutdown.log').open('w') as log:
    result = subprocess.run(['make', 'down'], stdout=log, stderr=subprocess.STDOUT, timeout=280)
record['downExitCode'] = result.returncode
record['downSeconds'] = round(time.monotonic() - started, 2)
assert result.returncode == 0

def observe():
    ports = {}
    for port in (6081, 6082):
        with socket.socket() as sock:
            sock.settimeout(2)
            ports[str(port)] = sock.connect_ex(('127.0.0.1', port)) != 0
    ps = subprocess.run(['docker', 'compose', '--profile', 'bank', 'ps', '-a', '--format', 'json'], capture_output=True, text=True, check=True)
    return {'portsClosed': ports, 'containersAbsent': ps.stdout.strip() in ('', '[]')}
record['immediatelyAfter'] = observe()
time.sleep(8)
record['eightSecondsLater'] = observe()
assert all(record['immediatelyAfter']['portsClosed'].values()) and record['immediatelyAfter']['containersAbsent']
assert all(record['eightSecondsLater']['portsClosed'].values()) and record['eightSecondsLater']['containersAbsent']
record['status'] = 'passed'
(out / 'live-shutdown.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps(record), flush=True)
