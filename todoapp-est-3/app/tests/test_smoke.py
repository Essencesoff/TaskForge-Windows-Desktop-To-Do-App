"""Basic smoke tests covering the core service layer.

Run with:  python -m pytest app/tests -q
(Requires QT_QPA_PLATFORM=offscreen on machines without a display, and a
QApplication instance since some services build Qt colors/icons indirectly.)
"""
import os
import sys
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication


@pytest.fixture(scope="session", autouse=True)
def qapp():
    app = QApplication.instance() or QApplication(sys.argv)
    yield app


@pytest.fixture(autouse=True)
def isolated_db(monkeypatch, tmp_path):
    """Point the app at a throwaway SQLite file per test."""
    from app.config import constants
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(constants, "get_db_path", lambda: str(db_path))
    from app.database import db as db_module
    db_module._conn = None
    db_module.init_db()
    yield
    db_module._conn = None


def test_default_categories_seeded():
    from app.services import category_service
    cats = category_service.list_categories()
    names = {c.name for c in cats}
    assert {"School", "Work", "Personal", "Goals", "Ideas"}.issubset(names)


def test_create_and_complete_task():
    from app.services import task_service, category_service
    from app.models.task import Task

    cat = category_service.list_categories()[0]
    task = task_service.create_task(Task(id=None, title="Test task", category_id=cat.id))
    assert task.id is not None

    task_service.complete_task(task.id)
    reloaded = task_service.get_task(task.id)
    assert reloaded.status == "Completed"


def test_recurring_task_spawns_next_occurrence():
    from app.services import task_service
    from app.models.task import Task
    import datetime as dt

    today = dt.date.today().strftime("%Y-%m-%d")
    task = task_service.create_task(
        Task(id=None, title="Daily habit", due_date=today, recurrence="Daily"))
    task_service.complete_task(task.id)

    all_tasks = task_service.list_tasks()
    titles = [t.title for t in all_tasks]
    assert titles.count("Daily habit") == 2


def test_soft_delete_and_undo():
    from app.services import task_service
    from app.models.task import Task

    task = task_service.create_task(Task(id=None, title="Delete me"))
    task_service.soft_delete_task(task.id)
    assert task_service.get_task(task.id).is_deleted is True

    entry = task_service.pop_undo()
    assert entry["action"] == "delete"
    task_service.restore_task(entry["payload"]["task_id"])
    assert task_service.get_task(task.id).is_deleted is False


def test_smart_planner_orders_by_urgency_and_priority():
    from app.services import task_service, planner_service
    from app.models.task import Task
    import datetime as dt

    soon = (dt.date.today() + dt.timedelta(days=1)).strftime("%Y-%m-%d")
    far = (dt.date.today() + dt.timedelta(days=30)).strftime("%Y-%m-%d")
    task_service.create_task(Task(id=None, title="Urgent critical", due_date=soon, priority="Critical"))
    task_service.create_task(Task(id=None, title="Distant low", due_date=far, priority="Low"))

    order = planner_service.suggest_order()
    assert order[0].title == "Urgent critical"


def test_goal_progress_calculation():
    from app.services import goal_service, task_service
    from app.models.task import Task

    goal = goal_service.create_goal("Learn PySide6")
    t1 = task_service.create_task(Task(id=None, title="Read docs", goal_id=goal.id))
    task_service.create_task(Task(id=None, title="Build app", goal_id=goal.id))
    task_service.complete_task(t1.id)

    goals = goal_service.list_goals()
    g = next(g for g in goals if g["id"] == goal.id)
    assert g["total_tasks"] == 2
    assert g["completed_tasks"] == 1
    assert g["progress_pct"] == 50


def test_export_import_json_roundtrip(tmp_path):
    from app.services import task_service, backup_service
    from app.models.task import Task

    task_service.create_task(Task(id=None, title="Exportable", tags=["a", "b"]))
    path = tmp_path / "export.json"
    backup_service.export_json(str(path))
    assert path.exists()

    backup_service.import_json(str(path))
    titles = [t.title for t in task_service.list_tasks()]
    assert titles.count("Exportable") == 2  # original + re-imported copy
