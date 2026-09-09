"""Lightweight dataclass wrappers around DB rows. Not an ORM on purpose —
the app is small enough that plain SQL in services/ stays readable and fast.
"""
from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class Subtask:
    id: Optional[int]
    task_id: Optional[int]
    title: str
    is_done: bool = False
    sort_order: int = 0


@dataclass
class Task:
    id: Optional[int]
    title: str
    description: str = ""
    due_date: Optional[str] = None
    due_time: Optional[str] = None
    priority: str = "Medium"
    category_id: Optional[int] = None
    status: str = "To Do"
    notes: str = ""
    estimated_minutes: int = 0
    reminder_offset_min: Optional[int] = None
    reminder_fired: bool = False
    recurrence: str = "None"
    recurrence_data: str = ""
    goal_id: Optional[int] = None
    is_favorite: bool = False
    is_deleted: bool = False
    sort_order: int = 0
    created_at: Optional[str] = None
    completed_at: Optional[str] = None
    deleted_at: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    subtasks: List[Subtask] = field(default_factory=list)

    @staticmethod
    def from_row(row: dict) -> "Task":
        data = {k: v for k, v in row.items() if k in Task.__dataclass_fields__}
        data["is_favorite"] = bool(row.get("is_favorite", 0))
        data["is_deleted"] = bool(row.get("is_deleted", 0))
        data["reminder_fired"] = bool(row.get("reminder_fired", 0))
        return Task(**data)


@dataclass
class Category:
    id: Optional[int]
    name: str
    icon: str = ""
    color: str = "#5C6BC0"
    description: str = ""


@dataclass
class Goal:
    id: Optional[int]
    title: str
    description: str = ""
    deadline: Optional[str] = None
    created_at: Optional[str] = None
    is_deleted: bool = False
