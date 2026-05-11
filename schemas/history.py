from datetime import datetime
from typing import List, Any

from pydantic import BaseModel, Field, ConfigDict

from schemas.base import NewsItemBase


class HistoryAddRequest(BaseModel):
    news_id: int = Field(...,alias="newsId")


class HistoryAddResponse(BaseModel):
    """添加浏览记录响应"""
    history_id: int = Field(..., alias="historyId", description="历史记录ID")
    news_id: int = Field(..., alias="newsId", description="新闻ID")
    view_time: datetime = Field(..., alias="viewTime", description="浏览时间")

    model_config = {"populate_by_name": True, "from_attributes": True}


# 浏览历史更新请求（类似收藏的 FavoriteUpdateRequest）
class HistoryUpdateRequest(NewsItemBase):
    history_id: int = Field(..., alias="historyId")
    view_time: datetime = Field(..., alias="viewTime")

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True
    )


from pydantic import BaseModel


class HistoryListResponse(BaseModel):
    list: List[Any]
    total: int
    has_more: bool = Field(..., alias="hasMore")

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
        arbitrary_types_allowed=True,  # 添加这个
        extra="ignore"  # 添加这个
    )