"""One session-bound, exclusive input path shared by every application surface.

Bank sessions apply the operator-owned read-only policy at dispatch. Native
calibration remains a trusted developer utility, not a model execution surface.
"""

from __future__ import annotations

import fcntl
import math
import time
from pathlib import Path

from .session import LOCK, STOP, read_session
from .types import DesktopBackend


class DesktopError(RuntimeError):
    def __init__(self, code, message):
        self.code = code
        super().__init__(message)


KEYS = frozenset(
    (
        'enter',
        'tab',
        'backspace',
        'delete',
        'home',
        'end',
        'left',
        'right',
        'up',
        'down',
        'esc',
        'space',
        'ctrl',
        'shift',
        'alt',
        *'abcdefghijklmnopqrstuvwxyz0123456789',
    )
)
FIELDS = {
    'click': {'x', 'y'},
    'move': {'x', 'y'},
    'type': {'text'},
    'press': {'key'},
    'hotkey': {'keys'},
    'scroll': {'amount'},
}


def validate(action, width, height):
    def invalid(message):
        raise DesktopError('invalid_action', message)

    if not isinstance(action, dict) or not isinstance(action.get('type'), str):
        invalid('Action must be an object with a supported type')
    kind = action['type']
    if kind not in FIELDS or set(action) != FIELDS[kind] | {'type'}:
        invalid('Unknown action type, missing arguments, or unexpected fields')
    if kind in ('click', 'move'):
        if any(type(action[key]) is not int for key in ('x', 'y')):
            invalid('Coordinates must be integers')
        if not (0 <= action['x'] < width and 0 <= action['y'] < height):
            invalid('Coordinates are outside the desktop')
    if kind == 'type':
        value = action['text']
        if (
            not isinstance(value, str)
            or not 1 <= len(value) <= 256
            or any(not 32 <= ord(c) <= 126 for c in value)
        ):
            invalid('Text must contain 1–256 printable ASCII characters')
    if kind == 'press' and (not isinstance(action['key'], str) or action['key'] not in KEYS):
        invalid('Unsupported key')
    if kind == 'hotkey':
        keys = action['keys']
        if (
            not isinstance(keys, list)
            or not 2 <= len(keys) <= 4
            or any(not isinstance(k, str) or k not in KEYS for k in keys)
            or len(set(keys)) != len(keys)
        ):
            invalid('Hotkey needs 2–4 distinct supported keys')
    if kind == 'scroll' and (
        type(action['amount']) is not int or not 0 < abs(action['amount']) <= 20
    ):
        invalid('Scroll amount must be a nonzero integer between -20 and 20')
    return kind


class Desktop:
    def __init__(
        self,
        session_id=None,
        *,
        timeout=45,
        backend: DesktopBackend | None = None,
        session_reader=read_session,
        stop_path=STOP,
        lock_path=LOCK,
        clock=time.monotonic,
        event_sink=None,
        calibration=False,
        role='automation',
        epoch=None,
    ):
        if (
            type(timeout) not in (int, float)
            or not math.isfinite(timeout)
            or not 0 < timeout <= 120
        ):
            raise DesktopError('invalid_deadline', 'Timeout must be in (0, 120] seconds')
        self._read = session_reader
        self.session = self._read()
        self.id = self.session['id'] if session_id is None else session_id
        if self.id != self.session['id']:
            raise DesktopError('stale_session', 'The requested desktop session no longer exists')
        self.width, self.height = self.session['width'], self.session['height']
        self.backend = backend
        self.stop_path, self.lock_path = Path(stop_path), Path(lock_path)
        from .ownership import Ownership

        if role not in ('automation', 'human'):
            raise DesktopError('invalid_action', 'Unsupported input owner')
        self.ownership = Ownership(self.lock_path.parent, self.id)
        self.role = role
        self.epoch = self.ownership.read()['epoch'] if epoch is None else epoch
        self.clock, self.deadline = clock, clock() + timeout
        self.event_sink = event_sink or (lambda event: None)
        self._lock = None
        self._sequence = 0
        # Only trusted Python calibration code can select this path. There is no
        # action JSON/CLI/model field for disabling the bank policy.
        self._calibration = calibration
        self.policy = None

    def __enter__(self):
        self._lock = self.lock_path.open('a')
        try:
            fcntl.flock(self._lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            self._lock.close()
            self._lock = None
            raise DesktopError(
                'busy', 'Another controller owns this desktop input session'
            ) from None
        try:
            if self.backend is None:
                from .backend import X11Backend

                self.backend = X11Backend()
            self._check(observation=True)
            if (
                self.session['mode'] == 'bank'
                and not self._calibration
                and self.role == 'automation'
            ):
                from interface_ai.policy.bank import BankPolicy

                self.policy = BankPolicy()
            return self
        except BaseException:
            self.__exit__(None, None, None)
            raise

    def __exit__(self, *_):
        try:
            if self.backend is not None:
                self.backend.close()
        finally:
            if self._lock is not None:
                fcntl.flock(self._lock, fcntl.LOCK_UN)
                self._lock.close()
                self._lock = None

    def _check(self, *, observation=False):
        if self._lock is None:
            raise DesktopError('not_acquired', 'Use Desktop as a context manager')
        try:
            current = self._read()
        except (OSError, ValueError, RuntimeError):
            raise DesktopError('session_unavailable', 'Desktop session is unavailable') from None
        if current['id'] != self.id:
            raise DesktopError('stale_session', 'Desktop was reset; old actions are rejected')
        if self.clock() >= self.deadline:
            raise DesktopError('deadline', 'Desktop operation deadline exceeded')
        if self.backend.size() != (self.width, self.height):
            raise DesktopError('display_changed', 'Desktop dimensions changed')
        if not observation:
            self.ownership.check(self.role, self.epoch)
            if self.stop_path.exists():
                raise DesktopError('stopped', 'Input stopped; reset before another run')
            if self.backend.active_window() != current['windowId']:
                raise DesktopError(
                    'unexpected_focus', 'The bootstrapped application is not focused'
                )
            if current['mode'] == 'bank' and not self.backend.application_matches(current):
                raise DesktopError(
                    'policy_application_denied',
                    'Application identity does not match the approved session',
                )

    def screenshot(self):
        self._check(observation=True)
        image = self.backend.screenshot()
        if image.size != (self.width, self.height):
            raise DesktopError('display_changed', 'Screenshot dimensions changed')
        return image

    def checkpoint(self):
        """Recheck session, focus, stop, display, and total deadline without input."""
        self._check()

    def execute(self, action):
        try:
            kind = validate(action, self.width, self.height)
        except DesktopError:
            if self.policy is not None:
                self.policy.clear()
            raise
        self._sequence += 1
        event = {'sequence': self._sequence, 'action': kind, 'status': 'started'}
        started = self.clock()
        try:
            self._check()
            if self.policy is not None:
                self.policy.authorize(action, self)
                self._check()  # Recognition may take time; check again at dispatch.
            if kind in ('click', 'move'):
                getattr(self.backend, kind)(action['x'], action['y'])
            elif kind == 'type':
                # A stop arriving during typing prevents the next character.
                for character in action['text']:
                    self._check()
                    self.backend.type_character(character)
            elif kind in ('press', 'hotkey'):
                held = []
                try:
                    for key in [action['key']] if kind == 'press' else action['keys']:
                        self._check()
                        held.append(key)
                        self.backend.key_down(key)
                finally:
                    for key in reversed(held):
                        self.backend.key_up(key)
            elif kind == 'scroll':
                self.backend.scroll(action['amount'])
            event['status'] = 'completed'
            if self.policy is not None:
                self.policy.completed()
        except DesktopError as exc:
            if self.policy is not None:
                self.policy.clear()
            event.update(status='rejected', code=exc.code)
            raise
        except Exception as exc:
            if self.policy is not None:
                self.policy.clear()
            event.update(status='failed', code='input_failed')
            raise DesktopError(
                'input_failed', 'OS input failed; no automatic retry was attempted'
            ) from exc
        finally:
            event['durationMs'] = round((self.clock() - started) * 1000, 3)
            # Never record typed text or raw key sequences in routine events.
            self.event_sink(event)

    def click(self, x, y):
        self.execute({'type': 'click', 'x': x, 'y': y})

    def move(self, x, y):
        self.execute({'type': 'move', 'x': x, 'y': y})

    def type_text(self, text):
        self.execute({'type': 'type', 'text': text})

    def press(self, key):
        self.execute({'type': 'press', 'key': key})

    def hotkey(self, *keys):
        self.execute({'type': 'hotkey', 'keys': list(keys)})

    def scroll(self, amount):
        self.execute({'type': 'scroll', 'amount': amount})

    def wait(self, description, predicate, timeout=5):
        if (
            type(timeout) not in (int, float)
            or not math.isfinite(timeout)
            or not 0 < timeout <= 120
        ):
            raise DesktopError('invalid_deadline', 'Wait timeout must be in (0, 120] seconds')
        deadline = min(self.deadline, self.clock() + timeout)
        while self.clock() < deadline:
            self._check()
            value = predicate()
            self._check()
            if self.clock() >= deadline:
                break
            if value:
                return value
            time.sleep(0.05)
        raise DesktopError(
            'checkpoint_timeout', f'{description} did not complete within its deadline'
        )
