from fastapi import APIRouter, Request, Response

from .client import github_oauth
from .service import github_callback_handling
from ..common import login, AuthProvider

github_oauth2_router = APIRouter(tags=["github"], prefix="/auth/github")


@github_oauth2_router.get('/login')
async def github_login(request: Request) -> Response:
    return await login(
        request=request,
        provider_name=AuthProvider.GITHUB,
        provider=github_oauth.github
    )


@github_oauth2_router.get(path="/callback")
async def github_callback(request: Request) -> Response:
    return await github_callback_handling(request=request)
