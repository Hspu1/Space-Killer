from asyncio import gather, wait_for

from fastapi import APIRouter, HTTPException
from starlette.status import HTTP_200_OK, HTTP_503_SERVICE_UNAVAILABLE

from .core.dependencies import (
    get_auth_http_client,
    get_core_nats_manager,
    get_pg_manager,
    get_redis_manager,
)

health_router = APIRouter(prefix="/health", tags=["System"])


@health_router.get("/readiness", status_code=HTTP_200_OK)
async def readiness():
    pg = await get_pg_manager()
    redis = await get_redis_manager()
    nats_core = await get_core_nats_manager()
    auth = await get_auth_http_client()

    try:
        await wait_for(
            gather(
                pg.ping(),
                redis.ping(),
                nats_core.ping(),
                auth.ping(),
            ),
            timeout=5.0,
        )
        print("app resources HEALTHY", flush=True)

    except Exception as e:
        print(f"app resources FUCKED: {type(e).__name__} - {e}", flush=True)
        raise HTTPException(
            status_code=HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Error: {e}",
        ) from e
