from asyncio import gather, wait_for
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from starlette.status import HTTP_200_OK, HTTP_503_SERVICE_UNAVAILABLE

from src.infra.auth_http_client import AuthHttpClient
from src.infra.nats.core_manager import CoreNATSManager
from src.infra.persistence.postgres import PostgresManager
from src.infra.redis import RedisManager
from src.infra.scylla.manager import ScyllaManager
from src.infra.seaweed import SeaweedManager

from .core.dependencies import (
    get_auth_http_client,
    get_core_nats_manager,
    get_pg_manager,
    get_redis_manager,
    get_scylla_manager,
    get_seaweed_manager,
)
from .utils.log_helpers import log_healthz

healthz_router = APIRouter(prefix="/healthz", tags=["System"])


@healthz_router.get("/readiness", status_code=HTTP_200_OK)
async def readiness(  # noqa: PLR0913
    pg: Annotated[PostgresManager, Depends(get_pg_manager)],
    redis: Annotated[RedisManager, Depends(get_redis_manager)],
    nats_core: Annotated[CoreNATSManager, Depends(get_core_nats_manager)],
    scylla: Annotated[ScyllaManager, Depends(get_scylla_manager)],
    seaweed: Annotated[SeaweedManager, Depends(get_seaweed_manager)],
    auth: Annotated[AuthHttpClient, Depends(get_auth_http_client)],
):

    try:
        results = await wait_for(
            gather(
                pg.ping(),
                redis.ping(),
                nats_core.ping(),
                scylla.ping(),
                seaweed.ping(),
                auth.ping(),
                return_exceptions=True,
            ),
            timeout=5.0,
        )
        if errors := [res for res in results if isinstance(res, Exception)]:
            raise ExceptionGroup(
                f"Readiness healthz failed with {len(errors)} errors",  # noqa: EM102
                errors,
            )

        log_healthz(success=True)

    except Exception as e:
        log_healthz(success=False, e=e)
        raise HTTPException(
            status_code=HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Error: {e}",
        ) from e
