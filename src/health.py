from asyncio import gather, wait_for

from fastapi import APIRouter, HTTPException
from starlette.status import HTTP_200_OK, HTTP_503_SERVICE_UNAVAILABLE

from src.core.env_conf import auth_stg, pg_stg, redis_stg, server_stg
from src.infra.auth_http_client import AuthHttpClient
from src.infra.persistence.postgres import PostgresManager
from src.infra.redis import RedisManager

health_router = APIRouter(prefix="/health", tags=["System"])


@health_router.get("/readiness", status_code=HTTP_200_OK)
async def readiness():
    # Duh
    try:
        await wait_for(
            gather(
                PostgresManager(config=pg_stg).connect(), 
                RedisManager(config=redis_stg).connect(),
                AuthHttpClient(auth_stg=auth_stg, server_stg=server_stg).connect()
                ), 
            timeout=4.0
        )
        print("NICE", flush=True)

    except Exception as e:
        print(f"FUCK: {type(e).__name__} - {e}", flush=True)
        raise HTTPException(
            status_code=HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Error: {e}",
        )
    
    finally:
        await wait_for(
            gather(
                PostgresManager(config=pg_stg).disconnect(), 
                RedisManager(config=redis_stg).disconnect(),
                AuthHttpClient(auth_stg=auth_stg, server_stg=server_stg).disconnect(),
                return_exceptions=True
                ),
            timeout=4.0
        )
