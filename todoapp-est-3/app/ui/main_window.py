import sys
import logging
from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
                                QStackedWidget, QLabel, QSystemTrayIcon, QMenu, QMessageBox,
                                QButtonGroup)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QAction, QKeySequence, QShortcut, QPixmap, QPainter, QColor, QFont

from app.services import task_service, settings_service, reminder_service
from app.utils import theme
from app.config.constants import APP_NAME
from app.dialogs.quick_add_dialog import QuickAddDialog
from app.dialogs.task_editor_dialog import TaskEditorDialog

from app.ui.dashboard import DashboardPage
from app.ui.tasks_view import TasksPage
from app.ui.calendar_view import CalendarPage
from app.ui.statistics_view import StatisticsPage
from app.ui.goals_view import GoalsPage
from app.ui.pomodoro_view import PomodoroPage
from app.ui.categories_view import CategoriesPage
from app.ui.trash_view import TrashPage
from app.ui.shortcuts_view import ShortcutsPage
from app.ui.settings_view import SettingsPage
from app.ui.planner_view import PlannerPage

log = logging.getLogger("taskforge.ui")

NAV_ITEMS = [
    ("dashboard", "\U0001F3E0  Dashboard"),
    ("tasks", "\u2705  Tasks"),
    ("planner", "\U0001F9E0  Smart Planner"),
    ("calendar", "\U0001F4C5  Calendar"),
    ("goals", "\U0001F3AF  Goals"),
    ("pomodoro", "\u23F1\uFE0F  Pomodoro"),
    ("statistics", "\U0001F4CA  Statistics"),
    ("categories", "\U0001F4C2  Categories"),
    ("trash", "\U0001F5D1\uFE0F  Trash"),
    ("shortcuts", "\u2328\uFE0F  Shortcuts"),
    ("settings", "\u2699\uFE0F  Settings"),
]


def _make_app_icon() -> QIcon:
    """Generate a simple rounded checkmark app icon in-memory (no asset file needed)."""
    pix = QPixmap(64, 64)
    pix.fill(Qt.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setBrush(QColor("#6C7CFF"))
    painter.setPen(Qt.NoPen)
    painter.drawRoundedRect(4, 4, 56, 56, 16, 16)
    painter.setPen(QColor("white"))
    font = QFont()
    font.setPointSize(28)
    font.setBold(True)
    painter.setFont(font)
    painter.drawText(pix.rect(), Qt.AlignCenter, "\u2713")
    painter.end()
    return QIcon(pix)


class MainWindow(QMainWindow):
    def __init__(self, user_name: str = "there"):
        super().__init__()
        self.user_name = user_name
        self.setWindowTitle(APP_NAME)
        self.resize(1180, 760)
        self.app_icon = _make_app_icon()
        self.setWindowIcon(self.app_icon)

        self._build_ui()
        self._build_tray()
        self._build_shortcuts()
        self.apply_theme()

        self.reminder_timer = QTimer(self)
        self.reminder_timer.setInterval(30_000)  # check every 30s
        self.reminder_timer.timeout.connect(self.check_reminders)
        self.reminder_timer.start()
        self.check_reminders()

    # ---------------------------------------------------------------- UI ---
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        sidebar = QWidget()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(220)
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(12, 20, 12, 20)

        brand = QLabel(f"\u2705 {APP_NAME}")
        brand.setStyleSheet("font-size: 18px; font-weight: 700; padding: 0 8px 16px 8px;")
        side_layout.addWidget(brand)

        self.nav_buttons = {}
        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        for key, label in NAV_ITEMS:
            btn = QPushButton(label)
            btn.setObjectName("NavButton")
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, k=key: self.navigate(k))
            side_layout.addWidget(btn)
            self.nav_group.addButton(btn)
            self.nav_buttons[key] = btn
        side_layout.addStretch()

        quick_add_btn = QPushButton("+ Quick Add (Ctrl+N)")
        quick_add_btn.setObjectName("Primary")
        quick_add_btn.clicked.connect(self.open_quick_add)
        side_layout.addWidget(quick_add_btn)

        root.addWidget(sidebar)

        self.stack = QStackedWidget()
        root.addWidget(self.stack, 1)

        self.pages = {
            "dashboard": DashboardPage(self),
            "tasks": TasksPage(self),
            "planner": PlannerPage(self),
            "calendar": CalendarPage(self),
            "goals": GoalsPage(self),
            "pomodoro": PomodoroPage(self),
            "statistics": StatisticsPage(self),
            "categories": CategoriesPage(self),
            "trash": TrashPage(self),
            "shortcuts": ShortcutsPage(self),
            "settings": SettingsPage(self),
        }
        for key, _ in NAV_ITEMS:
            self.stack.addWidget(self.pages[key])

        self.navigate("dashboard")

    def navigate(self, key: str):
        self.nav_buttons[key].setChecked(True)
        self.stack.setCurrentWidget(self.pages[key])
        page = self.pages[key]
        if hasattr(page, "refresh"):
            page.refresh()
        if key == "tasks":
            page.setFocus()

    # ------------------------------------------------------------- Tray ---
    def _build_tray(self):
        self.tray = QSystemTrayIcon(self.app_icon, self)
        self.tray.setToolTip(APP_NAME)
        menu = QMenu()
        show_action = QAction("Open", self)
        show_action.triggered.connect(self.showNormal)
        menu.addAction(show_action)
        quick_add_action = QAction("Quick Add Task", self)
        quick_add_action.triggered.connect(self.open_quick_add)
        menu.addAction(quick_add_action)
        menu.addSeparator()
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self._quit_app)
        menu.addAction(quit_action)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.show()

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.showNormal()
            self.activateWindow()

    def _quit_app(self):
        from PySide6.QtWidgets import QApplication
        self.tray.hide()
        QApplication.quit()

    def closeEvent(self, event):
        """Minimize to tray instead of quitting, so reminders keep working."""
        if self.tray.isVisible():
            event.ignore()
            self.hide()
            self.tray.showMessage(APP_NAME, "Still running in the system tray.",
                                   self.app_icon, 2000)
        else:
            event.accept()

    def notify(self, title: str, message: str):
        if settings_service.get_bool("notifications_enabled"):
            self.tray.showMessage(title, message, self.app_icon, 5000)

    # -------------------------------------------------------- Shortcuts ---
    def _build_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+N"), self, activated=self.open_quick_add)
        QShortcut(QKeySequence("Ctrl+F"), self, activated=self._focus_search)
        QShortcut(QKeySequence("Ctrl+K"), self, activated=self.open_quick_add)
        QShortcut(QKeySequence("Ctrl+,"), self, activated=lambda: self.navigate("settings"))

    def _focus_search(self):
        self.navigate("tasks")
        self.pages["tasks"].focus_search()

    # ----------------------------------------------------------- Theme ---
    def apply_theme(self):
        from PySide6.QtWidgets import QApplication
        mode = settings_service.get("theme", "dark")
        if mode == "system":
            mode = theme.detect_system_theme()
        QApplication.instance().setStyleSheet(theme.get_stylesheet(mode))

    # ------------------------------------------------------- Task ops ----
    def open_quick_add(self):
        dlg = QuickAddDialog(self)
        if dlg.exec():
            task_service.create_task(dlg.get_task())
            self.refresh_all()

    def open_task_editor(self, task_id: int = None, prefill_date: str = None):
        task = task_service.get_task(task_id) if task_id else None
        dlg = TaskEditorDialog(task, self)
        if prefill_date and not task:
            dlg.due_date_check.setChecked(True)
            y, m, d = map(int, prefill_date.split("-"))
            from PySide6.QtCore import QDate
            dlg.date_edit.setDate(QDate(y, m, d))
        if dlg.exec():
            new_task = dlg.get_task()
            if task:
                task_service.update_task(new_task)
            else:
                task_service.create_task(new_task)
            self.refresh_all()

    def handle_complete_toggle(self, task_id: int, checked: bool):
        if checked:
            task_service.complete_task(task_id)
        else:
            task_service.uncomplete_task(task_id)
        self.refresh_all()
        self._show_undo_toast("Task updated")

    def handle_delete_task(self, task_id: int):
        task_service.soft_delete_task(task_id)
        self.refresh_all()
        self._show_undo_toast("Task moved to Trash")

    def handle_duplicate_task(self, task_id: int):
        task_service.duplicate_task(task_id)
        self.refresh_all()

    def handle_favorite_toggle(self, task_id: int):
        task_service.toggle_favorite(task_id)
        self.refresh_all()

    def _show_undo_toast(self, message: str):
        self.statusBar().showMessage(f"{message}  \u2014  Ctrl+Z to undo", 4000)

    def undo_last_action(self):
        entry = task_service.pop_undo()
        if not entry:
            return
        action, payload = entry["action"], entry["payload"]
        if action == "delete":
            task_service.restore_task(payload["task_id"])
        elif action == "complete":
            task_service.uncomplete_task(payload["task_id"])
        self.refresh_all()

    def keyPressEvent(self, event):
        if event.matches(QKeySequence.Undo):
            self.undo_last_action()
            return
        super().keyPressEvent(event)

    # --------------------------------------------------------- Refresh ---
    def refresh_all(self):
        for page in self.pages.values():
            if hasattr(page, "refresh"):
                page.refresh()

    def refresh_category_dependents(self):
        for key in ("dashboard", "tasks", "calendar", "trash"):
            page = self.pages[key]
            if hasattr(page, "_reload_categories"):
                page._reload_categories()
            if hasattr(page, "refresh"):
                page.refresh()

    # ------------------------------------------------------- Reminders ---
    def check_reminders(self):
        try:
            due = reminder_service.due_reminders()
        except Exception as e:
            log.error("Reminder check failed: %s", e)
            return
        for row in due:
            self.notify("Upcoming: " + row["title"],
                         f"Due {row['due_date']} {row['due_time'] or ''}".strip())
            reminder_service.mark_fired(row["id"])

        overdue = task_service.overdue_tasks()
        if overdue and not getattr(self, "_overdue_notified_today", False):
            self.notify("Overdue tasks", f"You have {len(overdue)} overdue task(s).")
            self._overdue_notified_today = True

    # --------------------------------------------------- Windows startup -
    def set_launch_on_startup(self, enabled: bool):
        if sys.platform != "win32":
            return
        try:
            import winreg
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            reg_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
            if enabled:
                exe_path = sys.executable if getattr(sys, "frozen", False) else sys.argv[0]
                winreg.SetValueEx(reg_key, APP_NAME, 0, winreg.REG_SZ, f'"{exe_path}"')
            else:
                try:
                    winreg.DeleteValue(reg_key, APP_NAME)
                except FileNotFoundError:
                    pass
            winreg.CloseKey(reg_key)
        except OSError as e:
            log.warning("Could not update startup registry key: %s", e)
