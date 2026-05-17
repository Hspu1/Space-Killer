from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response

from src.core.dependencies import get_auth_http_client, get_pg_manager, rate_limiter
from src.infra.auth_http_client import AuthHttpClient
from src.infra.persistence.postgres import PostgresManager

from ..common import AuthProvider, login
from ..third_party_apps.github import github_callback_handler

github_router = APIRouter(tags=["github"], prefix="/auth/github")


@github_router.get(
    path="/login",
    dependencies=[
        Depends(rate_limiter(limit=5, period=60, burst=5, scope="github_login"))
    ],
)
async def github_login(request: Request) -> Response:
    return await login(
        request=request,
        provider=AuthProvider.GITHUB,
    )


@github_router.get(
    path="/callback",
    dependencies=[
        Depends(rate_limiter(limit=3, period=60, burst=5, scope="github_callback"))
    ],
)
async def github_callback(
    request: Request,
    pg_manager: Annotated[PostgresManager, Depends(get_pg_manager)],
    auth_http_client: Annotated[AuthHttpClient, Depends(get_auth_http_client)],
) -> Response:

    host = request.headers.get("x-forwarded-host") or request.headers.get("host")
    redirect_uri = f"https://{host}/auth/github/callback"
    return await github_callback_handler(
        request=request,
        pg_manager=pg_manager,
        redirect_uri=redirect_uri,
        auth_http_client=auth_http_client,
    )
