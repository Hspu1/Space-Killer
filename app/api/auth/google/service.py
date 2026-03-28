from time import perf_counter

from authlib.integrations.starlette_client import OAuthError
from fastapi import Request
from fastapi.responses import RedirectResponse

from app.infra.postgres.service import PostgresService
from app.utils import log_debug_auth, log_error_auth

from ..common import AuthProvider, get_safe_info, get_user_id
from .client import google_oauth


async def google_callback_handling(
    request: Request, pg_svc: PostgresService
) -> RedirectResponse:
    start = perf_counter()
    if request.query_params.get("error"):
        return RedirectResponse(url="/?msg=access_denied")

    try:
        start_token = perf_counter()
        token = await google_oauth.google.authorize_access_token(request)
        log_debug_auth(
            label="token_fetch", start_time=start_token, provider=AuthProvider.GOOGLE
        )

        user_info = token.get("userinfo")
        safe_user_info = get_safe_info(user_info=user_info, provider=AuthProvider.GOOGLE)
        user_id = await get_user_id(
            pg_svc=pg_svc, user_info=safe_user_info, provider=AuthProvider.GOOGLE
        )

        request.session.pop("user_id", None)
        request.session.pop("given_name", None)
        request.session.update({"user_id": user_id, "given_name": safe_user_info.name})

        log_debug_auth(label="total", start_time=start, provider=AuthProvider.GOOGLE)
        return RedirectResponse(url="/welcome")

    except (OAuthError, Exception) as e:
        log_error_auth(provider=AuthProvider.GOOGLE, message=str(e), exc=e)
        return RedirectResponse(url="/?msg=provider_error")
