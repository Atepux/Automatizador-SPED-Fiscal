"""Identidade visual Windows, sem acesso ao PVA ou aos cadastros."""
import ctypes
import sys

from .runtime import RESOURCES

ICON = RESOURCES / 'recursos' / 'SPED_Minimalista.ico'
APP_ID = 'Atepux.AutomatizadorSPEDFiscal.V2'


def configure_taskbar():
    """Definir a identidade antes de criar a primeira janela Windows."""
    if sys.platform == 'win32':
        result = ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)
        if result:
            raise OSError(result, 'Nao foi possivel configurar a identidade visual')


def apply_icon(window):
    """Aplicar o icone e herda-lo nas futuras janelas secundarias Tk."""
    window.iconbitmap(default=str(ICON))
    window.iconbitmap(str(ICON))


def create_toplevel(parent):
    import tkinter as tk
    window = tk.Toplevel(parent)
    apply_icon(window)
    return window
