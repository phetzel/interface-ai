"""Normalize only supported provider primitives; never execute generated code."""

from interface_ai.desktop import DesktopError
from interface_ai.desktop.adapter import validate


def normalize(action, member):
    if not isinstance(action, dict):
        raise DesktopError('invalid_action', 'Expected an action object')
    kind = action.get('type')
    native = None
    if kind in ('screenshot', 'wait') and set(action) == {'type'}:
        return None
    if (
        kind == 'click'
        and {'type', 'button', 'x', 'y'} <= set(action) <= {'type', 'button', 'x', 'y', 'keys'}
        and action.get('keys', []) == []
        and action['button'] == 'left'
    ):
        native = {k: action[k] for k in ('type', 'x', 'y')}
    elif kind == 'type' and set(action) == {'type', 'text'} and action['text'] == member:
        native = dict(action)
    elif (
        kind == 'keypress'
        and set(action) == {'type', 'keys'}
        and isinstance(action['keys'], list)
        and all(isinstance(k, str) for k in action['keys'])
    ):
        keys = [k.lower() for k in action['keys']]
        if keys == ['enter']:
            native = {'type': 'press', 'key': 'enter'}
        elif keys in (['ctrl', 'a'], ['control', 'a']):
            native = {'type': 'hotkey', 'keys': ['ctrl', 'a']}
    if native is None:
        raise DesktopError('invalid_action', 'Unsupported provider primitive')
    validate(native, 1280, 800)
    return native
