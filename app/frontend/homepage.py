from fastapi import APIRouter, Request, Response
from fastapi.responses import HTMLResponse

from app.core.templates_conf import templates

homepage_router = APIRouter(tags=["UI"])


@homepage_router.get("/", response_class=HTMLResponse, response_model=None)
async def homepage(request: Request) -> Response:
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "msg": request.query_params.get("msg")}
    )
