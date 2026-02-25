from contextlib import asynccontextmanager
from asyncio import gather, wait_for
from typing import Awaitable

from fastapi import FastAPI

from app.infra.postgres.service import PostgresService
from app.infra.redis import RedisService, RateLimiter
from app.infra.http import HttpService
from app.utils.log_helpers import log_error_infra


async def safe_start(service_name: str, coroutine: Awaitable):
    try:
        await wait_for(coroutine, timeout=5.0)
    except Exception as e:
        log_error_infra(service=service_name, op="STARTUP FAILED", exc=e)
        raise RuntimeError("Application failed to start -> infrastructure is down") from e


async def silent_close(service_name: str, coroutine: Awaitable):
    try:
        await wait_for(coroutine, timeout=5.0)
    except Exception as e:
        log_error_infra(service=service_name, op="SHUTDOWN FAILED", exc=e)


def get_lifespan(
        pg_svc: PostgresService, redis_svc: RedisService,
        http_svc: HttpService
):
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        results = await gather(
            safe_start(service_name="Postgres", coroutine=pg_svc.connect()),
            safe_start(service_name="Redis", coroutine=redis_svc.connect()),
            safe_start(service_name="HTTP", coroutine=http_svc.connect()),
            return_exceptions=True
        )
        if errors := [res for res in results if isinstance(res, Exception)]:
            log_error_infra(service="LIFESPAN", op="STARTUP FAILED", exc_tuple=results)
            await gather(
                silent_close(service_name="Postgres", coroutine=pg_svc.disconnect()),
                silent_close(service_name="Redis", coroutine=redis_svc.disconnect()),
                silent_close(service_name="HTTP", coroutine=http_svc.disconnect()),
                return_exceptions=True
            )
            raise RuntimeError(f"Startup failed with {len(errors)} errors")

        limiter = RateLimiter(redis_svc=redis_svc)
        await limiter.init()

        (app.state.pg_svc, app.state.redis_svc,
         app.state.limiter, app.state.http_svc) = (
            pg_svc, redis_svc, limiter, http_svc
        )

        yield

        await gather(
            silent_close(service_name="Postgres", coroutine=pg_svc.disconnect()),
            silent_close(service_name="Redis", coroutine=redis_svc.disconnect()),
            silent_close(service_name="HTTP", coroutine=http_svc.disconnect()),
            return_exceptions=True
        )

    return lifespan
