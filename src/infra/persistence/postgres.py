from asyncio import wait_for
from time import perf_counter
from typing import Any

from orjson import (
    OPT_NON_STR_KEYS,
    OPT_SERIALIZE_UUID,
    dumps,
    loads,
)
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.core.env_conf import PostgresSettings
from src.core.exceptions import PostgresNotReachableError
from src.utils import log_debug_db


def orjson_dumps(data: Any) -> bytes:
    return dumps(data, option=OPT_SERIALIZE_UUID | OPT_NON_STR_KEYS)


def orjson_loads(data: str | bytes) -> Any:
    return loads(data)


class PostgresManager:
    def __init__(self, config: PostgresSettings) -> None:
        self._config = config
        self._engine: AsyncEngine | None = None
        self._session_maker: async_sessionmaker[AsyncSession] | None = None

    async def connect(self) -> None:
        if self._engine and self._session_maker:
            return

        try:
            start = perf_counter()
            self._engine = create_async_engine(
                url=self._config.db_url,
                json_serializer=orjson_dumps,
                json_deserializer=orjson_loads,
                pool_pre_ping=True,
                pool_recycle=self._config.pool_recycle,
                pool_size=self._config.pool_size,
                max_overflow=self._config.max_overflow,
                pool_timeout=self._config.pool_timeout,
            )
            self._session_maker = async_sessionmaker(
                bind=self._engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=False,
            )
            await wait_for(self.ping(), 3.0)

            log_debug_db(
                op="CONNECTED",
                start_time=start,
                detail=f"pool={self._config.pool_size}+{self._config.max_overflow}",
            )

        except (SQLAlchemyError, TimeoutError, Exception) as e:
            await self.disconnect()
            raise PostgresNotReachableError from e

    async def ping(self) -> None:
        if not self._engine:
            raise PostgresNotReachableError

        async with self._session_maker() as session:
            await session.execute(text("SELECT 1"))

    def get_session_maker(self) -> async_sessionmaker[AsyncSession]:
        if not self._session_maker:
            raise PostgresNotReachableError

        return self._session_maker

    async def disconnect(self) -> None:
        if not self._engine:
            self._engine, self._session_maker = None, None
            return

        start = perf_counter()
        try:
            await self._engine.dispose()
            log_debug_db(op="DISCONNECTED", start_time=start)

        finally:
            self._engine, self._session_maker = None, None
