"""Qt port of the Swift pet's on-demand performance window."""
from collections import deque
import math
import os
import platform
import sys
import time
import psutil

from PySide6.QtCore import Qt, QTimer, QPointF, QRectF
from PySide6.QtGui import QFont, QPainter, QPainterPath, QPalette, QPen
from PySide6.QtWidgets import (QApplication, QWidget, QLabel, QVBoxLayout,
                               QHBoxLayout, QScrollArea, QPushButton, QCheckBox)

from performance_metrics import (PlaybackStatistics, ProcessStatistics,
                                 byte_text, frame_cache_statistics)
from version import VERSION


class FPSGraph(QWidget):
    def __init__(self):
        super().__init__()
        self.values = deque(maxlen=60)
        self.setMinimumHeight(100)
        self.setAccessibleName('最近 60 次 FPS 采样，每秒一次')

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        palette = self.palette()
        painter.fillRect(self.rect(), palette.brush(QPalette.ColorRole.Base))
        plot = QRectF(self.rect()).adjusted(12, 22, -12, -24)
        ceiling = max(30, math.ceil(max(self.values, default=0) / 10) * 10)
        painter.setPen(palette.color(QPalette.ColorRole.Mid))
        for step in range(3):
            y = plot.bottom() - plot.height() * step / 2
            painter.drawLine(QPointF(plot.left(), y), QPointF(plot.right(), y))
        painter.setPen(palette.color(QPalette.ColorRole.Text))
        painter.drawText(12, 15, f'{ceiling} FPS')
        painter.drawText(12, self.height() - 5, '最近 60 次采样 · 每秒一次')
        path = QPainterPath()
        for index, value in enumerate(self.values):
            point = QPointF(plot.left() + plot.width() * index / 59,
                            plot.bottom() - plot.height() * value / ceiling)
            if index == 0:
                path.moveTo(point)
            else:
                path.lineTo(point)
        painter.setPen(QPen(palette.color(QPalette.ColorRole.Highlight), 2))
        painter.drawPath(path)


class DiagnosticsWindow(QWidget):
    def __init__(self, pet, root):
        super().__init__(None, Qt.WindowType.Window)
        self.pet = pet
        self.root = root
        self.setWindowTitle('应用性能信息统计')
        self.setWindowIcon(pet.windowIcon())
        self.resize(500, 700)
        self.setMinimumSize(440, 360)
        self.changing_pin = False
        self.statistics = ProcessStatistics()
        self.frames = PlaybackStatistics(time.monotonic())
        self.previous = None
        self.decoder_previous = None
        self.disk_cache = ''
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.sample)
        QApplication.instance().aboutToQuit.connect(self.timer.stop)

        outer = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        body = QWidget()
        content = QVBoxLayout(body)
        content.setSpacing(12)
        metrics = QHBoxLayout()
        self.values = []
        for title, size in (('FPS', 36), ('HI', 28), ('LO', 28)):
            column = QVBoxLayout()
            column.addWidget(QLabel(title))
            value = QLabel('—')
            font = QFont(); font.setPointSize(size); font.setBold(True)
            value.setFont(font)
            value.setAccessibleName(title)
            column.addWidget(value)
            metrics.addLayout(column, 1)
            self.values.append(value)
        content.addLayout(metrics)
        self.graph = FPSGraph()
        content.addWidget(self.graph)
        self.playback = self.add_text(content)
        self.resources = self.add_text(content)
        self.identity = self.add_text(content)
        self.connections = self.add_text(content)
        self.identity.setText(
            f'版本 {VERSION} · {platform.machine()}\n'
            f'进程 {os.path.basename(sys.executable)} · PID {os.getpid()}\n'
            f'CPU {platform.processor() or platform.machine()} · '
            f'{self.statistics.cores} 个逻辑核心\n{platform.platform()}')
        content.addStretch()
        scroll.setWidget(body)
        outer.addWidget(scroll, 1)
        footer = QHBoxLayout()
        pin = QCheckBox('置顶显示')
        pin.setChecked(pet.settings.value('diagnosticsPinned', True, type=bool))
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, pin.isChecked())
        pin.toggled.connect(self.toggle_pin)
        footer.addWidget(pin)
        footer.addStretch()
        close = QPushButton('关闭'); close.clicked.connect(self.close)
        copy = QPushButton('拷贝信息'); copy.clicked.connect(self.copy_information)
        footer.addWidget(close); footer.addWidget(copy)
        outer.addLayout(footer)

    @staticmethod
    def add_text(layout):
        label = QLabel()
        label.setWordWrap(True)
        label.setTextFormat(Qt.TextFormat.PlainText)
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(label)
        return label

    def reveal(self):
        if self.isMinimized():
            self.showNormal()
        else:
            self.show()
        self.raise_()
        self.activateWindow()

    def showEvent(self, event):
        super().showEvent(event)
        if not self.timer.isActive():
            self.previous = self.statistics.read()
            self.decoder_previous = None
            self.frames = PlaybackStatistics(self.previous.at)
            self.graph.values.clear(); self.graph.update()
            # Legacy disk caches are no longer read by the streaming player.
            try:
                size = sum(path.stat().st_size for path in
                           (self.root / 'app/cache').rglob('*') if path.is_file())
                self.disk_cache = byte_text(size)
            except OSError as error:
                self.disk_cache = f'读取失败：{error}'
            self.update_text(self.previous)
            self.timer.start()

    def hideEvent(self, event):
        if not self.changing_pin:
            self.timer.stop()
        super().hideEvent(event)

    def closeEvent(self, event):
        self.timer.stop()
        super().closeEvent(event)

    def toggle_pin(self, enabled):
        self.pet.settings.setValue('diagnosticsPinned', enabled)
        self.changing_pin = True
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, enabled)
        self.show()
        self.changing_pin = False

    def record(self, frame):
        if self.timer.isActive():
            self.frames.record(frame.cacheKey())

    def sample(self):
        current = self.statistics.read()
        fps, draws = self.frames.sample(current.at)
        self.graph.values.append(fps); self.graph.update()
        elapsed = current.at - self.previous.at
        cpu = gpu = swap_rate = None
        if current.cpu is not None and self.previous.cpu is not None:
            cpu = (current.cpu - self.previous.cpu) / elapsed * 100
        if current.gpu and self.previous.gpu:
            group, nanos = current.gpu
            old_group, old_nanos = self.previous.gpu
            if group == old_group and nanos >= old_nanos:
                gpu = (nanos - old_nanos) / 1e9 / elapsed * 100
            else:
                current.gpu_status = '重新建立采样基线'
        if current.swapins is not None and self.previous.swapins is not None:
            if current.swapins >= self.previous.swapins:
                swap_rate = (current.swapins - self.previous.swapins) / elapsed
        self.update_text(current, fps, draws, cpu, gpu, swap_rate)
        self.previous = current

    def update_text(self, process, fps=None, draws=None, cpu=None, gpu=None, swap_rate=None):
        def number(value):
            return '—' if value is None else f'{value:.1f}'

        for label, value in zip(self.values, (fps, self.frames.high, self.frames.low)):
            label.setText(number(value))
        pet = self.pet
        item = pet.current or {}
        buffered = pet.stream.statistics()
        count = buffered['count']
        frame = pet.frames[0] if pet.frames else None
        resolution = f'{frame.width()}×{frame.height()}' if frame else '未提供'
        state = '隐藏' if pet.desktop_hidden() else ('解码中' if pet.loading else ('播放' if pet.tick.isActive() else '暂停'))
        source_rate = number(buffered['rate'])
        self.playback.setText(
            f'有限预加载 · {item.get("name") or item.get("id", "未提供")} · {state}\n'
            f'解码尺寸 {resolution} · 素材帧率 {source_rate} FPS\n'
            f'帧 {0 if pet.loading else pet.source_index + 1}/{count if count is not None else "—"} · 累计 {self.frames.total} · '
            f'绘制 {number(draws)}/s')
        size, clips, frames = frame_cache_statistics(pet)
        cpu_text = (f'CPU 总体 {number(cpu / self.statistics.cores if cpu is not None else None)}%'
                    f' · 单核基准 {number(cpu)}%')
        if process.cpu_error:
            cpu_text = f'CPU 读取失败：{process.cpu_error}'
        ram_scope = '物理占用' if self.statistics.mac else '驻留集 RSS'
        ram = byte_text(process.ram) if not process.memory_error else process.memory_error
        swap = byte_text(process.system_swap) if not process.swap_error else process.swap_error
        gpu_text = f'{gpu:.2f}%' if gpu is not None else process.gpu_status
        swapins = (f'累计 {byte_text(process.swapins)}' if process.swapins else '未观察到换入')
        if process.swapins is None:
            swapins = process.memory_error or ('系统未返回进程换入计数' if self.statistics.mac
                                              else '当前平台未接入进程换入计数')
        if swap_rate is not None:
            swapins += f' · {byte_text(swap_rate)}/s'
        self.resources.setText(
            f'主进程 {cpu_text}\n主进程运行内存 (RAM) · {ram_scope} {ram}\n'
            f'{self.decoder_text(buffered["pid"])}\n'
            f'GPU（应用组）{gpu_text}\n'
            f'本进程压缩 {byte_text(process.compressed)} · 系统 Swap {swap}\n'
            f'本进程 Swap-in：{swapins}\n'
            f'帧缓存像素估算 {byte_text(size)} · {clips} 段 / {frames} 帧\n'
            f'预加载缓冲 {buffered["buffered"]}/{buffered["capacity"]} 帧 · 全库预加载：关闭\n'
            f'旧动画磁盘缓存 {self.disk_cache}（流式播放不读取）')
        sync = pet.desktop_sync
        watching = '观察中' if sync.timer.isActive() else '已停止'
        worker = pet.chat.worker if pet.chat else None
        self.connections.setText(
            f'只读同步 {watching} · 执行中 {len(sync.running)} · 已观察 {len(sync.known)}\n'
            f'连续读取失败 {sync.errors} 次\n'
            f'内置任务 {"执行中" if worker and worker.isRunning() else "空闲"}')

    def decoder_text(self,pid):
        if pid is None:
            self.decoder_previous=None
            return 'FFmpeg：未运行'
        try:
            decoder=psutil.Process(pid)
            with decoder.oneshot():
                times=decoder.cpu_times();ram=decoder.memory_info().rss
            now=time.monotonic();seconds=times.user+times.system
            cpu='等待采样'
            if self.decoder_previous and self.decoder_previous[0]==pid:
                _,before,previous=self.decoder_previous
                cpu=f'{(seconds-previous)/(now-before)*100:.1f}%'
            self.decoder_previous=(pid,now,seconds)
            return f'FFmpeg · PID {pid} · CPU 单核基准 {cpu}\n解码进程运行内存 (RAM) · RSS {byte_text(ram)}'
        except psutil.NoSuchProcess:
            self.decoder_previous=None
            return 'FFmpeg：本次解码进程已结束'
        except psutil.AccessDenied as error:
            self.decoder_previous=None
            return f'FFmpeg 统计读取失败：{error}'

    def copy_information(self):
        values = ' · '.join(f'{title} {label.text()}' for title, label in
                            zip(('FPS', 'HI', 'LO'), self.values))
        QApplication.clipboard().setText('\n\n'.join([
            self.windowTitle(), values, self.playback.text(), self.resources.text(),
            self.identity.text(), self.connections.text()]))
