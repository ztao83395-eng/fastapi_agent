"""Docker 集成测试 —— 覆盖核心 API 链路"""
import os
import pytest


# ============================================================
# 1. 健康检查
# ============================================================
@pytest.mark.asyncio
async def test_health_check(client):
    resp = await client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert "message" in data


# ============================================================
# 2. 用户注册
# ============================================================
@pytest.mark.asyncio
async def test_register_user(client):
    resp = await client.post(
        "/api/users/register",
        json={"username": "newuser", "password": "pass123456"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["code"] == 200
    assert "token" in data["data"]
    assert "userInfo" in data["data"]


# ============================================================
# 3. 重复注册应返回 409
# ============================================================
@pytest.mark.asyncio
async def test_duplicate_register(client):
    resp = await client.post(
        "/api/users/register",
        json={"username": "dupuser", "password": "pass123456"},
    )
    assert resp.status_code == 200

    resp = await client.post(
        "/api/users/register",
        json={"username": "dupuser", "password": "pass123456"},
    )
    assert resp.status_code == 409


# ============================================================
# 4. 用户登录
# ============================================================
@pytest.mark.asyncio
async def test_login_user(client):
    # 先注册
    await client.post(
        "/api/users/register",
        json={"username": "loginuser", "password": "pass123456"},
    )
    # 再登录
    resp = await client.post(
        "/api/users/login",
        json={"username": "loginuser", "password": "pass123456"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["code"] == 200
    assert "token" in data["data"]


# ============================================================
# 5. 获取新闻分类
# ============================================================
@pytest.mark.asyncio
async def test_get_categories(client):
    resp = await client.get("/api/news/categories")
    assert resp.status_code == 200
    data = resp.json()
    assert data["code"] == 200
    assert isinstance(data["data"], list)


# ============================================================
# 6. 获取新闻列表（需要 seed_news 先插入数据）
# ============================================================
@pytest.mark.asyncio
async def test_get_news_list(client, seed_news):
    resp = await client.get(
        "/api/news/list",
        params={"categoryId": seed_news["category_id"], "page": 1, "pageSize": 10},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["code"] == 200
    assert "list" in data["data"]
    assert "total" in data["data"]


# ============================================================
# 7. 未登录访问受保护接口应返回 403
# ============================================================
@pytest.mark.asyncio
async def test_unauthorized_access(client):
    resp = await client.get("/api/favorite/list")
    assert resp.status_code in (401, 403)


# ============================================================
# 8. 收藏功能完整链路（需要登录 + 种子新闻）
# ============================================================
@pytest.mark.asyncio
async def test_favorite_flow(client, auth_headers, seed_news):
    news_id = seed_news["news_id"]

    # 添加收藏
    resp = await client.post(
        "/api/favorite/add",
        headers=auth_headers,
        json={"newsId": news_id},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["code"] == 200

    # 检查收藏状态
    resp = await client.get(
        "/api/favorite/check",
        headers=auth_headers,
        params={"newsId": news_id},
    )
    data = resp.json()
    assert data["data"]["isFavorite"] is True

    # 获取收藏列表
    resp = await client.get(
        "/api/favorite/list",
        headers=auth_headers,
        params={"page": 1, "pageSize": 10},
    )
    data = resp.json()
    assert data["code"] == 200
    assert data["data"]["total"] >= 1

    # 取消收藏
    resp = await client.delete(
        "/api/favorite/remove",
        headers=auth_headers,
        params={"newsId": news_id},
    )
    assert resp.status_code == 200


# ============================================================
# 9. 浏览历史完整链路（需要登录 + 种子新闻）
# ============================================================
@pytest.mark.asyncio
async def test_history_flow(client, auth_headers, seed_news):
    news_id = seed_news["news_id"]

    # 添加浏览记录
    resp = await client.post(
        "/api/history/add",
        headers=auth_headers,
        json={"newsId": news_id},
    )
    assert resp.status_code == 200

    # 获取浏览历史列表
    resp = await client.get(
        "/api/history/list",
        headers=auth_headers,
        params={"page": 1, "pageSize": 10},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["code"] == 200
    assert data["data"]["total"] >= 1

    # 删除单条记录
    resp = await client.delete(
        f"/api/history/delete/{news_id}",
        headers=auth_headers,
    )
    assert resp.status_code == 200


# ============================================================
# 10. RAG 问答（需要 API Key 和种子数据，否则跳过）
# ============================================================
@pytest.mark.asyncio
async def test_rag_ask(client, seed_news):
    if not os.getenv("BAILIAN_API_KEY"):
        pytest.skip("未设置 BAILIAN_API_KEY，跳过 RAG 测试")

    resp = await client.post(
        "/api/agent/rag",
        json={"question": "测试新闻是什么内容？"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "data" in data


# ============================================================
# 11. Agent 对话（需要登录 + API Key，否则跳过）
# ============================================================
@pytest.mark.asyncio
async def test_agent_chat(client, auth_headers):
    if not os.getenv("BAILIAN_API_KEY"):
        pytest.skip("未设置 BAILIAN_API_KEY，跳过 Agent 测试")

    resp = await client.post(
        "/api/agent/chat",
        headers=auth_headers,
        json={"question": "帮我看看我的收藏"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "data" in data
