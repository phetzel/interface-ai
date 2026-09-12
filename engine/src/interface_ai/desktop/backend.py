"""The only module that emits OS input. X11 capture stays in memory."""
import sys


class X11Backend:
    def __init__(self):
        if sys.platform != 'linux' or sys.byteorder != 'little':
            raise RuntimeError('This adapter requires the tested little-endian Linux X11 desktop')
        import pyautogui
        from Xlib.display import Display
        self.gui = pyautogui
        self.gui.PAUSE = 0.01
        self.display = Display()
        self.root = self.display.screen().root
        if self.root.get_geometry().depth != 24:
            raise RuntimeError('Expected a 24-bit X11 framebuffer')

    def size(self):
        geometry = self.root.get_geometry()
        return geometry.width, geometry.height

    def active_window(self):
        from Xlib import Xatom
        prop = self.root.get_full_property(self.display.intern_atom('_NET_ACTIVE_WINDOW'), Xatom.WINDOW)
        return int(prop.value[0]) if prop is not None and len(prop.value) else 0

    def screenshot(self):
        from Xlib import X
        from PIL import Image
        width, height = self.size()
        pixels = self.root.get_image(0, 0, width, height, X.ZPixmap, 0xffffffff)
        return Image.frombytes('RGB', (width, height), pixels.data, 'raw', 'BGRX')

    def click(self, x, y):
        self.gui.click(x, y)

    def move(self, x, y):
        self.gui.moveTo(x, y)

    def type_character(self, character):
        self.gui.write(character)

    def key_down(self, key):
        self.gui.keyDown(key)

    def key_up(self, key):
        # Cleanup must remain possible after stop, deadline, or fail-safe trips.
        saved = self.gui.FAILSAFE
        self.gui.FAILSAFE = False
        try:
            self.gui.keyUp(key, _pause=False)
        finally:
            self.gui.FAILSAFE = saved

    def scroll(self, amount):
        self.gui.scroll(amount)

    def close(self):
        self.display.close()
