from fastapi import APIRouter, Request, Response
from app.api.auth.telegram.service import telegram_callback_handling

telegram_router = APIRouter(tags=["telegram_auth"], prefix="/auth/telegram")


@telegram_router.get(path="/callback")
async def telegram_callback(request: Request) -> Response:
    return await telegram_callback_handling(request=request)
