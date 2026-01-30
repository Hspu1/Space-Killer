from fastapi import APIRouter, Request, Response
from fastapi.responses import RedirectResponse

from .client import yandex_oauth
from .service import yandex_callback_handling

yandex_oauth2_router = APIRouter(tags=["yandex"], prefix="/auth/yandex")


@yandex_oauth2_router.get('/login')
async def yandex_login(request: Request) -> Response:
    base_url = f"{request.url.scheme}://{request.url.netloc}"
    if "loca.lt" in base_url:
        base_url = base_url.replace("http://", "https://")
    redirect_uri = f"{base_url}/auth/yandex/callback"

    github_url = await yandex_oauth.yandex.authorize_redirect(request, redirect_uri)
    url = github_url.headers.get("location")

    return Response(headers={"HX-Redirect": url}) \
        if request.headers.get("HX-Request") else RedirectResponse(url)


@yandex_oauth2_router.get(path="/callback")
async def yandex_callback(request: Request) -> Response:
    return await yandex_callback_handling(request=request)
