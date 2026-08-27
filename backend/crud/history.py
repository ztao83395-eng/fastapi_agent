#添加浏览记录
from datetime import datetime

from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from models.history import History
from models.news import News


async def add_history(
        db:AsyncSession,
        user_id:int,
        news_id:int,
):
    """
      添加浏览记录
      逻辑：检查当前用户是否已浏览过该新闻
      - 如果已存在：更新浏览时间为当前时间
      - 如果不存在：新增浏览记录
      """
    # 1. 查询是否已存在浏览记录
    stmt = select(History).where(
        History.user_id == user_id,
        History.news_id == news_id
    )
    result = await db.execute(stmt)
    existing_history = result.scalar_one_or_none()

    current_time = datetime.utcnow()

    if existing_history :
        existing_history.view_time = current_time
        await db.commit()
        await db.refresh(existing_history)
        return existing_history
    else:
        history = History(
            user_id=user_id,
            news_id=news_id,
            view_time=current_time
        )
        db.add(history)
        await db.commit()
        await db.refresh(history)
        return history

#获取浏览历史列表
async def get_list(
        db:AsyncSession,
        user_id:int,
        page:int=1,
        page_size:int=10,
):
    #总量-》浏览的新闻列表
    count_query=select(func.count()).where(History.user_id == user_id)
    count_result=await db.execute(count_query)
    total=count_result.scalar_one_or_none()

    # 获取浏览历史列表 - 列表查询 join() + 浏览时间排序 + 分页
    # select(查询新闻模型类，字段别名).join(联合查询的模型类，联合查询的条件).where().order_by().offset().limit()
    # rows的格式为 [(新闻对象，浏览时间，历史id)]
    # 别名主要防止字段名冲突

    offset=(page-1)*page_size
    query=(select(News,History.view_time.label('view_time'),History.id.label("history_id"))
           .join(History,History.news_id == News.id)
           .where(History.user_id == user_id)
           .order_by(History.view_time.desc())
           .offset(offset).limit(page_size))
    result = await db.execute(query)
    rows = result.all()

    return rows, total

#删除浏览历史
async def delete_history(
        db:AsyncSession,
        user_id:int,
        news_id:int
):
    stmt=delete(History).where(History.user_id == user_id, History.news_id == news_id)
    result=await db.execute(stmt)
    await db.commit()
    return result.rowcount>0

#清空浏览历史
async def remove_history(
        db:AsyncSession,
        user_id:int,
):
    stmt=delete(History).where(History.user_id == user_id)
    result=await db.execute(stmt)
    return result.rowcount or 0