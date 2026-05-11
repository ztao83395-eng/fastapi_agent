# cache/__init__.py
"""缓存模块"""
from .news_cache import (
    get_cached_categories,
    set_cached_categories,
    delete_cached_categories,
    get_cached_news_list,
    set_cached_news_list,
    delete_cached_news_list,
    get_cached_news_detail,
    set_cached_news_detail,
    delete_cached_news_detail,
)

__all__ = [
    "get_cached_categories",
    "set_cached_categories",
    "delete_cached_categories",
    "get_cached_news_list",
    "set_cached_news_list",
    "delete_cached_news_list",
    "get_cached_news_detail",
    "set_cached_news_detail",
    "delete_cached_news_detail",
]