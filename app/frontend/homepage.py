from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.core.templates_conf import templates

homepage_router = APIRouter(tags=["UI"])


@homepage_router.get("/", response_class=HTMLResponse)
async def homepage(request: Request):
    msg = request.query_params.get("msg")

    response = templates.TemplateResponse(
        "index.html", {"request": request, "msg": msg}
    )

    return response
