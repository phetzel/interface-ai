"""Small operator CLI; input always requires an explicit observed session ID."""
import argparse
import json
import sys
from pathlib import Path
import re

from .desktop import Desktop, DesktopError
from .desktop.session import STOP, read_session, request_stop


def main():
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('status')
    commands.add_parser('stop')
    export = commands.add_parser('export-evidence')
    export.add_argument('--run', required=True, help='Replay directory name under /artifacts')
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
        if args.command == 'export-evidence':
            from .policy.evidence import export_bundle
            if not re.fullmatch(r'[0-9]{8}T[0-9]{6}Z-replay-[0-9a-f]{8}', args.run):
                raise DesktopError('evidence_rejected', 'Expected a replay run directory name')
            root = Path('/artifacts')
            exports = root / 'exports'
            if exports.is_symlink():
                raise DesktopError('evidence_rejected', 'Invalid export directory')
            exports.mkdir(exist_ok=True)
            path = export_bundle(root / args.run, exports / args.run)
            print(json.dumps({'status': 'exported', 'evidence': str(path)}))
            return 0
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
