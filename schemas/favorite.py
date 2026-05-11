from datetime import datetime
from typing import Optional, List

from pydantic import Field, BaseModel, ConfigDict

from schemas.base import NewsItemBase


class FavoriteCheckResponse(BaseModel):
    is_favorite: bool = Field(...,alias="isFavorite")
    class Config:
        populate_by_name = True

class FavoriteAddRequest(BaseModel):
    news_id: int = Field(...,alias="newsId")

#规划两个类：一个是新闻模型类+收藏的模型类
class FavoriteUpdateRequest(NewsItemBase):
    favorite_id: int = Field(...,alias="favoriteId")
    favorite_time: datetime = Field(...,alias="favoriteTime")

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True
    )

#收藏列表接口响应类
class FavoriteListResponse(NewsItemBase):
    list: List[FavoriteCheckResponse]
    total:int
    has_more: bool=Field(...,alias="hasMore")

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True
    )
