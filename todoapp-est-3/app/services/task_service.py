"""All task-related business logic (CRUD, search, trash, recurrence)."""
import datetime as dt
import logging
from typing import Optional, List

from app.database import db
from app.models.task import Task, Subtask
from app.config.constants import DATE_FMT

log = logging.getLogger("taskforge.tasks")

# In-memory single-slot undo buffer: (action, payload)
_undo_stack: List[dict] = []
MAX_UNDO = 20


def _now():
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _push_undo(action: str, payload: dict):
    _undo_stack.append({"action": action, "payload": payload})
    if len(_undo_stack) > MAX_UNDO:
        _undo_stack.pop(0)


def pop_undo() -> Optional[dict]:
    if _undo_stack:
        return _undo_stack.pop()
    return None


def _row_to_task(row: dict) -> Task:
    task = Task.from_row(row)
    task.tags = [r["name"] for r in db.query_all(
        "SELECT t.name FROM tags t JOIN task_tags tt ON tt.tag_id=t.id WHERE tt.task_id=?",
        (task.id,))]
    task.subtasks = [
        Subtask(id=r["id"], task_id=r["task_id"], title=r["title"],
                is_done=bool(r["is_done"]), sort_order=r["sort_order"])
        for r in db.query_all(
            "SELECT * FROM subtasks WHERE task_id=? ORDER BY sort_order", (task.id,))
    ]
    return task


def get_task(task_id: int) -> Optional[Task]:
    row = db.query_one("SELECT * FROM tasks WHERE id=?", (task_id,))
    return _row_to_task(row) if row else None


def list_tasks(status: Optional[str] = None, category_id: Optional[int] = None,
                include_deleted: bool = False, favorites_only: bool = False,
                search: Optional[str] = None, priority: Optional[str] = None,
                date_from: Optional[str] = None, date_to: Optional[str] = None) -> List[Task]:
    clauses = []
    params = []
    if not include_deleted:
        clauses.append("is_deleted=0")
    if status:
        clauses.append("status=?")
        params.append(status)
    if category_id is not None:
        clauses.append("category_id=?")
        params.append(category_id)
    if favorites_only:
        clauses.append("is_favorite=1")
    if priority:
        clauses.append("priority=?")
        params.append(priority)
    if date_from:
        clauses.append("due_date>=?")
        params.append(date_from)
    if date_to:
        clauses.append("due_date<=?")
        params.append(date_to)
    if search:
        like = f"%{search}%"
        clauses.append(
            "(title LIKE ? OR description LIKE ? OR notes LIKE ? OR id IN "
            "(SELECT tt.task_id FROM task_tags tt JOIN tags t ON t.id=tt.tag_id WHERE t.name LIKE ?))"
        )
        params.extend([like, like, like, like])
    where = " AND ".join(clauses) if clauses else "1=1"
    rows = db.query_all(f"SELECT * FROM tasks WHERE {where} ORDER BY sort_order, due_date IS NULL, due_date", tuple(params))
    return [_row_to_task(r) for r in rows]


def create_task(task: Task) -> Task:
    task.created_at = task.created_at or _now()
    cur = db.execute(
        """INSERT INTO tasks
        (title, description, due_date, due_time, priority, category_id, status, notes,
         estimated_minutes, reminder_offset_min, recurrence, recurrence_data, goal_id,
         is_favorite, sort_order, created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (task.title, task.description, task.due_date, task.due_time, task.priority,
         task.category_id, task.status, task.notes, task.estimated_minutes,
         task.reminder_offset_min, task.recurrence, task.recurrence_data, task.goal_id,
         int(task.is_favorite), task.sort_order, task.created_at),
    )
    task.id = cur.lastrowid
    _sync_tags(task.id, task.tags)
    _sync_subtasks(task.id, task.subtasks)
    log.info("Created task #%s: %s", task.id, task.title)
    return get_task(task.id)


def update_task(task: Task) -> Task:
    db.execute(
        """UPDATE tasks SET title=?, description=?, due_date=?, due_time=?, priority=?,
        category_id=?, status=?, notes=?, estimated_minutes=?, reminder_offset_min=?,
        recurrence=?, recurrence_data=?, goal_id=?, is_favorite=? WHERE id=?""",
        (task.title, task.description, task.due_date, task.due_time, task.priority,
         task.category_id, task.status, task.notes, task.estimated_minutes,
         task.reminder_offset_min, task.recurrence, task.recurrence_data, task.goal_id,
         int(task.is_favorite), task.id),
    )
    _sync_tags(task.id, task.tags)
    _sync_subtasks(task.id, task.subtasks)
    return get_task(task.id)


def _sync_tags(task_id: int, tag_names: List[str]):
    db.execute("DELETE FROM task_tags WHERE task_id=?", (task_id,))
    for name in tag_names or []:
        name = name.strip()
        if not name:
            continue
        db.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (name,))
        row = db.query_one("SELECT id FROM tags WHERE name=?", (name,))
        db.execute("INSERT OR IGNORE INTO task_tags (task_id, tag_id) VALUES (?,?)",
                   (task_id, row["id"]))


def _sync_subtasks(task_id: int, subtasks: List[Subtask]):
    db.execute("DELETE FROM subtasks WHERE task_id=?", (task_id,))
    for i, st in enumerate(subtasks or []):
        db.execute(
            "INSERT INTO subtasks (task_id, title, is_done, sort_order) VALUES (?,?,?,?)",
            (task_id, st.title, int(st.is_done), i),
        )


def complete_task(task_id: int):
    task = get_task(task_id)
    if not task:
        return
    db.execute("UPDATE tasks SET status='Completed', completed_at=? WHERE id=?",
               (_now(), task_id))
    _bump_daily_stat(dt.date.today().strftime(DATE_FMT))
    _push_undo("complete", {"task_id": task_id, "prev_status": task.status})
    if task.recurrence and task.recurrence != "None":
        _spawn_next_recurrence(task)


def uncomplete_task(task_id: int):
    db.execute("UPDATE tasks SET status='To Do', completed_at=NULL WHERE id=?", (task_id,))


def _spawn_next_recurrence(task: Task):
    """Create the next occurrence of a recurring task."""
    if not task.due_date:
        return
    try:
        current = dt.datetime.strptime(task.due_date, DATE_FMT).date()
    except ValueError:
        return
    if task.recurrence == "Daily":
        nxt = current + dt.timedelta(days=1)
    elif task.recurrence == "Weekly":
        nxt = current + dt.timedelta(weeks=1)
    elif task.recurrence == "Weekdays":
        nxt = current + dt.timedelta(days=1)
        while nxt.weekday() >= 5:
            nxt += dt.timedelta(days=1)
    elif task.recurrence == "Monthly":
        month = current.month % 12 + 1
        year = current.year + (1 if current.month == 12 else 0)
        day = min(current.day, 28)
        nxt = dt.date(year, month, day)
    elif task.recurrence == "Custom":
        days = [d.strip()[:3].lower() for d in (task.recurrence_data or "").split(",") if d.strip()]
        wd_map = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}
        target_days = {wd_map[d] for d in days if d in wd_map}
        if not target_days:
            return
        nxt = current + dt.timedelta(days=1)
        for _ in range(14):
            if nxt.weekday() in target_days:
                break
            nxt += dt.timedelta(days=1)
    else:
        return

    new_task = Task(
        id=None, title=task.title, description=task.description,
        due_date=nxt.strftime(DATE_FMT), due_time=task.due_time, priority=task.priority,
        category_id=task.category_id, status="To Do", notes=task.notes,
        estimated_minutes=task.estimated_minutes, reminder_offset_min=task.reminder_offset_min,
        recurrence=task.recurrence, recurrence_data=task.recurrence_data, goal_id=task.goal_id,
        tags=list(task.tags),
    )
    create_task(new_task)


def soft_delete_task(task_id: int):
    task = get_task(task_id)
    if not task:
        return
    db.execute("UPDATE tasks SET is_deleted=1, deleted_at=? WHERE id=?", (_now(), task_id))
    _push_undo("delete", {"task_id": task_id})


def restore_task(task_id: int):
    db.execute("UPDATE tasks SET is_deleted=0, deleted_at=NULL WHERE id=?", (task_id,))


def permanently_delete_task(task_id: int):
    db.execute("DELETE FROM tasks WHERE id=?", (task_id,))


def empty_trash():
    db.execute("DELETE FROM tasks WHERE is_deleted=1", ())


def duplicate_task(task_id: int) -> Optional[Task]:
    task = get_task(task_id)
    if not task:
        return None
    task.id = None
    task.title = f"{task.title} (copy)"
    task.status = "To Do"
    task.completed_at = None
    task.created_at = _now()
    return create_task(task)


def toggle_favorite(task_id: int):
    task = get_task(task_id)
    if task:
        db.execute("UPDATE tasks SET is_favorite=? WHERE id=?",
                   (0 if task.is_favorite else 1, task_id))


def reorder_tasks(ordered_ids: List[int]):
    for i, tid in enumerate(ordered_ids):
        db.execute("UPDATE tasks SET sort_order=? WHERE id=?", (i, tid))


def toggle_subtask(subtask_id: int):
    row = db.query_one("SELECT is_done FROM subtasks WHERE id=?", (subtask_id,))
    if row:
        db.execute("UPDATE subtasks SET is_done=? WHERE id=?",
                   (0 if row["is_done"] else 1, subtask_id))


def _bump_daily_stat(date_str: str):
    row = db.query_one("SELECT completed_count FROM daily_stats WHERE date=?", (date_str,))
    if row:
        db.execute("UPDATE daily_stats SET completed_count=completed_count+1 WHERE date=?",
                   (date_str,))
    else:
        db.execute("INSERT INTO daily_stats (date, completed_count) VALUES (?,1)", (date_str,))


def overdue_tasks() -> List[Task]:
    today = dt.date.today().strftime(DATE_FMT)
    rows = db.query_all(
        "SELECT * FROM tasks WHERE is_deleted=0 AND status NOT IN ('Completed','Archived') "
        "AND due_date IS NOT NULL AND due_date<?", (today,))
    return [_row_to_task(r) for r in rows]


def upcoming_tasks(days: int = 7) -> List[Task]:
    today = dt.date.today()
    end = (today + dt.timedelta(days=days)).strftime(DATE_FMT)
    rows = db.query_all(
        "SELECT * FROM tasks WHERE is_deleted=0 AND status NOT IN ('Completed','Archived') "
        "AND due_date BETWEEN ? AND ? ORDER BY due_date, due_time",
        (today.strftime(DATE_FMT), end))
    return [_row_to_task(r) for r in rows]
