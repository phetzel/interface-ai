"""Session-bound host bootstrap; output is captured privately by the trusted host."""

import json
import os
import secrets
from interface_ai.desktop.session import RUNTIME
from interface_ai.files import read_regular

CREDENTIALS = RUNTIME / 'discovery-capability.json'


def provision(session):
    value = {'session': session, 'token': secrets.token_hex(32)}
    temporary = CREDENTIALS.with_suffix('.next')
    temporary.unlink(missing_ok=True)
    with temporary.open('x') as stream:
        # This directory is private to the trusted desktop user. Set permissions
        # before writing so even a preexisting process cannot read a partial token.
        os.fchmod(stream.fileno(), 0o600)
        json.dump(value, stream)
    temporary.replace(CREDENTIALS)
    return value['token']


def credentials():
    """Only the fixed local launcher reads this; never embed it in panel HTML."""
    return json.loads(read_regular(CREDENTIALS, 1024))


if __name__ == '__main__':
    print(json.dumps(credentials()))
