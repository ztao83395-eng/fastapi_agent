import asyncio
import sys

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# 修复 Windows + Python 3.12 的事件循环问题
if sys.platform == 'win32' and sys.version_info >= (3, 12):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

#1创建异步引擎
ASYNC_DATABASE_URL = "mysql+aiomysql://root:123456@localhost:3306/news_app?charset=utf8mb4"
async_engine=create_async_engine(
    ASYNC_DATABASE_URL,
    echo=True,#输出SQL日志
    pool_size=10, #设置连接池活跃的连接数
    max_overflow=20,  #允许额外的连接数
)

#需求：查询功能的接口，查询图书->依赖注入：创建依赖项获取数据库会话->Depends注入路由处理函数

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,  #绑定数据库引擎
    class_=AsyncSession,    #制定会话类
    expire_on_commit=False, #提交后会话不过期,不会重新查询数据库
)

#依赖项
async def get_database():
    session = AsyncSessionLocal()  # 不要用 async with
    try:
        yield session
        await session.commit()
    except:
        await session.rollback()
        raise
    finally:
        await session.close()