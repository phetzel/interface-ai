"""Browser-operated control-panel checks; never inspect the bank DOM."""

from lib.acceptance import attempt, command, source_hashes, write_json
from lib.builds import retain_builds, verify_running

output = attempt('operator-checks')
frozen = source_hashes()
summary = dict(
    status='running',
    provenance='automated-operator-ui-test',
    realHumanWitnessed=False,
    modelCalls=0,
    checks=[],
)
try:
    retain_builds(output)
    for name in ('operator_ui', 'operator_stop'):
        reset = command(
            ['./scripts/desktop', 'reset', 'bank', 'expired'],
            directory=output,
            name=name + '-reset',
        )
        if reset.returncode:
            raise ValueError('Desktop reset failed')
        verify_running(output)
        response = command(
            ['node', 'scripts/checks/' + name + '.mjs', str(output / name)],
            directory=output,
            name=name,
        )
        if response.returncode:
            raise ValueError(name + ' failed; inspect its retained log')
        summary['checks'].append(name)
        print('PASS ' + name, flush=True)
    if source_hashes() != frozen:
        raise ValueError('Source changed during operator checks')
    summary['status'] = 'passed'
except Exception as exc:
    summary.update(status='failed', failure=str(exc))
    raise
finally:
    write_json(output / 'summary.json', summary)
    print('Evidence: ' + str(output), flush=True)
