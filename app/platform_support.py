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
    from AppKit import NSApplication, NSApplicationPresentationFullScreen, NSWorkspace
    front=NSWorkspace.sharedWorkspace().frontmostApplication()
    if front is None or front.processIdentifier()==os.getpid():return False
    # 读取前台应用当前生效的系统全屏标志。填充窗口、自动隐藏 Dock／菜单栏
    # 都不等于全屏，不能再用窗口尺寸或屏幕安全区域推断。
    options=NSApplication.sharedApplication().currentSystemPresentationOptions()
    return bool(options & NSApplicationPresentationFullScreen)
