from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout
from app.services import stats_service
from app.widgets.bar_chart import BarChart


def _card(title):
    frame = QFrame()
    frame.setObjectName("Card")
    layout = QVBoxLayout(frame)
    lbl = QLabel(title)
    lbl.setStyleSheet("font-weight: 600;")
    layout.addWidget(lbl)
    return frame, layout


class StatisticsPage(QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.setLayout(QVBoxLayout())
        self.refresh()

    def refresh(self):
        layout = self.layout()
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        title = QLabel("Statistics")
        title.setObjectName("Heading")
        layout.addWidget(title)

        today = stats_service.today_progress()
        week = sum(r["completed_count"] for r in stats_service.completed_counts("week"))
        month = sum(r["completed_count"] for r in stats_service.completed_counts("month"))

        grid = QGridLayout()
        for i, (label, value) in enumerate([
            ("Completed today", today["completed"]),
            ("Completed this week", week),
            ("Completed this month", month),
            ("Overdue", today["overdue"]),
        ]):
            frame, flayout = _card(label)
            val = QLabel(str(value))
            val.setStyleSheet("font-size: 24px; font-weight: 700;")
            flayout.addWidget(val)
            grid.addWidget(frame, 0, i)
        layout.addLayout(grid)

        # Productivity over last 30 days
        prod_frame, prod_layout = _card("Productivity \u2014 last 30 days")
        series = stats_service.productivity_series(30)
        chart_data = [(d["date"][5:], d["count"]) for d in series[-14:]]  # last 14 for readability
        chart = BarChart(chart_data, color="#6C7CFF")
        prod_layout.addWidget(chart)
        layout.addWidget(prod_frame)

        row = QHBoxLayout()
        cat_frame, cat_layout = _card("Tasks by category")
        cat_data = [(r["name"], r["count"]) for r in stats_service.tasks_by_category()]
        cat_chart = BarChart(cat_data, color="#26A69A")
        cat_layout.addWidget(cat_chart)
        row.addWidget(cat_frame)

        prio_frame, prio_layout = _card("Tasks by priority")
        prio_data = [(r["priority"], r["count"]) for r in stats_service.tasks_by_priority()]
        prio_chart = BarChart(prio_data, color="#FF7043")
        prio_layout.addWidget(prio_chart)
        row.addWidget(prio_frame)
        layout.addLayout(row)
        layout.addStretch()
