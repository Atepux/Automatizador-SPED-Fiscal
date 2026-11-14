from pathlib import Path
import sys
if not getattr(sys,'frozen',False):sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.runtime import command,RESOURCES,DATA
from app.win_focus import allow_foreground,focus_window
