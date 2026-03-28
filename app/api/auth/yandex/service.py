from time import perf_counter

from authlib.integrations.starlette_client import OAuthError
from fastapi import Request
from fastapi.responses import RedirectResponse
from starlette.status import HTTP_200_OK

from app.infra.postgres.service import PostgresService
from app.utils import log_debug_auth, log_error_auth

from ..common import AuthProvider, get_safe_info, get_user_id
from .client import yandex_oauth


async def yandex_callback_handling(
    request: Request, pg_svc: PostgresService
) -> RedirectResponse:
    start = perf_counter()
    if request.query_params.get("error"):
        return RedirectResponse(url="/?msg=access_denied")

    try:
        start_token = perf_counter()
        token = await yandex_oauth.yandex.authorize_access_token(request)
        log_debug_auth(
            label="token_fetch", start_time=start_token, provider=AuthProvider.YANDEX
        )

        start_api = perf_counter()
        resp = await yandex_oauth.yandex.get("info", token=token)
        log_debug_auth(
            label="api_fetch", start_time=start_api, provider=AuthProvider.YANDEX
        )

        if resp.status_code != HTTP_200_OK:
            log_error_auth(
                provider=AuthProvider.YANDEX,
                message=f"API failed status={resp.status_code} body={resp.text[:50]}",
            )
            return RedirectResponse(url="/?msg=provider_error")

        user_info = resp.json()
        safe_user_info = get_safe_info(user_info=user_info, provider=AuthProvider.YANDEX)
        user_id = await get_user_id(
            pg_svc=pg_svc, user_info=safe_user_info, provider=AuthProvider.YANDEX
        )

        request.session.pop("user_id", None)
        request.session.pop("given_name", None)
        request.session.update({"user_id": user_id, "given_name": safe_user_info.name})

        log_debug_auth(label="total", start_time=start, provider=AuthProvider.YANDEX)
        return RedirectResponse(url="/welcome")

    except (OAuthError, Exception) as e:
        log_error_auth(provider=AuthProvider.YANDEX, message=str(e), exc=e)
        return RedirectResponse(url="/?msg=provider_error")
