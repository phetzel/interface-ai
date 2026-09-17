"""Cross-process ownership epochs; input.lock is the quiescence barrier.

Changing to quiescing revokes admission immediately. Human ownership is granted
only after the old Desktop context releases input.lock (including key cleanup).
"""

from contextlib import contextmanager
import fcntl
import json
from pathlib import Path
import time


class Ownership:
    def __init__(self, root, session_id):
        self.root, self.session_id = Path(root), session_id
        self.path = self.root / 'ownership.json'

    @contextmanager
    def locked(self):
        with (self.root / 'ownership.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            yield

    def _read(self):
        from .adapter import DesktopError

        if not self.path.exists():
            return {'session': self.session_id, 'owner': 'automation', 'epoch': 0}
        state = json.loads(self.path.read_text())
        if state['session'] != self.session_id:
            raise DesktopError('stale_session', 'Ownership belongs to a different session')
        return state

    def read(self):
        with self.locked():
            return self._read()

    def check(self, role, epoch):
        from .adapter import DesktopError

        state = self.read()
        if state['owner'] != role or state['epoch'] != epoch:
            raise DesktopError(
                'ownership_revoked', 'Input ownership changed; discard pending actions'
            )

    def change(self, owner, *, expected):
        from .adapter import DesktopError

        if owner not in ('automation', 'quiescing', 'human', 'stopped'):
            raise ValueError('Invalid owner')
        with self.locked():
            state = self._read()
            if state != expected:
                raise DesktopError('ownership_revoked', 'Ownership changed before transition')
            state = dict(state, owner=owner, epoch=state['epoch'] + 1)
            temporary = self.path.with_suffix('.next')
            temporary.write_text(json.dumps(state))
            temporary.replace(self.path)
            return state

    def takeover(self, input_lock, *, expected, timeout=5):
        from .adapter import DesktopError

        if expected['owner'] not in ('automation', 'quiescing'):
            raise DesktopError('ownership_revoked', 'There is no automation handoff to drain')
        pending = (
            self.change('quiescing', expected=expected)
            if expected['owner'] == 'automation'
            else expected
        )
        deadline = time.monotonic() + timeout
        with Path(input_lock).open('a') as lock:
            while True:
                try:
                    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except BlockingIOError:
                    if time.monotonic() >= deadline:
                        # Stay quiescing: never grant control while input is live.
                        raise DesktopError(
                            'quiesce_timeout', 'Input has not drained; reset required'
                        ) from None
                    time.sleep(0.02)
            return self.change('human', expected=pending)
