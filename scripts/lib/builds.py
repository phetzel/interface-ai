"""Bind host source to immutable image IDs and verify their shipped bytes."""

import importlib.util
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    'build_manifest', ROOT / 'infra/desktop/build_manifest.py'
)
manifest = importlib.util.module_from_spec(spec)
spec.loader.exec_module(manifest)


def output(args):
    return subprocess.check_output(args, cwd=ROOT, text=True, timeout=60)


def verify_builds(root=ROOT):
    fixture_root = root / 'apps/bank-fixture'
    fixture_spec = json.loads((fixture_root / 'package.json').read_text())['interfaceAiBuild']
    expected = {
        'desktop': manifest.inputs(root, manifest.desktop_spec()),
        'fixture': manifest.inputs(fixture_root, fixture_spec),
    }
    scripts = {
        'desktop': [
            'python',
            '-c',
            "import hashlib,json,pathlib; m=json.loads(pathlib.Path('/opt/build-manifest.json').read_text()); assert all(hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()==h for p,h in m['runtime'].items()), 'Runtime bytes changed'; print(json.dumps(m))",
        ],
        'fixture': [
            'node',
            '-e',
            "const fs=require('fs'),c=require('crypto'),m=JSON.parse(fs.readFileSync('/app/build-manifest.json')); for(const [p,h] of Object.entries(m.runtime))if(c.createHash('sha256').update(fs.readFileSync(p)).digest('hex')!==h)throw Error('Runtime bytes changed'); console.log(JSON.stringify(m))",
        ],
    }
    result = {}
    for component, tag in [
        ('desktop', 'interface-ai-desktop:local'),
        ('fixture', 'interface-ai-bank-fixture:local'),
    ]:
        image = json.loads(output(['docker', 'image', 'inspect', tag]))[0]
        command = scripts[component]
        built = json.loads(
            output(
                [
                    'docker',
                    'run',
                    '--rm',
                    '--network',
                    'none',
                    '--entrypoint',
                    command[0],
                    image['Id'],
                    *command[1:],
                ]
            )
        )
        wanted = expected[component]
        changed = sorted(
            name
            for name in wanted.keys() | built['sources'].keys()
            if wanted.get(name) != built['sources'].get(name)
        )
        if changed:
            raise ValueError(
                component + ' image is stale: ' + ', '.join(changed) + '; run make build'
            )
        if built.get('format') != 'build-v1' or not built.get('runtime'):
            raise ValueError('Missing build/runtime manifest; run make build')
        if component == 'desktop':
            for name, digest in wanted.items():
                path = manifest.runtime_path(name)
                if path is not None and built['runtime'].get(str(path)) != digest:
                    raise ValueError('Shipped desktop source differs: ' + name)
        else:
            for name in ('server/index.mjs', 'server/scenarios.mjs'):
                if built['runtime'].get('/app/' + name) != wanted[name]:
                    raise ValueError('Shipped fixture server differs: ' + name)
        result[component] = {'imageId': image['Id'], 'architecture': image['Architecture'], **built}
    return result


def verify_running(directory):
    """After reset, prove Compose actually launched the images preflight verified."""
    images = json.loads((directory / 'build-preflight.json').read_text())['images']
    ids = output(['docker', 'compose', '--profile', 'bank', 'ps', '-q']).splitlines()
    if not ids:
        raise ValueError('No running project containers')
    for container in json.loads(output(['docker', 'inspect', *ids])):
        service = container['Config']['Labels']['com.docker.compose.service']
        component = 'fixture' if service == 'fixture' else 'desktop'
        if container['Image'] != images[component]['imageId']:
            raise ValueError('Running ' + service + ' differs from verified build')


def retain_builds(directory):
    try:
        result = verify_builds()
    except Exception as exc:
        (directory / 'build-preflight.json').write_text(
            json.dumps({'status': 'failed', 'reason': str(exc)}, indent=2) + '\n'
        )
        raise
    (directory / 'build-preflight.json').write_text(
        json.dumps({'status': 'passed', 'images': result}, indent=2) + '\n'
    )
    return result
