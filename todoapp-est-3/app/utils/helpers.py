import datetime as dt
from app.config.constants import DATE_FMT


def format_friendly_date(date_str: str) -> str:
    if not date_str:
        return ""
    try:
        d = dt.datetime.strptime(date_str, DATE_FMT).date()
    except ValueError:
        return date_str
    today = dt.date.today()
    diff = (d - today).days
    if diff == 0:
        return "Today"
    if diff == 1:
        return "Tomorrow"
    if diff == -1:
        return "Yesterday"
    return d.strftime("%a, %b %d")


def greeting_for_now() -> str:
    hour = dt.datetime.now().hour
    if hour < 12:
        return "Good morning"
    if hour < 18:
        return "Good afternoon"
    return "Good evening"


def safe_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
