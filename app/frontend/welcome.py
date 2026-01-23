from fastapi import APIRouter, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse

from app.core.templates_conf import templates

welcome_router = APIRouter(tags=["UI"])


async def get_full_name(request: Request) -> str | None:
    return request.session.get("full_name") \
        if request.session.get("user_id") else None


@welcome_router.get("/welcome", response_class=HTMLResponse, response_model=None)
async def welcome(request: Request) -> Response:
    user = await get_full_name(request=request)
    if not user:
        return RedirectResponse(url="/?msg=session_expired")

    response = templates.TemplateResponse(
        "welcome.html", {"request": request, "user": user}
    )

    return response
