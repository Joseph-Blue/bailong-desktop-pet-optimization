"""Read hardware names and desktop presence only while diagnostics are open."""
import ctypes as C
import json
from pathlib import Path
import shlex
import shutil
import sys
import re
from collections import Counter

import psutil
from PySide6.QtCore import QObject, QProcess, QTimer, Signal


def display_architecture(machine):
    return 'x86_64' if machine.lower() in ('amd64', 'x86_64', 'x64') else machine


def desktop_summary(status):
    entries = [re.fullmatch(r'(.+?) · PID (\d+)', entry) for entry in status.split('、')]
    if not all(entries):
        return status
    counts = Counter(entry[1] for entry in entries)
    return ' · '.join(f'{name}（{count} 个进程）' for name, count in counts.items())


def cpu_model():
    if sys.platform == 'darwin':
        lib = C.CDLL('/usr/lib/libSystem.B.dylib', use_errno=True)
        lib.sysctlbyname.argtypes = [C.c_char_p, C.c_void_p, C.POINTER(C.c_size_t), C.c_void_p, C.c_size_t]
        lib.sysctlbyname.restype = C.c_int
        size = C.c_size_t()
        key = b'machdep.cpu.brand_string'
        if lib.sysctlbyname(key, None, C.byref(size), None, 0):
            raise OSError(C.get_errno(), '无法读取 CPU 型号')
        value = C.create_string_buffer(size.value)
        if lib.sysctlbyname(key, value, C.byref(size), None, 0):
            raise OSError(C.get_errno(), '无法读取 CPU 型号')
        return value.value.decode('utf-8')
    if sys.platform.startswith('linux'):
        fields = dict(line.split(':', 1) for line in Path('/proc/cpuinfo').read_text().splitlines() if ':' in line)
        fields = {key.strip(): value.strip() for key, value in fields.items()}
        return fields.get('model name') or fields.get('Hardware') or '系统未提供 CPU 型号'
    return '读取中'


def parse_hardware(output, platform_name):
    if platform_name == 'darwin':
        data = json.loads(output)
        models = [v.get('sppci_model') or v.get('_name') for v in data.get('SPDisplaysDataType', [])]
        return None, '、'.join(dict.fromkeys(v for v in models if v)) or '系统未提供 GPU 型号'
    if platform_name == 'win32':
        data = json.loads(output.lstrip('\ufeff'))
        gpu = data.get('gpu') or []
        if isinstance(gpu, str):gpu = [gpu]
        return data.get('cpu') or '系统未提供 CPU 型号', '、'.join(dict.fromkeys(gpu)) or '系统未提供 GPU 型号'
    models = []
    for line in output.splitlines():
        fields = shlex.split(line)
        if len(fields) >= 4 and fields[1] in ('VGA compatible controller', '3D controller', 'Display controller'):
            models.append(fields[2] + ' ' + fields[3])
    return None, '、'.join(dict.fromkeys(models)) or '系统未提供 GPU 型号'


class HardwareProbe(QObject):
    changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cpu = self.gpu = '读取中'
        self.loaded = False
        self.cancelled = False
        self.process = QProcess(self)
        self.process.finished.connect(self.finished)
        self.process.errorOccurred.connect(self.failed)
        self.timeout = QTimer(self);self.timeout.setSingleShot(True)
        self.timeout.setInterval(10000);self.timeout.timeout.connect(self.timed_out)

    def start(self):
        if self.loaded or self.process.state() != QProcess.ProcessState.NotRunning:return
        self.cancelled = False
        try:self.cpu = cpu_model()
        except OSError as error:self.cpu = f'读取失败：{error}'
        if sys.platform == 'darwin':
            command = ['/usr/sbin/system_profiler', '-json', 'SPDisplaysDataType']
        elif sys.platform == 'win32':
            command = ['powershell.exe', '-NoProfile', '-NonInteractive', '-Command',
                       '[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new(); '
                       '[pscustomobject]@{cpu=((Get-CimInstance Win32_Processor | Select-Object -First 1).Name); '
                       'gpu=@(Get-CimInstance Win32_VideoController | ForEach-Object {$_.Name})} | ConvertTo-Json -Compress']
        else:
            executable = shutil.which('lspci')
            if not executable:
                self.gpu = '未提供（未安装 lspci）';self.loaded = True;self.changed.emit();return
            command = [executable, '-mm']
        self.gpu = '读取中';self.changed.emit()
        self.timeout.start();self.process.start(command[0], command[1:])

    def finished(self, code, status):
        self.timeout.stop()
        if self.cancelled:return
        if code != 0 or status != QProcess.ExitStatus.NormalExit:
            self.gpu = f'读取失败：硬件查询退出码 {code}'
        else:
            try:
                cpu, self.gpu = parse_hardware(bytes(self.process.readAllStandardOutput()).decode('utf-8'), sys.platform)
                if cpu:self.cpu = cpu
                self.loaded = True
            except (ValueError, TypeError, KeyError) as error:
                self.gpu = f'读取失败：硬件型号数据格式错误（{type(error).__name__}）'
        if sys.platform == 'win32' and not self.loaded:self.cpu = self.gpu
        self.changed.emit()

    def failed(self, error):
        if self.cancelled:return
        self.timeout.stop()
        self.gpu = '读取失败：' + self.process.errorString()
        if sys.platform == 'win32':self.cpu = self.gpu
        self.changed.emit()

    def timed_out(self):
        self.stop();self.gpu = '读取失败：硬件查询超时'
        if sys.platform == 'win32':self.cpu = self.gpu
        self.changed.emit()

    def stop(self):
        self.timeout.stop();self.cancelled = True
        if self.process.state() != QProcess.ProcessState.NotRunning:self.process.kill()


def desktop_status():
    if sys.platform == 'darwin':
        from AppKit import NSWorkspace
        apps = NSWorkspace.sharedWorkspace().runningApplications()
        matches = [f'{app.localizedName()} · PID {app.processIdentifier()}' for app in apps
                   if app.bundleIdentifier() in ('com.openai.codex', 'com.openai.chat')]
        return '、'.join(matches) or '未运行'
    if sys.platform == 'win32':
        matches = []
        for process in psutil.process_iter(['pid', 'name']):
            if (process.info['name'] or '').lower() not in ('chatgpt.exe', 'codex.exe'):continue
            try:
                executable = process.exe().lower().replace('\\', '/')
                if '/windowsapps/openai.' in executable and '/resources/' not in executable:
                    matches.append(f'{process.info["name"]} · PID {process.pid}')
            except psutil.NoSuchProcess:continue
            except psutil.AccessDenied:return '读取失败：无法核对桌面应用路径'
        return '、'.join(matches) or '未识别到 Microsoft Store 桌面应用'
    return '当前平台未接入桌面端识别'


def cli_status(pet):
    worker = pet.chat.worker if pet.chat else None
    session = getattr(worker, 'session', None)
    process = getattr(session, 'process', None)
    if process is not None and process.poll() is None:
        state = '会话已就绪' if session.initialized else '会话未就绪'
        try:path = psutil.Process(process.pid).exe()
        except psutil.Error as error:path = f'读取失败：{error}'
        return f'内置 CLI 进程运行中 · PID {process.pid} · {state}\n实际可执行文件：{path}'
    from quota import find_codex
    try:path = find_codex()
    except RuntimeError as error:return f'内置 CLI 未启动\n可执行文件：{error}'
    return f'内置 CLI 未启动\n候选可执行文件（启动时选择）：{path}'
