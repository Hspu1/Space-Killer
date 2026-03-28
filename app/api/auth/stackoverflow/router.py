from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response

from app.core.dependencies import get_pg, rate_limiter
from app.infra.postgres.service import PostgresService

from ..common import AuthProvider, login
from .service import stackoverflow_callback_handling

stackoverflow_router = APIRouter(tags=["stackoverflow"], prefix="/auth/stackoverflow")


@stackoverflow_router.get(
    path="/login",
    dependencies=[
        Depends(rate_limiter(limit=1, period=5, burst=5, scope="stackoverflow_login"))
    ],
)
async def stackoverflow_login(request: Request) -> Response:
    return await login(
        request=request,
        provider=AuthProvider.STACKOVERFLOW,
    )


@stackoverflow_router.get(
    path="/callback",
    dependencies=[
        Depends(rate_limiter(limit=1, period=7, burst=3, scope="stackoverflow_callback"))
    ],
)
async def stackoverflow_callback(
    request: Request,
    pg: Annotated[PostgresService, Depends(get_pg)],
) -> Response:

    redirect_uri = str(request.url_for("stackoverflow_callback"))
    return await stackoverflow_callback_handling(
        request=request, redirect_uri=redirect_uri, pg_svc=pg
    )
