from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response

from src.core.dependencies import get_pg_manager, rate_limiter
from src.infra.persistence.postgres import PostgresManager

from ..third_party_apps.telegram import telegram_callback_handler

telegram_router = APIRouter(tags=["telegram"], prefix="/auth/telegram")


@telegram_router.get(
    path="/callback",
    dependencies=[
        Depends(rate_limiter(limit=1, period=7, burst=3, scope="telegram_callback"))
    ],
)
async def telegram_callback(
    request: Request,
    pg_manager: Annotated[PostgresManager, Depends(get_pg_manager)],
) -> Response:

    return await telegram_callback_handler(request=request, pg_manager=pg_manager)
