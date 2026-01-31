from fastapi import APIRouter, Request, Response

from .client import yandex_oauth
from .service import yandex_callback_handling
from ..common import login, AuthProvider

yandex_oauth2_router = APIRouter(tags=["yandex"], prefix="/auth/yandex")


@yandex_oauth2_router.get('/login')
async def yandex_login(request: Request) -> Response:
    return await login(
        request=request,
        provider_name=AuthProvider.YANDEX,
        provider=yandex_oauth.yandex
    )


@yandex_oauth2_router.get(path="/callback")
async def yandex_callback(request: Request) -> Response:
    return await yandex_callback_handling(request=request)
