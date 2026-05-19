from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from jinja2 import Environment, FileSystemLoader
from bcrypt import checkpw, hashpw, gensalt

from models import (
    approve_user,
    create_user,
    get_active_todos,
    get_pending_users,
    get_unfinished_previous_todos,
    get_user_by_username,
)

page_router = APIRouter()
TEMPLATE_DIR = Path(__file__).parent.parent / "templates"
jinja_env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)), autoescape=True)


def _render(name: str, request: Request, **kwargs) -> HTMLResponse:
    user = request.session.get("user")
    template = jinja_env.get_template(name)
    return HTMLResponse(template.render(request=request, user=user, **kwargs))


def _require_auth(request: Request) -> dict | None:
    """Returns user dict from session, or None if not logged in."""
    return request.session.get("user")


# ===== Auth routes =====

@page_router.get("/login")
def login_page(request: Request):
    user = _require_auth(request)
    if user:
        return RedirectResponse("/", status_code=303)
    return _render("login.html", request, error=None, success=None)


@page_router.post("/login")
async def login_handler(request: Request):
    form = await request.form()
    username = form.get("username", "").strip()
    password = form.get("password", "").strip()

    if not username or not password:
        return _render("login.html", request, error="Username and password are required.", success=None)

    user = get_user_by_username(username)
    if not user or not checkpw(password.encode(), user["password"].encode()):
        return _render("login.html", request, error="Invalid username or password.", success=None)

    if not user["is_approved"]:
        return _render("login.html", request, error="Your account is pending admin approval.", success=None)

    request.session["user"] = {
        "id": user["id"],
        "username": user["username"],
        "is_admin": bool(user["is_admin"]),
    }
    return RedirectResponse("/", status_code=303)


@page_router.get("/register")
def register_page(request: Request):
    user = _require_auth(request)
    if user:
        return RedirectResponse("/", status_code=303)
    return _render("register.html", request, error=None)


@page_router.post("/register")
async def register_handler(request: Request):
    form = await request.form()
    username = form.get("username", "").strip()
    password = form.get("password", "").strip()
    confirm = form.get("confirm", "").strip()

    if not username or not password:
        return _render("register.html", request, error="All fields are required.")
    if len(username) < 2 or len(username) > 50:
        return _render("register.html", request, error="Username must be 2-50 characters.")
    if len(password) < 4:
        return _render("register.html", request, error="Password must be at least 4 characters.")
    if password != confirm:
        return _render("register.html", request, error="Passwords do not match.")

    password_hash = hashpw(password.encode(), gensalt()).decode()
    created = create_user(username, password_hash)
    if not created:
        return _render("register.html", request, error="Username already taken.")

    return _render("login.html", request,
                   error=None,
                   success="Registration submitted. Please wait for admin approval.")


@page_router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)


# ===== Admin routes =====

@page_router.get("/admin")
def admin_page(request: Request):
    user = _require_auth(request)
    if not user:
        return RedirectResponse("/login", status_code=303)
    if not user.get("is_admin"):
        return RedirectResponse("/", status_code=303)
    pending = get_pending_users()
    return _render("admin.html", request, pending_users=pending)


@page_router.post("/admin/approve/{user_id}")
def admin_approve(user_id: int, request: Request):
    user = _require_auth(request)
    if not user or not user.get("is_admin"):
        return RedirectResponse("/login", status_code=303)
    approve_user(user_id)
    return RedirectResponse("/admin", status_code=303)


# ===== Page routes =====

@page_router.get("/")
def main_page(request: Request):
    user = _require_auth(request)
    if not user:
        return RedirectResponse("/login", status_code=303)
    return _render("index.html", request,
                   active_todos=get_active_todos(user["id"]),
                   unfinished_todos=get_unfinished_previous_todos(user["id"]))


@page_router.get("/stats")
def stats_page(request: Request):
    user = _require_auth(request)
    if not user:
        return RedirectResponse("/login", status_code=303)
    return _render("stats.html", request)
