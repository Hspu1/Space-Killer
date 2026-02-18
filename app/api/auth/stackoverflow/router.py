from fastapi import APIRouter, Request, Response, Depends

from app.infra.dependencies import get_pg
from app.infra.postgres.service import PostgresService
from .client import stackoverflow_oauth
from .service import stackoverflow_callback_handling
from ..common import login, AuthProvider

stackoverflow_router = APIRouter(tags=["stackoverflow"], prefix="/auth/stackoverflow")


@stackoverflow_router.get('/login')
async def stackoverflow_login(request: Request) -> Response:
    return await login(
        request=request,
        provider_name=AuthProvider.STACKOVERFLOW,
        provider=stackoverflow_oauth.stackoverflow
    )


@stackoverflow_router.get('/callback')
async def stackoverflow_callback(
        request: Request, pg: PostgresService = Depends(get_pg)
) -> Response:

    redirect_uri = str(request.url_for("stackoverflow_callback"))
    return await stackoverflow_callback_handling(
        request=request, redirect_uri=redirect_uri, pg_svc=pg
    )
