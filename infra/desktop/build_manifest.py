"""Build input enumeration shared with the trusted host verifier (not the agent)."""

import hashlib
import json
from pathlib import Path
import sys

EXCLUDED_PARTS = {
    '__pycache__',
    '.venv',
    '.ruff_cache',
    'node_modules',
    'dist',
    'test-results',
    'playwright-report',
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inputs(root, spec):
    paths = {root / name for name in spec['files']}
    for name in spec['trees']:
        paths.update(
            p
            for p in (root / name).rglob('*')
            if p.is_file()
            and not set(p.relative_to(root / name).parts) & EXCLUDED_PARTS
            and p.suffix not in ('.pyc', '.md', '.LICENSE')
        )
    if any(p.is_symlink() or not p.is_file() for p in paths):
        raise ValueError('Build inputs must be regular files')
    return {p.relative_to(root).as_posix(): digest(p) for p in sorted(paths)}


def desktop_spec():
    return {
        'files': ['.dockerignore'],
        'trees': ['engine', 'capabilities', 'infra/desktop'],
    }


def runtime_path(name):
    if name.startswith(('engine/', 'capabilities/')):
        return Path('/opt') / name
    if name.startswith('infra/desktop/') and name.endswith('.py'):
        return Path('/opt/desktop') / Path(name).name
    if name == 'infra/desktop/requirements.lock':
        return Path('/opt/desktop/requirements.lock')
    if name == 'infra/desktop/chromium-policy.json':
        return Path('/etc/chromium/policies/managed/interface-ai.json')
    return None


if __name__ == '__main__':
    source = inputs(Path(sys.argv[1]), desktop_spec())
    runtime = {
        str(path): digest(path) for name in source if (path := runtime_path(name)) is not None
    }
    Path(sys.argv[2]).write_text(
        json.dumps({'format': 'build-v1', 'sources': source, 'runtime': runtime}, indent=2) + '\n'
    )
