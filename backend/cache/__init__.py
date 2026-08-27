# cache/__init__.py
"""缓存模块"""
from .news_cache import (
    get_cached_categories,
    get_cached_news_list,
    get_cached_news_detail,
    delete_cached_news_detail,
)

__all__ = [
    "get_cached_categories",
    "get_cached_news_list",
    "get_cached_news_detail",
    "delete_cached_news_detail",
]