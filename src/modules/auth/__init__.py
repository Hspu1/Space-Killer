from typing import Final

from fastapi import APIRouter

from .common import logout_router
from .entrypoints import (
    github_router,
    google_router,
    stackoverflow_router,
    telegram_router,
    yandex_router,
)

auth_router = APIRouter()

ROUTERS: Final[list[APIRouter]] = [
    github_router,
    google_router,
    telegram_router,
    yandex_router,
    stackoverflow_router,
    logout_router,
]

for router in ROUTERS:
    auth_router.include_router(router)

__all__ = ("auth_router",)
