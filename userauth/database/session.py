"""
Module to manage the scope of the session.
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from userauth.common.config import SERVER_CONFIG

from .manager import DatabaseManager
from .models import Base

if SERVER_CONFIG.DATABASE_ENGINE_ARGS is None:
    engine = create_async_engine(SERVER_CONFIG.DATABASE_ENGINE_URL)
else:
    engine = create_async_engine(
        SERVER_CONFIG.DATABASE_ENGINE_URL,
        connect_args=SERVER_CONFIG.DATABASE_ENGINE_ARGS.model_dump(),
    )


async def get_database_manager():
    session = AsyncSession(engine)
    try:
        yield DatabaseManager(session)
    finally:
        await session.close()


async def safe_create_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
