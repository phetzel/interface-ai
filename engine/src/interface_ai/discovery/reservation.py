"""Shared exclusive input reservation for online discovery and transport diagnostics."""

from concurrent.futures import Future
from queue import Queue
import threading
import time
import uuid

from interface_ai.desktop import Desktop, DesktopError


class Reservation:
    def __init__(self, controller, *, desktop_factory=Desktop, policy_factory):
        self.controller = controller
        self.desktop_factory, self.policy_factory = desktop_factory, policy_factory
        self.commands = Queue(maxsize=1)
        self.call_lock = threading.Lock()
        self.cancelled = threading.Event()
        self.worker = None
        self.status = None
        self.code = None
        self.run_id = str(uuid.uuid4())
        self.sequence = 0
        self.epoch = None
        self.directory = None
        self.actions = 0
        self.observations = 0
        self.started = time.monotonic()

    def request(self, operation, data):
        if not self.call_lock.acquire(blocking=False):
            raise DesktopError('busy', 'Discovery already has a pending command')
        try:
            if self.status != 'running':
                raise DesktopError('invalid_transition', 'Discovery is no longer active')
            future = Future()
            self.commands.put_nowait((operation, data, future))
            return self.wait(future)
        finally:
            self.call_lock.release()

    def lease(self):
        return dict(
            runId=self.run_id,
            session=self.controller.session['id'],
            epoch=self.epoch,
            sequence=self.sequence,
        )
