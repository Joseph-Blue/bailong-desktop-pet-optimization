"""On-demand desktop performance statistics using platform-native Qt controls."""
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
                               QHBoxLayout, QScrollArea, QDialogButtonBox, QCheckBox,
                               QGroupBox, QFormLayout)

from performance_metrics import (PlaybackStatistics, ProcessStatistics,
                                 byte_text, frame_cache_statistics)
from diagnostic_identity import HardwareProbe, desktop_status, cli_status
from version import VERSION
from performance_ui import Columns, configure_window


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
        metrics = self.fontMetrics()
        plot = QRectF(self.rect()).adjusted(12, metrics.height() + 8, -12, -metrics.height() - 8)
        ceiling = max(30, math.ceil(max(self.values, default=0) / 10) * 10)
        painter.setPen(palette.color(QPalette.ColorRole.Mid))
        for step in range(3):
            y = plot.bottom() - plot.height() * step / 2
            painter.drawLine(QPointF(plot.left(), y), QPointF(plot.right(), y))
        painter.setPen(palette.color(QPalette.ColorRole.Text))
        painter.drawText(12, metrics.ascent() + 3, f'{ceiling} FPS')
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


class InfoSection(QGroupBox):
    def __init__(self, title):
        super().__init__(title)
        self.form = QFormLayout(self)
        self.form.setHorizontalSpacing(18)
        self.form.setVerticalSpacing(8)
        self.form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        self.form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        self.labels = {}

    def set_rows(self, rows):
        if tuple(self.labels) != tuple(name for name, _ in rows):
            while self.form.rowCount():
                self.form.removeRow(0)
            self.labels.clear()
            for name, _ in rows:
                label = QLabel()
                label.setWordWrap(True)
                label.setTextFormat(Qt.TextFormat.PlainText)
                label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                self.labels[name] = label
                self.form.addRow(name, label)
        for name, value in rows:
            self.labels[name].setText(str(value))

    def text(self):
        return self.title() + '\n' + '\n'.join(f'{name}：{label.text()}' for name, label in self.labels.items())


class DiagnosticsWindow(QWidget):
    def __init__(self, pet, root):
        super().__init__(None, Qt.WindowType.Window)
        configure_window(self)
        self.pet = pet
        self.root = root
        self.setWindowTitle('性能统计')
        self.setWindowIcon(pet.windowIcon())
        self.resize(1000, 720)
        self.setMinimumSize(440, 360)
        self.changing_pin = False
        self.statistics = ProcessStatistics()
        self.hardware = HardwareProbe(self)
        self.hardware.changed.connect(self.update_identity)
        self.frames = PlaybackStatistics(time.monotonic())
        self.previous = None
        self.decoder_previous = None
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.sample)
        QApplication.instance().aboutToQuit.connect(self.timer.stop)
        QApplication.instance().aboutToQuit.connect(self.hardware.stop)

        outer = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        body = QWidget()
        content = QVBoxLayout(body)
        content.setSpacing(12)
        metrics = QHBoxLayout()
        self.values = []
        for title, scale in (('FPS', 1.333 ** 3), ('最高', 1.333 ** 2), ('最低', 1.333 ** 2)):
            column = QVBoxLayout()
            column.addWidget(QLabel(title))
            value = QLabel('—')
            font = QFont(self.font())
            font.setPointSizeF(self.font().pointSizeF() * scale)
            font.setWeight(QFont.Weight.Medium)
            value.setFont(font)
            value.setAccessibleName(title)
            column.addWidget(value)
            metrics.addLayout(column, 1)
            self.values.append(value)
        content.addLayout(metrics)
        self.graph = FPSGraph()
        content.addWidget(self.graph)
        self.playback = InfoSection('播放')
        self.resources = InfoSection('资源')
        self.identity = InfoSection('硬件与版本')
        self.connections = InfoSection('连接与任务')
        left, right = QWidget(), QWidget()
        for column, sections in ((left, (self.playback, self.resources)),
                                 (right, (self.identity, self.connections))):
            group = QVBoxLayout(column)
            group.setContentsMargins(0, 0, 0, 0)
            group.setSpacing(12)
            for section in sections:
                group.addWidget(section)
            group.addStretch()
        self.columns = Columns(left, right)
        content.addWidget(self.columns)
        self.update_identity()
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
        buttons = QDialogButtonBox()
        copy = buttons.addButton('复制信息', QDialogButtonBox.ButtonRole.ActionRole)
        copy.clicked.connect(self.copy_information)
        footer.addWidget(buttons)
        outer.addLayout(footer)

    def reveal(self):
        if self.isMinimized():
            self.showNormal()
        else:
            self.show()
        self.raise_()
        self.activateWindow()

    def showEvent(self, event):
        super().showEvent(event)
        self.hardware.start()
        if not self.timer.isActive():
            self.previous = self.statistics.read()
            self.decoder_previous = None
            self.frames = PlaybackStatistics(self.previous.at)
            self.graph.values.clear(); self.graph.update()
            self.update_text(self.previous)
            self.timer.start()

    def hideEvent(self, event):
        if not self.changing_pin:
            self.timer.stop()
            self.hardware.stop()
        super().hideEvent(event)

    def closeEvent(self, event):
        self.timer.stop()
        self.hardware.stop()
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
        limit = '满帧' if pet.fps_limit == 'full' else f'{pet.fps_limit} FPS'
        self.playback.set_rows([
            ('当前动作', f'{item.get("name") or item.get("id", "未提供")} · {state}'),
            ('解码分辨率', resolution),
            ('运行帧率', f'{source_rate} FPS · 上限 {limit}'),
            ('动画帧', f'{0 if pet.loading else pet.source_index + 1} / {count if count is not None else "—"}'),
            ('累计帧数', self.frames.total),
            ('绘制频率', f'{number(draws)} / 秒')])
        size, _, frames = frame_cache_statistics(pet)
        cpu_text = (f'{number(cpu / self.statistics.cores if cpu is not None else None)}%（总体）'
                    f' · {number(cpu)}%（单核）')
        if process.cpu_error:
            cpu_text = f'CPU 读取失败：{process.cpu_error}'
        ram_scope = '物理占用' if self.statistics.mac else 'RSS'
        ram = byte_text(process.ram) if not process.memory_error else process.memory_error
        gpu_text = f'{gpu:.2f}%' if gpu is not None else process.gpu_status
        swapins = (f'累计 {byte_text(process.swapins)}' if process.swapins else '未观察到换入')
        if process.swapins is None:
            swapins = process.memory_error or ('系统未返回进程换入计数' if self.statistics.mac
                                              else '当前平台未接入进程换入计数')
        if swap_rate is not None:
            swapins += f' · {byte_text(swap_rate)}/s'
        decoder_text, decoder_ram = self.decoder_text(buffered['pid'])
        total_ram = (process.ram + decoder_ram
                     if process.ram is not None and decoder_ram is not None else None)
        resources = [
            ('桌宠 RAM', f'{byte_text(total_ram)}（主进程 + FFmpeg）'),
            ('主进程 RAM', f'{ram} · {ram_scope}'),
            ('FFmpeg RAM', f'{byte_text(decoder_ram)} · {ram_scope}'),
            ('主进程 CPU', cpu_text),
            ('FFmpeg', decoder_text)]
        if self.statistics.mac:
            resources += [('GPU（应用组）', gpu_text),
                          ('进程压缩内存', byte_text(process.compressed)),
                          ('进程换入', swapins)]
        if self.statistics.platform == 'win32':
            resources.append(('虚拟内存（系统）', process.commit_error or
                f'{byte_text(process.system_commit)} / {byte_text(process.system_commit_limit)}（已提交 / 上限）'))
        else:
            resources.append(('Swap（系统）', process.swap_error or
                f'{byte_text(process.system_swap)} / {byte_text(process.system_swap_total)}（已用 / 总量）'))
        resources.append(('帧缓存估算', f'{byte_text(size)} · {frames} 帧'))
        if buffered['preloadWhole']:
            resources.append(('整段预加载', f'{buffered["buffered"]} / {count if count is not None else "—"} 帧'))
        else:
            resources.append(('动画缓冲', f'{buffered["buffered"]} / {buffered["capacity"]} 帧'))
        self.resources.set_rows(resources)
        sync = pet.desktop_sync
        watching = '观察中' if sync.timer.isActive() else '已停止'
        worker = pet.chat.worker if pet.chat else None
        self.connections.set_rows([
            ('桌面端', desktop_status()),
            ('只读同步', f'{watching} · 执行中 {len(sync.running)} · 已观察 {len(sync.known)}'),
            ('连续读取失败', f'{sync.errors} 次'),
            ('内置 CLI', cli_status(pet)),
            ('额度查询', '执行中' if pet.quota_inflight else '空闲'),
            ('内置任务', '执行中' if worker and worker.isRunning() else '空闲')])

    def update_identity(self):
        self.identity.set_rows([
            ('版本', f'{VERSION} · {platform.machine()}'),
            ('进程', f'{os.path.basename(sys.executable)} · PID {os.getpid()}'),
            ('CPU', f'{self.hardware.cpu} · {self.statistics.cores} 个逻辑核心'),
            ('GPU', self.hardware.gpu),
            ('系统', platform.platform())])

    def decoder_text(self,pid):
        if pid is None:
            self.decoder_previous=None
            return '未运行', 0
        try:
            decoder=psutil.Process(pid)
            with decoder.oneshot():
                times=decoder.cpu_times()
                ram=(self.statistics.mac.process_footprint(pid) if self.statistics.mac
                     else decoder.memory_info().rss)
            now=time.monotonic();seconds=times.user+times.system
            cpu='等待采样'
            if self.decoder_previous and self.decoder_previous[0]==pid:
                _,before,previous=self.decoder_previous
                cpu=f'{(seconds-previous)/(now-before)*100:.1f}%'
            self.decoder_previous=(pid,now,seconds)
            return f'PID {pid} · CPU {cpu}（单核）', ram
        except psutil.NoSuchProcess:
            self.decoder_previous=None
            return '本次解码已结束', None
        except (psutil.AccessDenied, OSError) as error:
            self.decoder_previous=None
            return f'FFmpeg 统计读取失败：{error}', None

    def copy_information(self):
        values = ' · '.join(f'{title} {label.text()}' for title, label in
                            zip(('FPS', '最高', '最低'), self.values))
        QApplication.clipboard().setText('\n\n'.join([
            self.windowTitle(), values, self.playback.text(), self.resources.text(),
            self.identity.text(), self.connections.text()]))
