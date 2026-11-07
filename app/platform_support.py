"""Platform paths and optional macOS desktop integration."""
import os
import sys
from pathlib import Path

def resource_root():
    if not getattr(sys,'frozen',False):return Path(__file__).resolve().parents[1]
    executable=Path(sys.executable).resolve()
    return executable.parents[1]/'Resources' if sys.platform=='darwin' else executable.parent

def user_data():
    if os.environ.get('BAILONG_DATA_DIR'):return Path(os.environ['BAILONG_DATA_DIR'])
    # The independent Python macOS port owns BailongPet and uses a different
    # history schema. Never read or overwrite that application's data here.
    if sys.platform=='darwin':return Path.home()/'Library/Application Support/BailongPetOriginal'
    return Path(os.environ.get('LOCALAPPDATA') or Path.home()/'.local/share')/'BailongPet'

def state_root():
    return user_data() if sys.platform=='darwin' else resource_root()

def configure_mac_window(widget):
    if sys.platform!='darwin':return
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication
    widget.setAttribute(Qt.WidgetAttribute.WA_MacAlwaysShowToolWindow)
    if QApplication.platformName()!='cocoa':return
    import objc
    from AppKit import (NSWindowCollectionBehaviorCanJoinAllSpaces,
                        NSWindowCollectionBehaviorMoveToActiveSpace,
                        NSWindowCollectionBehaviorFullScreenAuxiliary,
                        NSFloatingWindowLevel)
    view=objc.objc_object(c_void_p=int(widget.winId()))
    window=view.window()
    # Also update already-created NSPanel instances: changing the Qt attribute
    # after winId()/show() does not update hidesOnDeactivate in Qt 6.9.2.
    window.setHidesOnDeactivate_(False)
    window.setLevel_(max(window.level(),NSFloatingWindowLevel))
    # Qt tool windows can start with MoveToActiveSpace. AppKit rejects
    # combining it with CanJoinAllSpaces; retain unrelated Qt flags.
    behavior=window.collectionBehavior() & ~NSWindowCollectionBehaviorMoveToActiveSpace
    window.setCollectionBehavior_(behavior|NSWindowCollectionBehaviorCanJoinAllSpaces|NSWindowCollectionBehaviorFullScreenAuxiliary)

def mac_fullscreen():
    try:
        import Quartz as q
        from AppKit import NSWorkspace
        front=NSWorkspace.sharedWorkspace().frontmostApplication()
        pid=front.processIdentifier()
        if pid==os.getpid():return False
        from desktop_visibility import covers_monitor
        displays=q.CGGetActiveDisplayList(32,None,None)[1]
        monitors=[]
        for display in displays:
            r=q.CGDisplayBounds(display);monitors.append((r.origin.x,r.origin.y,r.origin.x+r.size.width,r.origin.y+r.size.height))
        for w in q.CGWindowListCopyWindowInfo(q.kCGWindowListOptionOnScreenOnly|q.kCGWindowListExcludeDesktopElements,q.kCGNullWindowID) or []:
            if w.get(q.kCGWindowOwnerPID)!=pid or w.get(q.kCGWindowLayer)!=0:continue
            b=w[q.kCGWindowBounds];r=(b['X'],b['Y'],b['X']+b['Width'],b['Y']+b['Height'])
            return any(covers_monitor(r,m) for m in monitors)
    except (ImportError,AttributeError,KeyError,TypeError):pass
    return False
