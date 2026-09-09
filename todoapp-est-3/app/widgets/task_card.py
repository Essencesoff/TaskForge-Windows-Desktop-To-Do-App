from PySide6.QtWidgets import (QFrame, QHBoxLayout, QVBoxLayout, QLabel, QCheckBox,
                                QPushButton, QMenu, QSizePolicy)
from PySide6.QtCore import Qt, Signal
from app.config.constants import PRIORITY_COLORS
from app.utils.helpers import format_friendly_date


class TaskCard(QFrame):
    completed_toggled = Signal(int, bool)
    edit_requested = Signal(int)
    delete_requested = Signal(int)
    duplicate_requested = Signal(int)
    favorite_toggled = Signal(int)

    def __init__(self, task, category=None, parent=None):
        super().__init__(parent)
        self.task = task
        self.setObjectName("Card")
        self.setFrameShape(QFrame.NoFrame)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._selected = False

        outer = QHBoxLayout(self)
        outer.setContentsMargins(14, 10, 14, 10)
        outer.setSpacing(10)

        self.checkbox = QCheckBox()
        self.checkbox.setChecked(task.status == "Completed")
        self.checkbox.stateChanged.connect(
            lambda state: self.completed_toggled.emit(task.id, self.checkbox.isChecked()))
        outer.addWidget(self.checkbox)

        col = QVBoxLayout()
        col.setSpacing(2)
        title_row = QHBoxLayout()
        title = QLabel(task.title)
        title.setStyleSheet("font-weight: 600; font-size: 14px;" +
                             ("text-decoration: line-through; color: #888;" if task.status == "Completed" else ""))
        title_row.addWidget(title)
        if task.is_favorite:
            star = QLabel("\u2605")
            star.setStyleSheet("color: #FFC107;")
            title_row.addWidget(star)
        title_row.addStretch()
        col.addLayout(title_row)

        meta_bits = []
        if task.due_date:
            meta_bits.append(format_friendly_date(task.due_date) + (f" {task.due_time}" if task.due_time else ""))
        if category:
            meta_bits.append(f"{category.icon} {category.name}")
        if task.subtasks:
            done = sum(1 for s in task.subtasks if s.is_done)
            meta_bits.append(f"{done}/{len(task.subtasks)} subtasks")
        meta = QLabel("  \u2022  ".join(meta_bits))
        meta.setObjectName("SubHeading")
        col.addWidget(meta)
        outer.addLayout(col, 1)

        prio_dot = QLabel("\u25CF")
        prio_dot.setStyleSheet(f"color: {PRIORITY_COLORS.get(task.priority, '#999')}; font-size: 16px;")
        prio_dot.setToolTip(task.priority)
        outer.addWidget(prio_dot)

        menu_btn = QPushButton("\u22EF")
        menu_btn.setFixedWidth(32)
        menu_btn.clicked.connect(self._show_menu)
        outer.addWidget(menu_btn)
        self._menu_btn = menu_btn

    def set_selected(self, selected: bool, accent: str = "#6C7CFF"):
        """Visual highlight used for keyboard (Up/Down + Space) navigation."""
        self._selected = selected
        self.setStyleSheet(f"QFrame#Card {{ border: 2px solid {accent}; }}" if selected else "")

    def _show_menu(self):
        menu = QMenu(self)
        edit_act = menu.addAction("Edit")
        fav_act = menu.addAction("Unfavorite" if self.task.is_favorite else "Favorite")
        dup_act = menu.addAction("Duplicate")
        del_act = menu.addAction("Delete")
        chosen = menu.exec(self._menu_btn.mapToGlobal(self._menu_btn.rect().bottomLeft()))
        if chosen == edit_act:
            self.edit_requested.emit(self.task.id)
        elif chosen == fav_act:
            self.favorite_toggled.emit(self.task.id)
        elif chosen == dup_act:
            self.duplicate_requested.emit(self.task.id)
        elif chosen == del_act:
            self.delete_requested.emit(self.task.id)
