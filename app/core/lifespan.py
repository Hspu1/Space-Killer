from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from app.core.env_conf import redis_stg
from app.infra.redis import RedisService


def get_lifespan(redis_service: RedisService):
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        await redis_service.init_state(
            host=redis_stg.host, port=redis_stg.port, db=redis_stg.db
        )
        yield
        await redis_service.aclose()

    return lifespan
