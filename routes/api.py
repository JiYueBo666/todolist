from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

api_router = APIRouter(prefix="/api")


def _require_user_id(request: Request) -> int:
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user["id"]


@api_router.get("/todos")
def list_todos(request: Request):
    from models import get_active_todos
    user_id = _require_user_id(request)
    return {"todos": get_active_todos(user_id)}


@api_router.post("/todos")
async def create_todo_handler(request: Request):
    from models import create_todo
    from keywords import extract_keywords

    user_id = _require_user_id(request)
    data = await request.json()
    title = data.get("title", "").strip()
    if not title:
        return JSONResponse({"error": "Title cannot be empty"}, status_code=400)
    if len(title) > 500:
        return JSONResponse({"error": "Title too long"}, status_code=400)

    keywords = extract_keywords(title)
    todo = create_todo(user_id, title, keywords)
    return JSONResponse({"todo": todo}, status_code=201)


@api_router.put("/todos/{todo_id}")
async def update_todo_handler(todo_id: int, request: Request):
    from models import toggle_todo
    user_id = _require_user_id(request)
    data = await request.json()
    is_completed = bool(data.get("is_completed", False))
    todo = toggle_todo(todo_id, user_id, is_completed)
    if todo is None:
        return JSONResponse({"error": "Todo not found"}, status_code=404)
    return {"todo": todo}


@api_router.delete("/todos/{todo_id}")
def delete_todo_handler(todo_id: int, request: Request):
    from models import soft_delete_todo
    user_id = _require_user_id(request)
    if not soft_delete_todo(todo_id, user_id):
        return JSONResponse({"error": "Todo not found"}, status_code=404)
    return {"success": True}


@api_router.get("/keywords")
def suggest_keywords(request: Request, q: str = ""):
    from models import get_keyword_suggestions
    user_id = _require_user_id(request)
    return {"keywords": get_keyword_suggestions(q.strip().lower(), user_id=user_id)}


@api_router.get("/stats")
def stats_handler(request: Request):
    from models import get_monthly_stats
    user_id = _require_user_id(request)
    return {"months": get_monthly_stats(user_id)}
