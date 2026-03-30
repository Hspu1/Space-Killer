from datetime import timedelta
from time import perf_counter

from fastapi import HTTPException, Request
from throttled.asyncio.rate_limiter.gcra import GCRARateLimiter
from throttled.asyncio.store.redis import RedisStore
from throttled.rate_limiter.base import per_duration

from src.infra.auth_http_client import AuthHttpClient
from src.infra.persistence.postgres import PostgresManager
from src.utils import log_error_infra
from src.utils.log_helpers import log_debug_redis


async def get_pg_manager(request: Request) -> PostgresManager:
    return request.app.state.pg_manager


async def get_auth_http_client(request: Request) -> AuthHttpClient:
    return request.app.state.auth_http_client


async def get_rate_limiter(request: Request) -> RedisStore:
    return request.app.state.redis_manager.get_rate_limiter()


def get_client_ip(request: Request) -> str:
    if real_ip := request.headers.get(
        "X-Real-IP"
    ):  # !!! DO NOT FORGET TO CUSTOMIZE NGINX !!!
        return real_ip

    return request.client.host if request.client else "127.0.0.1"


def rate_limiter(
    limit: int, period: int, scope: str = "default", burst: int | None = None
):
    quota = per_duration(
        duration=timedelta(seconds=period), limit=limit, burst=burst or limit
    )

    async def _check_limit(request: Request) -> None:
        user_id = get_client_ip(request)
        store = await get_rate_limiter(request=request)

        start = perf_counter()
        gcra_rl = GCRARateLimiter(quota=quota, store=store)

        result = await gcra_rl.limit(key=f"{scope}:{user_id}")
        log_debug_redis(
            op="GCRA-RL CHECK",
            start_time=start,
            detail=f"""scope={scope} ip={user_id} limited={result.limited}
            retry_after={round(result.state.retry_after, 3)}""",
        )

        if result.limited:
            log_error_infra(
                service="REDIS GCRA-RL",
                op="EXCEEDED",
                exc=(
                    f"User {user_id} hit limit on {scope}. "
                    f"Retry after: {int(result.state.retry_after)}s"
                ),
            )
            raise HTTPException(
                status_code=429,
                headers={"Retry-After": str(int(result.state.retry_after))},
            )

    return _check_limit
