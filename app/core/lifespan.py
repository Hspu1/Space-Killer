from contextlib import asynccontextmanager
from asyncio import gather
from time import perf_counter
from typing import Awaitable

from fastapi import FastAPI

from app.infra.postgres.service import PostgresService
from app.infra.redis import RedisService
from app.utils import log_debug_db
from app.utils.log_helpers import log_error_infra


async def safe_close(service_name: str, coroutine: Awaitable):
    try:
        await coroutine
    except Exception as e:
        log_error_infra(service=service_name, op="SHUTDOWN_ERROR", exc=e)


def get_lifespan(pg: PostgresService, redis: RedisService):
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await gather(pg.connect(), redis.connect())
        warmup_size, start_warm = 15, perf_counter()

        try:
            await gather(*(pg.ping() for _ in range(warmup_size)))
            log_debug_db(
                op="WARMUP", start_time=start_warm,
                detail=f"conns: {warmup_size}"
            )

        except Exception as e:
            log_error_infra(service="DB", op="WARMUP_FAILED", exc=e)

        app.state.pg_svc, app.state.redis_svc = pg, redis
        try:
            yield

        finally:
            await gather(
                safe_close(service_name="Postgres", coroutine=pg.disconnect()),
                safe_close(service_name="Redis", coroutine=redis.disconnect())
            )

    return lifespan
