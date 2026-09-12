import json
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace

from interface_ai.desktop import Desktop, DesktopError


class Backend:
    def __init__(self):
        self.calls = []
        self.window = 9
        self.dimensions = (1280, 800)
        self.hook = lambda: None
    def size(self): return self.dimensions
    def active_window(self): return self.window
    def screenshot(self): return SimpleNamespace(size=self.dimensions)
    def close(self): pass
    def record(self, *args):
        self.calls.append(args)
        self.hook()
    def click(self, x, y): self.record('click', x, y)
    def move(self, x, y): self.record('move', x, y)
    def type_character(self, text): self.record('type', text)
    def key_down(self, key): self.record('down', key)
    def key_up(self, key): self.calls.append(('up', key))
    def scroll(self, amount): self.record('scroll', amount)


class DesktopTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.stop = self.root / 'STOP'
        self.current = {'id': 'session-a', 'width': 1280, 'height': 800, 'windowId': 9, 'mode': 'native'}
        self.backend = Backend()
        self.events = []
    def desktop(self, **kwargs):
        return Desktop(backend=self.backend, session_reader=lambda: dict(self.current),
                       stop_path=self.stop, lock_path=self.root / 'lock', event_sink=self.events.append, **kwargs)
    def assert_code(self, code, operation):
        with self.assertRaises(DesktopError) as error: operation()
        self.assertEqual(error.exception.code, code)

    def test_all_invalid_arguments_rejected_before_input(self):
        actions = [None, {}, {'type':'shell','text':'echo hi'}, {'type':'click','x':-1,'y':2},
                   {'type':'click','x':1280,'y':2}, {'type':'move','x':2,'y':800},
                   {'type':'click','x':True,'y':2}, {'type':'click','x':1.5,'y':2},
                   {'type':'click','x':2,'y':2,'extra':0}, {'type':'type','text':''},
                   {'type':'type','text':'x'*257}, {'type':'type','text':'\n'},
                   {'type':'type','text':'é'}, {'type':'hotkey','keys':['ctrl','invalid']},
                   {'type':'hotkey','keys':['ctrl','ctrl']}, {'type':'press','key':[]},
                   {'type':'scroll','amount':0}, {'type':'scroll','amount':True}, {'type':'scroll','amount':21}]
        with self.desktop() as desktop:
            for action in actions:
                with self.subTest(action=action): self.assert_code('invalid_action', lambda: desktop.execute(action))
        self.assertEqual(self.backend.calls, [])

    def test_typing_and_events_omit_input(self):
        with self.desktop() as desktop:
            desktop.type_text('sensitive-sentinel')
            desktop.click(100, 200)
        self.assertEqual(''.join(call[1] for call in self.backend.calls if call[0]=='type'), 'sensitive-sentinel')
        self.assertNotIn('sensitive-sentinel', json.dumps(self.events))
        self.assertEqual([event['action'] for event in self.events], ['type','click'])

    def test_stop_before_action_but_observation_allowed(self):
        self.stop.touch()
        with self.desktop() as desktop:
            self.assertEqual(desktop.screenshot().size, (1280,800))
            self.assert_code('stopped',lambda: desktop.click(2,2))
        self.assertEqual(self.backend.calls, [])

    def test_stop_interrupts_typing_between_characters(self):
        self.backend.hook = self.stop.touch
        with self.desktop() as desktop:
            self.assert_code('stopped', lambda: desktop.type_text('00123'))
        self.assertEqual(self.backend.calls, [('type','0')])

    def test_hotkey_stop_releases_pressed_modifier(self):
        self.backend.hook = self.stop.touch
        with self.desktop() as desktop:
            self.assert_code('stopped', lambda: desktop.hotkey('ctrl','a'))
        self.assertEqual(self.backend.calls, [('down','ctrl'),('up','ctrl')])

    def test_hotkey_backend_failure_also_releases(self):
        def fail(): raise OSError('synthetic failure')
        self.backend.hook = fail
        with self.desktop() as desktop:
            self.assert_code('input_failed', lambda: desktop.hotkey('shift','end'))
        self.assertEqual(self.backend.calls, [('down','shift'),('up','shift')])

    def test_focus_change_rejects_input(self):
        with self.desktop() as desktop:
            self.backend.window = 42
            self.assert_code('unexpected_focus', lambda: desktop.click(2,2))
        self.assertEqual(self.backend.calls, [])

    def test_reset_rejects_old_session_actions(self):
        with self.desktop() as desktop:
            self.current['id'] = 'session-b'
            self.assert_code('stale_session', lambda: desktop.click(2,2))
        self.assertEqual(self.backend.calls, [])

    def test_explicit_stale_id_fails_at_construction(self):
        for session_id in ['old', '']:
            self.assert_code('stale_session', lambda: self.desktop(session_id=session_id))
        self.assertEqual(self.backend.calls, [])

    def test_deadline_during_typing(self):
        now = [0]
        def advance(): now[0] += 2
        self.backend.hook = advance
        with self.desktop(timeout=1, clock=lambda: now[0]) as desktop:
            self.assert_code('deadline', lambda: desktop.type_text('abc'))
        self.assertEqual(self.backend.calls, [('type','a')])

    def test_display_change_rejects_input(self):
        with self.desktop() as desktop:
            self.backend.dimensions = (1024,768)
            self.assert_code('display_changed', lambda: desktop.click(2,2))
        self.assertEqual(self.backend.calls, [])

    def test_second_controller_rejected_and_lock_released(self):
        with self.desktop() as owner:
            self.assert_code('busy', lambda: self.desktop().__enter__())
            owner.click(1,1)
        with self.desktop() as next_owner: next_owner.click(2,2)
        self.assertEqual(len(self.backend.calls),2)

    def test_missing_checkpoint_has_bounded_timeout(self):
        with self.desktop() as desktop:
            self.assert_code('checkpoint_timeout',lambda: desktop.wait('missing',lambda:False,timeout=.01))

    def test_backend_failure_is_not_retried(self):
        def fail(): raise OSError('synthetic failure')
        self.backend.hook = fail
        with self.desktop() as desktop:
            self.assert_code('input_failed',lambda:desktop.click(2,2))
        self.assertEqual(len(self.backend.calls),1)

    def test_invalid_deadlines_rejected(self):
        for value in [0, -1, 121, True, float('inf'), float('nan')]:
            self.assert_code('invalid_deadline',lambda:self.desktop(timeout=value))


if __name__ == '__main__': unittest.main()
