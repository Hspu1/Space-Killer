from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from app.core.env_conf import stg
from app.infra.redis import RedisService


def get_lifespan(redis_service: RedisService):
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        await redis_service.init_state(host=stg.host, port=stg.port, db=stg.db)
        yield
        await redis_service.aclose()

    return lifespan
