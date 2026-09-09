from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor, QFont
from PySide6.QtCore import Qt


class BarChart(QWidget):
    """A minimal, dependency-free bar chart: list of (label, value)."""

    def __init__(self, data=None, color="#6C7CFF", parent=None):
        super().__init__(parent)
        self.data = data or []
        self.color = QColor(color)
        self.setMinimumHeight(180)

    def set_data(self, data):
        self.data = data
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        if not self.data:
            painter.setPen(QColor("#888"))
            painter.drawText(self.rect(), Qt.AlignCenter, "No data yet")
            return

        margin_bottom = 24
        max_val = max((v for _, v in self.data), default=1) or 1
        n = len(self.data)
        bar_gap = 8
        bar_w = max(6, (w - bar_gap * (n + 1)) / n)

        font = QFont()
        font.setPointSize(8)
        painter.setFont(font)

        x = bar_gap
        for label, value in self.data:
            bar_h = (h - margin_bottom - 10) * (value / max_val)
            y = h - margin_bottom - bar_h
            painter.setBrush(self.color)
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(int(x), int(y), int(bar_w), int(bar_h), 4, 4)
            painter.setPen(QColor("#999"))
            painter.drawText(int(x - 4), h - margin_bottom + 4, int(bar_w + 8), 18,
                              Qt.AlignCenter, str(label)[:6])
            if value:
                painter.drawText(int(x - 4), int(y - 16), int(bar_w + 8), 14,
                                  Qt.AlignCenter, str(value))
            x += bar_w + bar_gap
