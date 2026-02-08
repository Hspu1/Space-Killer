from fastapi import APIRouter, Request, Response
from fastapi.responses import HTMLResponse

from ..core.env_conf import auth_stg
from ..core.templates_conf import templates

homepage_router = APIRouter(tags=["UI"])


@homepage_router.get("/", response_class=HTMLResponse)
async def homepage(request: Request) -> Response:
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request, "bot_id": auth_stg.telegram_bot_id,
            "msg": request.query_params.get("msg")
        }
    )
