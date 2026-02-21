from fastapi import Request, HTTPException, status

from app.infra.http import HttpService
from app.infra.postgres.service import PostgresService
from app.infra.redis import RateLimiter


async def get_pg(request: Request) -> PostgresService:
    return request.app.state.pg_svc


async def get_http_service(request: Request) -> HttpService:
    return request.app.state.http_svc


async def get_limiter(request: Request) -> RateLimiter:
    return request.app.state.limiter


def rate_limit(limit: int, window: int, scope: str = "default"):
    async def _check_limit(request: Request) -> None:
        key = "%s:%s" % (scope, request.client.host)
        limiter: RateLimiter = await get_limiter(request=request)

        if not await limiter.is_allowed(key, limit, window):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many attempts. Please try again later."
            )

    return _check_limit
