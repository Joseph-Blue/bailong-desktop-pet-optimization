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
                        NSWindowCollectionBehaviorFullScreenPrimary,
                        NSWindowCollectionBehaviorFullScreenAuxiliary,
                        NSWindowCollectionBehaviorFullScreenNone,
                        NSFloatingWindowLevel)
    view=objc.objc_object(c_void_p=int(widget.winId()))
    window=view.window()
    # Also update already-created NSPanel instances: changing the Qt attribute
    # after winId()/show() does not update hidesOnDeactivate in Qt 6.9.2.
    window.setHidesOnDeactivate_(False)
    window.setLevel_(max(window.level(),NSFloatingWindowLevel))
    # 参照原生工程 Pet.swift / Bubble.swift / ChatComposer.swift：普通桌面共享，
    # 但不作为辅助窗口跟入全屏空间。清除 Qt 原有的冲突标志，保留其他行为。
    excluded=(NSWindowCollectionBehaviorMoveToActiveSpace|
              NSWindowCollectionBehaviorFullScreenPrimary|NSWindowCollectionBehaviorFullScreenAuxiliary)
    behavior=window.collectionBehavior() & ~excluded
    window.setCollectionBehavior_(behavior|NSWindowCollectionBehaviorCanJoinAllSpaces|NSWindowCollectionBehaviorFullScreenNone)

def mac_fullscreen():
    import Quartz as q
    from AppKit import NSScreen, NSWorkspace
    from desktop_visibility import covers_monitor
    front=NSWorkspace.sharedWorkspace().frontmostApplication()
    if front is None or front.processIdentifier()==os.getpid():return False
    screens=NSScreen.screens()
    if not screens:return False
    # 与原生工程 PetController.checkDesktop 一致：AppKit 屏幕坐标转换到
    # Quartz 坐标，使用完整 frame，不扣刘海安全区，也不使用填充对应的 visibleFrame。
    top=screens[0].frame().origin.y+screens[0].frame().size.height
    monitors=[]
    for screen in screens:
        frame=screen.frame()
        x,y,width,height=frame.origin.x,frame.origin.y,frame.size.width,frame.size.height
        monitors.append((x,top-y-height,x+width,top-y))
    windows=q.CGWindowListCopyWindowInfo(q.kCGWindowListOptionOnScreenOnly|q.kCGWindowListExcludeDesktopElements,q.kCGNullWindowID) or []
    for window in windows:
        if window.get(q.kCGWindowOwnerPID)!=front.processIdentifier() or window.get(q.kCGWindowLayer)!=0:continue
        bounds=window[q.kCGWindowBounds]
        rect=(bounds['X'],bounds['Y'],bounds['X']+bounds['Width'],bounds['Y']+bounds['Height'])
        if any(covers_monitor(rect,monitor) for monitor in monitors):return True
    return False
