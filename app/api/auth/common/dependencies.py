from fastapi import Request

from app.infra.postgres.service import PostgresService
from app.infra.redis import RedisService


async def get_pg(request: Request) -> PostgresService:
    return request.app.state.pg_svc


async def get_redis(request: Request) -> RedisService:
    return request.app.state.redis_svc
