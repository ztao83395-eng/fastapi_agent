import sys
from pathlib import Path

import pytest_asyncio
import httpx

# 让测试从项目根目录执行时，也能导入 backend 下的后端模块。
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from config.db_conf import init_db, AsyncSessionLocal
from main import app


@pytest_asyncio.fixture(scope="module")
async def client():
    """创建 httpx AsyncClient，直接对接 FastAPI app（ASGI 内存通信）"""
    await init_db()
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


@pytest_asyncio.fixture(scope="module")
async def auth_headers(client):
    """注册测试用户并登录，返回带 Bearer Token 的请求头"""
    username = "testuser_auto"
    password = "test123456"

    # 注册
    resp = await client.post(
        "/api/users/register",
        json={"username": username, "password": password},
    )
    if resp.status_code == 200:
        data = resp.json()
        token = data["data"]["token"]
    else:
        # 可能已有残留用户，尝试登录
        resp = await client.post(
            "/api/users/login",
            json={"username": username, "password": password},
        )
        data = resp.json()
        token = data["data"]["token"]

    return {
        "Authorization": f"Bearer {token}",
        "X-Username": username,
    }


@pytest_asyncio.fixture(scope="module")
async def seed_news(client):
    """在数据库中插入测试分类和新闻，返回 news_id"""
    from models.news import News, Category
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        # 检查是否已有测试分类
        result = await db.execute(
            select(Category).where(Category.name == "测试分类")
        )
        cat = result.scalar_one_or_none()
        if cat is None:
            cat = Category(name="测试分类", sort_order=1)
            db.add(cat)
            await db.flush()

        # 插入测试新闻
        news = News(
            title="测试新闻标题",
            description="这是一条用于集成测试的新闻",
            content="测试新闻的详细内容，包含足够的文字用于向量检索测试。",
            author="测试作者",
            category_id=cat.id,
            views=0,
        )
        db.add(news)
        await db.commit()
        await db.refresh(news)
        return {"news_id": news.id, "category_id": cat.id}
