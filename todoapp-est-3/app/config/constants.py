"""Central constants, enums and default values for the To-Do app."""
import os
import sys

APP_NAME = "TaskForge"
ORG_NAME = "TaskForgeApps"


def get_data_dir() -> str:
    """Return a writable per-user data directory (never next to the exe)."""
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
    else:
        base = os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
    path = os.path.join(base, APP_NAME)
    os.makedirs(path, exist_ok=True)
    return path


def get_db_path() -> str:
    return os.path.join(get_data_dir(), "taskforge.db")


def get_backup_dir() -> str:
    path = os.path.join(get_data_dir(), "backups")
    os.makedirs(path, exist_ok=True)
    return path


def get_log_path() -> str:
    return os.path.join(get_data_dir(), "app.log")


# ---- Enums (stored as plain strings in SQLite for simplicity/portability) ----
STATUSES = ["To Do", "In Progress", "Completed", "Archived"]
PRIORITIES = ["Low", "Medium", "High", "Critical"]
PRIORITY_COLORS = {
    "Low": "#4CAF50",
    "Medium": "#FFC107",
    "High": "#FF9800",
    "Critical": "#F44336",
}
PRIORITY_WEIGHT = {"Low": 1, "Medium": 2, "High": 3, "Critical": 4}

RECURRENCE_TYPES = ["None", "Daily", "Weekdays", "Weekly", "Monthly", "Custom"]

DEFAULT_CATEGORIES = [
    # name, icon (emoji), color, description
    ("School", "\U0001F4DA", "#5C6BC0", "Homework, classes and exams"),
    ("Work", "\U0001F4BC", "#26A69A", "Professional tasks and projects"),
    ("Personal", "\U0001F3E0", "#EC407A", "Personal life and errands"),
    ("Goals", "\U0001F3AF", "#AB47BC", "Long-term goals"),
    ("Ideas", "\U0001F4A1", "#FFA726", "Ideas and things to explore"),
]

REMINDER_OFFSETS_MIN = {
    "5 minutes before": 5,
    "15 minutes before": 15,
    "30 minutes before": 30,
    "1 hour before": 60,
    "1 day before": 1440,
}

POMODORO_DEFAULT_FOCUS_MIN = 25
POMODORO_DEFAULT_BREAK_MIN = 5

DATE_FMT = "%Y-%m-%d"
TIME_FMT = "%H:%M"
DATETIME_FMT = "%Y-%m-%d %H:%M"
