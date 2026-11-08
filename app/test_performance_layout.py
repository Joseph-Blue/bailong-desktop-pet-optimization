import os
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
import re
import unittest
from html import unescape

from PySide6.QtCore import QUrl
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QBoxLayout
from diagnostics import InfoSection, linked_details
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


if __name__ == '__main__':
    unittest.main()
