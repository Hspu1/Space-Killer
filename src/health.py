from asyncio import gather, wait_for

from fastapi import APIRouter, HTTPException
from starlette.status import HTTP_200_OK, HTTP_503_SERVICE_UNAVAILABLE

from .infra.persistence.postgres import PostgresManager
from .infra.redis import RedisManager

health_router = APIRouter(prefix="/health", tags=["System"])


@health_router.get("/readiness", status_code=HTTP_200_OK)
async def readiness() -> dict[str, str]:
    try:
        print("Checking Postgres...", flush=True)
        await PostgresManager.ping()
        print("Postgres OK. Checking Redis...", flush=True)
        await RedisManager.ping()
        print("All OK", flush=True)
        return {"status": "infra is reachable"}
    except Exception as e:
        print(f"HEALTHCHECK CRASHED: {type(e).__name__} - {e}", flush=True)
        raise HTTPException(
            status_code=HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Error: {e}",
        )
