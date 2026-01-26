from fastapi import APIRouter, Request, Response
from fastapi.responses import RedirectResponse

from app.api.auth.google_oauth2.client import google_oauth
from app.api.auth.google_oauth2.service import callback_handling


google_oauth2_router = APIRouter(tags=["google_oauth2"], prefix="/auth/google")


@google_oauth2_router.get("/login")
async def google_login(request: Request) -> Response:
    redirect_uri = request.url_for('google_callback')
    google_url = await google_oauth.google.authorize_redirect(request, redirect_uri)
    url = google_url.headers.get("location")

    return Response(headers={"HX-Redirect": url}) \
        if request.headers.get("HX-Request") else RedirectResponse(url)


@google_oauth2_router.get(path="/callback")
async def google_callback(request: Request) -> Response:
    return await callback_handling(request=request)
