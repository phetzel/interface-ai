#!/usr/bin/env python3
"""Generated replay offline boundary and sanitized export verification."""

import json
import shutil
import sys
from pathlib import Path
from lib.acceptance import ROOT, attempt, command, source_hashes, write_json
from lib.builds import retain_builds


def main():
    output = attempt('offline-checks')
    summary = dict(
        status='running',
        provenance='automated-integration-of-genuine-recorded-artifact',
        modelCalls=0,
        realHumanWitnessed=False,
    )
    frozen = source_hashes()
    write_json(output / 'source-manifest.json', frozen)
    try:
        retain_builds(output)
        proof = command(
            ['docker', 'compose', 'exec', '-T', 'desktop', 'python', '-'],
            script="""import importlib.util,json,os,socket
assert importlib.util.find_spec('openai') is None
assert not any(k.startswith('OPENAI') for k in os.environ)
try:
 sock=socket.create_connection(('api.openai.com',443),timeout=2)
except OSError:
 pass
else:
 sock.close();raise AssertionError('Provider egress unexpectedly available')
print(json.dumps({'providerSDKAbsent':True,'providerKeyAbsent':True,'providerEgressBlocked':True}))
""",
            directory=output,
            name='offline-boundary',
        )
        if proof.returncode:
            raise ValueError('Offline boundary proof failed')
        summary['offlineBoundary'] = json.loads(proof.stdout)
        response = command(
            ['make', 'demo', 'CAPABILITY=discovered-savings', 'MEMBER_ID=00456'],
            directory=output,
            name='final-member-b',
            timeout=180,
        )
        if response.returncode:
            raise ValueError('Final member-B replay failed')
        state = json.loads(response.stdout.splitlines()[-1])
        run = Path(state['evidence']).name
        exported = command(
            ['./scripts/desktop', 'export-evidence', '--run', run],
            directory=output,
            name='safe-export',
        )
        if exported.returncode:
            raise ValueError('Generated event vocabulary failed export')
        source = ROOT / 'tmp/desktop-artifacts' / run
        for filename in ('report.json', 'result.json', 'events.jsonl'):
            shutil.copyfile(source / filename, output / ('member-b-' + filename))
        safe = ROOT / 'tmp/desktop-artifacts/exports' / run
        shutil.copytree(safe, output / 'safe-export')
        for path in (output / 'safe-export').iterdir():
            if any(
                secret in path.read_text()
                for secret in ('00456', 'Demo Member B', '98.07', 'SECRET-SENTINEL')
            ):
                raise ValueError('Unexpected business value in safe export')
        if source_hashes() != frozen:
            raise ValueError('Executable source changed during acceptance')
        summary['status'] = 'passed'
    except Exception as exc:
        summary.update(status='failed', failure=str(exc))
    finally:
        write_json(output / 'summary.json', summary)
        print('Evidence: ' + str(output), flush=True)
    return 0 if summary['status'] == 'passed' else 1


if __name__ == '__main__':
    sys.exit(main())
