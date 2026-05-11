from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from models.news import Category, News


async def get_categories(db:AsyncSession, skip: int = 0, limit: int = 100):
    stmt=select(Category).offset(skip).limit(limit)
    results = await db.execute(stmt)
    return results.scalars().all()

async def get_news_list(db:AsyncSession, category_id:int ,skip: int = 0, limit: int = 100):
    #查询的是指定的分类下的所有新闻
    stmt=select(News).where(News.category_id == category_id).offset(skip).limit(limit)
    results = await db.execute(stmt)
    return results.scalars().all()

async def get_news_count(db:AsyncSession, category_id:int):
    #查询的是指定分类下的新闻数量
    stmt=select(func.count(News.id)).where(News.category_id == category_id)
    results = await db.execute(stmt)
    return results.scalar_one()

#按id查询新闻
async def get_news_detail(db:AsyncSession, news_id:int):
    stmt=select(News).where(News.id == news_id)
    results = await db.execute(stmt)
    return results.scalar_one_or_none()
#每次访问，浏览量+1
async def increase_news_views(db:AsyncSession, news_id:int):
    stmt=update(News).where(News.id == news_id).values(views=News.views + 1)
    result=await db.execute(stmt)
    await db.commit()

    #更新->检查数据库是否真的命中->命中了返回True
    return result.rowcount>0

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