from contextlib import asynccontextmanager
from asyncio import gather

from fastapi import FastAPI

from app.infra.postgres.service import PostgresService
from app.infra.redis import RedisService


def get_lifespan(pg: PostgresService, redis: RedisService):
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await gather(pg.connect(), redis.connect())

        app.state.pg_svc, app.state.redis_svc = pg, redis
        try:
            yield

        finally:
            await gather(
                pg.disconnect(), redis.disconnect(),
                return_exceptions=True
            )

    return lifespan
