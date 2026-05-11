
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from config.db_conf import get_database
from crud import news, news_cache

#创建APIRouter实例
#prefix 路由器前缀(API接口规范文档)
#tags 分组 标签
router = APIRouter(prefix="/api/news",tags=["news"])

#接口实现流程
#1 模块话路由->API接口规范文档
#2 定义模型类->数据库表（数据库设计文档）
#3 在crud 文件夹里面创建文件,封装操作数据库的方法
#4 在路由器处理函数里面调用 crud 封装好的方法,响应结果

@router.get("/categories")
async def get_categories(skip: int = 0, limit: int = 100,db:AsyncSession=Depends(get_database),use_cache: bool = Query(True, description="是否使用缓存")):
    #先获取数据库里的新闻数据分类->先定义模型类->封装查询数据的方法
    categories=await news_cache.get_categories(db,skip,limit,use_cache)
    return{
        "code":200,
        "msg":"获取分类成功",
        "data":categories
    }

@router.get("/list")
async def get_news_list(
        category_id:int=Query(...,alias="categoryId"),
        page:int=1,
        page_size:int=Query(10,alias="pageSize",le=100),
        db:AsyncSession=Depends(get_database),
        use_cache: bool = Query(True, description="是否使用缓存"),
):
    #思路：处理分页规则->查询新闻列表->计算总量->计算是否还有更多
    offset = (page-1)*page_size
    news_list=await news_cache.get_news_list(db,category_id,offset,page_size,use_cache)
    total=await news_cache.get_news_count(db,category_id)
    #(跳过的+当前列表里面的数量)<总量
    has_more=(offset+len(news_list)) < total
    return {
        "code":200,
        "msg":"success",
        "data":{
            "list":news_list,
            "total":total,
            "hasMore":has_more,
        }
    }

@router.get("/detail")
async def get_news_detail(
        news_id: int = Query(..., alias="id"),
        use_cache: bool = Query(True, description="是否使用缓存"),  # 新增
        db: AsyncSession = Depends(get_database)
):
    news_detail = await news_cache.get_news_detail(db, news_id, use_cache=use_cache)
    if news_detail is None:
        raise HTTPException(status_code=404, detail="新闻不存在")

    # 浏览量+1 会内部自动删除缓存
    await news_cache.increase_news_views(db, news_detail.id)

    related_news = await news.get_related_news(db, news_detail.category_id, news_detail.id)

    return {
        "code": 200,
        "message": "success",
        "data": {
            "id": news_detail.id,
            "title": news_detail.title,
            "content": news_detail.content,
            "image": news_detail.image,
            "author": news_detail.author,
            "publishTime": news_detail.publish_time,
            "categoryId": news_detail.category_id,
            "views": news_detail.views,
            "relatedNews": related_news,
        }
    }