from fastapi import APIRouter

__all__ = "auth_router"

from .github import github_router
from .google import google_router
from .telegram import telegram_router
from .yandex import yandex_router
from .stackoverflow import stackoverflow_router
from .common import logout_router

auth_router = APIRouter()

for router in (
        github_router, google_router, telegram_router,
        yandex_router, stackoverflow_router, logout_router
):
    auth_router.include_router(router)
