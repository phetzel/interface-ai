#!/usr/bin/env python3
"""No live desktop needed: source/build identity, formatting, tests, schemas, types."""

import json
from lib.acceptance import ROOT, attempt, command, compare_schemas, write_json
from lib.builds import retain_builds

output = attempt('quick-checks')
summary = {'status': 'running', 'checks': []}


def check(name, args):
    response = command(args, directory=output, name=name, timeout=180)
    if response.returncode:
        raise RuntimeError(name + ' failed; see retained log')
    summary['checks'].append(name)
    print('PASS ' + name, flush=True)
    return response.stdout


try:
    check('quality', ['./scripts/quality'])
    check(
        'host-harness-tests', ['python3', '-m', 'unittest', 'discover', '-s', 'scripts/tests', '-v']
    )
    images = retain_builds(output)
    image = images['desktop']['imageId']
    prefix = ['docker', 'run', '--rm', '--network', 'none', '--entrypoint', 'python', image]
    check('engine-tests', prefix + ['-m', 'unittest', 'discover', '-s', '/opt/engine/tests', '-v'])
    generated = json.loads(check('model-schemas', prefix + ['-m', 'interface_ai.contracts.schema']))
    summary['schemas'] = compare_schemas(ROOT / 'capabilities/schemas', generated)
    check('fixture-typecheck', ['npm', '--prefix', 'apps/bank-fixture', 'run', 'typecheck'])
    summary['status'] = 'passed'
except Exception as exc:
    summary.update(status='failed', failure=str(exc))
    raise
finally:
    write_json(output / 'summary.json', summary)
    print('Evidence: ' + str(output), flush=True)
