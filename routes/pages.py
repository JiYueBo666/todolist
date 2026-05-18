from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader

page_router = APIRouter()
TEMPLATE_DIR = Path(__file__).parent.parent / "templates"
jinja_env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)), autoescape=True)


def _render(name: str, request: Request, **kwargs) -> HTMLResponse:
    template = jinja_env.get_template(name)
    return HTMLResponse(template.render(request=request, **kwargs))


@page_router.get("/")
def main_page(request: Request):
    from models import get_active_todos, get_unfinished_previous_todos
    return _render("index.html", request,
                   active_todos=get_active_todos(),
                   unfinished_todos=get_unfinished_previous_todos())


@page_router.get("/stats")
def stats_page(request: Request):
    return _render("stats.html", request)
