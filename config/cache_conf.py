import os
import logging
from typing import Any, Optional

import redis.asyncio as redis
import json

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
RAG_REDIS_DB = int(os.getenv("RAG_REDIS_DB", "15"))

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    decode_responses=True
)

rag_redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=RAG_REDIS_DB,
    decode_responses=True
)

logger = logging.getLogger(__name__)


async def get_cache(key: str, use_rag: bool = False) -> Optional[str]:
    """获取字符串缓存"""
    client = rag_redis_client if use_rag else redis_client
    try:
        return await client.get(key)
    except Exception as e:
        logger.error(f"获取缓存失败 key={key}: {e}")
        return None


async def get_json_cache(key: str, use_rag: bool = False) -> Optional[Any]:
    """获取JSON缓存"""
    client = rag_redis_client if use_rag else redis_client
    try:
        data = await client.get(key)
        if data:
            return json.loads(data)
        return None
    except Exception as e:
        logger.error(f"获取缓存失败 key={key}: {e}")
        return None


async def set_cache(key: str, value: Any, expire: int = 3600, use_rag: bool = False) -> bool:
    """设置缓存"""
    client = rag_redis_client if use_rag else redis_client
    try:
        if isinstance(value, (dict, list)):
            value = json.dumps(value, ensure_ascii=False)
        await client.set(key, value, ex=expire)
        return True
    except Exception as e:
        logger.error(f"获取缓存失败 key={key}: {e}")
        return False


async def delete_cache(key: str, use_rag: bool = False) -> int:
    """删除单个缓存"""
    client = rag_redis_client if use_rag else redis_client
    try:
        return await client.delete(key)
    except Exception as e:
        logger.error(f"获取缓存失败 key={key}: {e}")
        return 0


async def cache_exists(key: str, use_rag: bool = False) -> bool:
    """检查缓存是否存在"""
    client = rag_redis_client if use_rag else redis_client
    try:
        return await client.exists(key) > 0
    except Exception as e:
        logger.error(f"检查缓存失败 key={key}: {e}")
        return False
