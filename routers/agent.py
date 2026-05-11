import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field
import asyncio
from models.users import User
from services.agent_tools import create_agent_executor
from services.context import current_user_id_var
from services.rag_chain import rag
from utils.auth import get_current_user
from utils.response import success_response, error_response

logger=logging.getLogger(__name__)
router=APIRouter(prefix="/api/agent",tags=["agent"])

class ChatRequest(BaseModel):
    question:str=Field(...,min_length=1,max_length=1000)

class RAGRequest(BaseModel):
    question:str=Field(...,min_length=1,max_length=1000)

_agent_executor=None
_agent_lock=asyncio.Lock()

async def get_agent():
    global _agent_executor
    if _agent_executor is None:
        async with _agent_lock:
            if _agent_executor is None:
                #在线程池创建agent避免阻塞事件循环
                _agent_executor = await asyncio.to_thread(create_agent_executor)
    return _agent_executor


@router.post("/chat")
async def agent_chat(
        req: ChatRequest,
        user: User = Depends(get_current_user),
):
    """Agent 对话接口,支持工具调用（需要登录）"""
    token = current_user_id_var.set(user.id)
    try:
        executor = await get_agent()
        result = await asyncio.wait_for(
            executor.ainvoke({"input": req.question}),
            timeout=30.0
        )
        return success_response(data={"answer": result.get("output", "")})
    except asyncio.TimeoutError:
        logger.warning(f"Agent timeout for user {user.id}")
        return error_response(message="请求超时,请稍后重试")
    except Exception as e:
        logger.error(f"Agent error for user {user.id}:{str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        current_user_id_var.reset(token)

@router.post("/rag")
async def rag_ask(req: RAGRequest):
    """纯RAG问答接口，基于新闻库检索生成答案（无需登录）"""
    try:
        result = await rag.ask(req.question)
        return success_response(data=result)
    except Exception as e:
        logger.error(f"RAG error: {str(e)}")
        return error_response(message="RAG查询失败")