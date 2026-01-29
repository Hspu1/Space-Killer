from fastapi import APIRouter, Request, Response
from fastapi.responses import RedirectResponse

from .client import github_oauth
from .service import github_callback_handling

github_oauth2_router = APIRouter(tags=["github"], prefix="/auth/github")


@github_oauth2_router.get('/login')
async def github_login(request: Request) -> Response:
    base_url = f"{request.url.scheme}://{request.url.netloc}"
    if "loca.lt" in base_url:
        base_url = base_url.replace("http://", "https://")
    redirect_uri = f"{base_url}/auth/github/callback"

    github_url = await github_oauth.github.authorize_redirect(request, redirect_uri)
    url = github_url.headers.get("location")

    return Response(headers={"HX-Redirect": url}) \
        if request.headers.get("HX-Request") else RedirectResponse(url)


@github_oauth2_router.get(path="/callback")
async def github_callback(request: Request) -> Response:
    return await github_callback_handling(request=request)
