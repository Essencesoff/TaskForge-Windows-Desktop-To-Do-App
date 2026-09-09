from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
                                QPushButton, QFrame)
from PySide6.QtCore import Qt
from app.services import planner_service, category_service
from app.config.constants import PRIORITY_COLORS

PRIORITY_DOT = {
    "Critical": "\U0001F534",
    "High": "\U0001F7E0",
    "Medium": "\U0001F7E1",
    "Low": "\U0001F7E2",
}


class PlannerPage(QWidget):
    """Suggests a recommended order of work; user can drag to reorder manually."""

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        layout = QVBoxLayout(self)

        header = QHBoxLayout()
        title = QLabel("Smart Planner")
        title.setObjectName("Heading")
        header.addWidget(title)
        header.addStretch()
        refresh_btn = QPushButton("Recalculate")
        refresh_btn.clicked.connect(self.refresh)
        header.addWidget(refresh_btn)
        layout.addLayout(header)

        note = QLabel("Ranked by priority, deadline proximity, and estimated duration. "
                       "Drag items in the Tasks tab to fine-tune manually.")
        note.setObjectName("SubHeading")
        note.setWordWrap(True)
        layout.addWidget(note)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.container = QWidget()
        self.c_layout = QVBoxLayout(self.container)
        self.c_layout.setSpacing(6)
        self.scroll.setWidget(self.container)
        layout.addWidget(self.scroll, 1)
        self.refresh()

    def refresh(self):
        while self.c_layout.count():
            item = self.c_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        ordered = planner_service.suggest_order()
        categories = {c.id: c for c in category_service.list_categories()}
        if not ordered:
            empty = QLabel("Nothing to plan \u2014 you're all caught up!")
            empty.setObjectName("SubHeading")
            self.c_layout.addWidget(empty)

        for i, t in enumerate(ordered, start=1):
            row = QFrame()
            row.setObjectName("Card")
            h = QHBoxLayout(row)
            num = QLabel(str(i))
            num.setFixedWidth(28)
            num.setStyleSheet("font-weight: 700; font-size: 15px;")
            h.addWidget(num)
            dot = QLabel(PRIORITY_DOT.get(t.priority, "\u26AA"))
            h.addWidget(dot)
            title_lbl = QLabel(t.title)
            title_lbl.setStyleSheet("font-weight: 600;")
            h.addWidget(title_lbl, 1)
            cat = categories.get(t.category_id)
            if cat:
                cat_lbl = QLabel(f"{cat.icon} {cat.name}")
                cat_lbl.setObjectName("SubHeading")
                h.addWidget(cat_lbl)
            prio_lbl = QLabel(t.priority)
            prio_lbl.setStyleSheet(f"color: {PRIORITY_COLORS.get(t.priority, '#999')}; font-weight: 600;")
            h.addWidget(prio_lbl)
            edit_btn = QPushButton("Open")
            edit_btn.clicked.connect(lambda _, tid=t.id: self.main_window.open_task_editor(tid))
            h.addWidget(edit_btn)
            self.c_layout.addWidget(row)
        self.c_layout.addStretch()
