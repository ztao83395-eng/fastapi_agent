#新闻相关的缓存方法：新闻分类的读取和写入
#key-value
from typing import Any, Dict, List, Optional

from config.cache_conf import get_json_cache, set_cache, delete_cache

CATEGORIES_KEY="news:categories"
NEWS_LIST_PREFIX="news_list:"
NEWS_DETAIL_PREFIX = "news_detail:"

"""---------------分类缓存--------------------"""

#获取新闻分类缓存
async def get_cached_categories():
    return await get_json_cache(CATEGORIES_KEY)

#写入新闻分类缓存:缓存的数据、过期时间
#避免所有的key同时过期，引起缓存雪崩
async def set_caches_categories(data:List[Dict[str,Any]],expire:int=7200):
    return await set_cache(CATEGORIES_KEY,data,expire)

#删除分类缓存
async def delete_caches_categories()->int:
    """"删除分类缓存"""
    return await delete_cache(CATEGORIES_KEY)

"""---------------新闻列表缓存-------------"""
def _make_news_list_key(category_id:int,page:int,size:int)->str:
    """生成新闻列表缓存键"""
    return f"{NEWS_LIST_PREFIX}{category_id}:{page}:{size}"


#写入缓存-新闻列表 key=news_list:分类id:页码:每页数量+列表数据+过期时间
async def set_cache_news_list(category_id:int,page:int,size:int,data:List[Dict[str,Any]],expire:int=7200)->bool:
    #调用的 设置Redis的方法。存新闻列表到缓存
    key=_make_news_list_key(category_id,page,size)
    return await set_cache(key,data,expire)

#读取缓存
async def get_cached_news_list(category_id:int,page:int,size:int)->Optional[List[Dict[str,Any]]]:
    key=_make_news_list_key(category_id,page,size)
    return await get_json_cache(key)

async def delete_cache_news_list(category_id:int=None)->int:
    """删除新闻列表缓存"""
    if category_id:
        pattern = f"{NEWS_LIST_PREFIX}{category_id}:*"
    else:
        pattern = f"{NEWS_LIST_PREFIX}*"
    return await delete_cache(pattern)

"""-----------新闻详情缓存--------------"""
async def get_cached_news_detail(news_id:int)->Optional[Dict[str,Any]]:
    """获取缓存的新闻详情"""
    key=f"{NEWS_DETAIL_PREFIX}{news_id}"
    return await get_json_cache(key)

async def set_cache_news_detail(
        news_id:int,
        data:List[Dict[str,Any]],
        expire:int=7200
)->bool:
    """缓存新闻详情（默认1小时）"""
    key = f"{NEWS_DETAIL_PREFIX}{news_id}"
    return await set_cache(key,data,expire)

async def delete_cached_news_detail(news_id: int) -> int:
    """删除新闻详情缓存"""
    key = f"{NEWS_DETAIL_PREFIX}{news_id}"
    return await delete_cache(key)