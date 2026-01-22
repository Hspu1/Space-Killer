from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.core.templates_conf import templates

welcome_router = APIRouter(tags=["UI"])


async def get_full_name(request: Request) -> dict[str, str] | None:
    # wb redis huh
    user_id = request.session.get("user_id")
    user_name = request.session.get("full_name")

    if user_id and user_name:
        return {"name": user_name}
    return None


@welcome_router.get("/welcome", response_class=HTMLResponse)
async def welcome(request: Request):
    user = await get_full_name(request=request)
    if not user:
        return RedirectResponse(url="/?msg=session_expired")

    response = templates.TemplateResponse(
        "welcome.html", {"request": request, "user": user}
    )

    return response
