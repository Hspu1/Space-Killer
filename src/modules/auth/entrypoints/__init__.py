from .github import github_router
from .google import google_router
from .stackoverflow import stackoverflow_router
from .telegram import telegram_router
from .yandex import yandex_router

__all__ = (
    "github_router",
    "google_router",
    "stackoverflow_router",
    "telegram_router",
    "yandex_router",
)
