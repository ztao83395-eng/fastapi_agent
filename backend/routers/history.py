from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from utils.auth import get_current_user
from config.db_conf import get_database
from models.users import User
from schemas.history import HistoryAddRequest, HistoryAddResponse, HistoryListResponse
from utils.response import success_response
from crud import history

router = APIRouter(prefix="/api/history",tags=["history"])

@router.post("/add")
async def add_news_history(
        data: HistoryAddRequest,
        user:User=Depends(get_current_user),
        db:AsyncSession = Depends( get_database )
):
    """
        添加浏览记录
        - 需要登录认证（Token）
        - 参数：newsId
        """
    try:
        result = await history.add_history(db, user.id, data.news_id)
        # History ORM 无 history_id 字段（主键是 id），不能 model_validate，显式构造响应
        return success_response(
            message="添加浏览历史成功",
            data=HistoryAddResponse(
                history_id=result.id,
                news_id=result.news_id,
                view_time=result.view_time,
            ))
    except Exception as e:
        await db.rollback()
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"添加浏览记录失败: {str(e)}")


#得到浏览历史列表
@router.get("/list")
async def get_list_history(
        page: int = Query(1, ge=1),
        page_size: int = Query(10, ge=1, le=100, alias="pageSize"),
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_database)
):
    rows, total = await history.get_list(db, user.id, page, page_size)

    # 过滤掉私有属性
    history_list = []
    for news, view_time, history_id in rows:
        # 只取需要的字段，不包含 _sa_instance_state
        item = {
            "id": news.id,
            "title": news.title,
            "description": news.description,
            "image": news.image,
            "author": news.author,
            "categoryId": news.category_id,
            "views": news.views,
            "publishedTime": news.publish_time,
            "viewTime": view_time,
            "historyId": history_id
        }
        history_list.append(item)

    has_more = total > page * page_size

    # 直接返回字典，不使用 HistoryListResponse 和 success_response
    return {
        "code": 200,
        "message": "获取浏览历史成功",
        "data": {
            "list": history_list,
            "total": total,
            "hasMore": has_more
        }
    }

#删除浏览历史
@router.delete("/delete/{news_id}")
async def delete_history(
        news_id: int,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_database)
):
    result = await history.delete_history(db, user.id, news_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="浏览历史不存在")
    return success_response(message="删除成功")

#清空浏览历史
@router.delete("/clear")
async def clear_history(
        db: AsyncSession = Depends(get_database),
        user: User = Depends(get_current_user)
):
    result=await history.remove_history(db, user.id)
    return success_response(message=f"清空成功,清除了{result}条")

