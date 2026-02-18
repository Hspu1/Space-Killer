from fastapi import APIRouter, Request, Response, Depends

from app.infra.dependencies import get_pg
from app.infra.postgres.service import PostgresService
from .service import telegram_callback_handling


telegram_router = APIRouter(tags=["telegram"], prefix="/auth/telegram")


@telegram_router.get(path="/callback")
async def telegram_callback(
        request: Request, pg: PostgresService = Depends(get_pg)
) -> Response:
    return await telegram_callback_handling(request=request, pg_svc=pg)
