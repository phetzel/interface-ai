"""Small operator CLI; input always requires an explicit observed session ID."""
import argparse
import json
import sys

from .desktop import Desktop, DesktopError
from .desktop.session import STOP, read_session, request_stop


def main():
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('status')
    commands.add_parser('stop')
    action = commands.add_parser('action')
    action.add_argument('--session', required=True)
    action.add_argument('--json', required=True)
    args = parser.parse_args()
    try:
        if args.command == 'status':
            result = read_session() | {'inputStopped': STOP.exists()}
        elif args.command == 'stop':
            request_stop()
            result = {'status': 'stopped', 'resetRequired': True}
        else:
            events = []
            with Desktop(args.session, event_sink=events.append) as desktop:
                desktop.execute(json.loads(args.json))
                result = {'sessionId': desktop.id, 'events': events}
        print(json.dumps(result))
    except (DesktopError, OSError, ValueError, RuntimeError) as exc:
        print(json.dumps({'status': 'failed', 'code': getattr(exc, 'code', 'invalid_or_unavailable'),
                          'message': str(exc) if isinstance(exc, DesktopError) else 'Invalid request or unavailable desktop'}), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
