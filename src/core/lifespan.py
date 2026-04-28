from asyncio import gather, wait_for, create_task
from collections.abc import Awaitable
from contextlib import asynccontextmanager, suppress
from datetime import UTC, datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI

from src.core.exceptions import SafeStartError
from src.infra.auth_http_client import AuthHttpClient
from src.infra.nats.core_manager import CoreNATSManager
from src.infra.persistence.postgres import PostgresManager
from src.infra.redis import RedisManager
from src.utils.log_helpers import log_error_infra
from src.modules.geo.coords import ISSData, update_tle


async def safe_start(service_name: str, coroutine: Awaitable) -> None:
    try:
        await wait_for(coroutine, timeout=5.0)
    except Exception as e:
        log_error_infra(service=service_name, op="STARTUP FAILED", exc=e)
        raise SafeStartError from e


async def silent_close(service_name: str, coroutine: Awaitable) -> None:
    try:
        await wait_for(coroutine, timeout=5.0)
    except Exception as e:
        log_error_infra(service=service_name, op="SHUTDOWN FAILED", exc=e)


def get_lifespan(
    pg_manager: PostgresManager,
    redis_manager: RedisManager,
    core_nats_manager: CoreNATSManager,
    auth_http_client: AuthHttpClient,
):
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        results = await gather(
            safe_start(service_name="Postgres", coroutine=pg_manager.connect()),
            safe_start(service_name="Redis", coroutine=redis_manager.connect()),
            safe_start(service_name="NATS (Core)", coroutine=core_nats_manager.connect()),
            safe_start(service_name="HTTP", coroutine=auth_http_client.connect()),
            return_exceptions=True,
        )

        if errors := [res for res in results if isinstance(res, Exception)]:
            log_error_infra(service="LIFESPAN", op="STARTUP FAILED", exc_tuple=results)
            await silent_close(
                service_name="HTTP", coroutine=auth_http_client.disconnect()
            )
            await silent_close(service_name="NATS (Core)", coroutine=core_nats_manager.disconnect())
            await silent_close(service_name="Redis", coroutine=redis_manager.disconnect())
            await silent_close(service_name="Postgres", coroutine=pg_manager.disconnect())
            raise SafeStartError(error_count=len(errors)) from errors[
                0
            ]  # from any real err

        (
            app.state.pg_manager,
            app.state.redis_manager,
            app.state.core_nats_manager,
            app.state.auth_http_client,
        ) = (
            pg_manager,
            redis_manager,
            core_nats_manager,
            auth_http_client,
        )

        iss = ISSData(nats=core_nats_manager)
        app.state.iss = iss

        iss_task = create_task(iss.broadcast())
        scheduler = AsyncIOScheduler()
        scheduler.add_job(
            update_tle,
            "interval",
            args=[iss],
            hours=1,
            next_run_time=datetime.now(UTC),
        )
        scheduler.start()

        try:
            yield
        finally:
            iss_task.cancel()
            with suppress(asyncio.CancelledError):
                await iss_task
            scheduler.shutdown(wait=False)

            await silent_close(service_name="HTTP", coroutine=auth_http_client.disconnect())
            await silent_close(service_name="NATS (Core)", coroutine=core_nats_manager.disconnect())
            await silent_close(service_name="Redis", coroutine=redis_manager.disconnect())
            await silent_close(service_name="Postgres", coroutine=pg_manager.disconnect())

    return lifespan
