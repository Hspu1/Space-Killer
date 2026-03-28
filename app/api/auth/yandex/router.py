from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response

from app.core.dependencies import get_pg, rate_limiter
from app.infra.postgres.service import PostgresService

from ..common import AuthProvider, login
from .client import yandex_oauth
from .service import yandex_callback_handling

yandex_router = APIRouter(tags=["yandex"], prefix="/auth/yandex")


@yandex_router.get(
    path="/login",
    dependencies=[
        Depends(rate_limiter(limit=1, period=5, burst=5, scope="yandex_login"))
    ],
)
async def yandex_login(request: Request) -> Response:
    return await login(
        request=request,
        provider=AuthProvider.YANDEX,
        oauth_app=yandex_oauth.yandex,
    )


@yandex_router.get(
    path="/callback",
    dependencies=[
        Depends(rate_limiter(limit=1, period=7, burst=3, scope="yandex_callback"))
    ],
)
async def yandex_callback(
    request: Request,
    pg: Annotated[PostgresService, Depends(get_pg)],
) -> Response:

    return await yandex_callback_handling(request=request, pg_svc=pg)
