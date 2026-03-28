from time import perf_counter

from authlib.integrations.starlette_client import OAuthError
from curl_cffi.requests.exceptions import RequestException
from fastapi import HTTPException, Request
from fastapi.responses import RedirectResponse

from app.infra.postgres.service import PostgresService
from app.utils import log_debug_auth, log_error_auth

from ..common import AuthProvider, get_safe_info, get_user_id
from .utils import exchange_so_token, fetch_so_user


async def stackoverflow_callback_handling(
    request: Request, redirect_uri: str, pg_svc: PostgresService
) -> RedirectResponse:
    start = perf_counter()

    if request.query_params.get("error"):
        return RedirectResponse(url="/?msg=access_denied")

    returned_state, returned_code = (
        request.query_params.get("state", None),
        request.query_params.get("code", None),
    )
    if not returned_state or not returned_code:
        return RedirectResponse(url="/?msg=provider_error")

    saved_state = request.session.pop("state", None)
    if returned_state != saved_state:
        log_error_auth(provider=AuthProvider.STACKOVERFLOW, message="CSRF state mismatch")
        return RedirectResponse(url="/?msg=session_expired")

    try:
        start_token = perf_counter()
        token_dict = await exchange_so_token(request=request, redirect_uri=redirect_uri)
        log_debug_auth(
            label="token_exchange",
            start_time=start_token,
            provider=AuthProvider.STACKOVERFLOW,
        )

        start_user_info = perf_counter()
        user_info = await fetch_so_user(access_token=token_dict["access_token"])
        log_debug_auth(
            label="api_fetch",
            start_time=start_user_info,
            provider=AuthProvider.STACKOVERFLOW,
        )

        safe_user_info = get_safe_info(
            user_info=user_info, provider=AuthProvider.STACKOVERFLOW
        )
        user_id = await get_user_id(
            pg_svc=pg_svc, user_info=safe_user_info, provider=AuthProvider.STACKOVERFLOW
        )

        request.session.pop("user_id", None)
        request.session.pop("given_name", None)
        request.session.update({"user_id": user_id, "given_name": safe_user_info.name})

        log_debug_auth(
            label="total", start_time=start, provider=AuthProvider.STACKOVERFLOW
        )
        return RedirectResponse(url="/welcome")

    except HTTPException:
        raise

    except (ValueError, RequestException, OAuthError, Exception) as e:
        log_error_auth(provider=AuthProvider.STACKOVERFLOW, message=str(e), exc=e)
        return RedirectResponse(url="/?msg=provider_error")
