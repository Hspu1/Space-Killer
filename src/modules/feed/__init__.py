from typing import Final

from fastapi import APIRouter

from .entrypoints import (
    global_feed_router,
)

feed_router = APIRouter()

ROUTERS: Final[tuple[APIRouter, ...]] = (global_feed_router,)

for router in ROUTERS:
    feed_router.include_router(router, tags=["feed"], prefix="/feed")

__all__ = ("feed_router",)
