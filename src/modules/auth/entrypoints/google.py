from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response

from src.core.dependencies import get_pg_manager, rate_limiter
from src.infra.persistence.postgres import PostgresManager

from ..common import AuthProvider, login
from ..third_party_apps.google import google_callback_handler, google_oauth

google_router = APIRouter(tags=["google"], prefix="/auth/google")


@google_router.get(
    path="/login",
    dependencies=[
        Depends(rate_limiter(limit=1, period=5, burst=5, scope="google_login"))
    ],
)
async def google_login(request: Request) -> Response:
    return await login(
        request=request,
        provider=AuthProvider.GOOGLE,
        oauth_app=google_oauth.google,
    )


@google_router.get(
    path="/callback",
    dependencies=[
        Depends(rate_limiter(limit=1, period=7, burst=3, scope="google_callback"))
    ],
)
async def google_callback(
    request: Request, pg_manager: Annotated[PostgresManager, Depends(get_pg_manager)]
) -> Response:

    return await google_callback_handler(request=request, pg_manager=pg_manager)
