from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse

from src.core.dependencies import get_pg_manager
from src.infra.persistence.postgres import PostgresManager
from src.infra.seaweed import SeaweedManager
from src.modules.profile.handlers.get.user_profile import (
    get_profile_fragment_handler,
    get_user_profile_handler,
)
from src.modules.profile.infra.get.user_meta_repo import pg_resolve_user_meta

from ..core.env_conf import auth_stg
from .templates_conf import templates

ui_router = APIRouter(tags=["UI"])


@ui_router.get("/", response_class=HTMLResponse)
async def homepage(request: Request) -> Response:
    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={
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
        request=request, name="welcome.html", context={"user": {"name": name}}
    )


@ui_router.get("/map", response_class=HTMLResponse)
async def interactive_map(request: Request) -> Response:
    return templates.TemplateResponse(request=request, name="map.html")


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
            public_url="https://space-killer.com",
            fid=user_meta["fid"],
            resize={"width": 140, "height": 140, "mode": "fill"},
        )

    return templates.TemplateResponse(
        request=request,
        name="feed.html",
        context={
            "username": user_meta["username"],
            "avatar_url": avatar_url,
        },
    )


@ui_router.get("/profile/get/{username}", response_class=HTMLResponse)
async def profile_page(
    request: Request,
    username: str,
    pg_manager: Annotated[PostgresManager, Depends(get_pg_manager)],
):
    return await get_user_profile_handler(
        request=request,
        username=username,
        pg_manager=pg_manager,
        editing=False,
    )


@ui_router.get("/profile/edit/inline", response_class=HTMLResponse)
async def edit_form_fragment(
    request: Request,
    pg_manager: Annotated[PostgresManager, Depends(get_pg_manager)],
) -> Response:
    if not request.session.get("user_id"):
        return HTMLResponse(status_code=401, content="<div>Unauthorized</div>")

    return await get_profile_fragment_handler(
        request=request,
        pg_manager=pg_manager,
        mode="edit_form",
    )


@ui_router.get("/profile/view/inline", response_class=HTMLResponse)
async def view_fragment(
    request: Request,
    pg_manager: Annotated[PostgresManager, Depends(get_pg_manager)],
) -> Response:
    if not request.session.get("user_id"):
        return HTMLResponse(status_code=401, content="<div>Unauthorized</div>")

    return await get_profile_fragment_handler(
        request=request,
        pg_manager=pg_manager,
        mode="view",
    )
