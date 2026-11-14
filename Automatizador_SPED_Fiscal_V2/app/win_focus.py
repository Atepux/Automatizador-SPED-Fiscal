"""Ativacao verificada, sem teclas sinteticas e sem cliques de tentativa."""
import time


def allow_foreground(pid):
    import ctypes
    try:return bool(ctypes.windll.user32.AllowSetForegroundWindow(int(pid)))
    except (AttributeError,OSError):return False


def focus_window(hwnd,gui=None,process=None,current_thread=None,clock=time.monotonic,sleep=time.sleep):
    if gui is None:import win32gui as gui
    if process is None:import win32process as process
    if current_thread is None:
        import win32api
        current_thread=win32api.GetCurrentThreadId()
    if gui.IsIconic(hwnd):gui.ShowWindow(hwnd,9)
    if gui.GetForegroundWindow()==hwnd:return
    try:gui.SetForegroundWindow(hwnd)
    except Exception:pass
    def confirmed(timeout):
        until=clock()+timeout
        while clock()<until:
            if gui.GetForegroundWindow()==hwnd:return True
            sleep(.025)
        return gui.GetForegroundWindow()==hwnd
    if confirmed(.35):return
    foreground=gui.GetForegroundWindow();attached=False
    try:
        other=process.GetWindowThreadProcessId(foreground)[0] if foreground else current_thread
        if other!=current_thread:
            process.AttachThreadInput(current_thread,other,True);attached=True
        gui.BringWindowToTop(hwnd);gui.SetForegroundWindow(hwnd)
    finally:
        if attached:process.AttachThreadInput(current_thread,other,False)
    if not confirmed(1.5):raise RuntimeError('foco_nao_confirmado')
