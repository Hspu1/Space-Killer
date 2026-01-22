from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from app.api.auth.google_oauth2.client import oauth
from app.api.auth.google_oauth2.service import callback_handling


google_oauth2_router = APIRouter(tags=["google_oauth2"], prefix="/auth/google")


@google_oauth2_router.get("/login")
async def login(request: Request) -> RedirectResponse:
    redirect_uri = request.url_for('callback')
    return await oauth.google.authorize_redirect(request, redirect_uri)


@google_oauth2_router.get(path="/callback")
async def callback(request: Request) -> RedirectResponse:
    return await callback_handling(request=request)


@google_oauth2_router.get("/logout")
async def logout(request: Request) -> RedirectResponse:
    request.session.clear()
    return RedirectResponse(url="/")
