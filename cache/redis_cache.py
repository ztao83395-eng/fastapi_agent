"""Redis 通用缓存函数：字符串 / JSON 读写、删除、存在性检查

use_rag=True 时操作 RAG 专用 db（15），否则操作业务缓存 db（0）。
"""
import json
import logging
from typing import Any, Optional

import redis.asyncio as redis

from config.redis_conf import redis_client, REDIS_HOST, REDIS_PORT, RAG_REDIS_DB

logger = logging.getLogger(__name__)

# RAG 问答缓存客户端（缓存层专用，隔离 db）
_rag_redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=RAG_REDIS_DB,
    decode_responses=True
)


def _pick_client(use_rag: bool):
    return _rag_redis_client if use_rag else redis_client


async def get_cache(key: str, use_rag: bool = False) -> Optional[str]:
    """获取字符串缓存"""
    client = _pick_client(use_rag)
    try:
        return await client.get(key)
    except Exception as e:
        logger.error(f"获取缓存失败 key={key}: {e}")
        return None


async def get_json_cache(key: str, use_rag: bool = False) -> Optional[Any]:
    """获取JSON缓存"""
    client = _pick_client(use_rag)
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
    client = _pick_client(use_rag)
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
    client = _pick_client(use_rag)
    try:
        return await client.delete(key)
    except Exception as e:
        logger.error(f"获取缓存失败 key={key}: {e}")
        return 0


async def cache_exists(key: str, use_rag: bool = False) -> bool:
    """检查缓存是否存在"""
    client = _pick_client(use_rag)
    try:
        return await client.exists(key) > 0
    except Exception as e:
        logger.error(f"检查缓存失败 key={key}: {e}")
        return False
