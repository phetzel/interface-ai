"""Independent portable-schema and retained-evidence audit (jsonschema 4.25.1).

uv run --no-project --with jsonschema==4.25.1 python evidence/poc-m1/acceptance/verify_evidence.py
"""
import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = Path(__file__).resolve().parent
index = json.loads((EVIDENCE/'attempts.json').read_text())
schemas = {p.stem:json.loads(p.read_text()) for p in (ROOT/'capabilities/schemas').glob('*.json')}
assert len(schemas)==4
for schema in schemas.values():
    Draft202012Validator.check_schema(schema)
capability = ROOT/'capabilities/poc/savings-balance/capability.json'
Draft202012Validator(schemas['capability-v1.schema']).validate(json.loads(capability.read_text()))
digest = hashlib.sha256(capability.read_bytes()).hexdigest()
result_validator = Draft202012Validator(schemas['result-v1.schema'])
allowed = {'elapsedMs','kind','step','action','status','target','score','candidateCount','box',
           'sequence','durationMs','code','checkpoint','field','confidence'}
values = {'00123','00456','00999','Demo Member A','Demo Member B','$1,234.56','$98.07'}
results = events = transient = 0
for attempt in index['attempts']:
    directory = EVIDENCE/'attempts'/attempt['directory']
    summary = json.loads((directory/'summary.json').read_text())
    assert summary['status']==attempt['status'] and summary['capabilitySha256']==digest
    for result in directory.rglob('result.json'):
        result_validator.validate(json.loads(result.read_text()))
        results += 1
        assert not list(result.parent.glob('*.png'))
        for line in result.with_name('events.jsonl').read_text().splitlines():
            event = json.loads(line)
            assert set(event)<=allowed
            assert not any(isinstance(value,str) and value in values for value in event.values())
            events += 1
            if attempt['status']=='passed' and event.get('code')=='invalid_identity' and event['status']=='unsatisfied':
                transient += 1
current = EVIDENCE/'attempts'/index['acceptedAttempt']
manifest = json.loads((current/'source-sha256.json').read_text())
for name, expected in manifest.items():
    assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==expected, name
assert json.loads((current/'summary.json').read_text())['status']=='passed'
assert len(index['attempts'])==2 and results==41
print(json.dumps({'status':'passed','schemasChecked':len(schemas),'artifactValid':True,
                  'attemptsRetained':len(index['attempts']),'typedResultsValidated':results,
                  'metadataOnlyEventsChecked':events,'acceptedRunTransientIdentityObservations':transient,
                  'acceptedSourceHashesChecked':len(manifest)},indent=2))
