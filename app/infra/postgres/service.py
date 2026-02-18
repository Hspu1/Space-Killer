from asyncio import TimeoutError as AsyncTimeoutError
from time import perf_counter

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine, AsyncSession,
    async_sessionmaker, create_async_engine
)

from app.core.env_conf import PostgresSettings
from app.utils import log_debug_db, log_error_infra


class PostgresService:
    __slots__ = ("_config", "_engine", "_session_maker")

    def __init__(self, config: PostgresSettings) -> None:
        self._config = config
        self._engine: AsyncEngine | None = None
        self._session_maker: async_sessionmaker[AsyncSession] | None = None

    async def connect(self) -> None:
        if self._engine:
            return

        start = perf_counter()
        self._engine = create_async_engine(
            url=self._config.db_url, pool_pre_ping=True, pool_recycle=self._config.pool_recycle,
            pool_size=self._config.pool_size, max_overflow=self._config.max_overflow,
            pool_timeout=self._config.pool_timeout
        )
        self._session_maker = async_sessionmaker(
            bind=self._engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
        )

        try:
            log_debug_db(
                op="CONNECTED", start_time=start,
                detail=f"pool={self._config.pool_size}+{self._config.max_overflow}"
            )

        except (SQLAlchemyError, AsyncTimeoutError) as e:
            await self.disconnect()
            self._engine, self._session_maker = None, None
            log_error_infra(service="DB", op="CONNECT", exc=e)
            raise ConnectionError("Postgres isn't ready") from e

    async def ping(self) -> None:
        if not self._engine:
            raise RuntimeError("Engine isn't initialized")

        async with self._engine.connect() as conn:
            await conn.execute(text("SELECT 1"))

    def get_session_maker(self) -> async_sessionmaker[AsyncSession]:
        if self._session_maker is None:
            raise RuntimeError("PostgresService isn't initialized")

        return self._session_maker

    async def disconnect(self) -> None:
        if not self._engine:
            return

        start = perf_counter()
        try:
            await self._engine.dispose()
            log_debug_db(op="DISCONNECTED", start_time=start)
        except Exception as e:
            log_error_infra(service="DB", op="DISCONNECT", exc=e)
        finally:
            self._engine, self._session_maker = None, None
