import os
import logging
from typing import Any

import redis.asyncio as redis
import json

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("RAG_REDIS_DB", "15"))

RAG_KEY_PREFIX = "rag"

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    decode_responses=True
)


def _make_key(key: str) -> str:
    return f"{RAG_KEY_PREFIX}{key}"


logger = logging.getLogger(__name__)


async def get_cache(key: str):
    try:
        full_key = _make_key(key)
        return await redis_client.get(full_key)
    except Exception as e:
        logger.error(f"获取缓存失败:{e}")
        return None


async def get_json_cache(key: str):
    try:
        full_key = _make_key(key)
        data = await redis_client.get(full_key)
        if data:
            return json.loads(data)
        return None
    except Exception as e:
        logger.error(f"获取JSON缓存失败:{e}")
        return None


async def set_cache(key: str, value: Any, expire: int = 3600):
    try:
        full_key = _make_key(key)
        if isinstance(value, (dict, list)):
            value = json.dumps(value, ensure_ascii=False)
        await redis_client.set(full_key, value, ex=expire)
        return True
    except Exception as e:
        logger.error(f"设置缓存失败:{e}")
        return False
