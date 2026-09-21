"""Trusted operator test client. Never reads banking DOM or hidden fixture state."""

import json
import re
import time
import urllib.error
import urllib.request

BASE = 'http://127.0.0.1:6081'


class Operator:
    def __init__(self):
        with urllib.request.urlopen(BASE, timeout=5) as response:
            html = response.read().decode()
        token = re.search("const token='([0-9a-f]+)'", html)[1]
        self.headers = {
            'X-Operator-Token': token,
            'Origin': BASE,
            'Content-Type': 'application/json',
        }

    def status(self):
        deadline = time.monotonic() + 10
        while True:
            try:
                with urllib.request.urlopen(
                    urllib.request.Request(BASE + '/status', headers=self.headers), timeout=10
                ) as response:
                    return json.load(response)
            except urllib.error.HTTPError as exc:
                with exc:
                    if (
                        exc.code != 503
                        or json.load(exc).get('code') != 'busy'
                        or time.monotonic() >= deadline
                    ):
                        raise
                time.sleep(0.05)  # Retry observations only; input is never retried.

    @staticmethod
    def lease(state):
        return {key: state[key] for key in ('session', 'epoch')}

    def post(self, path, *, expected=200, lease=None, **extra):
        data = {'lease': lease or self.lease(self.status()), **extra}
        request = urllib.request.Request(
            BASE + path, data=json.dumps(data).encode(), headers=self.headers
        )
        try:
            response = urllib.request.urlopen(request, timeout=15)
        except urllib.error.HTTPError as exc:
            response = exc
        with response:
            result = json.load(response)
            assert response.status == expected, (path, response.status, result)
            return result

    def action(self, action):
        return self.post('/action', action=action, sequence=self.status()['sequence'])

    def click(self, x, y):
        self.action({'type': 'click', 'x': x, 'y': y})

    def type(self, text):
        self.action({'type': 'type', 'text': text})

    def press(self, key):
        self.action({'type': 'press', 'key': key})

    def wait(self, phase):
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            state = self.status()
            if state['phase'] == phase:
                return state
            assert state['phase'] not in ('failure', 'stopped'), state
            time.sleep(0.1)
        raise AssertionError('Operator phase deadline: ' + phase)
