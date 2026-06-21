from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request, Response, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse

from src.core.dependencies import get_pg_manager, get_seaweed_manager
from src.infra.persistence.postgres import PostgresManager
from src.infra.seaweed import SeaweedManager
from src.modules.profile.handlers.get.user_profile import (
    get_profile_fragment_handler,
    get_user_profile_handler,
)
from src.modules.profile.infra.get.user_meta_repo import pg_resolve_user_meta
from src.modules.profile.infra.get.user_profile_repo import (
    pg_resolve_profile,
    pg_update_avatar,
    pg_update_profile,
)
from src.ui.templates_conf import templates

from ..core.env_conf import auth_stg

ui_router = APIRouter(tags=["UI"])

AVATAR_PUBLIC_URL = "https://laughing-goggles-pjqp4454pr7275q9-80.app.github.dev/media"
# AVATAR_RESIZE = {"width": 140, "height": 140, "mode": "fill"}


def _build_avatar_url(fid: str | None) -> str | None:
    if not fid:
        return None
    return SeaweedManager.build_read_url(
        public_url=AVATAR_PUBLIC_URL,
        fid=fid,
        # resize=AVATAR_RESIZE,
    )


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
        avatar_url = _build_avatar_url(user_meta["fid"])

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
    return await get_user_profile_handler(request, username, pg_manager)


@ui_router.get("/profile/edit/inline", response_class=HTMLResponse)
async def edit_form_fragment(
    request: Request,
    pg_manager: Annotated[PostgresManager, Depends(get_pg_manager)],
):

    return await get_profile_fragment_handler(request, pg_manager, mode="edit_form")


@ui_router.get("/profile/view/inline", response_class=HTMLResponse)
async def view_fragment(
    request: Request,
    pg_manager: Annotated[PostgresManager, Depends(get_pg_manager)],
):

    return await get_profile_fragment_handler(request, pg_manager, mode="view")


@ui_router.patch("/profile/edit/save", response_class=HTMLResponse)
async def save_profile_fragment(
    request: Request,
    nickname: Annotated[str, Form()],
    pg_manager: Annotated[PostgresManager, Depends(get_pg_manager)],
    bio: Annotated[str | None, Form()] = None,
):
    user_id = request.session.get("user_id")
    if not user_id:
        return HTMLResponse(status_code=401, content="<div>Unauthorized</div>")

    nickname = nickname.strip()
    bio = bio.strip() if bio else None

    errors = []
    if not nickname:
        errors.append("Nickname cannot be empty")
    elif len(nickname) > 50:
        errors.append("Nickname is too long (max 50 characters)")

    if bio and len(bio) > 500:
        errors.append("Bio is too long (max 500 characters)")

    if errors:
        return templates.TemplateResponse(
            request=request,
            name="fragments/profile_edit_form.html",
            context={
                "nickname": nickname,
                "bio": bio,
                "errors": errors,
            },
        )

    await pg_update_profile(pg_manager, user_id=user_id, nickname=nickname, bio=bio)

    return templates.TemplateResponse(
        request=request,
        name="fragments/profile_view.html",
        context={
            "nickname": nickname,
            "bio": bio,
        },
    )


@ui_router.post("/profile/avatar/upload", response_class=HTMLResponse)
async def upload_avatar(
    request: Request,
    file: UploadFile,
    pg_manager: Annotated[PostgresManager, Depends(get_pg_manager)],
    seaweed: Annotated[SeaweedManager, Depends(get_seaweed_manager)],
):
    user_id = request.session.get("user_id")
    if not user_id:
        return HTMLResponse(status_code=401)

    if not file.content_type or not file.content_type.startswith("image/"):
        return HTMLResponse(status_code=400, content="Invalid file type")

    assign = await seaweed.assign_fid(count=1)
    if not assign:
        return HTMLResponse(status_code=500, content="Storage error")

    fid = assign["fid"]
    content = await file.read()

    upload_res = await seaweed.upload_blob(
        volume_url=assign["url"],
        fid=fid,
        content=content,
        filename=file.filename or "avatar.jpg",
        mime_type=file.content_type,
    )
    if not upload_res:
        return HTMLResponse(status_code=500, content="Upload failed")

    await pg_update_avatar(pg_manager, user_id=user_id, fid=fid)

    avatar_url = _build_avatar_url(fid)
    return HTMLResponse(
        content=f"""
            <div id="avatar-box" class="avatar-box">
                <img src="{avatar_url}" alt="Avatar">
            </div>

            <div id="avatar-remove-wrapper" hx-swap-oob="true">
                <button hx-delete="/profile/avatar" hx-target="#avatar-box" hx-swap="outerHTML" hx-confirm="Remove avatar?" class="btn-cancel" style="font-size: 12px; padding: 4px 12px;">Remove</button>
            </div>
            """
    )


@ui_router.delete("/profile/avatar", response_class=HTMLResponse)
async def delete_avatar(
    request: Request,
    pg_manager: Annotated[PostgresManager, Depends(get_pg_manager)],
    seaweed: Annotated[SeaweedManager, Depends(get_seaweed_manager)],
):
    user_id = request.session.get("user_id")
    if not user_id:
        return HTMLResponse(status_code=401)

    profile = await pg_resolve_profile(pg_manager, user_id=user_id)

    if profile and profile["fid"]:
        await seaweed.delete_blob(fid=profile["fid"])

    await pg_update_avatar(pg_manager, user_id=user_id, fid=None)

    return HTMLResponse(
        content="""
            <div id="avatar-box" class="avatar-box"></div>
            <div id="avatar-remove-wrapper" hx-swap-oob="true"></div>
            """
    )
