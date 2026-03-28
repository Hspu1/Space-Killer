from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response

from app.core.dependencies import get_http_service, get_pg, rate_limiter
from app.infra.http import HttpService
from app.infra.postgres.service import PostgresService

from ..common import AuthProvider, login
from .service import github_callback_handling

github_router = APIRouter(tags=["github"], prefix="/auth/github")


@github_router.get(
    path="/login",
    dependencies=[
        Depends(rate_limiter(limit=1, period=5, burst=5, scope="github_login"))
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
        Depends(rate_limiter(limit=1, period=7, burst=3, scope="github_callback"))
    ],
)
async def github_callback(
    request: Request,
    pg: Annotated[PostgresService, Depends(get_pg)],
    http_svc: Annotated[HttpService, Depends(get_http_service)],
) -> Response:

    redirect_uri = str(request.url_for("github_callback"))
    return await github_callback_handling(
        request=request, pg_svc=pg, redirect_uri=redirect_uri, http_svc=http_svc
    )
