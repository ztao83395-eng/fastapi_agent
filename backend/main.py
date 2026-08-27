import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

# 兼容两种启动方式：
# 1. 在 backend 目录运行 `uvicorn main:app`
# 2. 在项目根目录运行 `uvicorn backend.main:app`
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from routers import news, users, favorite, history, agent, chat
from fastapi.middleware.cors import CORSMiddleware

from utils.exception_handlers import register_exception_handlers
from config.db_conf import init_db

app = FastAPI()

# 本地新闻图片（backend/static/images/），避免外链图源国内访问超时
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

register_exception_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    await init_db()


@app.get("/")
async def root():
    return {"message": "新闻 Agent 服务已启动，使用阿里云百炼大模型"}


app.include_router(news.router)
app.include_router(users.router)
app.include_router(favorite.router)
app.include_router(history.router)
app.include_router(agent.router)
app.include_router(chat.router)
