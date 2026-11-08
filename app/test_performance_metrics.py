import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from performance_metrics import (ProcessSnapshot, ProcessStatistics,
                                 system_memory_text, windows_commit_memory)


class SystemMemoryTests(unittest.TestCase):
    def test_windows_queries_commit_not_swap(self):
        with patch('performance_metrics.sys.platform', 'win32'):
            stats = ProcessStatistics()
        with patch('performance_metrics.windows_commit_memory', return_value=(1024, 4096)), \
             patch('performance_metrics.psutil.swap_memory') as swap:
            snapshot = stats.read()
        swap.assert_not_called()
        self.assertEqual((snapshot.system_commit, snapshot.system_commit_limit), (1024, 4096))
        self.assertEqual(system_memory_text(snapshot, 'win32'),
                         '系统虚拟内存（已提交 / 上限）1.0 KiB / 4.0 KiB')

    def test_linux_and_mac_query_swap(self):
        for platform in ('linux', 'darwin'):
            with self.subTest(platform=platform):
                with patch('performance_metrics.sys.platform', platform), \
                     patch('performance_metrics.MacCounters') as mac:
                    mac.return_value.memory.return_value = (100, 0, 0)
                    mac.return_value.gpu.return_value = (1, 0)
                    stats = ProcessStatistics()
                with patch('performance_metrics.psutil.swap_memory', return_value=SimpleNamespace(used=1024, total=8192)), \
                     patch('performance_metrics.windows_commit_memory') as commit:
                    snapshot = stats.read()
                commit.assert_not_called()
                self.assertEqual(system_memory_text(snapshot, platform),
                                 '系统 Swap（已用 / 总量）1.0 KiB / 8.0 KiB')

    def test_failed_queries_are_not_reported_as_zero(self):
        with patch('performance_metrics.sys.platform', 'win32'):
            stats = ProcessStatistics()
        with patch('performance_metrics.windows_commit_memory', side_effect=OSError('denied')):
            snapshot = stats.read()
        self.assertIsNone(snapshot.system_commit)
        self.assertIn('denied', system_memory_text(snapshot, 'win32'))

    @unittest.skipUnless(sys.platform == 'win32', 'Windows API smoke test')
    def test_real_windows_commit_counters(self):
        used, limit = windows_commit_memory()
        self.assertGreater(used, 0)
        self.assertGreaterEqual(limit, used)


if __name__ == '__main__':
    unittest.main()
