"""Trusted host harness mechanics. Case assertions and oracles stay with each gate."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import uuid

ROOT = Path(__file__).resolve().parents[2]


def attempt(kind):
    name = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8]
    directory = ROOT / 'tmp' / kind / name
    directory.mkdir(parents=True)
    return directory


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def command(arguments, *, timeout=180, script=None, directory=None, name=None):
    try:
        result = subprocess.run(
            arguments, cwd=ROOT, input=script, text=True, capture_output=True, timeout=timeout
        )
    except subprocess.TimeoutExpired as exc:
        if directory is not None:
            data = (exc.stdout or b'') + (exc.stderr or b'')
            (directory / (name + '.log')).write_bytes(data + b'\nCommand deadline exceeded\n')
        raise
    if directory is not None:
        (directory / (name + '.log')).write_text(result.stdout + result.stderr)
    return result


def source_hashes():
    names = command(
        ['git', 'ls-files', '--cached', '--others', '--exclude-standard']
    ).stdout.splitlines()
    return {
        name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
        for name in sorted(set(names))
        if (
            name.startswith(
                ('engine/', 'infra/', 'scripts/', 'apps/bank-fixture/', 'capabilities/')
            )
            or name
            in ('.dockerignore', 'compose.yaml', 'Makefile', 'ruff.toml', '.prettierrc.json')
        )
        and (ROOT / name).is_file()
        and not name.endswith(('.md', '.LICENSE'))
    }


def compare_schemas(directory, generated):
    published = {
        p.name.removesuffix('.schema.json'): json.loads(p.read_text())
        for p in directory.glob('*.schema.json')
    }
    if published != generated:
        changed = sorted(
            key
            for key in published.keys() | generated.keys()
            if published.get(key) != generated.get(key)
        )
        raise ValueError('Published schemas differ from models: ' + ', '.join(changed))
    return sorted(published)
