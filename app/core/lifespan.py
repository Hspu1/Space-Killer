from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from app.core.env_conf import redis_stg, pg_stg
from app.infra.postgres.service import PostgresService
from app.infra.redis import RedisService


def get_lifespan(redis_service: RedisService, pg_service: PostgresService):
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        await redis_service.init_state(
            host=redis_stg.host, port=redis_stg.port, db=redis_stg.db,
            max_connections=redis_stg.max_connections,
            socket_connect_timeout=redis_stg.socket_connect_timeout
        )
        await pg_service.init_state(
            db_url=pg_stg.db_url, pool_recycle=pg_stg.pool_recycle,
            pool_size=pg_stg.pool_size, max_overflow=pg_stg.max_overflow,
            pool_timeout=pg_stg.pool_timeout
        )

        yield
        await redis_service.aclose()
        await pg_service.aclose()

    return lifespan
