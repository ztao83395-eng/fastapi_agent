import logging
from typing import Any, Optional

import redis.asyncio as redis
import json



REDIS_HOST="localhost"
REDIS_PORT=6379
REDIS_DB=0
RAG_REDIS_DB=15

#创建Redis的链接对象(通用缓存)
redis_client=redis.Redis(
    host=REDIS_HOST,        #Redis 服务器的主机地址
    port=REDIS_PORT,        #Redis端口号
    db=REDIS_DB,            #Redis 数据库编号 0-15
    decode_responses=True   #是否将字节数据解码为字符串
)

rag_redis_client=redis.Redis(
    host=REDIS_HOST,  # Redis 服务器的主机地址
    port=REDIS_PORT,  # Redis端口号
    db=RAG_REDIS_DB,  # Redis 数据库编号 0-15
    decode_responses=True
)

logger = logging.getLogger(__name__)

#设置 和 读取缓存
#读字符串
async def get_cache(key:str,use_rag:bool=False)->Optional[str]:
    """获取字符串缓存"""
    client=rag_redis_client if use_rag else redis_client
    try:
        return await client.get(key)
    except Exception as e:
        logger.error(f"获取缓存失败 key={key}: {e}")
        return None

#读取：列表或字典
async def get_json_cache(key:str,use_rag:bool=False)->Optional[Any]:
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

#设置缓存
async def set_cache(key:str,value:Any,expire:int =3600,use_rag:bool=False)->bool:
    """设置缓存"""
    client = rag_redis_client if use_rag else redis_client
    try:
        if isinstance(value,(dict,list)):
            #转字符再存
            value = json.dumps(value,ensure_ascii=False) #中文正常保存
        await client.set(key, value, ex=expire)
        return True
    except Exception as e:
        logger.error(f"获取缓存失败 key={key}: {e}")
        return False

async def delete_cache(key:str,use_rag:bool=False)->int:
    """删除单个缓存"""
    client = rag_redis_client if use_rag else redis_client
    try:
        return await client.delete(key)
    except Exception as e:
        logger.error(f"获取缓存失败 key={key}: {e}")
        return 0

async def cache_exists(key:str,use_rag:bool=False)->bool:
    """检查缓存是否存在"""
    client = rag_redis_client if use_rag else redis_client
    try:
        return await client.exists(key)>0
    except Exception as e:
        logger.error(f"检查缓存失败 key={key}: {e}")
        return False
