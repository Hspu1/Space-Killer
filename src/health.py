from asyncio import gather, wait_for

from fastapi import APIRouter, HTTPException
from starlette.status import HTTP_200_OK, HTTP_503_SERVICE_UNAVAILABLE

from .infra.persistence.postgres import PostgresManager
from .infra.redis import RedisManager

health_router = APIRouter(prefix="/health", tags=["System"])


@health_router.get("/readiness", status_code=HTTP_200_OK)
async def readiness() -> dict[str, str]:
    try:
        await wait_for(gather(PostgresManager.ping(), RedisManager.ping()), timeout=4)
        return {"status": "infra is reachable"}

    except Exception as e:
        raise HTTPException(
            status_code=HTTP_503_SERVICE_UNAVAILABLE,
            detail="Infra is not reachable",
        ) from e
