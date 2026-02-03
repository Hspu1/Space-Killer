from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from app.infra import redis_service


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    redis_service.init_state(host="127.0.0.1", port=6379, db=2)
    yield
    await redis_service.aclose()
