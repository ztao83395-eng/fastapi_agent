"""新闻数据访问层：查询走 Redis 缓存（命中→DB→回填），写入同步失效缓存"""
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select, func, update

from cache import delete_cached_news_detail
from cache.news_cache import (
    get_cached_categories,
    set_caches_categories,
    get_cached_news_list,
    set_cache_news_list,
    get_cached_news_detail,
    set_cache_news_detail,
)
from models.news import Category, News


# ==================== 新闻分类 ====================

async def get_categories(db, skip: int = 0, limit: int = 100, use_cache: bool = True):
    """分类列表（优先缓存，未命中查库并回填）"""
    if use_cache:
        cached_categories = await get_cached_categories()
        if cached_categories:
            return [Category(**item) for item in cached_categories]

    stmt = select(Category).offset(skip).limit(limit)
    results = await db.execute(stmt)
    categories = results.scalars().all()  # ORM

    # 写入缓存（避免所有 key 同时过期引起缓存雪崩，缓存 2 小时）
    if use_cache and categories:
        await set_caches_categories(jsonable_encoder(categories))

    return categories


# ==================== 新闻列表（分页） ====================

async def get_news_list(
    db,
    category_id: int,
    skip: int = 0,
    limit: int = 100,
    use_cache: bool = True,
):
    """分类下的新闻分页列表（优先缓存，未命中查库并回填）"""
    page = skip // limit + 1  # 页码
    if use_cache:
        cache_list = await get_cached_news_list(category_id, page, limit)
        if cache_list:
            return [News(**items) for items in cache_list]

    stmt = select(News).where(News.category_id == category_id).offset(skip).limit(limit)
    results = await db.execute(stmt)
    news_list = results.scalars().all()

    # 先把 ORM 数据转换成字典才能写入缓存
    if use_cache and news_list:
        news_data = jsonable_encoder(news_list)
        await set_cache_news_list(category_id, page, limit, news_data)

    return news_list


async def get_news_count(db, category_id: int):
    """分类下的新闻总数"""
    stmt = select(func.count(News.id)).where(News.category_id == category_id)
    results = await db.execute(stmt)
    return results.scalar_one()


# ==================== 新闻详情 ====================

async def get_news_detail(db, news_id: int, use_cache: bool = True):
    """新闻详情（优先缓存，未命中查库并回填）"""
    if use_cache:
        cached = await get_cached_news_detail(news_id)
        if cached:
            return News(**cached)

    stmt = select(News).where(News.id == news_id)
    results = await db.execute(stmt)
    news = results.scalar_one_or_none()

    if use_cache and news:
        await set_cache_news_detail(news_id, jsonable_encoder(news))

    return news


async def increase_news_views(db, news_id: int):
    """浏览量 +1，并失效详情缓存（内容/浏览量已变化）"""
    stmt = update(News).where(News.id == news_id).values(views=News.views + 1)
    result = await db.execute(stmt)
    await db.commit()

    if result.rowcount > 0:
        await delete_cached_news_detail(news_id)

    return result.rowcount > 0


# ==================== 相关推荐 ====================

async def get_related_news(db, category_id: int, news_id: int, limit: int = 5):
    """同分类下的其他新闻，按浏览量降序、发布时间降序推荐"""
    stmt = (
        select(News)
        .where(News.category_id == category_id, News.id != news_id)
        .order_by(News.views.desc(), News.publish_time.desc())
        .limit(limit)
    )
    results = await db.execute(stmt)
    related_news = results.scalars().all()
    # 列表推导式，推导出新闻的核心数据，然后再 return
    return [{
        "id": item.id,
        "title": item.title,
        "content": item.content,
        "image": item.image,
        "author": item.author,
        "publishTime": item.publish_time,
        "categoryId": item.category_id,
        "views": item.views,
    } for item in related_news]
