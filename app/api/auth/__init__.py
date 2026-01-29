__all__ = (
    "github_oauth2_router",
    "google_oauth2_router",
    "telegram_auth_router",
    "auth_logout_router"
)

from .github import github_oauth2_router
from .google import google_oauth2_router
from .telegram import telegram_auth_router
from .auth_logout import auth_logout_router
