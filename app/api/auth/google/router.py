from fastapi import APIRouter, Request, Response, Depends

from app.infra.dependencies import get_pg
from app.infra.postgres.service import PostgresService
from .client import google_oauth
from .service import google_callback_handling
from ..common import login, AuthProvider

google_router = APIRouter(tags=["google"], prefix="/auth/google")


@google_router.get("/login")
async def google_login(request: Request) -> Response:
    return await login(
        request=request,
        provider_name=AuthProvider.GOOGLE,
        provider=google_oauth.google
    )


@google_router.get(path="/callback")
async def google_callback(
        request: Request, pg: PostgresService = Depends(get_pg)
) -> Response:
    return await google_callback_handling(request=request, pg_svc=pg)
