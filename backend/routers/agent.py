import asyncio
import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Security
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from typing import Optional

from langchain_core.messages import AIMessage, HumanMessage
from models.users import User
from services.agent_tools import create_agent_executor
from services.context import current_user_id_var
from services.rag_chain import rag
from services.usage import TokenUsageHandler, check_quota, get_today_usage, record_usage
from config.db_conf import get_database
from config.llm_conf import AI_DAILY_TOKEN_LIMIT
from utils.auth import get_current_user
from utils.response import success_response, error_response
from crud import chat as chat_crud

logger=logging.getLogger(__name__)
router=APIRouter(prefix="/api/agent",tags=["agent"])

class ChatRequest(BaseModel):
    question:str=Field(...,min_length=1,max_length=1000)
    # 会话 id：传入则追加到该会话并带多轮上下文；不传则自动新建会话
    session_id:Optional[int]=Field(default=None, alias="sessionId")

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
        db: AsyncSession = Depends(get_database),
):
    """Agent 对话接口,支持工具调用（需要登录）"""
    token = current_user_id_var.set(user.id)
    # 调用前检查今日额度
    available, today_used, daily_limit = await check_quota(db, user.id)
    if not available:
        return error_response(message="今日 AI 额度已用完，请明天再试", code=429)
    try:
        executor = await get_agent()
        handler = TokenUsageHandler()
        result = await asyncio.wait_for(
            executor.ainvoke({"input": req.question}, config={"callbacks": [handler]}),
            timeout=30.0
        )
        # 记录本次消耗
        await record_usage(db, user.id, handler.prompt_tokens, handler.completion_tokens)
        return success_response(data={
            "answer": result.get("output", ""),
            "usage": handler.to_dict(),
        })
    except asyncio.TimeoutError:
        logger.warning(f"Agent timeout for user {user.id}")
        return error_response(message="请求超时,请稍后重试")
    except Exception as e:
        logger.error(f"Agent error for user {user.id}:{str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        current_user_id_var.reset(token)


# 工具调用时展示给用户的状态文案（key 为 agent_tools.py 中的工具名）
TOOL_MESSAGES = {
    "search_news_by_keyword": "🔍 正在搜索新闻…",
    "add_favorite": "⭐ 正在收藏…",
    "remove_favorite": "💔 正在取消收藏…",
    "get_my_favorites": "📋 正在查看我的收藏…",
    "clear_favorites": "🗑 正在清空收藏…",
}


@router.post("/chat/stream")
async def agent_chat_stream(
        req: ChatRequest,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_database),
):
    """Agent 对话流式接口（SSE，需要登录）：token 级逐字返回 + 工具状态 + 用量"""
    available, today_used, daily_limit = await check_quota(db, user.id)
    if not available:
        return error_response(message="今日 AI 额度已用完，请明天再试", code=429)
    try:
        executor = await get_agent()

        async def event_generator():
            # contextvar 必须在生成器内部 set（不能放外层函数）：
            # StreamingResponse 的生成器在接口函数返回后才由响应 task 消费，
            # 若在外层 set + finally reset，工具执行时 contextvar 已被重置为 0，
            # 导致 clear_favorites 等工具误判"未登录，无法操作"
            token = current_user_id_var.set(user.id)
            try:
                # —— 会话解析：无 sessionId 自动新建；有则校验归属 ——
                if req.session_id:
                    session = await chat_crud.get_session(db, req.session_id, user.id)
                    if not session:
                        yield f"data: {json.dumps({'type': 'error', 'message': '会话不存在或无权访问'}, ensure_ascii=False)}\n\n"
                        return
                    session_id = req.session_id
                else:
                    session = await chat_crud.create_session(db, user.id)
                    session_id = session.id

                # 多轮上下文：最近 10 条消息转 Human/AIMessage 注入 chat_history（prompt 模板已有该占位符）
                recent_messages = await chat_crud.get_recent_messages(db, session_id, 10)
                chat_history = [
                    HumanMessage(content=m.content) if m.role == "user" else AIMessage(content=m.content)
                    for m in recent_messages
                ]

                # 流式模式下 callbacks 收不到统计，改从 on_chat_model_end 的 usage_metadata 累计
                # （工具循环会多次调用 LLM，各轮累加；OpenAI API 会返回 usage）
                prompt_tokens = 0
                completion_tokens = 0
                full_answer = ""
                try:
                    # 30 秒超时（与 /chat 一致），用 astream_events 监听模型输出事件，
                    # 事件粒度是 token 块（chunk.content 纯文本，工具参数在 tool_call_chunks 中，天然被过滤）
                    # v2 事件格式：on_chat_model_end 的 output 是带 usage_metadata 的消息对象（v1 是 LLMResult，拿不到 usage）
                    async with asyncio.timeout(30):
                        async for event in executor.astream_events(
                            {"input": req.question, "chat_history": chat_history},
                            version="v2",
                        ):
                            if event["event"] == "on_chat_model_stream":
                                chunk = event["data"]["chunk"]
                                content = chunk.content if isinstance(chunk.content, str) else ""
                                if content:
                                    full_answer += content
                                    yield f"data: {json.dumps({'type': 'token', 'content': content}, ensure_ascii=False)}\n\n"
                            elif event["event"] == "on_tool_start":
                                # 工具调用开始：工具名在事件顶层 name 字段
                                tool_name = event.get("name", "")
                                yield f"data: {json.dumps({'type': 'tool', 'message': TOOL_MESSAGES.get(tool_name, '⏳ 正在处理…')}, ensure_ascii=False)}\n\n"
                            elif event["event"] == "on_chat_model_end":
                                # 流式模式下 callbacks 收不到统计，从 end 事件的 usage_metadata 累计
                                # （工具循环会多次调用 LLM，各轮累加；OpenAI API 会返回 usage）
                                usage = getattr(event["data"].get("output"), "usage_metadata", None) or {}
                                prompt_tokens += usage.get("input_tokens", 0)
                                completion_tokens += usage.get("output_tokens", 0)
                except asyncio.TimeoutError:
                    yield f"data: {json.dumps({'type': 'error', 'message': '请求超时，请稍后重试'}, ensure_ascii=False)}\n\n"
                    return
                except Exception as e:
                    logger.error(f"Agent stream error for user {user.id}:{str(e)}")
                    yield f"data: {json.dumps({'type': 'error', 'message': 'AI 服务异常，请稍后重试'}, ensure_ascii=False)}\n\n"
                    return
                # 正常结束：落库本轮问答（问题 + 回答），记录用量，告知前端（sessionId 供前端绑定当前会话）
                await chat_crud.add_message(db, session_id, "user", req.question)
                await chat_crud.add_message(db, session_id, "assistant", full_answer)
                await record_usage(db, user.id, prompt_tokens, completion_tokens)
                yield f"data: {json.dumps({'type': 'done', 'usage': {'promptTokens': prompt_tokens, 'completionTokens': completion_tokens, 'totalTokens': prompt_tokens + completion_tokens}, 'sessionId': session_id}, ensure_ascii=False)}\n\n"
                yield "data: [DONE]\n\n"
            finally:
                # 流结束（含客户端断开）时复位，避免污染后续请求
                current_user_id_var.reset(token)

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache"},
        )
    except Exception:
        raise


@router.post("/rag")
async def rag_ask(req: RAGRequest):
    """纯RAG问答接口，基于新闻库检索生成答案（无需登录）"""
    try:
        handler = TokenUsageHandler()
        result = await rag.ask(req.question, callbacks=[handler])
        result["usage"] = handler.to_dict()
        return success_response(data=result)
    except Exception as e:
        logger.error(f"RAG error: {str(e)}")
        return error_response(message="RAG查询失败")


@router.get("/usage")
async def get_usage(
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_database),
):
    """查询用户今日 AI token 消耗与剩余额度"""
    today_used = await get_today_usage(db, user.id)
    return success_response(data={
        "todayUsed": today_used,
        "dailyLimit": AI_DAILY_TOKEN_LIMIT,
        "remaining": max(0, AI_DAILY_TOKEN_LIMIT - today_used),
    })
