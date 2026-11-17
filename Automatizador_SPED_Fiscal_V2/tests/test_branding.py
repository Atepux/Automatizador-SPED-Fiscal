import struct
import tkinter as tk
import unittest

from app.branding import ICON, apply_icon, configure_taskbar, create_toplevel


class BrandingTests(unittest.TestCase):
    def test_official_ico_contains_images(self):
        reserved, kind, count = struct.unpack('<HHH', ICON.read_bytes()[:6])
        self.assertEqual((reserved, kind), (0, 1))
        self.assertGreater(count, 0)

    def test_main_and_secondary_window_icons(self):
        configure_taskbar()
        root = tk.Tk()
        root.withdraw()
        try:
            apply_icon(root)
            child = create_toplevel(root)
            child.withdraw()
            root.deiconify();child.deiconify();root.update()
            import win32gui, win32con
            for window in (root, child):
                hwnd = win32gui.GetParent(window.winfo_id())
                self.assertTrue(win32gui.SendMessage(hwnd, win32con.WM_GETICON, 1, 0))
        finally:
            root.destroy()
