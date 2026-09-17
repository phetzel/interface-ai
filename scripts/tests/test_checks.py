"""Host-only regression checks: no Docker, fixture state or desktop actions."""

import json
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.acceptance import compare_schemas, command  # noqa: E402
from lib import builds  # noqa: E402


class CheckTests(unittest.TestCase):
    def test_schema_drift_fails_without_rewriting_published_files(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'input-v1.schema.json'
            original = '{"type":"string"}\n'
            path.write_text(original)
            self.assertEqual(
                compare_schemas(path.parent, {'input-v1': {'type': 'string'}}), ['input-v1']
            )
            with self.assertRaisesRegex(ValueError, 'input-v1'):
                compare_schemas(path.parent, {'input-v1': {'type': 'integer'}})
            self.assertEqual(path.read_text(), original)

    def test_new_untracked_source_changes_build_fingerprint(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'src').mkdir()
            (root / 'src/main.py').write_text('original')
            spec = {'files': [], 'trees': ['src']}
            before = builds.manifest.inputs(root, spec)
            (root / 'src/new.py').write_text('untracked')
            self.assertNotEqual(builds.manifest.inputs(root, spec), before)
            self.assertIn('src/new.py', builds.manifest.inputs(root, spec))

    def test_stale_image_rejected_even_with_unchanged_image_id(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture = root / 'apps/bank-fixture'
            fixture.mkdir(parents=True)
            (fixture / 'package.json').write_text(
                json.dumps({'interfaceAiBuild': {'files': ['package.json'], 'trees': []}})
            )
            (root / 'input.py').write_text('current')
            responses = [
                json.dumps([{'Id': 'sha256:test', 'Architecture': 'arm64'}]),
                json.dumps({'format': 'build-v1', 'sources': {'input.py': 'stale'}, 'runtime': {}}),
            ]
            with (
                patch.object(
                    builds.manifest,
                    'desktop_spec',
                    return_value={'files': ['input.py'], 'trees': []},
                ),
                patch.object(builds, 'output', side_effect=responses),
            ):
                with self.assertRaisesRegex(ValueError, 'input.py; run make build'):
                    builds.verify_builds(root)

    def test_timed_out_command_retains_partial_output(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(subprocess.TimeoutExpired) as error:
                command(
                    [
                        sys.executable,
                        '-c',
                        "import time; print('started',flush=True); time.sleep(3)",
                    ],
                    timeout=0.1,
                    directory=Path(directory),
                    name='timeout',
                )
            self.assertEqual(type(error.exception).__name__, 'TimeoutExpired')
            self.assertIn('started', (Path(directory) / 'timeout.log').read_text())


if __name__ == '__main__':
    unittest.main()
