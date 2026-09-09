from app.database import db

DEFAULTS = {
    "theme": "dark",              # dark | light | system
    "ui_density": "comfortable",  # comfortable | compact
    "notifications_enabled": "1",
    "default_reminder_min": "30",
    "default_priority": "Medium",
    "default_category_id": "",
    "default_sort": "due_date",
    "start_minimized": "0",
    "launch_on_startup": "0",
    "pomodoro_focus_min": "25",
    "pomodoro_break_min": "5",
}


def get(key: str, default=None):
    row = db.query_one("SELECT value FROM settings WHERE key=?", (key,))
    if row:
        return row["value"]
    return DEFAULTS.get(key, default)


def set(key: str, value):
    value = str(value)
    existing = db.query_one("SELECT key FROM settings WHERE key=?", (key,))
    if existing:
        db.execute("UPDATE settings SET value=? WHERE key=?", (value, key))
    else:
        db.execute("INSERT INTO settings (key, value) VALUES (?,?)", (key, value))


def get_bool(key: str) -> bool:
    return str(get(key, "0")) == "1"


def get_all() -> dict:
    result = dict(DEFAULTS)
    for row in db.query_all("SELECT key, value FROM settings"):
        result[row["key"]] = row["value"]
    return result
