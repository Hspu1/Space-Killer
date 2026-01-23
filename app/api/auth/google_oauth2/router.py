from fastapi import APIRouter, Request, Response
from fastapi.responses import RedirectResponse

from app.api.auth.google_oauth2.client import oauth
from app.api.auth.google_oauth2.service import callback_handling


google_oauth2_router = APIRouter(tags=["google_oauth2"], prefix="/auth/google")


@google_oauth2_router.get("/login", response_model=None)
async def login(request: Request) -> Response | RedirectResponse:
    redirect_uri = request.url_for('callback')
    google_url = await oauth.google.authorize_redirect(request, redirect_uri)
    url = google_url.headers.get("location")

    return Response(headers={"HX-Redirect": url}) \
        if request.headers.get("HX-Request") else RedirectResponse(url)


@google_oauth2_router.get(path="/callback")
async def callback(request: Request) -> RedirectResponse:
    return await callback_handling(request=request)


@google_oauth2_router.post("/logout", response_model=None)
async def logout(request: Request) -> Response | RedirectResponse:
    request.session.clear()

    if request.headers.get("HX-Request"):
        return Response(headers={"HX-Location": "/"})

    return RedirectResponse(url="/", status_code=303)
