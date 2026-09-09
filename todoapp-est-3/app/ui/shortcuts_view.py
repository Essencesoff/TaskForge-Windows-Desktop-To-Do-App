from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QHBoxLayout

SHORTCUTS = [
    ("Ctrl + N", "New task (quick add)"),
    ("Ctrl + F", "Search tasks"),
    ("Ctrl + K", "Command menu"),
    ("Ctrl + ,", "Open settings"),
    ("Esc", "Close dialog"),
    ("Enter", "Confirm"),
    ("Space", "Complete selected task"),
]


class ShortcutsPage(QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        title = QLabel("Keyboard Shortcuts")
        title.setObjectName("Heading")
        layout.addWidget(title)

        for keys, desc in SHORTCUTS:
            row = QFrame()
            row.setObjectName("Card")
            h = QHBoxLayout(row)
            key_lbl = QLabel(keys)
            key_lbl.setStyleSheet("font-weight: 700; font-family: Consolas, monospace;")
            key_lbl.setFixedWidth(120)
            h.addWidget(key_lbl)
            h.addWidget(QLabel(desc))
            layout.addWidget(row)
        layout.addStretch()
