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
    validate = commands.add_parser('validate-capability')
    validate.add_argument('--capability', default='/opt/capabilities/poc/savings-balance/capability.json')
    replay = commands.add_parser('replay')
    replay.add_argument('--capability', default='/opt/capabilities/poc/savings-balance/capability.json')
    replay.add_argument('--session')
    inputs = replay.add_mutually_exclusive_group(required=True)
    inputs.add_argument('--member-id')
    inputs.add_argument('--inputs-json')
    args = parser.parse_args()
    try:
        if args.command == 'replay':
            from .replay.command import replay as run
            return run(args)
        if args.command == 'validate-capability':
            from .replay.loader import load_bundle
            bundle = load_bundle(args.capability)
            result = {'status': 'valid', 'capability': bundle.capability.name, 'sha256': bundle.sha256}
        elif args.command == 'status':
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
