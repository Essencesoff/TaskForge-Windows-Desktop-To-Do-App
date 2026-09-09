from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCalendarWidget,
                                QScrollArea, QPushButton)
from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QColor, QTextCharFormat

from app.services import task_service, category_service
from app.widgets.task_card import TaskCard
from app.config.constants import DATE_FMT


class CalendarPage(QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        layout = QVBoxLayout(self)

        header = QHBoxLayout()
        title = QLabel("Calendar")
        title.setObjectName("Heading")
        header.addWidget(title)
        header.addStretch()
        new_btn = QPushButton("+ New Task on this day")
        new_btn.clicked.connect(self._add_task_on_selected_day)
        header.addWidget(new_btn)
        layout.addLayout(header)

        body = QHBoxLayout()
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.selectionChanged.connect(self.refresh_day_list)
        self.calendar.currentPageChanged.connect(self._mark_month)
        body.addWidget(self.calendar, 2)

        right = QVBoxLayout()
        self.day_label = QLabel()
        self.day_label.setObjectName("SubHeading")
        right.addWidget(self.day_label)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.container = QWidget()
        self.c_layout = QVBoxLayout(self.container)
        self.scroll.setWidget(self.container)
        right.addWidget(self.scroll, 1)
        body.addLayout(right, 1)

        layout.addLayout(body, 1)
        self._mark_month(self.calendar.yearShown(), self.calendar.monthShown())
        self.refresh_day_list()

    def _add_task_on_selected_day(self):
        date_str = self.calendar.selectedDate().toString("yyyy-MM-dd")
        self.main_window.open_task_editor(prefill_date=date_str)

    def _mark_month(self, year, month):
        """Highlight days that have tasks due, using a subtle background color."""
        default_fmt = QTextCharFormat()
        # reset formatting for the visible month range (cheap approximation: reset -3..+3 weeks)
        start = QDate(year, month, 1)
        for day in range(1, start.daysInMonth() + 1):
            self.calendar.setDateTextFormat(QDate(year, month, day), default_fmt)

        rows = task_service.list_tasks()
        fmt = QTextCharFormat()
        fmt.setBackground(QColor("#6C7CFF"))
        fmt.setForeground(QColor("#FFFFFF"))
        for t in rows:
            if not t.due_date:
                continue
            try:
                y, m, d = map(int, t.due_date.split("-"))
            except ValueError:
                continue
            if y == year and m == month:
                self.calendar.setDateTextFormat(QDate(y, m, d), fmt)

    def refresh_day_list(self):
        selected = self.calendar.selectedDate()
        date_str = selected.toString("yyyy-MM-dd")
        self.day_label.setText(selected.toString("dddd, MMMM d, yyyy"))

        while self.c_layout.count():
            item = self.c_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        categories = {c.id: c for c in category_service.list_categories()}
        tasks = task_service.list_tasks(date_from=date_str, date_to=date_str)
        if not tasks:
            empty = QLabel("No tasks on this day.")
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
        self.c_layout.addStretch()

    def refresh(self):
        self._mark_month(self.calendar.yearShown(), self.calendar.monthShown())
        self.refresh_day_list()
