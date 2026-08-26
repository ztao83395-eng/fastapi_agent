import asyncio
import concurrent.futures

from langchain_classic.agents import create_openai_tools_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from sqlalchemy import select, delete

from config.db_conf import get_database
from config.llm_conf import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL, TEMPERATURE
from crud import favorite
from models.favorite import Favorite
from models.news import News
from services.context import get_current_user_id


def run_async(coro):
    """在同步工具中运行异步协程（线程安全版本）"""

    def _run_in_thread():
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        try:
            return new_loop.run_until_complete(coro)
        finally:
            new_loop.close()

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(_run_in_thread)
        return future.result()


@tool
async def search_news_by_keyword(keyword: str) -> str:
    """根据关键词搜索新闻标题和内容，返回新闻列表（最多5条）"""
    async for db in get_database():
        try:
            stmt = select(News).where(
                News.title.contains(keyword) | News.content.contains(keyword)
            ).limit(5)
            result = await db.execute(stmt)
            news_list = result.scalars().all()
            if not news_list:
                return "未找到相关新闻"
            return "\n".join([f"{n.id}.{n.title}" for n in news_list])
        finally:
            await db.close()
        break


import logging
import traceback

logger = logging.getLogger(__name__)


@tool
async def add_favorite(news_id: int) -> str:
    """收藏指定新闻，参数为新闻ID"""
    user_id = get_current_user_id()
    if user_id == 0:
        return "未登录，无法收藏"

    async for db in get_database():
        try:
            # 检查新闻是否存在
            news_result = await db.execute(select(News).where(News.id == news_id))
            news = news_result.scalar_one_or_none()
            if not news:
                return f"新闻 ID {news_id} 不存在"

            # 检查是否已收藏
            if await favorite.is_new_favorite(db, user_id, news_id):
                return f"新闻《{news.title}》已经在您的收藏夹中"

            # 添加收藏
            await favorite.add_news_favorite(db, user_id, news_id)
            return f"✅ 成功收藏新闻《{news.title}》"
        except Exception as e:
            return f"收藏失败：{str(e)}"
        finally:
            await db.close()
        break

@tool
async def remove_favorite(news_id: int) -> str:
    """取消收藏指定的新闻，参数为新闻ID"""
    user_id = get_current_user_id()
    if user_id == 0:
        return "未登录，无法操作"
    async for db in get_database():
        try:
            # 检查新闻是否存在
            news_result = await db.execute(select(News).where(News.id == news_id))
            news = news_result.scalar_one_or_none()
            if not news:
                return f"新闻 ID {news_id} 不存在"

            # 检查是否已收藏
            if not await favorite.is_new_favorite(db, user_id, news_id):
                return f"新闻《{news.title}》不在您的收藏夹中"

            # 取消收藏
            result = await favorite.delete_news_favorite(db, user_id, news_id)
            if result:
                return f" 已取消收藏《{news.title}》"
            return "取消收藏失败，请稍后重试"
        except Exception as e:
            return f"取消收藏失败：{str(e)}"
        finally:
            await db.close()
        break

@tool
async def get_my_favorites() -> str:
    """获取当前用户的收藏列表"""
    user_id = get_current_user_id()
    if user_id == 0:
        return "未登录"

    async for db in get_database():
        try:
            rows, total = await favorite.get_favorite_list(db, user_id, 1, 20)
            if not rows:
                return "暂无收藏"
            result = []
            for news, fav_time, fav_id in rows:
                result.append(f"{news.id}.{news.title}(收藏于{fav_time})")
            return "\n".join(result)
        except Exception as e:
            return f"获取收藏列表失败: {str(e)}"
        finally:
            await db.close()
        break

@tool
async def clear_favorites() -> str:
    """清空当前用户的所有收藏"""
    user_id = get_current_user_id()
    if user_id == 0:
        return "未登录，无法操作"

    async for db in get_database():
        try:
            # 先获取收藏数量
            rows, total = await favorite.get_favorite_list(db, user_id, 1, 100)
            if total == 0:
                return "您的收藏夹已经是空的"

            # 清空收藏
            count = await favorite.remove_all_favorite(db, user_id)
            return f"✅ 已清空您的收藏夹，共删除 {count} 条收藏"
        except Exception as e:
            return f"清空收藏失败：{str(e)}"
        finally:
            await db.close()
        break

tools = [search_news_by_keyword, add_favorite, remove_favorite,get_my_favorites,clear_favorites]


def create_agent_executor():
    llm = ChatOpenAI(
        openai_api_key=LLM_API_KEY,
        base_url=LLM_BASE_URL,
        model_name=LLM_MODEL,
        temperature=TEMPERATURE
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一个智能新闻助手，名字叫小闻。你可以搜索新闻、收藏新闻、查看收藏列表、推荐新闻。回答要简洁有帮助。"),
        MessagesPlaceholder(variable_name="chat_history", optional=True),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_openai_tools_agent(llm, tools, prompt)
    executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True
    )
    return executor