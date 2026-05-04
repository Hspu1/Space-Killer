from asyncio import gather, wait_for
from collections.abc import Awaitable
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI

from src.core.exceptions import SafeStartError
from src.infra.auth_http_client import AuthHttpClient
from src.infra.nats.core_manager import CoreNATSManager
from src.infra.persistence.postgres import PostgresManager
from src.infra.redis import RedisManager
from src.infra.centrifugo import CentrifugoManager
from src.modules.geo.satellite_manager import SatelliteManager
from src.utils.log_helpers import log_error_infra


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
    centrifugo_manager: CentrifugoManager,
    auth_http_client: AuthHttpClient,
):
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        results = await gather(
            safe_start(service_name="Postgres", coroutine=pg_manager.connect()),
            safe_start(service_name="Redis", coroutine=redis_manager.connect()),
            safe_start(service_name="NATS (Core)", coroutine=core_nats_manager.connect()),
            safe_start(service_name="Centrifugo (gRPC)", coroutine=centrifugo_manager.connect()),
            safe_start(service_name="HTTP", coroutine=auth_http_client.connect()),
            return_exceptions=True,
        )

        if errors := [res for res in results if isinstance(res, Exception)]:
            log_error_infra(service="LIFESPAN", op="STARTUP FAILED", exc_tuple=results)
            await silent_close(
                service_name="HTTP", coroutine=auth_http_client.disconnect()
            )
            await silent_close(service_name="Centrifugo", coroutine=centrifugo_manager.disconnect())
            await silent_close(
                service_name="NATS (Core)", coroutine=core_nats_manager.disconnect()
            )
            await silent_close(service_name="Redis", coroutine=redis_manager.disconnect())
            await silent_close(service_name="Postgres", coroutine=pg_manager.disconnect())
            raise SafeStartError(error_count=len(errors)) from errors[
                0
            ]  # from any real err

        (
            app.state.pg_manager,
            app.state.redis_manager,
            app.state.core_nats_manager,
            app.state.centrifugo_manager,
            app.state.auth_http_client,
        ) = (
            pg_manager,
            redis_manager,
            core_nats_manager,
            centrifugo_manager,
            auth_http_client,
        )

        sat_manager = SatelliteManager(
            centrifugo=centrifugo_manager
        )
        scheduler = AsyncIOScheduler()

        app.state.sat_manager = sat_manager

        await sat_manager.start(scheduler)
        scheduler.start()

        try:
            yield
        finally:
            scheduler.shutdown(wait=False)
            await sat_manager.stop()

            await silent_close(
                service_name="HTTP", coroutine=auth_http_client.disconnect()
            )
            await silent_close(service_name="Centrifugo", coroutine=centrifugo_manager.disconnect())
            await silent_close(
                service_name="NATS (Core)", coroutine=core_nats_manager.disconnect()
            )
            await silent_close(service_name="Redis", coroutine=redis_manager.disconnect())
            await silent_close(service_name="Postgres", coroutine=pg_manager.disconnect())

    return lifespan
