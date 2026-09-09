"""SQLite database connection and schema management.

Uses a single module-level connection (SQLite + Qt single-process app is fine
with check_same_thread=False plus a lock, since all DB calls happen on the
GUI thread or short-lived worker threads that never overlap writes).
"""
import sqlite3
import threading
import logging
from app.config.constants import get_db_path, DEFAULT_CATEGORIES, get_log_path

logging.basicConfig(
    filename=get_log_path(),
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("taskforge.db")

_lock = threading.Lock()
_conn = None


SCHEMA = """
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    icon TEXT DEFAULT '',
    color TEXT DEFAULT '#5C6BC0',
    description TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    due_date TEXT,              -- YYYY-MM-DD
    due_time TEXT,               -- HH:MM
    priority TEXT DEFAULT 'Medium',
    category_id INTEGER,
    status TEXT DEFAULT 'To Do',
    notes TEXT DEFAULT '',
    estimated_minutes INTEGER DEFAULT 0,
    reminder_offset_min INTEGER,   -- NULL = no reminder
    reminder_fired INTEGER DEFAULT 0,
    recurrence TEXT DEFAULT 'None',
    recurrence_data TEXT DEFAULT '',   -- e.g. "Mon,Wed,Fri"
    goal_id INTEGER,
    is_favorite INTEGER DEFAULT 0,
    is_deleted INTEGER DEFAULT 0,
    sort_order INTEGER DEFAULT 0,
    created_at TEXT,
    completed_at TEXT,
    deleted_at TEXT,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL,
    FOREIGN KEY (goal_id) REFERENCES goals(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS task_tags (
    task_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    PRIMARY KEY (task_id, tag_id),
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS subtasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    is_done INTEGER DEFAULT 0,
    sort_order INTEGER DEFAULT 0,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS goals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    deadline TEXT,
    created_at TEXT,
    is_deleted INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS habits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    frequency TEXT DEFAULT 'Daily',
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS habit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    habit_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    FOREIGN KEY (habit_id) REFERENCES habits(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS pomodoro_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER,
    started_at TEXT,
    ended_at TEXT,
    duration_min INTEGER,
    kind TEXT DEFAULT 'focus'   -- focus | break
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
);

CREATE TABLE IF NOT EXISTS achievements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT UNIQUE,
    title TEXT,
    unlocked_at TEXT
);

CREATE TABLE IF NOT EXISTS daily_stats (
    date TEXT PRIMARY KEY,   -- YYYY-MM-DD
    completed_count INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_tasks_due ON tasks(due_date);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_deleted ON tasks(is_deleted);
"""


def get_conn() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(get_db_path(), check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _conn.execute("PRAGMA foreign_keys = ON;")
    return _conn


def init_db():
    """Create tables if they don't exist and seed default categories."""
    conn = get_conn()
    try:
        with _lock:
            conn.executescript(SCHEMA)
            conn.commit()
            cur = conn.execute("SELECT COUNT(*) AS c FROM categories")
            if cur.fetchone()["c"] == 0:
                for name, icon, color, desc in DEFAULT_CATEGORIES:
                    conn.execute(
                        "INSERT INTO categories (name, icon, color, description) VALUES (?,?,?,?)",
                        (name, icon, color, desc),
                    )
                conn.commit()
    except sqlite3.DatabaseError as e:
        log.error("Database appears corrupted: %s", e)
        raise


def execute(query: str, params: tuple = ()):
    """Run an INSERT/UPDATE/DELETE and return the cursor (lastrowid, rowcount)."""
    conn = get_conn()
    with _lock:
        cur = conn.execute(query, params)
        conn.commit()
        return cur


def query_all(query: str, params: tuple = ()):
    conn = get_conn()
    with _lock:
        cur = conn.execute(query, params)
        return [dict(r) for r in cur.fetchall()]


def query_one(query: str, params: tuple = ()):
    conn = get_conn()
    with _lock:
        cur = conn.execute(query, params)
        row = cur.fetchone()
        return dict(row) if row else None
