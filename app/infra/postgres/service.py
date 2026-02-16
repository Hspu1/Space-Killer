from asyncio import wait_for, TimeoutError as AsyncTimeoutError
import logging
from time import perf_counter

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine, AsyncSession,
    async_sessionmaker, create_async_engine
)

from app.core.env_conf import PostgresSettings
from app.utils import Colors

logger = logging.getLogger(__name__)


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
            await wait_for(self.ping(), timeout=5.0)

        except (SQLAlchemyError, AsyncTimeoutError) as e:
            await self.disconnect()
            self._engine, self._session_maker = None, None
            logger.error(f"Database readiness check failed: {e}")

            raise ConnectionError("Postgres isn't ready") from e

        if logger.isEnabledFor(logging.DEBUG):
            dur_ms = (perf_counter() - start) * 1000
            logger.debug(
                "%s[DB] CONNECTED%s pool=%d+%d: total %s%.2fms%s",
                Colors.PURPLE, Colors.RESET, self._config.pool_size,
                self._config.max_overflow, Colors.YELLOW, dur_ms, Colors.RESET
            )

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
        finally:
            self._engine, self._session_maker = None, None

        if logger.isEnabledFor(logging.DEBUG):
            dur_ms = (perf_counter() - start) * 1000
            logger.debug(
                "%s[DB] DISCONNECTED%s: total %s%.2fms%s",
                Colors.PURPLE, Colors.RESET,
                Colors.YELLOW, dur_ms, Colors.RESET
            )
