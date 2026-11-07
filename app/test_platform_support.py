import unittest,sys,os,tempfile
from pathlib import Path
from unittest.mock import patch
import platform_support as p

class PlatformTests(unittest.TestCase):
    @unittest.skipUnless(sys.platform=='darwin','需要 macOS 原生窗口')
    def test_mac_tool_window_collection_behavior(self):
        import objc
        from AppKit import (NSWindowCollectionBehaviorCanJoinAllSpaces,
                            NSWindowCollectionBehaviorMoveToActiveSpace,
                            NSWindowCollectionBehaviorFullScreenAuxiliary,
                            NSFloatingWindowLevel)
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import QApplication,QWidget
        app=QApplication.instance() or QApplication([])
        if app.platformName()!='cocoa':self.skipTest('需要 Qt Cocoa 平台插件')
        widget=QWidget(None,Qt.WindowType.FramelessWindowHint|Qt.WindowType.WindowStaysOnTopHint|Qt.WindowType.Tool)
        view=objc.objc_object(c_void_p=int(widget.winId()))
        window=view.window()
        original=(window.collectionBehavior() & ~NSWindowCollectionBehaviorCanJoinAllSpaces)|NSWindowCollectionBehaviorMoveToActiveSpace
        window.setCollectionBehavior_(original)
        window.setHidesOnDeactivate_(True)
        original_level=window.level()
        try:
            p.configure_mac_window(widget)
            self.assertFalse(window.hidesOnDeactivate())
            self.assertGreaterEqual(window.level(),max(original_level,NSFloatingWindowLevel))
            self.assertTrue(widget.testAttribute(Qt.WidgetAttribute.WA_MacAlwaysShowToolWindow))
            behavior=window.collectionBehavior()
            self.assertFalse(behavior & NSWindowCollectionBehaviorMoveToActiveSpace)
            self.assertTrue(behavior & NSWindowCollectionBehaviorCanJoinAllSpaces)
            self.assertTrue(behavior & NSWindowCollectionBehaviorFullScreenAuxiliary)
            self.assertEqual(behavior & original,original & ~NSWindowCollectionBehaviorMoveToActiveSpace)
            p.configure_mac_window(widget)
            self.assertEqual(window.collectionBehavior(),behavior)
        finally:
            widget.close()
    def test_mac_bundle_resources(self):
        with patch.object(sys,'platform','darwin'),patch.object(sys,'frozen',True,create=True),patch.object(sys,'executable','/Applications/BailongPet.app/Contents/MacOS/BailongPet'):
            self.assertEqual(p.resource_root(),Path(sys.executable).resolve().parents[1]/'Resources')
    def test_mac_user_data_outside_bundle(self):
        with patch.object(sys,'platform','darwin'),patch.dict(os.environ,{'BAILONG_DATA_DIR':''}):
            self.assertEqual(p.user_data(),Path.home()/'Library/Application Support/BailongPetOriginal')
    def test_mac_history_isolated_from_independent_port(self):
        from chat_backend import HistoryStore
        with tempfile.TemporaryDirectory() as folder,patch.object(sys,'platform','darwin'),patch.dict(os.environ,{'BAILONG_DATA_DIR':''}),patch.object(Path,'home',return_value=Path(folder)):
            legacy=Path(folder)/'Library/Application Support/BailongPet/conversations.json'
            legacy.parent.mkdir(parents=True)
            original='{"schemaVersion": 1, "conversations": []}'
            legacy.write_text(original)
            store=HistoryStore()
            self.assertEqual(store.conversations,[])
            self.assertNotEqual(store.path,legacy)
            store.new(folder)
            self.assertEqual(len(HistoryStore().conversations),1)
            self.assertEqual(legacy.read_text(),original)
    def test_explicit_data_directory_is_preserved(self):
        with patch.dict(os.environ,{'BAILONG_DATA_DIR':'/explicit/pet-data'}):
            self.assertEqual(p.user_data(),Path('/explicit/pet-data'))
    def test_mac_launch_does_not_use_windows_flags(self):
        import autostart
        with patch.object(sys,'platform','darwin'),patch('autostart.subprocess.Popen') as launch:
            autostart.launch_pet();self.assertNotIn('creationflags',launch.call_args.kwargs)

if __name__=='__main__':unittest.main()
