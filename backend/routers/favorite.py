from fastapi import APIRouter, Query, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from config.db_conf import get_database
from models.users import User
from schemas.favorite import FavoriteCheckResponse, FavoriteAddRequest, FavoriteBatchCheckRequest
from utils.auth import get_current_user
from crud import favorite
from utils.response import success_response

router = APIRouter(prefix="/api/favorite",tags=["favorite"])

#查看一个新闻是否被用户收藏
@router.get("/check")
async def check_favorite(
        news_id: int = Query(..., alias="newsId"),
        user: User = Depends(get_current_user),
        db:AsyncSession = Depends(get_database)
):
    is_favorited = await favorite.is_new_favorite(db,user.id,news_id)
    return success_response(message="检查收藏状态成功",data=FavoriteCheckResponse(isFavorite=is_favorited))

#批量检查收藏状态：一次查询当前页所有新闻的收藏情况
#（新闻列表接口有 Redis 缓存，不能混入用户态数据，所以单独出批量接口，
#  前端在列表页加载后调用一次，避免逐条 check 发 N 个请求）
@router.post("/batch-check")
async def batch_check_favorite(
        data: FavoriteBatchCheckRequest,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_database)
):
    favorite_ids = await favorite.get_favorite_news_ids(db, user.id, data.news_ids)
    return success_response(message="批量检查收藏状态成功", data={"favoriteIds": list(favorite_ids)})

#添加收藏
@router.post("/add")
async def add_favorite(
        data: FavoriteAddRequest,
        user: User = Depends(get_current_user),
        db:AsyncSession = Depends(get_database)
):
    result=await favorite.add_news_favorite(db,user.id,data.news_id)
    return success_response(message="添加收藏成功",data=result)

#取消收藏
@router.delete("/remove")
#DELETE 请求 - 通常不带请求体
async def remove_favorite(
        news_id: int = Query(..., alias="newsId"),
        user: User = Depends(get_current_user),
        db:AsyncSession = Depends(get_database)
):
    result=await favorite.delete_news_favorite(db,user.id,news_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="收藏记录不存在")
    return success_response(message="取消收藏成功")

#获取收藏列表
@router.get("/list")
async def get_favorite_list(
        page:int=Query(1,ge=1),
        page_size:int=Query(10,ge=1,le=100,alias="pageSize"),
        user:User = Depends(get_current_user),
        db:AsyncSession=Depends(get_database),
):
    rows,total=await favorite.get_favorite_list(db,user.id, page, page_size)
    # 显式挑选字段（camelCase），避免 news.__dict__ 带 _sa_instance_state 且字段名与前端约定不符
    favorite_list=[{
        "id": news.id,
        "title": news.title,
        "description": news.description,
        "image": news.image,
        "author": news.author,
        "categoryId": news.category_id,
        "views": news.views,
        "publishedTime": news.publish_time,
        "favoriteTime": favorite_time,
        "favoriteId": favorite_id
    } for news,favorite_time,favorite_id in rows]
    has_more=total>page*page_size

    return success_response(message="获取收藏列表成功",data={
        "list": favorite_list,
        "total": total,
        "hasMore": has_more,
    })

@router.delete("/clear")
async def clear_favorite(
        user: User = Depends(get_current_user),
        db:AsyncSession = Depends(get_database)
):
    count=await favorite.remove_all_favorite(db,user.id)
    return success_response(message=f"清空{count}条记录")