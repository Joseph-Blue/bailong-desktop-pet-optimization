import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from performance_metrics import (ProcessSnapshot, ProcessStatistics,
                                 process_paging_rows, linux_process_swap)


class ProcessMemoryTests(unittest.TestCase):
    def test_windows_private_commit_is_not_reported_as_disk_writes(self):
        with patch('performance_metrics.sys.platform', 'win32'):
            stats = ProcessStatistics()
        with patch.object(stats.process, 'memory_info', return_value=SimpleNamespace(rss=512, private=1024)), \
             patch('performance_metrics.psutil.swap_memory') as swap:
            snapshot = stats.read()
        swap.assert_not_called()
        self.assertEqual(snapshot.ram, 512)
        self.assertEqual(process_paging_rows(snapshot, 'win32'),
                         [('主进程私有提交', '1.0 KiB（仅供参考）')])

    def test_linux_current_swap_is_not_a_lifetime_event_counter(self):
        for value, expected in ((0, '当前无换出页'), (1024, '当前已换出 1.0 KiB')):
            self.assertEqual(process_paging_rows(ProcessSnapshot(at=0, process_swap=value), 'linux')[0][1], expected)
        with patch('performance_metrics.Path.read_text', return_value='Name:\tapp\nVmSwap:\t12 kB\n'):
            self.assertEqual(linux_process_swap(123), 12288)
        with patch('performance_metrics.Path.read_text', return_value='Name:\tapp\n'):
            with self.assertRaisesRegex(OSError, 'VmSwap'):
                linux_process_swap(123)

    def test_linux_collector_reads_own_process(self):
        with patch('performance_metrics.sys.platform', 'linux'):
            stats = ProcessStatistics()
        with patch('performance_metrics.linux_process_swap', return_value=2048) as swap, \
             patch('performance_metrics.psutil.swap_memory') as system_swap:
            snapshot = stats.read()
        swap.assert_called_once_with(stats.process.pid)
        system_swap.assert_not_called()
        self.assertEqual(snapshot.process_swap, 2048)

    def test_mac_reports_swapins_without_claiming_no_swapout(self):
        with patch('performance_metrics.sys.platform', 'darwin'), patch('performance_metrics.MacCounters') as mac:
            mac.return_value.memory.return_value = (100, 0, 1024)
            mac.return_value.gpu.return_value = (1, 0)
            snapshot = ProcessStatistics().read()
        self.assertEqual(process_paging_rows(snapshot, 'darwin')[0][1], '有换入记录 · 累计 1.0 KiB')
        self.assertEqual(process_paging_rows(ProcessSnapshot(at=0, swapins=0), 'darwin')[0][1], '暂无换入记录')
        self.assertEqual(process_paging_rows(ProcessSnapshot(at=0), 'darwin')[0][1], '系统未返回换入计数')

    def test_failed_queries_keep_errors(self):
        for platform in ('win32', 'linux'):
            with patch('performance_metrics.sys.platform', platform):
                stats = ProcessStatistics()
            with patch.object(stats.process, 'memory_info', side_effect=OSError('memory denied')), \
                 patch('performance_metrics.linux_process_swap', side_effect=OSError('swap denied')):
                snapshot = stats.read()
            self.assertIsNone(snapshot.private_commit)
            self.assertIsNone(snapshot.process_swap)
            self.assertIn('denied', process_paging_rows(snapshot, platform)[0][1])

    @unittest.skipUnless(sys.platform == 'win32', 'Windows process counters')
    def test_real_windows_process_counters(self):
        snapshot = ProcessStatistics().read()
        self.assertGreater(snapshot.private_commit, 0)
        self.assertGreater(snapshot.ram, 0)
        self.assertEqual(snapshot.memory_error, '')


if __name__ == '__main__':
    unittest.main()
