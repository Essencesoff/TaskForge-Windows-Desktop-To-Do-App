"""Reminder checking. Runs on a QTimer in the GUI thread (lightweight DB
query every 30s), so it keeps working while minimized to the tray as long
as the process is alive."""
import datetime as dt
import logging
from app.database import db
from app.config.constants import DATE_FMT, TIME_FMT

log = logging.getLogger("taskforge.reminders")


def due_reminders():
    """Return tasks whose reminder window has arrived and hasn't fired yet."""
    now = dt.datetime.now()
    rows = db.query_all(
        "SELECT * FROM tasks WHERE is_deleted=0 AND reminder_fired=0 "
        "AND reminder_offset_min IS NOT NULL AND due_date IS NOT NULL "
        "AND status NOT IN ('Completed','Archived')"
    )
    due = []
    for r in rows:
        try:
            time_part = r["due_time"] or "23:59"
            due_dt = dt.datetime.strptime(f"{r['due_date']} {time_part}", f"{DATE_FMT} {TIME_FMT}")
        except ValueError:
            continue
        remind_at = due_dt - dt.timedelta(minutes=r["reminder_offset_min"])
        if remind_at <= now <= due_dt:
            due.append(r)
    return due


def mark_fired(task_id: int):
    db.execute("UPDATE tasks SET reminder_fired=1 WHERE id=?", (task_id,))


def overdue_unnotified_key(task_id: int) -> str:
    return f"overdue_notified_{task_id}"
