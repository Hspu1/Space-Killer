from typing import Final

from fastapi import APIRouter

from .feed import feed_router

ROUTERS: Final[tuple[APIRouter, ...]] = (feed_router,)

api_router = APIRouter()

for router in ROUTERS:
    api_router.include_router(router, prefix="/api")

__all__ = ("api_router",)
