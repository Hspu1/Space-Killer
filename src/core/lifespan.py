from asyncio import gather
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.core.exceptions import SafeStartError
from src.infra.auth_http_client import AuthHttpClient
from src.infra.nats.core_manager import CoreNATSManager
from src.infra.persistence.postgres import PostgresManager
from src.infra.redis import RedisManager
from src.utils.log_helpers import log_error_infra

from .lifespan_helpers import safe_start, silent_close


def get_lifespan(
    pg_manager: PostgresManager,
    redis_manager: RedisManager,
    core_nats_manager: CoreNATSManager,
    auth_http_client: AuthHttpClient,
):
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        results = await gather(
            safe_start(
                service_name="Postgres", coroutine=pg_manager.connect(), atimeout=10.0
            ),
            safe_start(
                service_name="Redis", coroutine=redis_manager.connect(), atimeout=10.0
            ),
            safe_start(
                service_name="NATS (Core)",
                coroutine=core_nats_manager.connect(),
                atimeout=10.0,
            ),
            safe_start(
                service_name="HTTP", coroutine=auth_http_client.connect(), atimeout=10.0
            ),
            return_exceptions=True,
        )

        if errors := [res for res in results if isinstance(res, Exception)]:
            log_error_infra(service="LIFESPAN", op="STARTUP FAILED", exc_tuple=results)
            await silent_close(
                service_name="HTTP", coroutine=auth_http_client.disconnect()
            )
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
            app.state.auth_http_client,
        ) = (
            pg_manager,
            redis_manager,
            core_nats_manager,
            auth_http_client,
        )

        try:
            yield
        finally:
            await silent_close(
                service_name="HTTP", coroutine=auth_http_client.disconnect()
            )
            await silent_close(
                service_name="NATS (Core)", coroutine=core_nats_manager.disconnect()
            )
            await silent_close(service_name="Redis", coroutine=redis_manager.disconnect())
            await silent_close(service_name="Postgres", coroutine=pg_manager.disconnect())

    return lifespan
