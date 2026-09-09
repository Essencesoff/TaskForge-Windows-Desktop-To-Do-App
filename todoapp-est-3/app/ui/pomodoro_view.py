import datetime as dt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSpinBox, QComboBox
from PySide6.QtCore import QTimer, Qt

from app.database import db
from app.services import settings_service, task_service


class PomodoroPage(QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.remaining_seconds = 0
        self.is_running = False
        self.is_break = False
        self._session_start = None

        layout = QVBoxLayout(self)
        title = QLabel("Pomodoro Timer")
        title.setObjectName("Heading")
        layout.addWidget(title)

        layout.addWidget(QLabel("Attach to a task (optional)"))
        self.task_combo = QComboBox()
        self._reload_tasks()
        layout.addWidget(self.task_combo)

        self.time_label = QLabel("25:00")
        self.time_label.setAlignment(Qt.AlignCenter)
        self.time_label.setStyleSheet("font-size: 64px; font-weight: 700;")
        layout.addWidget(self.time_label)

        self.mode_label = QLabel("Focus session")
        self.mode_label.setAlignment(Qt.AlignCenter)
        self.mode_label.setObjectName("SubHeading")
        layout.addWidget(self.mode_label)

        settings_row = QHBoxLayout()
        settings_row.addWidget(QLabel("Focus (min)"))
        self.focus_spin = QSpinBox()
        self.focus_spin.setRange(1, 180)
        self.focus_spin.setValue(int(settings_service.get("pomodoro_focus_min", 25)))
        settings_row.addWidget(self.focus_spin)
        settings_row.addWidget(QLabel("Break (min)"))
        self.break_spin = QSpinBox()
        self.break_spin.setRange(1, 60)
        self.break_spin.setValue(int(settings_service.get("pomodoro_break_min", 5)))
        settings_row.addWidget(self.break_spin)
        layout.addLayout(settings_row)

        btn_row = QHBoxLayout()
        self.start_btn = QPushButton("Start")
        self.start_btn.setObjectName("Primary")
        self.start_btn.clicked.connect(self.toggle_timer)
        btn_row.addWidget(self.start_btn)
        self.reset_btn = QPushButton("Reset")
        self.reset_btn.clicked.connect(self.reset_timer)
        btn_row.addWidget(self.reset_btn)
        layout.addLayout(btn_row)

        self.sessions_label = QLabel()
        self.sessions_label.setObjectName("SubHeading")
        layout.addWidget(self.sessions_label)
        layout.addStretch()

        self.qtimer = QTimer(self)
        self.qtimer.setInterval(1000)
        self.qtimer.timeout.connect(self._tick)

        self.reset_timer()
        self._update_sessions_label()

    def _reload_tasks(self):
        self.task_combo.clear()
        self.task_combo.addItem("No task", None)
        for t in task_service.list_tasks(status="To Do") + task_service.list_tasks(status="In Progress"):
            self.task_combo.addItem(t.title, t.id)

    def reset_timer(self):
        self.is_running = False
        self.is_break = False
        self.remaining_seconds = self.focus_spin.value() * 60
        self.mode_label.setText("Focus session")
        self.start_btn.setText("Start")
        self.qtimer.stop()
        self._update_label()

    def toggle_timer(self):
        if self.is_running:
            self.qtimer.stop()
            self.is_running = False
            self.start_btn.setText("Resume")
        else:
            if self._session_start is None:
                self._session_start = dt.datetime.now()
            self.qtimer.start()
            self.is_running = True
            self.start_btn.setText("Pause")

    def _tick(self):
        self.remaining_seconds -= 1
        if self.remaining_seconds <= 0:
            self._complete_session()
            return
        self._update_label()

    def _complete_session(self):
        self.qtimer.stop()
        self.is_running = False
        kind = "break" if self.is_break else "focus"
        duration = (self.focus_spin.value() if not self.is_break else self.break_spin.value())
        db.execute(
            "INSERT INTO pomodoro_sessions (task_id, started_at, ended_at, duration_min, kind) VALUES (?,?,?,?,?)",
            (self.task_combo.currentData(),
             (self._session_start or dt.datetime.now()).strftime("%Y-%m-%d %H:%M:%S"),
             dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), duration, kind))
        self._session_start = None

        self.main_window.notify(
            "Focus session complete!" if not self.is_break else "Break over!",
            "Time for a break." if not self.is_break else "Back to focus."
        )

        self.is_break = not self.is_break
        self.remaining_seconds = (self.break_spin.value() if self.is_break else self.focus_spin.value()) * 60
        self.mode_label.setText("Break time" if self.is_break else "Focus session")
        self.start_btn.setText("Start")
        self._update_label()
        self._update_sessions_label()

    def _update_label(self):
        m, s = divmod(max(0, self.remaining_seconds), 60)
        self.time_label.setText(f"{m:02d}:{s:02d}")

    def _update_sessions_label(self):
        rows = db.query_all(
            "SELECT COUNT(*) AS c FROM pomodoro_sessions WHERE kind='focus' AND date(started_at)=date('now','localtime')")
        count = rows[0]["c"] if rows else 0
        self.sessions_label.setText(f"Focus sessions completed today: {count}")

    def refresh(self):
        self._reload_tasks()
        self._update_sessions_label()
