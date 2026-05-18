from datetime import datetime

from database import get_db


def row_to_dict(row) -> dict:
    return dict(row) if row else None


def get_active_todos() -> list[dict]:
    db = get_db()
    rows = db.execute(
        "SELECT * FROM todos WHERE is_deleted = 0 ORDER BY created_at DESC"
    ).fetchall()
    result = [dict(r) for r in rows]
    db.close()
    return result


def get_unfinished_previous_todos() -> list[dict]:
    db = get_db()
    rows = db.execute(
        """SELECT * FROM todos
           WHERE is_deleted = 0
             AND is_completed = 0
             AND date(created_at) < date('now')
           ORDER BY created_at DESC"""
    ).fetchall()
    result = [dict(r) for r in rows]
    db.close()
    return result


def create_todo(title: str, keywords: str) -> dict:
    db = get_db()
    now = datetime.now().isoformat()
    cur = db.execute(
        "INSERT INTO todos (title, keywords, created_at) VALUES (?, ?, ?)",
        (title, keywords, now),
    )
    db.commit()
    row = db.execute("SELECT * FROM todos WHERE id = ?", (cur.lastrowid,)).fetchone()
    result = dict(row)
    db.close()
    return result


def toggle_todo(todo_id: int, is_completed: bool) -> dict | None:
    db = get_db()
    now = datetime.now().isoformat()
    if is_completed:
        db.execute(
            "UPDATE todos SET is_completed = 1, completed_at = ? WHERE id = ? AND is_deleted = 0",
            (now, todo_id),
        )
    else:
        db.execute(
            "UPDATE todos SET is_completed = 0, completed_at = NULL WHERE id = ? AND is_deleted = 0",
            (todo_id,),
        )
    db.commit()
    row = db.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()
    result = dict(row) if row else None
    db.close()
    return result


def soft_delete_todo(todo_id: int) -> bool:
    db = get_db()
    now = datetime.now().isoformat()
    cur = db.execute(
        "UPDATE todos SET is_deleted = 1, deleted_at = ? WHERE id = ? AND is_deleted = 0",
        (now, todo_id),
    )
    db.commit()
    affected = cur.rowcount > 0
    db.close()
    return affected


def get_keyword_suggestions(prefix: str = "", limit: int = 10) -> list[str]:
    db = get_db()
    rows = db.execute(
        "SELECT DISTINCT keywords FROM todos WHERE is_deleted = 0 AND keywords != ''"
    ).fetchall()
    db.close()

    matched = set()
    for row in rows:
        for kw in row["keywords"].split(","):
            if kw.startswith(prefix) and kw not in matched:
                matched.add(kw)
                if len(matched) >= limit:
                    return sorted(matched)
    return sorted(matched)


def get_monthly_stats() -> list[dict]:
    db = get_db()
    rows = db.execute(
        """SELECT substr(created_at, 1, 7) AS month,
                  COUNT(*) AS total, SUM(is_completed) AS completed
           FROM todos WHERE is_deleted = 0
           GROUP BY month ORDER BY month ASC"""
    ).fetchall()
    db.close()

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
