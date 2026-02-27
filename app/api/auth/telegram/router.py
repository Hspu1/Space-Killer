from fastapi import APIRouter, Request, Response, Depends

from app.infra.dependencies import get_pg, rate_limit
from app.infra.postgres.service import PostgresService
from .service import telegram_callback_handling


telegram_router = APIRouter(tags=["telegram"], prefix="/auth/telegram")


@telegram_router.get(path='/callback',
    dependencies=[Depends(rate_limit(
        limit=1, window=2, scope="telegram_callback")
    )]
)
async def telegram_callback(request: Request, pg: PostgresService = Depends(get_pg)) -> Response:
    return await telegram_callback_handling(request=request, pg_svc=pg)
