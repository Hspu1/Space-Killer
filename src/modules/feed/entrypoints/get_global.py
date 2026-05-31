from fastapi import (
    APIRouter,
    Depends,
    RedirectResponse,
    Request,
    Response,
)

from src.core.dependencies import rate_limiter

global_feed_router = APIRouter()


@global_feed_router.get(
    path="/global",
    dependencies=[
        Depends(rate_limiter(limit=60, period=60, burst=10, scope="global_feed"))
    ],
)
async def get_global(request: Request) -> Response:
    if request.headers.get("HX-Request"):
        return Response(headers={"HX-Redirect": "/feed/global"})

    return RedirectResponse(url="/feed/global", status_code=307)
