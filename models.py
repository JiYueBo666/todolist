import os
from datetime import datetime

from database import get_db


def row_to_dict(row) -> dict:
    return dict(row) if row else None


# ===== User functions =====

def create_user(username: str, password_hash: str, is_admin: bool = False) -> dict | None:
    with get_db() as db:
        with db.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE username = %s", (username,))
            if cur.fetchone():
                return None
            cur.execute(
                "INSERT INTO users (username, password, is_admin) VALUES (%s, %s, %s)",
                (username, password_hash, 1 if is_admin else 0),
            )
            db.commit()
            cur.execute("SELECT * FROM users WHERE id = %s", (cur.lastrowid,))
            return dict(cur.fetchone())


def get_user_by_username(username: str) -> dict | None:
    with get_db() as db:
        with db.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE username = %s", (username,))
            row = cur.fetchone()
            return dict(row) if row else None


def get_pending_users() -> list[dict]:
    with get_db() as db:
        with db.cursor() as cur:
            cur.execute(
                "SELECT id, username, is_approved, created_at FROM users "
                "WHERE is_admin = 0 AND is_approved = 0 ORDER BY created_at ASC"
            )
            return [dict(r) for r in cur.fetchall()]


def approve_user(user_id: int) -> bool:
    with get_db() as db:
        with db.cursor() as cur:
            cur.execute(
                "UPDATE users SET is_approved = 1 WHERE id = %s AND is_approved = 0",
                (user_id,),
            )
            db.commit()
            return cur.rowcount > 0


def init_admin_user():
    username = os.environ.get("ADMIN_USERNAME")
    password = os.environ.get("ADMIN_PASSWORD")
    if not username or not password:
        return
    existing = get_user_by_username(username)
    if existing:
        return
    from bcrypt import hashpw, gensalt
    password_hash = hashpw(password.encode(), gensalt()).decode()
    create_user(username, password_hash, is_admin=True)
    with get_db() as db:
        with db.cursor() as cur:
            cur.execute(
                "UPDATE users SET is_approved = 1 WHERE username = %s",
                (username,),
            )
            db.commit()


# ===== Todo functions =====

def get_active_todos(user_id: int) -> list[dict]:
    with get_db() as db:
        with db.cursor() as cur:
            cur.execute(
                "SELECT * FROM todos WHERE is_deleted = 0 AND user_id = %s ORDER BY created_at DESC",
                (user_id,),
            )
            return [dict(r) for r in cur.fetchall()]


def get_unfinished_previous_todos(user_id: int) -> list[dict]:
    with get_db() as db:
        with db.cursor() as cur:
            cur.execute(
                """SELECT * FROM todos
                   WHERE is_deleted = 0
                     AND is_completed = 0
                     AND user_id = %s
                     AND DATE(created_at) < CURDATE()
                   ORDER BY created_at DESC""",
                (user_id,),
            )
            return [dict(r) for r in cur.fetchall()]


def create_todo(user_id: int, title: str, keywords: str) -> dict:
    with get_db() as db:
        with db.cursor() as cur:
            now = datetime.now().isoformat()
            cur.execute(
                "INSERT INTO todos (user_id, title, keywords, created_at) VALUES (%s, %s, %s, %s)",
                (user_id, title, keywords, now),
            )
            db.commit()
            cur.execute("SELECT * FROM todos WHERE id = %s", (cur.lastrowid,))
            return dict(cur.fetchone())


def toggle_todo(todo_id: int, user_id: int, is_completed: bool) -> dict | None:
    with get_db() as db:
        with db.cursor() as cur:
            now = datetime.now().isoformat()
            if is_completed:
                cur.execute(
                    "UPDATE todos SET is_completed = 1, completed_at = %s WHERE id = %s AND is_deleted = 0 AND user_id = %s",
                    (now, todo_id, user_id),
                )
            else:
                cur.execute(
                    "UPDATE todos SET is_completed = 0, completed_at = NULL WHERE id = %s AND is_deleted = 0 AND user_id = %s",
                    (todo_id, user_id),
                )
            db.commit()
            cur.execute("SELECT * FROM todos WHERE id = %s", (todo_id,))
            row = cur.fetchone()
            return dict(row) if row else None


def soft_delete_todo(todo_id: int, user_id: int) -> bool:
    with get_db() as db:
        with db.cursor() as cur:
            now = datetime.now().isoformat()
            cur.execute(
                "UPDATE todos SET is_deleted = 1, deleted_at = %s WHERE id = %s AND is_deleted = 0 AND user_id = %s",
                (now, todo_id, user_id),
            )
            db.commit()
            return cur.rowcount > 0


def get_keyword_suggestions(prefix: str = "", user_id: int = None, limit: int = 10) -> list[str]:
    with get_db() as db:
        with db.cursor() as cur:
            if user_id is not None:
                cur.execute(
                    "SELECT DISTINCT keywords FROM todos WHERE is_deleted = 0 AND user_id = %s AND keywords != ''",
                    (user_id,),
                )
            else:
                cur.execute(
                    "SELECT DISTINCT keywords FROM todos WHERE is_deleted = 0 AND keywords != ''"
                )
            rows = cur.fetchall()

    matched = set()
    for row in rows:
        for kw in row["keywords"].split(","):
            if kw.startswith(prefix) and kw not in matched:
                matched.add(kw)
                if len(matched) >= limit:
                    return sorted(matched)
    return sorted(matched)


def get_monthly_stats(user_id: int) -> list[dict]:
    with get_db() as db:
        with db.cursor() as cur:
            cur.execute(
                """SELECT SUBSTR(created_at, 1, 7) AS month,
                          COUNT(*) AS total, SUM(is_completed) AS completed
                   FROM todos WHERE is_deleted = 0 AND user_id = %s
                   GROUP BY month ORDER BY month ASC""",
                (user_id,),
            )
            rows = cur.fetchall()

    stats = []
    for row in rows:
        total = row["total"]
        completed = row["completed"] or 0
        rate = round((completed / total) * 100, 1) if total > 0 else 0.0
        stats.append({
            "month": row["month"],
            "total": total,
            "completed": completed,
            "rate": rate,
        })
    return stats
