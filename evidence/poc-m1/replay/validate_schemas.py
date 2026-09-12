"""Host-only independent JSON Schema check; requires jsonschema 4.25.1."""
import copy
import json
from pathlib import Path
from jsonschema import Draft202012Validator, ValidationError

ROOT = Path(__file__).resolve().parents[3]
schemas = {path.stem: json.loads(path.read_text()) for path in (ROOT/'capabilities/schemas').glob('*.json')}
for schema in schemas.values():
    Draft202012Validator.check_schema(schema)
capability = json.loads((ROOT/'capabilities/poc/savings-balance/capability.json').read_text())
Draft202012Validator(schemas['capability-v1.schema']).validate(capability)
count = 0
for path in (ROOT/'evidence/poc-m1/replay').glob('*/result.json'):
    Draft202012Validator(schemas['result-v1.schema']).validate(json.loads(path.read_text()))
    count += 1
for schema, data in [(schemas['input-v1.schema'], {'memberId':123}),
                     (schemas['capability-v1.schema'], capability | {'schemaVersion':'2.0'}),
                     (schemas['result-v1.schema'], {'status':'success'})]:
    try:
        Draft202012Validator(schema).validate(data)
    except ValidationError:
        pass
    else:
        raise AssertionError('Invalid document passed the published schema')
print(json.dumps({'status':'passed','validator':'jsonschema 4.25.1 / Draft 2020-12',
                  'schemasChecked':len(schemas),'artifactValid':True,'resultsValidated':count,
                  'invalidDocumentsRejected':3}, indent=2))
