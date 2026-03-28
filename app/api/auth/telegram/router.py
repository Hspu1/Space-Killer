from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response

from app.core.dependencies import get_pg, rate_limiter
from app.infra.postgres.service import PostgresService

from .service import telegram_callback_handling

telegram_router = APIRouter(tags=["telegram"], prefix="/auth/telegram")


@telegram_router.get(
    path="/callback",
    dependencies=[
        Depends(rate_limiter(limit=1, period=7, burst=3, scope="telegram_callback"))
    ],
)
async def telegram_callback(
    request: Request,
    pg: Annotated[PostgresService, Depends(get_pg)],
) -> Response:

    return await telegram_callback_handling(request=request, pg_svc=pg)
