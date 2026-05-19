import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from database import init_db
from routes.api import api_router
from routes.pages import page_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    from models import init_admin_user
    init_admin_user()
    yield


app = FastAPI(title="TodoList", lifespan=lifespan)

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY, max_age=86400 * 30)

BASE_DIR = Path(__file__).parent
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

app.include_router(page_router)
app.include_router(api_router)


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)
