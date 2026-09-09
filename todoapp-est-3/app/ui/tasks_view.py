from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                                QComboBox, QScrollArea, QPushButton, QSizePolicy)
from PySide6.QtCore import Qt

from app.services import task_service, category_service
from app.config.constants import STATUSES, PRIORITIES
from app.widgets.task_card import TaskCard


class TasksPage(QWidget):
    """Task list with filters/search, plus keyboard navigation:
    Up/Down selects a row, Space toggles it complete (per the app's
    global shortcut list)."""

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self._cards = []          # [(TaskCard, task_id), ...] in display order
        self._selected_index = -1
        self.setFocusPolicy(Qt.StrongFocus)
        layout = QVBoxLayout(self)

        header = QHBoxLayout()
        title = QLabel("Tasks")
        title.setObjectName("Heading")
        header.addWidget(title)
        header.addStretch()
        new_btn = QPushButton("+ New Task")
        new_btn.setObjectName("Primary")
        new_btn.clicked.connect(lambda: self.main_window.open_task_editor())
        header.addWidget(new_btn)
        layout.addLayout(header)

        filter_row = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search tasks\u2026 (Ctrl+F)")
        self.search_edit.textChanged.connect(self.refresh)
        filter_row.addWidget(self.search_edit, 2)

        self.status_combo = QComboBox()
        self.status_combo.addItem("All Statuses", None)
        for s in STATUSES:
            self.status_combo.addItem(s, s)
        self.status_combo.currentIndexChanged.connect(self.refresh)
        filter_row.addWidget(self.status_combo)

        self.priority_combo = QComboBox()
        self.priority_combo.addItem("All Priorities", None)
        for p in PRIORITIES:
            self.priority_combo.addItem(p, p)
        self.priority_combo.currentIndexChanged.connect(self.refresh)
        filter_row.addWidget(self.priority_combo)

        self.category_combo = QComboBox()
        self.category_combo.addItem("All Categories", None)
        self.category_combo.currentIndexChanged.connect(self.refresh)
        filter_row.addWidget(self.category_combo)

        self.fav_btn = QPushButton("\u2605 Favorites")
        self.fav_btn.setCheckable(True)
        self.fav_btn.toggled.connect(self.refresh)
        filter_row.addWidget(self.fav_btn)

        layout.addLayout(filter_row)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFocusPolicy(Qt.NoFocus)  # let TasksPage keep focus for Up/Down/Space nav
        self.container = QWidget()
        self.c_layout = QVBoxLayout(self.container)
        self.c_layout.setSpacing(6)
        self.scroll.setWidget(self.container)
        layout.addWidget(self.scroll, 1)

        self._reload_categories()
        self.refresh()

    def _reload_categories(self):
        current = self.category_combo.currentData()
        self.category_combo.blockSignals(True)
        self.category_combo.clear()
        self.category_combo.addItem("All Categories", None)
        for c in category_service.list_categories():
            self.category_combo.addItem(f"{c.icon} {c.name}", c.id)
        idx = self.category_combo.findData(current)
        if idx >= 0:
            self.category_combo.setCurrentIndex(idx)
        self.category_combo.blockSignals(False)

    def focus_search(self):
        self.search_edit.setFocus()
        self.search_edit.selectAll()

    def refresh(self):
        while self.c_layout.count():
            item = self.c_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        self._cards = []
        self._selected_index = -1

        categories = {c.id: c for c in category_service.list_categories()}
        tasks = task_service.list_tasks(
            status=self.status_combo.currentData(),
            category_id=self.category_combo.currentData(),
            priority=self.priority_combo.currentData(),
            favorites_only=self.fav_btn.isChecked(),
            search=self.search_edit.text().strip() or None,
        )
        if not tasks:
            empty = QLabel("No tasks match your filters.")
            empty.setObjectName("SubHeading")
            self.c_layout.addWidget(empty)
        for t in tasks:
            card = TaskCard(t, categories.get(t.category_id))
            card.completed_toggled.connect(self.main_window.handle_complete_toggle)
            card.edit_requested.connect(self.main_window.open_task_editor)
            card.delete_requested.connect(self.main_window.handle_delete_task)
            card.duplicate_requested.connect(self.main_window.handle_duplicate_task)
            card.favorite_toggled.connect(self.main_window.handle_favorite_toggle)
            self.c_layout.addWidget(card)
            self._cards.append((card, t.id))
        self.c_layout.addStretch()
        if self._cards:
            self._select_index(0)

    # ---------------------------------------------------- keyboard nav ---
    def _select_index(self, index: int):
        if not self._cards:
            return
        index = max(0, min(index, len(self._cards) - 1))
        if self._selected_index != -1 and self._selected_index < len(self._cards):
            self._cards[self._selected_index][0].set_selected(False)
        self._selected_index = index
        card, _ = self._cards[index]
        card.set_selected(True)
        self.scroll.ensureWidgetVisible(card)

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Down:
            self._select_index(self._selected_index + 1)
            return
        if key == Qt.Key_Up:
            self._select_index(self._selected_index - 1)
            return
        if key == Qt.Key_Space and 0 <= self._selected_index < len(self._cards):
            card, task_id = self._cards[self._selected_index]
            new_checked = not card.checkbox.isChecked()
            card.checkbox.setChecked(new_checked)  # also fires completed_toggled -> refresh()
            return
        super().keyPressEvent(event)
