"""Bounded local file snapshots shared by artifact loading and evidence export."""

import os
from pathlib import Path
import stat


def read_regular(path: Path, maximum: int) -> bytes:
    # NONBLOCK lets fstat reject a FIFO before waiting for a writer. NOFOLLOW
    # protects the final component; callers own their path-confinement policy.
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_size > maximum:
            raise ValueError('Expected a bounded regular file')
        data = stream.read(maximum + 1)
        if len(data) > maximum:
            raise ValueError('File grew beyond its allowed size')
        return data


def safe_path(path: Path) -> Path:
    """Reject symlink components before canonicalizing an artifact location."""
    path = Path(path).absolute()
    if any(part.is_symlink() for part in (path, *path.parents)):
        raise ValueError('Symlink artifact path')
    return path.resolve(strict=True)
