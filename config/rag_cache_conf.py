import logging
from typing import Any

import redis.asyncio as redis
import json



REDIS_HOST="localhost"
REDIS_PORT=6379
REDIS_DB=15

#创建RAG专属前缀
RAG_KEY_PREFIX="rag"


#创建Redis的链接对象
redis_client=redis.Redis(
    host=REDIS_HOST,        #Redis 服务器的主机地址
    port=REDIS_PORT,        #Redis端口号
    db=REDIS_DB,            #Redis 数据库编号 0-15
    decode_responses=True   #是否将字节数据解码为字符串
)

# 辅助函数：自动添加前缀
def _make_key(key: str) -> str:
    return f"{RAG_KEY_PREFIX}{key}"

#设置 和 读取缓存
#读字符串
async def get_cache(key:str):
    try:
        full_key = _make_key(key)
        return await redis_client.get(full_key)
    except Exception as e:
        print(f"获取缓存失败:{e}")
        return None

#读取：列表或字典
async def get_json_cache(key:str):
    try:
        full_key = _make_key(key)
        data = await redis_client.get(full_key)
        if data:
            return json.loads(data)
        return None
    except Exception as e:
        print(f"获取JSON缓存失败:{e}")
        return None

#设置缓存
async def set_cache(key:str,value:Any,expire:int =3600):
    try:
        full_key = _make_key(key)
        if isinstance(value,(dict,list)):
            #转字符再存
            value = json.dumps(value,ensure_ascii=False) #中文正常保存
        await redis_client.set(full_key, value, ex=expire)
        return True
    except Exception as e:
        print(f"设置缓存失败:{e}")
        return False