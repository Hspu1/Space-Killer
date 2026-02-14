import logging
import time

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine, AsyncSession,
    async_sessionmaker, create_async_engine
)
from app.utils import Colors

logger = logging.getLogger(__name__)


class PostgresService:
    __slots__ = ("_engine", "_session_maker")

    def __init__(self) -> None:
        self._engine: AsyncEngine | None = None
        self._session_maker: async_sessionmaker[AsyncSession] | None = None

    async def init_state(
            self, db_url: str, pool_recycle: int,
            pool_size: int, max_overflow: int,
            pool_timeout: int
    ) -> None:

        start = time.perf_counter()
        self._engine = create_async_engine(
            db_url, pool_pre_ping=True, pool_recycle=pool_recycle,
            pool_size=pool_size, max_overflow=max_overflow,
            pool_timeout=pool_timeout
        )
        self._session_maker = async_sessionmaker(
            bind=self._engine, class_=AsyncSession,
            expire_on_commit=False, autoflush=False
        )

        async with self._engine.connect() as conn:
            await conn.execute(text("SELECT 1"))

        if logger.isEnabledFor(logging.DEBUG):
            dur_ms = (time.perf_counter() - start) * 1000
            logger.debug(
                "%s[DB] INIT%s pool=%d+%d: total %s%.2fms%s",
                Colors.PURPLE, Colors.RESET, pool_size, max_overflow,
                Colors.YELLOW, dur_ms, Colors.RESET
            )

    def get_session_maker(self) -> async_sessionmaker[AsyncSession]:
        if self._session_maker is None:
            msg = "PostgresService isn't initialized"
            logger.error(
                "%s[DB ERROR]%s %s",
                Colors.RED, Colors.RESET, msg
            )
            raise RuntimeError(msg)

        return self._session_maker

    async def aclose(self) -> None:
        if self._engine:
            start = time.perf_counter()
            await self._engine.dispose()

            if logger.isEnabledFor(logging.DEBUG):
                dur_ms = (time.perf_counter() - start) * 1000
                logger.debug(
                    "%s[DB] CLOSE%s engine disposed: total %s%.2fms%s",
                    Colors.PURPLE, Colors.RESET,
                    Colors.YELLOW, dur_ms, Colors.RESET
                )

            self._engine, self._session_maker = None, None


pg_service = PostgresService()
