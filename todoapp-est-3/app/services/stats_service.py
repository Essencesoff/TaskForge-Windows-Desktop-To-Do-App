import datetime as dt
from app.database import db
from app.config.constants import DATE_FMT


def today_progress():
    today = dt.date.today().strftime(DATE_FMT)
    rows = db.query_all(
        "SELECT status FROM tasks WHERE is_deleted=0 AND due_date=?", (today,))
    total = len(rows)
    completed = sum(1 for r in rows if r["status"] == "Completed")
    overdue_rows = db.query_all(
        "SELECT id FROM tasks WHERE is_deleted=0 AND status NOT IN ('Completed','Archived') "
        "AND due_date IS NOT NULL AND due_date<?", (today,))
    return {
        "total": total,
        "completed": completed,
        "remaining": total - completed,
        "overdue": len(overdue_rows),
        "pct": round(completed / total * 100) if total else 0,
    }


def current_and_best_streak():
    rows = db.query_all("SELECT date FROM daily_stats WHERE completed_count>0 ORDER BY date DESC")
    dates = set()
    for r in rows:
        try:
            dates.add(dt.datetime.strptime(r["date"], DATE_FMT).date())
        except ValueError:
            pass
    if not dates:
        return {"current": 0, "best": 0}

    # current streak: walk back from today (or yesterday if today has no entry yet)
    current = 0
    cursor = dt.date.today()
    if cursor not in dates:
        cursor -= dt.timedelta(days=1)
    while cursor in dates:
        current += 1
        cursor -= dt.timedelta(days=1)

    # best streak: scan sorted date list for longest consecutive run
    sorted_dates = sorted(dates)
    best = 1
    run = 1
    for i in range(1, len(sorted_dates)):
        if (sorted_dates[i] - sorted_dates[i - 1]).days == 1:
            run += 1
            best = max(best, run)
        else:
            run = 1
    return {"current": current, "best": best}


def completed_counts(period: str = "week"):
    today = dt.date.today()
    if period == "today":
        start = today
    elif period == "week":
        start = today - dt.timedelta(days=today.weekday())
    else:  # month
        start = today.replace(day=1)
    rows = db.query_all(
        "SELECT date, completed_count FROM daily_stats WHERE date>=? ORDER BY date",
        (start.strftime(DATE_FMT),))
    return rows


def tasks_by_category():
    return db.query_all(
        "SELECT COALESCE(c.name,'Uncategorized') AS name, COUNT(*) AS count "
        "FROM tasks t LEFT JOIN categories c ON c.id=t.category_id "
        "WHERE t.is_deleted=0 GROUP BY c.id ORDER BY count DESC")


def tasks_by_priority():
    return db.query_all(
        "SELECT priority, COUNT(*) AS count FROM tasks WHERE is_deleted=0 "
        "GROUP BY priority")


def productivity_series(days: int = 30):
    today = dt.date.today()
    start = today - dt.timedelta(days=days - 1)
    rows = {r["date"]: r["completed_count"] for r in db.query_all(
        "SELECT date, completed_count FROM daily_stats WHERE date>=?", (start.strftime(DATE_FMT),))}
    series = []
    for i in range(days):
        d = (start + dt.timedelta(days=i)).strftime(DATE_FMT)
        series.append({"date": d, "count": rows.get(d, 0)})
    return series
