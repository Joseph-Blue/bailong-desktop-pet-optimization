"""Shared native window and layout rules for performance panels."""
import sys
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QKeySequence, QShortcut
from PySide6.QtWidgets import QApplication, QBoxLayout, QWidget, QSizePolicy


def readable_font(scale=1.0):
    """Use point sizes so Qt handles monitor DPI; keep small bubbles readable."""
    font = QFont(QApplication.font())
    if sys.platform == 'win32':
        font.setFamilies(list(dict.fromkeys(font.families() + ['Microsoft YaHei UI', 'Microsoft YaHei'])))
    font.setPointSizeF(max(12.0, font.pointSizeF()) * max(1.0, scale))
    return font


def configure_window(window):
    window.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.CustomizeWindowHint |
                          Qt.WindowType.WindowTitleHint | Qt.WindowType.WindowSystemMenuHint |
                          Qt.WindowType.WindowCloseButtonHint)
    window.setFont(readable_font())
    QShortcut(QKeySequence(Qt.Key.Key_Escape), window, activated=window.close)


class Columns(QWidget):
    """Keep related controls together when a narrow window stacks its columns."""
    def __init__(self, left, right):
        super().__init__()
        self.columns = QBoxLayout(QBoxLayout.Direction.LeftToRight, self)
        self.columns.setContentsMargins(0, 0, 0, 0)
        self.columns.setSpacing(18)
        # Long labels must not impose a larger minimum width on either column.
        for panel in (left, right):
            panel.setMinimumWidth(0)
            panel.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.columns.addWidget(left, 1)
        self.columns.addWidget(right, 1)

    def resizeEvent(self, event):
        threshold = self.fontMetrics().horizontalAdvance('汉') * 40
        direction = (QBoxLayout.Direction.LeftToRight if event.size().width() >= threshold
                     else QBoxLayout.Direction.TopToBottom)
        self.columns.setDirection(direction)
        super().resizeEvent(event)
