from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response

from src.core.dependencies import get_pg_manager, rate_limiter
from src.infra.persistence.postgres import PostgresManager

from ..common import AuthProvider, login
from ..third_party_apps.stackoverflow import stackoverflow_callback_handler

stackoverflow_router = APIRouter(tags=["stackoverflow"], prefix="/auth/stackoverflow")


@stackoverflow_router.get(
    path="/login",
    dependencies=[
        Depends(rate_limiter(limit=5, period=60, burst=5, scope="stackoverflow_login"))
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
        Depends(rate_limiter(limit=3, period=60, burst=5, scope="stackoverflow_callback"))
    ],
)
async def stackoverflow_callback(
    request: Request,
    pg_manager: Annotated[PostgresManager, Depends(get_pg_manager)],
) -> Response:

    host = request.headers.get("x-forwarded-host") or request.headers.get("host")
    redirect_uri = f"https://{host}/auth/stackoverflow/callback"
    return await stackoverflow_callback_handler(
        request=request, redirect_uri=redirect_uri, pg_manager=pg_manager
    )
