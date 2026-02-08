from sqlalchemy.ext.asyncio import (
    create_async_engine, async_sessionmaker, AsyncSession
)

from app.core.env_conf import pg_stg


engine = create_async_engine(
    pg_stg.db_url, pool_pre_ping=True,
    pool_recycle=pg_stg.pool_recycle, pool_size=pg_stg.pool_size,
    max_overflow=pg_stg.max_overflow, pool_timeout=pg_stg.pool_timeout
)

async_session_maker = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)
