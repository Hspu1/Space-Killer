from fastapi import APIRouter, Request, Response, Depends

from app.infra.dependencies import get_pg
from app.infra.postgres.service import PostgresService
from .client import github_oauth
from .service import github_callback_handling
from ..common import login, AuthProvider

github_router = APIRouter(tags=["github"], prefix="/auth/github")


@github_router.get('/login')
async def github_login(request: Request) -> Response:
    return await login(
        request=request,
        provider_name=AuthProvider.GITHUB,
        provider=github_oauth.github
    )


@github_router.get(path="/callback")
async def github_callback(
        request: Request, pg: PostgresService = Depends(get_pg)
) -> Response:
    return await github_callback_handling(request=request, pg_svc=pg)
