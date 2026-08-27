import os
import asyncio
import sys

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from models import Base

# Windows + Python 3.12 事件循环修复
if sys.platform == 'win32' and sys.version_info >= (3, 12):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# 从环境变量读取数据库配置，保留本地开发默认值
DB_HOST = os.getenv("MYSQL_HOST", "localhost")
DB_PORT = int(os.getenv("MYSQL_PORT", "3306"))
DB_USER = os.getenv("MYSQL_USER", "root")
DB_PASSWORD = os.getenv("MYSQL_PASSWORD", "123456")
DB_NAME = os.getenv("MYSQL_DATABASE", "news_app")
_DEBUG = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")

ASYNC_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"mysql+aiomysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
)

async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=_DEBUG,
    pool_size=int(os.getenv("MYSQL_POOL_SIZE", "10")),
    max_overflow=int(os.getenv("MYSQL_MAX_OVERFLOW", "20")),
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db():
    """应用启动时自动创建数据库表"""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_database():
    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except:
        await session.rollback()
        raise
    finally:
        await session.close()
