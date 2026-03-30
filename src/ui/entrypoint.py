from fastapi import APIRouter, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse

from ..core.env_conf import auth_stg
from .templates_conf import templates

ui_router = APIRouter(tags=["UI"])


@ui_router.get("/", response_class=HTMLResponse)
async def homepage(request: Request) -> Response:
    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "bot_id": auth_stg.telegram_bot_id,
            "msg": request.query_params.get("msg"),
        },
    )


@ui_router.get("/welcome", response_class=HTMLResponse)
async def welcome(request: Request) -> Response:
    name, user_id = request.session.get("given_name"), request.session.get("user_id")

    return (
        RedirectResponse(url="/?msg=session_expired")
        if not name or not user_id
        else templates.TemplateResponse(
            "welcome.html", {"request": request, "user": {"name": name}}
        )
    )


@ui_router.get("/map", response_class=HTMLResponse)
async def interactive_map(request: Request) -> Response:
    return templates.TemplateResponse("map.html", {"request": request})
