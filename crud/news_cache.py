from fastapi.encoders import jsonable_encoder
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from cache import delete_cached_news_detail
from cache.news_cache import get_cached_categories, set_caches_categories, get_cached_news_list, set_cache_news_list, \
    get_cached_news_detail
from models.news import Category, News


async def get_categories(db:AsyncSession, skip: int = 0, limit: int = 100,use_cache=True):
    #先尝试从缓存中获取数据
    if use_cache:
        cached_categories=await get_cached_categories()
        if cached_categories:
            return [Category(**item) for item in cached_categories]

    stmt=select(Category).offset(skip).limit(limit)
    results = await db.execute(stmt)
    categories= results.scalars().all() #ORM

    #写入缓存
    if use_cache and categories:
        await set_caches_categories(jsonable_encoder(categories))

    #返回数据
    return categories

async def get_news_list(
    db: AsyncSession,
    category_id: int,
    skip: int = 0,
    limit: int = 100,
    use_cache: bool = True
):
    #查询的是指定的分类下的所有新闻
    #先尝试从缓存里获取新闻列表
    #跳过的数量 页码=skip//每页数量+1
    page=skip//limit+1
    if use_cache:
        cache_list=await get_cached_news_list(category_id,page,limit)
        if cache_list:
            return [News(**items) for items in cache_list ]

    stmt=select(News).where(News.category_id == category_id).offset(skip).limit(limit)
    results = await db.execute(stmt)
    news_list= results.scalars().all()

    #写入缓存
    if use_cache and news_list:
        #先把ORM数据转换成字典才能写入缓存
        news_data=jsonable_encoder(news_list)
        await set_cache_news_list(category_id,page,limit,news_data)

    return news_list

async def get_news_count(db:AsyncSession, category_id:int):
    #查询的是指定分类下的新闻数量
    stmt=select(func.count(News.id)).where(News.category_id == category_id)
    results = await db.execute(stmt)
    return results.scalar_one()

"""-------------新闻详情（带缓存）"""
async def get_news_detail(db:AsyncSession, news_id:int,use_cache=True):
    if use_cache:
        cached = await get_cached_news_detail(news_id)
        if cached:
            return News(**cached)

    stmt=select(News).where(News.id == news_id)
    results = await db.execute(stmt)
    news=results.scalar_one_or_none()

    if use_cache and news:
        await set_cache_news_list(news_id, jsonable_encoder(news))

    return news
#每次访问，浏览量+1
async def increase_news_views(db:AsyncSession, news_id:int):
    stmt=update(News).where(News.id == news_id).values(views=News.views + 1)
    result=await db.execute(stmt)
    await db.commit()

    # 新闻内容变化，删除详情缓存
    if result.rowcount > 0:
        await delete_cached_news_detail(news_id)

    return result.rowcount > 0

#查找相关（同类）新闻
async def get_related_news(db:AsyncSession, category_id:int, news_id:int,limit:int=5):
    stmt=select(News).where(
        News.category_id == category_id,
        News.id != news_id
    ).order_by(
        News.views.desc(), #默认是升序,desc表示降序
        News.publish_time.desc()
    ).limit(limit)
    results = await db.execute(stmt)
    related_news= results.scalars().all()
    #列表推导式,推导出新闻的核心数据,然后再return
    return [{
        "id": news_detail.id,
        "title": news_detail.title,
        "content": news_detail.content,
        "image": news_detail.image,
        "author": news_detail.author,
        "publishTime": news_detail.publish_time,
        "categoryId": news_detail.category_id,
        "views": news_detail.views,
    } for news_detail in related_news]