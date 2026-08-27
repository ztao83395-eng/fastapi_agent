"""AI 对话会话/消息的数据库操作"""
from datetime import datetime

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.chat import ChatMessage, ChatSession


async def create_session(db: AsyncSession, user_id: int) -> ChatSession:
    """新建会话（标题默认"新对话"，首条消息后自动更新）"""
    session = ChatSession(user_id=user_id, title="新对话")
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def get_session(db: AsyncSession, session_id: int, user_id: int) -> ChatSession | None:
    """按 id + 归属用户查会话（校验归属用）"""
    stmt = select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_session_list(db: AsyncSession, user_id: int, page: int = 1, page_size: int = 20):
    """会话列表：按更新时间倒序，带消息条数"""
    count_query = select(func.count()).where(ChatSession.user_id == user_id)
    total = (await db.execute(count_query)).scalar_one_or_none() or 0

    offset = (page - 1) * page_size
    # LEFT JOIN 消息计数：LEFT JOIN 后 count 消息 id 会乘行数，用 DISTINCT 会话 id 数
    stmt = (
        select(ChatSession, func.count(func.distinct(ChatMessage.id)).label('message_count'))
        .outerjoin(ChatMessage, ChatMessage.session_id == ChatSession.id)
        .where(ChatSession.user_id == user_id)
        .group_by(ChatSession.id)
        .order_by(ChatSession.updated_at.desc(), ChatSession.id.desc())
        .offset(offset).limit(page_size)
    )
    rows = (await db.execute(stmt)).all()
    return rows, total


async def get_session_messages(db: AsyncSession, session_id: int):
    """会话内全部消息，按 id 正序（会话内消息量小，不分页）"""
    stmt = (
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.id.asc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_recent_messages(db: AsyncSession, session_id: int, limit: int = 10):
    """最近 N 条消息（按 id 倒序取 limit 再反转为正序），供多轮上下文注入"""
    stmt = (
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.id.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    messages = result.scalars().all()
    return list(reversed(messages))


async def add_message(db: AsyncSession, session_id: int, role: str, content: str) -> ChatMessage:
    """写一条消息；同时刷新会话 updated_at，首条消息时用前 20 字生成标题"""
    now = datetime.utcnow()
    message = ChatMessage(session_id=session_id, role=role, content=content, created_at=now)
    db.add(message)

    session = await db.get(ChatSession, session_id)
    if session:
        session.updated_at = now
        if session.title == "新对话" and role == "user":
            # 首条提问生成会话标题（截断 20 字）
            session.title = content.strip().replace("\n", " ")[:20] or "新对话"

    await db.commit()
    await db.refresh(message)
    return message


async def delete_session(db: AsyncSession, session_id: int, user_id: int) -> bool:
    """删除会话（消息表 ondelete CASCADE 联动删除）；不属于当前用户返回 False"""
    session = await get_session(db, session_id, user_id)
    if not session:
        return False
    await db.execute(delete(ChatSession).where(ChatSession.id == session_id))
    await db.commit()
    return True
