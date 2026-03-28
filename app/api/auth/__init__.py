from typing import Final

from fastapi import APIRouter

from .common import logout_router
from .github import github_router
from .google import google_router
from .stackoverflow import stackoverflow_router
from .telegram import telegram_router
from .yandex import yandex_router

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
