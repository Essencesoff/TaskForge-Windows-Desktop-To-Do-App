import datetime as dt
from typing import List, Optional
from app.database import db
from app.models.task import Goal


def list_goals(include_deleted: bool = False) -> List[dict]:
    where = "" if include_deleted else "WHERE is_deleted=0"
    rows = db.query_all(f"SELECT * FROM goals {where} ORDER BY deadline IS NULL, deadline")
    result = []
    for r in rows:
        tasks = db.query_all("SELECT status FROM tasks WHERE goal_id=? AND is_deleted=0", (r["id"],))
        total = len(tasks)
        done = sum(1 for t in tasks if t["status"] == "Completed")
        pct = round(done / total * 100) if total else 0
        result.append({**r, "total_tasks": total, "completed_tasks": done,
                        "remaining_tasks": total - done, "progress_pct": pct})
    return result


def create_goal(title: str, description: str = "", deadline: Optional[str] = None) -> Goal:
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur = db.execute("INSERT INTO goals (title, description, deadline, created_at) VALUES (?,?,?,?)",
                      (title, description, deadline, now))
    return Goal(id=cur.lastrowid, title=title, description=description, deadline=deadline, created_at=now)


def update_goal(goal: Goal):
    db.execute("UPDATE goals SET title=?, description=?, deadline=? WHERE id=?",
               (goal.title, goal.description, goal.deadline, goal.id))


def delete_goal(goal_id: int):
    db.execute("UPDATE tasks SET goal_id=NULL WHERE goal_id=?", (goal_id,))
    db.execute("UPDATE goals SET is_deleted=1 WHERE id=?", (goal_id,))
