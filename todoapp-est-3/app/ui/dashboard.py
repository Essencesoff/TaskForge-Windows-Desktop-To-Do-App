import datetime as dt
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
                                QProgressBar, QScrollArea, QGridLayout, QSizePolicy)
from PySide6.QtCore import Qt

from app.services import task_service, stats_service, category_service
from app.utils.helpers import greeting_for_now, format_friendly_date
from app.widgets.task_card import TaskCard


def _stat_card(title, value, color=None):
    card = QFrame()
    card.setObjectName("Card")
    layout = QVBoxLayout(card)
    val = QLabel(str(value))
    val.setStyleSheet(f"font-size: 26px; font-weight: 700;" + (f" color: {color};" if color else ""))
    lbl = QLabel(title)
    lbl.setObjectName("SubHeading")
    layout.addWidget(val)
    layout.addWidget(lbl)
    return card


class DashboardPage(QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.setLayout(QVBoxLayout())
        self.refresh()

    def refresh(self):
        # clear
        old_layout = self.layout()
        while old_layout.count():
            item = old_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        user_name = self.main_window.user_name
        greeting = QLabel(f"{greeting_for_now()}, {user_name} \U0001F44B")
        greeting.setObjectName("Heading")
        old_layout.addWidget(greeting)

        date_lbl = QLabel(dt.datetime.now().strftime("%A, %B %d"))
        date_lbl.setObjectName("SubHeading")
        old_layout.addWidget(date_lbl)

        progress = stats_service.today_progress()
        card = QFrame()
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.addWidget(QLabel("Today's progress"))
        bar = QProgressBar()
        bar.setValue(progress["pct"])
        bar.setFormat(f"{progress['pct']}%")
        card_layout.addWidget(bar)
        summary = QLabel(f"{progress['completed']} completed \u2022 {progress['remaining']} remaining"
                          f"{' \u2022 ' + str(progress['overdue']) + ' overdue' if progress['overdue'] else ''}")
        summary.setObjectName("SubHeading")
        card_layout.addWidget(summary)
        old_layout.addWidget(card)

        streak = stats_service.current_and_best_streak()
        grid = QGridLayout()
        grid.addWidget(_stat_card("\U0001F525 Current streak", f"{streak['current']} days", "#FF7043"), 0, 0)
        grid.addWidget(_stat_card("\U0001F3C6 Best streak", f"{streak['best']} days", "#FFC107"), 0, 1)
        grid.addWidget(_stat_card("\u26A0\uFE0F Overdue", progress["overdue"], "#F44336"), 0, 2)
        upcoming = task_service.upcoming_tasks(7)
        grid.addWidget(_stat_card("\U0001F4C5 Due this week", len(upcoming), "#5C6BC0"), 0, 3)
        old_layout.addLayout(grid)

        # Upcoming deadlines list
        old_layout.addWidget(QLabel("Upcoming deadlines"))
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        c_layout = QVBoxLayout(container)
        c_layout.setSpacing(6)
        categories = {c.id: c for c in category_service.list_categories()}

        combined = task_service.overdue_tasks() + upcoming
        if not combined:
            empty = QLabel("Nothing due soon \u2014 nice work! \U0001F389")
            empty.setObjectName("SubHeading")
            c_layout.addWidget(empty)
        for t in combined[:15]:
            card_w = TaskCard(t, categories.get(t.category_id))
            card_w.completed_toggled.connect(self.main_window.handle_complete_toggle)
            card_w.edit_requested.connect(self.main_window.open_task_editor)
            card_w.delete_requested.connect(self.main_window.handle_delete_task)
            card_w.duplicate_requested.connect(self.main_window.handle_duplicate_task)
            card_w.favorite_toggled.connect(self.main_window.handle_favorite_toggle)
            c_layout.addWidget(card_w)
        c_layout.addStretch()
        scroll.setWidget(container)
        old_layout.addWidget(scroll, 1)
