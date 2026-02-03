from fastapi import APIRouter, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse

from ..core import templates

welcome_router = APIRouter(tags=["UI"])


@welcome_router.get("/welcome", response_class=HTMLResponse)
async def welcome(request: Request) -> Response:
    full_name, user_id = request.session.get("given_name"), request.session.get("user_id")

    return RedirectResponse(url="/?msg=session_expired") \
        if not full_name or not user_id \
        else templates.TemplateResponse(
        "welcome.html", {"request": request, "user": {"name": full_name}}
    )
