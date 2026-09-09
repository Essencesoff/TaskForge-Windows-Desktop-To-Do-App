"""Smart Planner: purely local heuristic scoring, no external API needed."""
import datetime as dt
from app.config.constants import PRIORITY_WEIGHT, DATE_FMT
from app.services import task_service


def _days_until(due_date):
    if not due_date:
        return 999
    try:
        d = dt.datetime.strptime(due_date, DATE_FMT).date()
        return (d - dt.date.today()).days
    except ValueError:
        return 999


def suggest_order():
    """Score = priority weight scaled + urgency bonus (closer deadline => higher),
    with a small penalty for very long estimated durations so quick wins
    don't get buried behind a single huge task."""
    tasks = [t for t in task_service.list_tasks(include_deleted=False)
             if t.status not in ("Completed", "Archived")]

    scored = []
    for t in tasks:
        days = _days_until(t.due_date)
        urgency = max(0, 30 - days) if days < 999 else 0
        if days < 0:
            urgency += 25  # overdue gets a strong bump
        priority_score = PRIORITY_WEIGHT.get(t.priority, 2) * 10
        duration_penalty = min(10, (t.estimated_minutes or 0) / 30)
        score = priority_score + urgency - duration_penalty
        scored.append((score, t))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [t for _, t in scored]
