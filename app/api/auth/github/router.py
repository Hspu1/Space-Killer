from fastapi import APIRouter, Request, Response, Depends

from app.infra.dependencies import get_pg, rate_limit, get_http_service
from app.infra.http import HttpService
from app.infra.postgres.service import PostgresService
from .client import github_oauth
from .service import github_callback_handling
from ..common import login, AuthProvider

github_router = APIRouter(tags=["github"], prefix="/auth/github")


@github_router.get(path='/login',
    dependencies=[Depends(rate_limit(
        limit=1, window=1, burst=3, scope="github_login")
    )]
)
async def github_login(request: Request) -> Response:
    return await login(
        request=request, provider_name=AuthProvider.GITHUB,
        provider=github_oauth.github
    )


@github_router.get(path="/callback",
    dependencies=[Depends(rate_limit(
        limit=1, window=2, scope="github_callback")
    )]
)
async def github_callback(
        request: Request, pg: PostgresService = Depends(get_pg),
        http_svc: HttpService = Depends(get_http_service)
) -> Response:
    redirect_uri = str(request.url_for("github_callback"))
    return await github_callback_handling(
        request=request, pg_svc=pg, redirect_uri=redirect_uri, http_svc=http_svc
    )
