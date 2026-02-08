from sqlalchemy.ext.asyncio import (
    create_async_engine, async_sessionmaker, AsyncSession
)

from app.core.env_conf import stg


engine = create_async_engine(
    stg.db_url, pool_pre_ping=True,
    pool_recycle=stg.pool_recycle, pool_size=stg.pool_size,
    max_overflow=stg.max_overflow, pool_timeout=stg.pool_timeout
)

async_session_maker = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)
