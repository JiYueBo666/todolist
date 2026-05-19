import os
from contextlib import contextmanager

import pymysql.cursors


def _get_ssl_config() -> dict | None:
    ca_path = os.environ.get("MYSQL_SSL_CA", "")
    if ca_path:
        return {"ca": ca_path}
    return None


@contextmanager
def get_db():
    conn = pymysql.connect(
        host=os.environ.get("MYSQL_HOST", "localhost"),
        port=int(os.environ.get("MYSQL_PORT", "3306")),
        user=os.environ.get("MYSQL_USER", "root"),
        password=os.environ.get("MYSQL_PASSWORD", ""),
        database=os.environ.get("MYSQL_DATABASE", "todolist"),
        ssl=_get_ssl_config(),
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
        charset="utf8mb4",
    )
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    with get_db() as db:
        with db.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id          INT AUTO_INCREMENT PRIMARY KEY,
                    username    VARCHAR(100) NOT NULL UNIQUE,
                    password    VARCHAR(255) NOT NULL,
                    is_admin    TINYINT NOT NULL DEFAULT 0,
                    is_approved TINYINT NOT NULL DEFAULT 0,
                    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS todos (
                    id            INT AUTO_INCREMENT PRIMARY KEY,
                    user_id       INT NOT NULL,
                    title         VARCHAR(500) NOT NULL,
                    keywords      VARCHAR(500) NOT NULL DEFAULT '',
                    is_completed  TINYINT NOT NULL DEFAULT 0,
                    is_deleted    TINYINT NOT NULL DEFAULT 0,
                    created_at    VARCHAR(30) NOT NULL,
                    completed_at  VARCHAR(30) DEFAULT NULL,
                    deleted_at    VARCHAR(30) DEFAULT NULL
                )
            """)
            cur.execute("""
                SELECT COUNT(*) AS cnt FROM information_schema.statistics
                WHERE table_schema = DATABASE()
                  AND table_name = 'todos'
                  AND index_name = 'idx_todos_active'
            """)
            if cur.fetchone()["cnt"] == 0:
                cur.execute("""
                    CREATE INDEX idx_todos_active
                        ON todos (user_id, is_deleted, is_completed, created_at DESC)
                """)
            db.commit()
