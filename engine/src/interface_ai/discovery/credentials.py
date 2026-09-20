"""Fixed trusted-host bootstrap; output must be captured privately, never logged."""

import json

from .probe import credentials

if __name__ == '__main__':
    print(json.dumps(credentials()))
