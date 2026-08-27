from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from utils.auth import get_current_user
from config.db_conf import get_database
from models.users import User
from crud import chat
from utils.response import success_response

router = APIRouter(prefix="/api/chat", tags=["chat"])


# 会话列表
@router.get("/sessions")
async def get_sessions(
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100, alias="pageSize"),
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_database),
):
    rows, total = await chat.get_session_list(db, user.id, page, page_size)
    session_list = [{
        "id": s.id,
        "title": s.title,
        "createdAt": s.created_at,
        "updatedAt": s.updated_at,
        "messageCount": message_count,
    } for s, message_count in rows]
    has_more = total > page * page_size
    return success_response(message="获取会话列表成功", data={"list": session_list, "total": total, "hasMore": has_more})


# 新建会话
@router.post("/sessions")
async def create_session(
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_database),
):
    session = await chat.create_session(db, user.id)
    return success_response(message="创建会话成功", data={"id": session.id, "title": session.title})


# 会话消息列表
@router.get("/sessions/{session_id}/messages")
async def get_messages(
        session_id: int,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_database),
):
    session = await chat.get_session(db, session_id, user.id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    messages = await chat.get_session_messages(db, session_id)
    message_list = [{"role": m.role, "content": m.content, "createdAt": m.created_at} for m in messages]
    return success_response(message="获取消息成功", data={"list": message_list})


# 删除会话
@router.delete("/sessions/{session_id}")
async def remove_session(
        session_id: int,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_database),
):
    if not await chat.delete_session(db, session_id, user.id):
        raise HTTPException(status_code=404, detail="会话不存在")
    return success_response(message="删除会话成功")
