import os
import sqlite3
from pathlib import Path

DB_PATH = Path(os.environ.get("TODO_DB_PATH", Path(__file__).parent / "todos.db"))


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = get_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS todos (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            title         TEXT NOT NULL,
            keywords      TEXT NOT NULL DEFAULT '',
            is_completed  INTEGER NOT NULL DEFAULT 0,
            is_deleted    INTEGER NOT NULL DEFAULT 0,
            created_at    TEXT NOT NULL,
            completed_at  TEXT DEFAULT NULL,
            deleted_at    TEXT DEFAULT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_todos_active
            ON todos (is_deleted, is_completed, created_at DESC);
    """)
    db.commit()
    db.close()
