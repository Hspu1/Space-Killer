from fastapi import (
    APIRouter,
    Depends,
    Request,
    Response,
)
from fastapi.responses import RedirectResponse

from src.core.dependencies import rate_limiter

global_feed_router = APIRouter()


@global_feed_router.get(
    path="/global",
    dependencies=[
        Depends(rate_limiter(limit=60, period=60, burst=10, scope="global_feed"))
    ],
)
async def get_global(request: Request) -> Response:
    return RedirectResponse(url="/feed/global", status_code=303)
