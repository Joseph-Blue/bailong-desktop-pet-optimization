import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from diagnostic_identity import parse_hardware, cli_status, display_architecture, desktop_summary


class IdentityTests(unittest.TestCase):
    def test_architecture_aliases_have_consistent_display(self):
        for machine in ('AMD64', 'amd64', 'x64', 'x86_64'):
            self.assertEqual(display_architecture(machine), 'x86_64')
        self.assertEqual(display_architecture('arm64'), 'arm64')

    def test_desktop_processes_are_grouped_without_hiding_errors(self):
        status = 'ChatGPT.exe · PID 1、ChatGPT.exe · PID 2、Codex.exe · PID 3'
        self.assertEqual(desktop_summary(status), 'ChatGPT.exe（2 个进程） · Codex.exe（1 个进程）')
        self.assertEqual(desktop_summary('读取失败：无法核对桌面应用路径'), '读取失败：无法核对桌面应用路径')

    def test_mac_gpu_model_without_display_details(self):
        output = json.dumps({'SPDisplaysDataType': [
            {'sppci_model': 'Apple M5 Pro', 'spdisplays_ndrvs': [{'serial': 'not-for-display'}]},
            {'sppci_model': 'Apple M5 Pro'}]})
        self.assertEqual(parse_hardware(output, 'darwin'), (None, 'Apple M5 Pro'))

    def test_windows_cpu_and_multiple_gpus(self):
        output = json.dumps({'cpu': 'Example CPU', 'gpu': ['GPU A', 'GPU B']})
        self.assertEqual(parse_hardware(output, 'win32'), ('Example CPU', 'GPU A、GPU B'))

    def test_discrete_gpu_precedes_virtual_and_integrated_adapters(self):
        output = json.dumps({'cpu': 'Example CPU', 'gpu': [
            'OrayIddDriver Device', 'AicUsbDisplay Device', 'Intel UHD Graphics',
            'NVIDIA GeForce RTX 5090 D', 'NVIDIA GeForce RTX 5090 D']})
        _, names = parse_hardware(output, 'win32')
        self.assertEqual(names.split('、'), ['NVIDIA GeForce RTX 5090 D', 'Intel UHD Graphics',
                                             'OrayIddDriver Device', 'AicUsbDisplay Device'])

    def test_linux_filters_non_display_devices(self):
        output = ('00:02.0 "VGA compatible controller" "Example Vendor" "GPU A"\n'
                  '00:03.0 "Audio device" "Other Vendor" "Audio"\n')
        self.assertEqual(parse_hardware(output, 'linux'), (None, 'Example Vendor GPU A'))

    def test_discrete_amd_and_intel_names_do_not_promote_integrated_models(self):
        for integrated, discrete in (('AMD Radeon RX Vega 11 Graphics', 'AMD Radeon RX 7900 XTX'),
                                     ('Intel Arc A140V', 'Intel Arc B580')):
            _, names = parse_hardware(json.dumps({'gpu': [integrated, discrete]}), 'win32')
            self.assertEqual(names.split('、'), [discrete, integrated])

    def test_no_cli_does_not_claim_candidate_is_running(self):
        pet = SimpleNamespace(chat=None)
        with patch('quota.find_codex', return_value='/candidate/codex'):
            result = cli_status(pet)
        self.assertIn('未启动', result)
        self.assertIn('候选可执行文件', result)

    def test_live_cli_uses_real_process_not_resolver(self):
        process = SimpleNamespace(pid=123, poll=lambda: None)
        session = SimpleNamespace(process=process, initialized=True)
        pet = SimpleNamespace(chat=SimpleNamespace(worker=SimpleNamespace(session=session)))
        with patch('diagnostic_identity.psutil.Process') as lookup, patch('quota.find_codex') as resolver:
            lookup.return_value.exe.return_value = '/actual/codex'
            result = cli_status(pet)
            resolver.assert_not_called()
        self.assertIn('PID 123', result)
        self.assertIn('会话已就绪', result)
        self.assertIn('/actual/codex', result)

    def test_exited_cli_does_not_report_live_connection(self):
        session = SimpleNamespace(process=SimpleNamespace(poll=lambda: 1))
        pet = SimpleNamespace(chat=SimpleNamespace(worker=SimpleNamespace(session=session)))
        with patch('quota.find_codex', side_effect=RuntimeError('未找到')):
            self.assertIn('未启动', cli_status(pet))


if __name__ == '__main__':
    unittest.main()
