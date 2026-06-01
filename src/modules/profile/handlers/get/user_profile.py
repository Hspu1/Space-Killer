from fastapi import HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from src.infra.persistence.postgres import PostgresManager
from src.infra.seaweed import SeaweedManager
from src.modules.profile.infra.get.user_profile_repo import pg_resolve_profile
from src.ui.templates_conf import templates


async def get_user_profile_handler(
    request: Request,
    username: str,
    pg_manager: PostgresManager,
) -> HTMLResponse | RedirectResponse:
    current_user_id = request.session.get("user_id")
    if not current_user_id:
        return RedirectResponse(url="/?msg=session_expired", status_code=303)

    profile = await pg_resolve_profile(pg_manager, username=username)
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")

    is_own = profile["user_id"] == current_user_id
    avatar_url = None
    if profile["fid"]:
        avatar_url = SeaweedManager.build_read_url(
            public_url="https://space-killer.com",
            fid=profile["fid"],
            resize={"width": 140, "height": 140, "mode": "fill"},
        )

    return templates.TemplateResponse(
        request=request,
        name="profile.html",
        context={
            "username": profile["username"],
            "nickname": profile["nickname"],
            "bio": profile["bio"],
            "is_own_profile": is_own,
            "avatar_url": avatar_url,
        },
    )


async def get_profile_fragment_handler(
    request: Request,
    pg_manager: PostgresManager,
    mode: str,
) -> HTMLResponse:
    user_id = request.session.get("user_id")
    if not user_id:
        return HTMLResponse(status_code=401, content="<div>Unauthorized</div>")

    profile = await pg_resolve_profile(pg_manager, user_id=user_id)
    if not profile:
        return HTMLResponse(status_code=404, content="<div>Profile not found</div>")

    template = (
        "fragments/profile_edit_form.html"
        if mode == "edit_form"
        else "fragments/profile_view.html"
    )

    return templates.TemplateResponse(
        request=request,
        name=template,
        context={
            "username": profile["username"],
            "nickname": profile["nickname"],
            "bio": profile["bio"],
        },
    )
