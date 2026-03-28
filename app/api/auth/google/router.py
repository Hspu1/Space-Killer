from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response

from app.core.dependencies import get_pg, rate_limiter
from app.infra.postgres.service import PostgresService

from ..common import AuthProvider, login
from .client import google_oauth
from .service import google_callback_handling

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
    request: Request, pg: Annotated[PostgresService, Depends(get_pg)]
) -> Response:

    return await google_callback_handling(request=request, pg_svc=pg)
