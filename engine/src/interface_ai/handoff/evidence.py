"""Terminal evidence. The summary is the last-written commit record for a result."""

import hashlib
import json
import os
from pathlib import Path
import tempfile


def atomic_write(path: Path, data: bytes) -> None:
    fd, name = tempfile.mkstemp(prefix='.' + path.name, dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def write_terminal(directory: Path, result, summary: dict) -> None:
    encoded = (result.model_dump_json(indent=2) + '\n').encode()
    atomic_write(directory / 'result.json', encoded)
    # Readers can detect an interrupted two-file update using this digest.
    summary = dict(summary, resultSha256=hashlib.sha256(encoded).hexdigest())
    atomic_write(directory / 'summary.json', (json.dumps(summary, indent=2) + '\n').encode())
