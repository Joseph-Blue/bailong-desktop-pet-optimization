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
    if sys.platform.startswith('linux'):
        return Path(os.environ.get('XDG_DATA_HOME') or Path.home()/'.local/share')/'BailongPet'
    return Path(os.environ.get('LOCALAPPDATA') or Path.home()/'.local/share')/'BailongPet'

def state_root():
    return user_data() if sys.platform=='darwin' or sys.platform.startswith('linux') else resource_root()

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
    import Quartz as q
    from AppKit import NSScreen, NSWorkspace
    from desktop_visibility import covers_monitor
    front=NSWorkspace.sharedWorkspace().frontmostApplication()
    if front is None or front.processIdentifier()==os.getpid():return False
    pid=front.processIdentifier()
    monitors=[]
    for screen in NSScreen.screens():
        r=q.CGDisplayBounds(screen.deviceDescription()['NSScreenNumber'])
        insets=screen.safeAreaInsets()
        # 刘海屏的系统全屏窗口位于安全区域内；Quartz 坐标的 Y 轴向下。
        # 不用 visibleFrame，避免把普通保留菜单栏和 Dock 的最大化窗口当成全屏。
        monitors.append((r.origin.x+insets.left,r.origin.y+insets.top,
                         r.origin.x+r.size.width-insets.right,r.origin.y+r.size.height-insets.bottom))
    for w in q.CGWindowListCopyWindowInfo(q.kCGWindowListOptionOnScreenOnly|q.kCGWindowListExcludeDesktopElements,q.kCGNullWindowID) or []:
        if w.get(q.kCGWindowOwnerPID)!=pid or w.get(q.kCGWindowLayer)!=0:continue
        b=w[q.kCGWindowBounds];r=(b['X'],b['Y'],b['X']+b['Width'],b['Y']+b['Height'])
        # 同一应用的工具栏、浮层可排在全屏主窗口前，必须继续检查后续窗口。
        if any(covers_monitor(r,m) for m in monitors):return True
    return False
