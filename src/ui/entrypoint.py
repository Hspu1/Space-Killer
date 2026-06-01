from fastapi import APIRouter, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse

from src.infra.seaweed import SeaweedManager
from src.modules.profile.handlers.get.pg_user_meta import pg_resolve_user_meta

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
    name = request.session.get("given_name")
    user_id = request.session.get("user_id")

    if not name or not user_id:
        return RedirectResponse(url="/?msg=session_expired", status_code=303)

    return templates.TemplateResponse(
        "welcome.html", {"request": request, "user": {"name": name}}
    )


@ui_router.get("/map", response_class=HTMLResponse)
async def interactive_map(request: Request) -> Response:
    return templates.TemplateResponse("map.html", {"request": request})


@ui_router.get("/feed/global", response_class=HTMLResponse)
async def global_feed_page(request: Request) -> Response:
    name = request.session.get("given_name")
    user_id = request.session.get("user_id")

    if not name or not user_id:
        return RedirectResponse(url="/?msg=session_expired", status_code=303)

    user_meta = await pg_resolve_user_meta(
        user_id=user_id,
        pg_manager=request.app.state.pg_manager,
    )

    avatar_url: str | None = None
    if user_meta["fid"]:
        avatar_url = SeaweedManager.build_read_url(
            public_url="https://space-killer.com/media",
            fid=user_meta["fid"],
            resize={"width": 140, "height": 140, "mode": "fill"},
        )

    return templates.TemplateResponse(
        "feed.html",
        {
            "request": request,
            "username": user_meta["username"],
            "avatar_url": avatar_url,
        },
    )
