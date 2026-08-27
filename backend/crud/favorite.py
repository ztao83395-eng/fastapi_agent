#检查收藏状态：当前用户是否收藏了这一条新闻
from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.favorite import Favorite
from models.news import News


#检查用户是否收藏了消息
async def is_new_favorite(
        db: AsyncSession,
        user_id: int,
        news_id: int,
):
    query=select(Favorite).where(Favorite.user_id == user_id,).where(Favorite.news_id == news_id)
    result=await db.execute(query)
    #是否有收藏记录
    #True（记录存在）或 False（记录不存在）
    return result.scalar_one_or_none() is not None

#批量查询收藏状态：一次 in 查询返回用户已收藏的新闻 id 集合
#（新闻列表页加载后调用一次，避免逐条 check 发 N 个请求）
async def get_favorite_news_ids(
        db: AsyncSession,
        user_id: int,
        news_ids: list[int],
) -> set[int]:
    if not news_ids:
        return set()
    query = select(Favorite.news_id).where(
        Favorite.user_id == user_id,
        Favorite.news_id.in_(news_ids),
    )
    result = await db.execute(query)
    return set(result.scalars().all())

#添加收藏
async def add_news_favorite(
        db: AsyncSession,
        user_id: int,
        news_id: int,
):
    # 已收藏过则直接返回现有记录（幂等），避免触发唯一约束 IntegrityError
    query=select(Favorite).where(Favorite.user_id == user_id, Favorite.news_id == news_id)
    result=await db.execute(query)
    existing=result.scalar_one_or_none()
    if existing:
        return existing

    favorite=Favorite(user_id=user_id,news_id=news_id)
    db.add(favorite)
    await db.commit()
    await db.refresh(favorite)
    return favorite


#取消收藏
async def delete_news_favorite(
        db: AsyncSession,
        user_id: int,
        news_id: int,
):
    stmt=delete(Favorite).where(Favorite.user_id == user_id,Favorite.news_id == news_id)
    result=await db.execute(stmt)
    await db.commit()
    return result.rowcount>0  #result.rowcount 返回的是受 SQL 语句影响的行数（即被删除、更新或插入的记录数量）。

#获取收藏列表：获取的是某个用户的收藏列表 -》 分页功能
async def get_favorite_list(
        db: AsyncSession,
        user_id: int,
        page: int = 1,
        page_size: int = 10,
):
    #总量-》收藏的新闻列表
    count_query=select(func.count()).where(Favorite.user_id == user_id)
    count_result=await db.execute(count_query)
    total=count_result.scalar_one_or_none()

    #获取收藏列表-》列表查询join（）+收藏时间排序+分页
    #select（查询主题模型类，字段别名）.join(联合查询的模型类，联合查询的条件).where().order_by().offest().limit()
    #rows的格式为 [(新闻对象，收藏时间，收藏id)]
    #别名主要防止字段名冲突
    offest=(page-1)*page_size
    query=(select(News,Favorite.created_at.label("favorite_time"),Favorite.id.label("favorite_id"))
           .join(Favorite,Favorite.news_id == News.id)
           .where(Favorite.user_id == user_id,)
           .order_by(Favorite.created_at.desc())
           .offset(offest).limit(page_size))
    result=await db.execute(query)
    rows=result.all()
    return rows , total

#清空收藏列表：当前用户的收藏列表
async def remove_all_favorite(
        db: AsyncSession,
        user_id: int,
):
    stmt=delete(Favorite).where(Favorite.user_id == user_id)
    result=await db.execute(stmt)
    await db.commit()

    #返回删除
    return result.rowcount or 0