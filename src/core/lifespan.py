from asyncio import gather, wait_for
from collections.abc import Awaitable
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.core.exceptions import SafeStartError
from src.infra.auth_http_client import AuthHttpClient
from src.infra.nats.manager import NATSManager
from src.infra.persistence.postgres import PostgresManager
from src.infra.redis import RedisManager
from src.utils.log_helpers import log_error_infra


async def safe_start(service_name: str, coroutine: Awaitable) -> None:
    try:
        await wait_for(coroutine, timeout=15.0)
    except Exception as e:
        log_error_infra(service=service_name, op="STARTUP FAILED", exc=e)
        raise SafeStartError from e


async def silent_close(service_name: str, coroutine: Awaitable) -> None:
    try:
        await wait_for(coroutine, timeout=15.0)
    except Exception as e:
        log_error_infra(service=service_name, op="SHUTDOWN FAILED", exc=e)


def get_lifespan(
    pg_manager: PostgresManager,
    redis_manager: RedisManager,
    nats_manager: NATSManager,
    auth_http_client: AuthHttpClient,
):
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        results = await gather(
            safe_start(service_name="Postgres", coroutine=pg_manager.connect()),
            safe_start(service_name="Redis", coroutine=redis_manager.connect()),
            safe_start(service_name="NATS", coroutine=nats_manager.connect()),
            safe_start(service_name="HTTP", coroutine=auth_http_client.connect()),
            return_exceptions=True,
        )
        if errors := [res for res in results if isinstance(res, Exception)]:
            log_error_infra(service="LIFESPAN", op="STARTUP FAILED", exc_tuple=results)
            await silent_close(
                service_name="HTTP", coroutine=auth_http_client.disconnect()
            )
            await silent_close(service_name="NATS", coroutine=nats_manager.disconnect())
            await silent_close(service_name="Redis", coroutine=redis_manager.disconnect())
            await silent_close(service_name="Postgres", coroutine=pg_manager.disconnect())
            raise SafeStartError(error_count=len(errors)) from errors[
                0
            ]  # from any real err

        (
            app.state.pg_manager,
            app.state.redis_manager,
            app.state.nats_manager,
            app.state.auth_http_client,
        ) = (
            pg_manager,
            redis_manager,
            nats_manager,
            auth_http_client,
        )

        yield

        await silent_close(service_name="HTTP", coroutine=auth_http_client.disconnect())
        await silent_close(service_name="NATS", coroutine=nats_manager.disconnect())
        await silent_close(service_name="Redis", coroutine=redis_manager.disconnect())
        await silent_close(service_name="Postgres", coroutine=pg_manager.disconnect())

    return lifespan
