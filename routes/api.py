from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

api_router = APIRouter(prefix="/api")


@api_router.get("/todos")
def list_todos():
    from models import get_active_todos
    return {"todos": get_active_todos()}


@api_router.post("/todos")
async def create_todo_handler(request: Request):
    from models import create_todo
    from keywords import extract_keywords

    data = await request.json()
    title = data.get("title", "").strip()
    if not title:
        return JSONResponse({"error": "Title cannot be empty"}, status_code=400)
    if len(title) > 500:
        return JSONResponse({"error": "Title too long"}, status_code=400)

    keywords = extract_keywords(title)
    todo = create_todo(title, keywords)
    return JSONResponse({"todo": todo}, status_code=201)


@api_router.put("/todos/{todo_id}")
async def update_todo_handler(todo_id: int, request: Request):
    from models import toggle_todo
    data = await request.json()
    is_completed = bool(data.get("is_completed", False))
    todo = toggle_todo(todo_id, is_completed)
    if todo is None:
        return JSONResponse({"error": "Todo not found"}, status_code=404)
    return {"todo": todo}


@api_router.delete("/todos/{todo_id}")
def delete_todo_handler(todo_id: int):
    from models import soft_delete_todo
    if not soft_delete_todo(todo_id):
        return JSONResponse({"error": "Todo not found"}, status_code=404)
    return {"success": True}


@api_router.get("/keywords")
def suggest_keywords(q: str = ""):
    from models import get_keyword_suggestions
    return {"keywords": get_keyword_suggestions(q.strip().lower())}


@api_router.get("/stats")
def stats_handler():
    from models import get_monthly_stats
    return {"months": get_monthly_stats()}
