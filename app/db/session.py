"""异步数据库引擎和会话管理。"""

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings

settings = get_settings()

# Engine 负责维护数据库连接池。
# 创建 Engine 时不会立即连接数据库，真正执行 SQL 时才获取连接。
engine = create_async_engine(
    settings.database_url,
    # 从连接池取出连接前进行有效性检查，
    # 避免使用已经被数据库断开的陈旧连接。
    pool_pre_ping=True,
    # 开发调试时可以输出 SQL；生产环境通常关闭。
    echo=settings.debug,
)

# Session 工厂负责为每次请求创建独立的数据库会话。
async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    # 提交事务后不立即让对象属性失效，减少异步环境中的隐式查询问题。
    expire_on_commit=False,
)


async def get_db_session() -> AsyncIterator[AsyncSession]:
    """为一次请求提供独立的异步数据库会话。

    这里只负责会话生命周期，不自动提交事务。
    写操作应由业务服务明确决定何时 commit 或 rollback。
    """
    async with async_session_factory() as session:
        yield session
