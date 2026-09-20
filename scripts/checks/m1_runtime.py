"""Read-only M1 acceptance probe, executed inside the isolated bank desktop.

The manifest contains expected source hashes and result paths, never the fixture
oracle. Network attempts send no application data and use no credentials.
"""

import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import socket
import shutil
import subprocess
import urllib.request

from pydantic import TypeAdapter
from interface_ai.contracts.models import RunResult
from interface_ai.contracts.schema import schemas

parser = argparse.ArgumentParser()
parser.add_argument('--manifest', required=True)
args = parser.parse_args()
manifest = json.loads(Path(args.manifest).read_text())
for name, digest in manifest['runtimeFiles'].items():
    assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == digest, name
exports = schemas()
for name, schema in exports.items():
    assert (
        json.loads(Path('/opt/capabilities/schemas', name + '.schema.json').read_text()) == schema
    )
validator = TypeAdapter(RunResult)
for name in manifest.get('results', []):
    validator.validate_json(Path(name).read_text(), strict=True)

assert os.getuid() != 0
assert not any('OPENAI' in name.upper() for name in os.environ), (
    'Unexpected OpenAI environment configuration'
)
packages = {
    dist.metadata['Name'].lower(): dist.version for dist in importlib.metadata.distributions()
}
assert not any(name in packages for name in ('openai', 'anthropic', 'google-genai'))
assert not Path('/var/run/docker.sock').exists()
assert not Path('/opt/apps/bank-fixture/tests/oracle.json').exists()
assert not any(
    line.split()[1] == '00000000' for line in Path('/proc/net/route').read_text().splitlines()[1:]
)
with urllib.request.urlopen('http://fixture:4173/healthz', timeout=3) as response:
    assert response.status == 200

for program in ('x11vnc', 'websockify'):
    assert shutil.which(program) is None, f'Legacy viewer software remains: {program}'
assert not Path('/usr/share/novnc').exists()
for port in (5900, 6080):
    try:
        connection = socket.create_connection(('127.0.0.1', port), timeout=1)
    except ConnectionRefusedError:
        pass
    else:
        connection.close()
        raise AssertionError(f'Legacy viewer port {port} is still listening')

probes = []
for address in ('1.1.1.1', '8.8.8.8', '2606:4700:4700::1111'):
    try:
        connection = socket.create_connection((address, 443), timeout=1)
    except OSError as exc:
        probes.append(
            {'destination': address, 'port': 443, 'blocked': True, 'reason': type(exc).__name__}
        )
    else:
        connection.close()
        raise AssertionError('External TCP probe unexpectedly connected')
# Resolve in a bounded child process because libc DNS waits have their own limits.
lookup = subprocess.run(
    [
        'python',
        '-c',
        "import json,socket; print(json.dumps(sorted(set(x[4][0] for x in socket.getaddrinfo('api.openai.com',443,type=socket.SOCK_STREAM)))))",
    ],
    text=True,
    capture_output=True,
    timeout=10,
)
if lookup.returncode == 0:
    addresses = json.loads(lookup.stdout)
    assert addresses
    for address in addresses:
        try:
            connection = socket.create_connection((address, 443), timeout=1)
        except OSError as exc:
            probes.append(
                {
                    'destination': 'api.openai.com',
                    'resolvedAddress': address,
                    'port': 443,
                    'blocked': True,
                    'reason': type(exc).__name__,
                }
            )
        else:
            connection.close()
            raise AssertionError('Model endpoint TCP probe unexpectedly connected')
else:
    probes.append(
        {'destination': 'api.openai.com', 'blocked': True, 'reason': 'dns_resolution_failed'}
    )

print(
    json.dumps(
        {
            'status': 'passed',
            'architecture': platform.machine(),
            'python': platform.python_version(),
            'runtimeFileHashesChecked': len(manifest['runtimeFiles']),
            'schemasMatchModels': len(exports),
            'resultsValidated': len(manifest.get('results', [])),
            'nonRoot': True,
            'noOpenAIConfiguration': True,
            'noModelSDK': True,
            'modelCalls': 0,
            'fixtureHealthReachable': True,
            'legacyViewerRemoved': True,
            'legacyPortsClosed': [5900, 6080],
            'noDefaultIPv4Route': True,
            'tcpProbes': probes,
            'packages': packages,
            'scope': 'Selected IPv4, IPv6 and model endpoint probes; not a comprehensive network policy audit',
        },
        indent=2,
    )
)
