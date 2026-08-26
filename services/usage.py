from datetime import datetime, time

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.callbacks import BaseCallbackHandler

from models.usage import AiUsage
from config.llm_conf import AI_DAILY_TOKEN_LIMIT


class TokenUsageHandler(BaseCallbackHandler):
    """捕获 LLM 调用的 token 用量（兼容 token_usage / usage_metadata 两种格式）"""

    def __init__(self):
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.total_tokens = 0

    def on_llm_end(self, response, **kwargs):
        llm_output = getattr(response, "llm_output", None) or {}
        usage = llm_output.get("token_usage") or {}
        usage_metadata = getattr(response, "usage_metadata", None) or {}
        prompt = usage.get("prompt_tokens") or usage_metadata.get("input_tokens") or 0
        completion = usage.get("completion_tokens") or usage_metadata.get("output_tokens") or 0
        self.prompt_tokens += int(prompt)
        self.completion_tokens += int(completion)
        self.total_tokens += int(prompt) + int(completion)

    def to_dict(self) -> dict:
        return {
            "promptTokens": self.prompt_tokens,
            "completionTokens": self.completion_tokens,
            "totalTokens": self.total_tokens,
        }


async def get_today_usage(db: AsyncSession, user_id: int) -> int:
    """统计用户今日已消耗的总 token 数"""
    today_start = datetime.combine(datetime.now().date(), time.min)
    stmt = select(func.coalesce(func.sum(AiUsage.total_tokens), 0)).where(
        AiUsage.user_id == user_id,
        AiUsage.created_at >= today_start,
    )
    result = await db.execute(stmt)
    return int(result.scalar_one())


async def check_quota(db: AsyncSession, user_id: int) -> tuple[bool, int, int]:
    """检查用户今日额度是否用尽，返回 (是否可用, 今日已用, 每日限额)"""
    today_used = await get_today_usage(db, user_id)
    return today_used < AI_DAILY_TOKEN_LIMIT, today_used, AI_DAILY_TOKEN_LIMIT


async def record_usage(db: AsyncSession, user_id: int, prompt_tokens: int, completion_tokens: int) -> AiUsage:
    """记录一次 AI 调用消耗，返回用量记录"""
    record = AiUsage(
        user_id=user_id,
        prompt_tokens=prompt_tokens or 0,
        completion_tokens=completion_tokens or 0,
        total_tokens=(prompt_tokens or 0) + (completion_tokens or 0),
    )
    db.add(record)
    await db.flush()
    return record
