# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally (MySQL must be running, defaults to localhost:3306)
python app.py

# Run with Docker (starts MySQL 8.0 + app)
docker compose up --build

# Default admin: admin / admin123 (set via ADMIN_USERNAME/ADMIN_PASSWORD env vars)
# API docs at http://localhost:8000/docs
# Health check at http://localhost:8000/health
```

## Architecture

**FastAPI app with server-side rendered HTML, vanilla JS frontend, MySQL storage, and session-based user auth.**

### Layers

- `app.py` — Entry point. Creates FastAPI with `SessionMiddleware` (30-day signed cookie sessions). Lifespan handler calls `init_db()` then `init_admin_user()`. Mounts `/static`, includes both routers.
- `database.py` — MySQL connection via PyMySQL with `DictCursor` (returns dicts). `get_db()` is a `@contextmanager`. `init_db()` creates `users` and `todos` tables with MySQL syntax. Connection config via `MYSQL_HOST/PORT/USER/PASSWORD/DATABASE/SSL_CA` env vars.
- `models.py` — Data access layer. All functions use `with get_db() as db: with db.cursor() as cur:` pattern. Todos use **soft delete**. **User functions**: `create_user`, `get_user_by_username`, `get_pending_users`, `approve_user`, `init_admin_user`. **Todo functions**: all accept `user_id` parameter and filter queries by it (`get_active_todos`, `get_unfinished_previous_todos`, `create_todo`, `toggle_todo`, `soft_delete_todo`, `get_keyword_suggestions`, `get_monthly_stats`).
- `keywords.py` — `extract_keywords(title)` tokenizes with unicode regex, filters stop words (English + French), deduplicates, returns comma-separated string.
- `routes/api.py` — REST API under `/api`. All endpoints require auth via `_require_user_id(request)` which reads session and raises 401 if missing. `GET/POST /api/todos`, `PUT /api/todos/{id}`, `DELETE /api/todos/{id}`, `GET /api/keywords?q=`, `GET /api/stats`.
- `routes/pages.py` — SSR routes. Auth routes: `GET/POST /login`, `GET/POST /register`, `GET /logout`. Admin routes: `GET /admin`, `POST /admin/approve/{user_id}`. Page routes: `GET /` (index with per-user todos), `GET /stats`.
- `templates/` — Jinja2 templates: `base.html` (auth-aware nav), `index.html`, `stats.html`, `login.html`, `register.html`, `admin.html`.
- `static/` — Vanilla JS (`app.js` for CRUD + autocomplete + 401 redirect, `stats.js` for Chart.js) and CSS.

### Auth flow

- **Session-based**: `SessionMiddleware` stores `{"id", "username", "is_admin"}` in a signed cookie.
- **Registration**: Anyone can register, but `is_approved` defaults to 0. Users see "pending admin approval" message.
- **Admin approval**: Admin (created from `ADMIN_USERNAME`/`ADMIN_PASSWORD` env vars) visits `/admin` to approve pending users.
- **Auth guards**: Page routes redirect to `/login`. API routes return 401. JS catches 401 and redirects to `/login`.
- **Per-user isolation**: Every todo query includes `AND user_id = %s`. No user can access another's data.

### Key behaviors

- **Soft deletes**: `is_deleted` flag, never hard-deleted. Toggling completion sets `completed_at` or NULL.
- **Unfinished todos banner**: incomplete todos from prior days (`DATE(created_at) < CURDATE()`) shown in collapsible warning.
- **Keyword autocomplete**: per-user keyword cache fetched on page load.
- **Monthly stats**: aggregated per-user, `SUBSTR(created_at, 1, 7)` grouping.
- **No FK constraints**: PlanetScale compatibility; referential integrity enforced at the application layer.

## Deployment

- `Dockerfile` — Python 3.12 slim, uvicorn on `$PORT` (default 8000).
- `docker-compose.yml` — MySQL 8.0 + app. MySQL with healthcheck, app depends on it. Named volume `mysql-data` for persistence. Default admin: `admin` / `admin123`.
- `render.yaml` — Render.com blueprint: Docker runtime, no disk mount (MySQL is external), env vars for MySQL connection, `SECRET_KEY`, admin credentials.
