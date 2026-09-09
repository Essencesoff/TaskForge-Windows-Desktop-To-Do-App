import json
import csv
import shutil
import datetime as dt
import os
from app.database import db
from app.config.constants import get_db_path, get_backup_dir


def export_json(path: str):
    data = {
        "categories": db.query_all("SELECT * FROM categories"),
        "tasks": db.query_all("SELECT * FROM tasks"),
        "subtasks": db.query_all("SELECT * FROM subtasks"),
        "goals": db.query_all("SELECT * FROM goals"),
        "tags": db.query_all("SELECT * FROM tags"),
        "task_tags": db.query_all("SELECT * FROM task_tags"),
        "exported_at": dt.datetime.now().isoformat(),
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def import_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    name_to_new_cat = {}
    for c in data.get("categories", []):
        existing = db.query_one("SELECT id FROM categories WHERE name=?", (c["name"],))
        if existing:
            name_to_new_cat[c["id"]] = existing["id"]
        else:
            cur = db.execute(
                "INSERT INTO categories (name, icon, color, description) VALUES (?,?,?,?)",
                (c["name"], c.get("icon", ""), c.get("color", "#5C6BC0"), c.get("description", "")))
            name_to_new_cat[c["id"]] = cur.lastrowid

    old_to_new_task = {}
    for t in data.get("tasks", []):
        new_cat = name_to_new_cat.get(t.get("category_id"))
        cur = db.execute(
            """INSERT INTO tasks (title, description, due_date, due_time, priority, category_id,
            status, notes, estimated_minutes, reminder_offset_min, recurrence, recurrence_data,
            is_favorite, sort_order, created_at, completed_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (t["title"], t.get("description", ""), t.get("due_date"), t.get("due_time"),
             t.get("priority", "Medium"), new_cat, t.get("status", "To Do"), t.get("notes", ""),
             t.get("estimated_minutes", 0), t.get("reminder_offset_min"), t.get("recurrence", "None"),
             t.get("recurrence_data", ""), t.get("is_favorite", 0), t.get("sort_order", 0),
             t.get("created_at"), t.get("completed_at")))
        old_to_new_task[t["id"]] = cur.lastrowid

    for st in data.get("subtasks", []):
        new_task_id = old_to_new_task.get(st["task_id"])
        if new_task_id:
            db.execute("INSERT INTO subtasks (task_id, title, is_done, sort_order) VALUES (?,?,?,?)",
                       (new_task_id, st["title"], st.get("is_done", 0), st.get("sort_order", 0)))

    for tag in data.get("tags", []):
        db.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (tag["name"],))


def export_csv(path: str):
    tasks = db.query_all("SELECT * FROM tasks WHERE is_deleted=0")
    if not tasks:
        with open(path, "w", newline="", encoding="utf-8") as f:
            f.write("")
        return
    fieldnames = list(tasks[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(tasks)


def create_backup() -> str:
    ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = os.path.join(get_backup_dir(), f"backup_{ts}.db")
    shutil.copy2(get_db_path(), dest)
    _prune_old_backups()
    return dest


def _prune_old_backups(keep: int = 10):
    backups = sorted(
        (f for f in os.listdir(get_backup_dir()) if f.endswith(".db")),
        reverse=True,
    )
    for old in backups[keep:]:
        try:
            os.remove(os.path.join(get_backup_dir(), old))
        except OSError:
            pass


def restore_backup(backup_path: str):
    global_conn = db.get_conn()
    global_conn.close()
    db._conn = None
    shutil.copy2(backup_path, get_db_path())
    db.get_conn()


def list_backups():
    d = get_backup_dir()
    files = sorted(
        (f for f in os.listdir(d) if f.endswith(".db")),
        reverse=True,
    )
    return [os.path.join(d, f) for f in files]


def clear_all_data():
    for table in ["task_tags", "subtasks", "tasks", "tags", "goals", "habit_logs",
                  "habits", "pomodoro_sessions", "daily_stats", "achievements"]:
        db.execute(f"DELETE FROM {table}")
