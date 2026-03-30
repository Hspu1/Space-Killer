from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response

from src.core.dependencies import get_pg_manager, rate_limiter
from src.infra.persistence.postgres import PostgresManager

from ..common import AuthProvider, login
from ..third_party_apps.yandex import yandex_callback_handler, yandex_oauth

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
    pg_manager: Annotated[PostgresManager, Depends(get_pg_manager)],
) -> Response:

    return await yandex_callback_handler(request=request, pg_manager=pg_manager)
