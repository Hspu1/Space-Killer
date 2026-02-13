from sqlalchemy.ext.asyncio import (
    AsyncEngine, AsyncSession,
    async_sessionmaker, create_async_engine
)
from sqlalchemy import text


class PostgresService:
    def __init__(self) -> None:
        self._engine: AsyncEngine | None = None
        self._session_maker: async_sessionmaker[AsyncSession] | None = None

    async def init_state(
            self, db_url: str, pool_recycle: int,
            pool_size: int, max_overflow: int,
            pool_timeout: int
    ) -> None:

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

    def get_session_maker(self) -> async_sessionmaker[AsyncSession]:
        if self._session_maker is None:
            raise RuntimeError("PostgresService isn't initialized")
        return self._session_maker

    async def aclose(self) -> None:
        if self._engine:
            await self._engine.dispose()
            self._engine, self._session_maker = None, None


pg_service = PostgresService()
