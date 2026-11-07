"""Small native Qt form for the bounded decoder's two controls."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QDialog,QVBoxLayout,QFormLayout,QHBoxLayout,QLabel,
                               QComboBox,QSpinBox,QPushButton,QApplication)


class PerformanceSettings(QDialog):
    def __init__(self,pet):
        super().__init__(pet,Qt.WindowType.Window)
        self.pet=pet
        self.setWindowTitle('性能设置');self.resize(440,250)
        layout=QVBoxLayout(self);layout.setContentsMargins(18,16,18,16);layout.setSpacing(12)
        form=QFormLayout()
        self.quality=QComboBox()
        for label,value in (('跟随屏幕（原设置，最高 512×512）',0),('原画 720×720',720),
                            ('较高 512×512',512),('中 384×384',384),('低 256×256',256)):
            self.quality.addItem(label,value)
        self.quality.setCurrentIndex(self.quality.findData(pet.resolution))
        self.capacity=QSpinBox();self.capacity.setRange(6,240);self.capacity.setSuffix(' 帧')
        self.capacity.setValue(pet.buffer_capacity)
        form.addRow('解码分辨率',self.quality);form.addRow('预加载帧数',self.capacity)
        layout.addLayout(form)
        self.estimate=QLabel();self.estimate.setWordWrap(True);layout.addWidget(self.estimate)
        note=QLabel('仅预读当前动作；保留素材帧率。隐藏桌宠时暂停解码。\n应用后重新开始当前动作，设置自动保存。')
        note.setWordWrap(True);layout.addWidget(note)
        layout.addStretch()
        row=QHBoxLayout();row.addStretch()
        close=QPushButton('关闭');close.clicked.connect(self.close)
        self.apply_button=QPushButton('应用');self.apply_button.clicked.connect(self.apply)
        row.addWidget(close);row.addWidget(self.apply_button);layout.addLayout(row)
        self.quality.currentIndexChanged.connect(self.refresh)
        self.capacity.valueChanged.connect(self.refresh)
        self.refresh()

    def refresh(self):
        size=self.quality.currentData() or min(512,max(256,round(256*max(s.devicePixelRatio() for s in QApplication.screens()))))
        size_mib=self.capacity.value()*size*size*4/1024**2
        self.estimate.setText(f'预加载像素约 {size_mib:.1f} MiB。\n运行内存 (RAM) 还包含显示画面、Qt 和 FFmpeg 等开销。')
        self.apply_button.setEnabled((self.quality.currentData(),self.capacity.value())!=
                                     (self.pet.resolution,self.pet.buffer_capacity))

    def apply(self):
        self.capacity.interpretText()
        self.pet.apply_performance(self.quality.currentData(),self.capacity.value())
        self.refresh()
