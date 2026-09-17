"""Print authoritative schemas for export; no desktop/runtime imports."""

import json
import argparse
from pathlib import Path
from pydantic import TypeAdapter
from .models import Capability, MemberInput, RunResult, SavingsOutput


def schemas():
    return {
        'capability-v1': Capability.model_json_schema(),
        'input-v1': MemberInput.model_json_schema(),
        'output-v1': SavingsOutput.model_json_schema(),
        'result-v1': TypeAdapter(RunResult).json_schema(),
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-dir', type=Path)
    args = parser.parse_args()
    if args.output_dir:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        for name, schema in schemas().items():
            (args.output_dir / (name + '.schema.json')).write_text(
                json.dumps(schema, indent=2) + '\n'
            )
    else:
        print(json.dumps(schemas(), indent=2))
