import os
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
import re
import unittest
from html import unescape

from PySide6.QtCore import QUrl
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QBoxLayout, QToolButton, QToolTip
from diagnostics import InfoSection, linked_details, resource_help
from performance_ui import Columns, configure_window

app = QApplication.instance() or QApplication([])


class PerformanceLayoutTests(unittest.TestCase):
    def test_long_hardware_and_process_lists_do_not_resize_columns(self):
        window = QWidget()
        configure_window(window)
        layout = QVBoxLayout(window)
        left, right = InfoSection('播放'), InfoSection('硬件与版本')
        left.set_rows([('当前动作', '待机动作04 · 贴贴枕头 · 播放')])
        processes = '、'.join(f'ChatGPT.exe · PID {n}' for n in range(13))
        right.set_rows([('GPU', 'OrayIddDriver Device、AicUsbDisplay Device、NVIDIA GeForce RTX 5090 D'),
                        ('桌面端', processes)], {'桌面端': 'ChatGPT.exe（13 个进程）'})
        columns = Columns(left, right)
        layout.addWidget(columns)
        try:
            window.resize(960, 440)
            window.show()
            app.processEvents()
            app.processEvents()
            self.assertEqual(columns.columns.direction(), QBoxLayout.Direction.LeftToRight)
            self.assertLessEqual(abs(left.width() - right.width()), 1)
            self.assertIn('PID 12', right.text())
            self.assertEqual(right.labels['桌面端'].text(), 'ChatGPT.exe（13 个进程）')
            self.assertIn('PID 12', right.labels['桌面端'].toolTip())
            self.assertIn('NVIDIA GeForce RTX 5090 D', right.labels['GPU'].toolTip())
            window.resize(480, 600)
            app.processEvents()
            app.processEvents()
            self.assertEqual(columns.columns.direction(), QBoxLayout.Direction.TopToBottom)
        finally:
            window.close()

    def test_paths_link_to_folders_and_escape_html(self):
        text = '内置 CLI 未启动\n候选可执行文件（启动时选择）：C:/工具 & test/bin/codex.exe\nGPU：<设备>'
        html = linked_details(text)
        self.assertIn('&lt;设备&gt;', html)
        link = unescape(re.search(r'href="([^"]+)"', html)[1])
        url = QUrl(link)
        self.assertTrue(url.isLocalFile())
        self.assertEqual(url.toLocalFile().replace('\\', '/'), 'C:/工具 & test/bin')
        self.assertNotIn('href="https', linked_details('错误：https://example.com'))

    def test_hover_text_preserves_full_literal_content(self):
        section = InfoSection('硬件')
        text = '<设备> & 显卡\nC:/some long path/driver.dll'
        section.set_rows([('GPU', text)], {'GPU': '独显'})
        tooltip = section.labels['GPU'].toolTip()
        self.assertIn('&lt;设备&gt; &amp; 显卡<br>', tooltip)
        self.assertIn('C:/some long path/driver.dll', tooltip)
        self.assertEqual(section.labels['GPU'].accessibleDescription(), text)

    def test_resource_help_only_on_windows_and_can_open_with_keyboard_action(self):
        for platform in ('win32', 'darwin', 'linux'):
            section = InfoSection('资源', resource_help(platform))
            button = section.findChild(QToolButton, 'resourceHelp')
            if platform == 'win32':
                self.assertIsNotNone(button)
                self.assertIn('运行内存 (RAM)', button.toolTip())
                self.assertIn('任务管理器', button.toolTip())
                self.assertIn('工作集（内存）', button.toolTip())
                section.show();app.processEvents();button.click()
                self.assertEqual(QToolTip.text(), button.toolTip())
                QToolTip.hideText()
            else:
                self.assertIsNone(button)
            section.close()


if __name__ == '__main__':
    unittest.main()
