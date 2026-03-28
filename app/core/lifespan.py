from asyncio import gather, wait_for
from collections.abc import Awaitable
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.exceptions import SafeStartError
from app.infra.http import HttpService
from app.infra.postgres.service import PostgresService
from app.infra.redis import RedisService
from app.utils.log_helpers import log_error_infra


async def safe_start(service_name: str, coroutine: Awaitable):
    try:
        await wait_for(coroutine, timeout=7.0)
    except Exception as e:
        log_error_infra(service=service_name, op="STARTUP FAILED", exc=e)
        raise SafeStartError from e


async def silent_close(service_name: str, coroutine: Awaitable):
    try:
        await wait_for(coroutine, timeout=7.0)
    except Exception as e:
        log_error_infra(service=service_name, op="SHUTDOWN FAILED", exc=e)


def get_lifespan(pg_svc: PostgresService, redis_svc: RedisService, http_svc: HttpService):
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        results = await gather(
            safe_start(service_name="Postgres", coroutine=pg_svc.connect()),
            safe_start(service_name="Redis", coroutine=redis_svc.connect()),
            safe_start(service_name="HTTP", coroutine=http_svc.connect()),
            return_exceptions=True,
        )
        if errors := [res for res in results if isinstance(res, Exception)]:
            log_error_infra(service="LIFESPAN", op="STARTUP FAILED", exc_tuple=results)
            await silent_close(service_name="HTTP", coroutine=http_svc.disconnect())
            await silent_close(service_name="Redis", coroutine=redis_svc.disconnect())
            await silent_close(service_name="Postgres", coroutine=pg_svc.disconnect())
            raise SafeStartError(error_count=len(errors)) from errors[
                0
            ]  # from any real err

        (
            app.state.pg_svc,
            app.state.redis_svc,
            app.state.http_svc,
        ) = (
            pg_svc,
            redis_svc,
            http_svc,
        )

        yield

        await silent_close(service_name="HTTP", coroutine=http_svc.disconnect())
        await silent_close(service_name="Redis", coroutine=redis_svc.disconnect())
        await silent_close(service_name="Postgres", coroutine=pg_svc.disconnect())

    return lifespan
