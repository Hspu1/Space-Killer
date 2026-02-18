from fastapi import APIRouter, Request, Response, Depends

from app.infra.dependencies import get_pg
from app.infra.postgres.service import PostgresService
from .client import yandex_oauth
from .service import yandex_callback_handling
from ..common import login, AuthProvider

yandex_router = APIRouter(tags=["yandex"], prefix="/auth/yandex")


@yandex_router.get('/login')
async def yandex_login(request: Request) -> Response:
    return await login(
        request=request,
        provider_name=AuthProvider.YANDEX,
        provider=yandex_oauth.yandex
    )


@yandex_router.get(path="/callback")
async def yandex_callback(
        request: Request, pg: PostgresService = Depends(get_pg)
) -> Response:
    return await yandex_callback_handling(request=request, pg_svc=pg)
