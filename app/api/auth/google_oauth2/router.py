from fastapi import APIRouter, Request, Response
from fastapi.responses import RedirectResponse

from app.api.auth.google_oauth2.client import oauth
from app.api.auth.google_oauth2.service import callback_handling


google_oauth2_router = APIRouter(tags=["google_oauth2"], prefix="/auth/google")


@google_oauth2_router.get("/login")
async def login(request: Request) -> Response:
    redirect_uri = request.url_for('callback')
    google_url = await oauth.google.authorize_redirect(request, redirect_uri)
    url = google_url.headers.get("location")

    return Response(headers={"HX-Redirect": url}) \
        if request.headers.get("HX-Request") else RedirectResponse(url)


@google_oauth2_router.get(path="/callback")
async def callback(request: Request) -> Response:
    return await callback_handling(request=request)


@google_oauth2_router.post("/logout")
async def logout(request: Request) -> Response:
    request.session.clear()

    return Response(headers={"HX-Location": "/"}) \
        if request.headers.get("HX-Request") \
        else RedirectResponse(url="/", status_code=303)
